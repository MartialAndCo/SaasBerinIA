"""Handler pour les tâches du bot Telegram"""
import logging
from datetime import datetime, timedelta
from telegram.constants import ParseMode

from services.api_client import BeriniaAPIClient
from utils.keyboards import get_back_keyboard, get_tasks_menu_keyboard
from utils.keyboards_advanced_tasks import (
    get_task_type_selection_keyboard, get_advanced_agents_selection_keyboard,
    get_advanced_agent_actions_keyboard, get_action_parameters_keyboard,
    get_condition_selection_keyboard, get_task_type_configuration_keyboard,
    get_final_task_confirmation_keyboard
)
from utils.formatters import format_scheduled_tasks, format_error, format_loading, format_success

# Import des modules core avec fallback simple
try:
    from core.safe_formatter import safe_formatter
except ImportError:
    class SafeFormatter:
        def safe_format_html(self, template, **kwargs):
            try:
                return template.format(**kwargs)
            except:
                return template
    safe_formatter = SafeFormatter()

try:
    from core.error_handler import error_handler
except ImportError:
    class ErrorHandler:
        def log_callback_error(self, callback_data, error):
            logger.error(f"Erreur callback {callback_data}: {error}")
    error_handler = ErrorHandler()

try:
    from core.callback_manager import callback_manager
except ImportError:
    callback_manager = None

# Session manager temporaire sans threading (évite deadlock asyncio)
class SimpleSessionManager:
    def __init__(self):
        self.sessions = {}
    
    def set_session_data(self, user_id, key, value):
        if user_id not in self.sessions:
            self.sessions[user_id] = {}
        self.sessions[user_id][key] = value
    
    def get_session_data(self, user_id, key, default=None):
        if user_id not in self.sessions:
            return default
        return self.sessions[user_id].get(key, default)
    
    def clear_session(self, user_id):
        if user_id in self.sessions:
            del self.sessions[user_id]
    
    def get_session(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {}
        return self.sessions[user_id]

session_manager = SimpleSessionManager()

logger = logging.getLogger(__name__)

class TasksHandler:
    """Gestionnaire des tâches"""
    
    def __init__(self):
        self.api_client = BeriniaAPIClient()
    
    async def handle_callback(self, query, callback_data: str):
        """Gère les callbacks des tâches"""
        logger.info(f"TasksHandler: callback reçu = {callback_data}")
        # Callback data simples (legacy)
        if callback_data == "tasks_main":
            await self._show_tasks_menu(query)
        elif callback_data == "tasks_list":
            await self._show_tasks_list(query)
        elif callback_data == "tasks_create":
            await self._show_tasks_create_advanced(query)
        elif callback_data == "tasks_delete":
            await self._show_tasks_delete_menu(query)
        elif callback_data.startswith("task_type_"):
            task_type = callback_data.replace("task_type_", "")
            await self._handle_task_type_selection(query, task_type)
        elif callback_data == "create_final_task":
            await self._create_final_advanced_task(query)
        elif callback_data.startswith("delete_task_"):
            task_id = callback_data.replace("delete_task_", "")
            await self._delete_task(query, task_id)
        elif callback_data.startswith("deletetask"):
            task_id = callback_data.replace("deletetask", "")
            await self._delete_task(query, task_id)
        else:
            # Essayer de résoudre via callback_manager
            try:
                global callback_manager
                if callback_manager is None:
                    import sys
                    import os
                    try:
                        from core.callback_manager import callback_manager
                    except ImportError:
                        # Ajouter le répertoire telegram_bot au path si nécessaire
                        telegram_bot_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        if telegram_bot_dir not in sys.path:
                            sys.path.insert(0, telegram_bot_dir)
                        from core.callback_manager import callback_manager
                
                resolved_data = callback_manager.resolve(callback_data)
            except Exception as e:
                logger.warning(f"Erreur import callback_manager: {e}")
                resolved_data = None
            
            if resolved_data:
                action = resolved_data.get('action')
                
                if action == "select_agent_for_task":
                    await self._handle_advanced_agent_selection_new(query, resolved_data)
                elif action == "select_action_for_task":
                    await self._handle_advanced_action_selection_new(query, resolved_data)
                elif action == "param_action":
                    await self._handle_action_parameters_new(query, resolved_data)
                elif action == "condition_selection":
                    await self._handle_condition_selection_new(query, resolved_data)
                elif action == "task_config":
                    await self._handle_task_configuration_new(query, resolved_data)
                else:
                    # Fallback pour les anciens callback_data
                    await self._handle_legacy_callbacks(query, callback_data)
            else:
                # Fallback pour les anciens callback_data
                await self._handle_legacy_callbacks(query, callback_data)
    
    async def _handle_legacy_callbacks(self, query, callback_data: str):
        """Gère les anciens callback_data non résolus"""
        try:
            if callback_data.startswith("select_agent_for_task_"):
                await self._handle_advanced_agent_selection(query, callback_data)
            elif callback_data.startswith("select_action_for_task_"):
                await self._handle_advanced_action_selection(query, callback_data)
            elif callback_data.startswith("param_"):
                await self._handle_action_parameters(query, callback_data)
            elif callback_data.startswith("condition_"):
                await self._handle_condition_selection(query, callback_data)
            elif callback_data.startswith("config_"):
                await self._handle_task_configuration(query, callback_data)
            else:
                text = safe_formatter.safe_format_html(
                    "❌ <b>Action non reconnue</b>\n\n<i>Callback: {callback_data}</i>",
                    callback_data=callback_data
                )
                await query.edit_message_text(
                    text=text,
                    reply_markup=get_back_keyboard("tasks_main"),
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            error_handler.log_callback_error(callback_data, e)
            raise
    
    async def _show_tasks_menu(self, query):
        """Affiche le menu principal des tâches"""
        text = """📆 **Gestion des tâches planifiées**

Gérez toutes les tâches automatisées du système BerinIA.

**Fonctionnalités disponibles :**
• 📋 Voir toutes les tâches existantes
• ➕ Créer une nouvelle tâche avancée
• 🗑 Supprimer une tâche
• ▶️ Exécuter une tâche immédiatement

Choisissez une action :"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_tasks_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_tasks_list(self, query):
        """Affiche la liste des tâches"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        tasks = self.api_client.get_scheduled_tasks()
        
        if tasks:
            text = format_scheduled_tasks(tasks)
        else:
            text = "ℹ️ Aucune tâche planifiée trouvée"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("tasks_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_tasks_delete_menu(self, query):
        """Affiche le menu de suppression des tâches"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        tasks = self.api_client.get_scheduled_tasks()
        
        if not tasks:
            text = "ℹ️ Aucune tâche à supprimer"
            await query.edit_message_text(
                text=text,
                reply_markup=get_back_keyboard("tasks_main"),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        text = "🗑️ **Supprimer une tâche**\n\nSélectionnez la tâche à supprimer :\n\n"
        
        # Créer des boutons pour chaque tâche
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = []
        for task in tasks[:10]:  # Limiter à 10 tâches
            task_id = task.get('task_id', task.get('id', 'unknown'))
            task_name = task.get('name', f'Tâche {task_id}')
            agent = task.get('agent', 'Agent inconnu')
            status = task.get('status', 'unknown')
            
            # Emoji selon le statut
            if status == 'pending':
                status_emoji = '⏳'
            elif status == 'running':
                status_emoji = '🟡'
            elif status == 'completed':
                status_emoji = '✅'
            elif status == 'failed':
                status_emoji = '❌'
            else:
                status_emoji = '❓'
            
            button_text = f"{status_emoji} {task_name} (ID: {task_id})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_task_{task_id}")])
            
            text += f"{status_emoji} **{task_name}** (ID: {task_id})\n"
            text += f"   🤖 Agent: {agent}\n\n"
        
        # Bouton retour
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="tasks_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_tasks_create_advanced(self, query):
        """Affiche la sélection du type de tâche (workflow avancé)"""
        user_id = query.from_user.id
        session_manager.clear_session(user_id)  # Nettoyer l'ancienne session
        
        text = safe_formatter.safe_format_html(
            """🆕 <b>Créer une nouvelle tâche</b>

Sélectionnez le type de tâche que vous souhaitez créer :

🔧 <b>SYSTEM_RECURRING</b> - Tâche système permanente
💼 <b>BUSINESS_RECURRING</b> - Tâche temporaire avec fin automatique  
⚡ <b>ONE_TIME</b> - Exécution unique puis suppression
❓ <b>CONDITIONAL</b> - Exécution selon condition prédéfinie"""
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_task_type_selection_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_task_type_selection(self, query, task_type: str):
        """Gère la sélection du type de tâche"""
        logger.info(f"_handle_task_type_selection: task_type = {task_type}")
        try:
            user_id = query.from_user.id
            logger.info(f"user_id = {user_id}")
        
            # Utiliser le session_manager au lieu de l'état global
            session_manager.set_session_data(user_id, 'task_type', task_type)
            logger.info(f"Session data saved for user {user_id}")
            
            type_descriptions = {
                "system_recurring": "Tâche système permanente - Ne sera jamais supprimée automatiquement",
                "business_recurring": "Tâche business temporaire - Avec date de fin et nettoyage automatique",
                "one_time": "Tâche ponctuelle - Exécutée une fois puis supprimée",
                "conditional": "Tâche conditionnelle - Exécutée selon une condition prédéfinie"
            }
            
            text = safe_formatter.safe_format_html(
                """🆕 <b>Type de tâche sélectionné</b>

<b>Type :</b> {task_type}
<b>Description :</b> {description}

Sélectionnez maintenant l'agent qui exécutera cette tâche :""",
                task_type=task_type.upper(),
                description=type_descriptions.get(task_type, 'Description non disponible')
            )
            logger.info(f"Text formatted successfully")
            
            logger.info(f"Fetching agents...")
            agents = self.api_client.get_agents_status()
            logger.info(f"Agents fetched: {len(agents) if agents else 0}")
            
            if agents:
                logger.info(f"Generating keyboard...")
                keyboard = get_advanced_agents_selection_keyboard(agents, task_type)
                logger.info(f"Keyboard generated with {len(keyboard.inline_keyboard)} lines")
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Message sent successfully")
            else:
                logger.warning(f"No agents found")
                await query.edit_message_text(
                    text=format_error("Impossible de récupérer la liste des agents"),
                    reply_markup=get_back_keyboard("tasks_create"),
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            logger.error(f"❌ ERREUR dans _handle_task_type_selection: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            await query.edit_message_text(
                text=format_error(f"Erreur : {str(e)}"),
                reply_markup=get_back_keyboard("tasks_create"),
                parse_mode=ParseMode.HTML
            )
    
    async def _handle_advanced_agent_selection_new(self, query, resolved_data: dict):
        """Nouvelle méthode pour gérer la sélection d'agent avec callback_manager"""
        user_id = query.from_user.id
        task_type = resolved_data.get('task_type')
        agent_name = resolved_data.get('agent_name')
        
        # Sauvegarder dans la session
        session_manager.set_session_data(user_id, 'agent_name', agent_name)
        
        current_task_type = session_manager.get_session_data(user_id, 'task_type', task_type)
        
        text = safe_formatter.safe_format_html(
            """🤖 <b>Agent sélectionné</b>

<b>Type de tâche :</b> {task_type}
<b>Agent :</b> {agent_name}

Choisissez l'action que cet agent doit exécuter :""",
            task_type=current_task_type.upper(),
            agent_name=agent_name
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_advanced_agent_actions_keyboard(agent_name, current_task_type),
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_advanced_action_selection_new(self, query, resolved_data: dict):
        """Nouvelle méthode pour gérer la sélection d'action avec callback_manager"""
        user_id = query.from_user.id
        task_type = resolved_data.get('task_type')
        agent_name = resolved_data.get('agent_name')
        action_code = resolved_data.get('action_code')
        
        # Sauvegarder dans la session
        session_manager.set_session_data(user_id, 'action', action_code)
        
        current_task_type = session_manager.get_session_data(user_id, 'task_type', task_type)
        current_agent = session_manager.get_session_data(user_id, 'agent_name', agent_name)
        
        text = safe_formatter.safe_format_html(
            """⚙️ <b>Action sélectionnée</b>

<b>Type :</b> {task_type}
<b>Agent :</b> {agent_name}
<b>Action :</b> {action}

Configurez les paramètres spécifiques à cette action :""",
            task_type=current_task_type.upper(),
            agent_name=current_agent,
            action=action_code
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_action_parameters_keyboard(current_agent, action_code, current_task_type),
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_action_parameters_new(self, query, resolved_data: dict):
        """Nouvelle méthode pour gérer les paramètres d'action avec callback_manager"""
        user_id = query.from_user.id
        task_type = resolved_data.get('task_type')
        agent_name = resolved_data.get('agent_name')
        action_code = resolved_data.get('action_code')
        param_type = resolved_data.get('param_type')
        
        # Mapper les types de paramètres
        param_descriptions = {
            "qualified_leads": "Tous les leads qualifiés",
            "specific_lead": "Lead spécifique (à configurer)",
            "campaign_leads": "Leads d'une campagne (à configurer)",
            "niche_leads": "Leads d'une niche (à configurer)",
            "no_params": "Aucun paramètre spécifique",
            "select_niche": "Sélection de niche",
            "select_city": "Sélection de ville",
            "campaign_reminder": "Rappel par campagne",
            "24h_reminder": "Rappel après 24h",
            "48h_reminder": "Rappel après 48h"
        }
        
        # Sauvegarder dans la session
        session_manager.set_session_data(user_id, 'target', param_type)
        
        # Récupérer les données actuelles de la session
        current_task_type = session_manager.get_session_data(user_id, 'task_type', task_type)
        current_agent = session_manager.get_session_data(user_id, 'agent_name', agent_name)
        current_action = session_manager.get_session_data(user_id, 'action', action_code)
        
        param_summary = param_descriptions.get(param_type, f"Paramètre : {param_type}")
        
        # Si c'est une tâche conditionnelle, aller aux conditions
        if current_task_type == "conditional":
            text = safe_formatter.safe_format_html(
                """❓ <b>Tâche conditionnelle</b>

<b>Paramètres :</b> {param_summary}

Sélectionnez la condition d'exécution :""",
                param_summary=param_summary
            )
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_condition_selection_keyboard(current_task_type, current_agent, current_action),
                parse_mode=ParseMode.HTML
            )
        else:
            text = safe_formatter.safe_format_html(
                """🔧 <b>Configuration de la tâche</b>

<b>Type :</b> {task_type}
<b>Agent :</b> {agent_name}
<b>Action :</b> {action}
<b>Paramètres :</b> {param_summary}

Configurez les paramètres spécifiques au type de tâche :""",
                task_type=current_task_type.upper(),
                agent_name=current_agent,
                action=current_action,
                param_summary=param_summary
            )
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_task_type_configuration_keyboard(current_task_type, current_agent, current_action, param_type),
                parse_mode=ParseMode.HTML
            )
    
    async def _handle_condition_selection_new(self, query, resolved_data: dict):
        """Nouvelle méthode pour gérer la sélection de condition avec callback_manager"""
        user_id = query.from_user.id
        task_type = resolved_data.get('task_type')
        agent_name = resolved_data.get('agent_name')
        action_code = resolved_data.get('action_code')
        condition = resolved_data.get('condition')
        
        # Sauvegarder dans la session
        session_manager.set_session_data(user_id, 'condition', condition)
        
        condition_descriptions = {
            "no_response_24h": "Aucune réponse après 24h",
            "no_response_48h": "Aucune réponse après 48h",
            "low_performance": "Performance campagne faible",
            "no_leads_today": "Aucun nouveau lead aujourd'hui",
            "system_idle": "Système inactif depuis 1h"
        }
        
        text = safe_formatter.safe_format_html(
            """❓ <b>Condition sélectionnée</b>

<b>Condition :</b> {condition_desc}

Configurez maintenant la fréquence de vérification :""",
            condition_desc=condition_descriptions.get(condition, condition)
        )
        
        # Récupérer les données actuelles de la session
        current_task_type = session_manager.get_session_data(user_id, 'task_type', task_type)
        current_agent = session_manager.get_session_data(user_id, 'agent_name', agent_name)
        current_action = session_manager.get_session_data(user_id, 'action', action_code)
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_task_type_configuration_keyboard(current_task_type, current_agent, current_action, "configured"),
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_task_configuration_new(self, query, resolved_data: dict):
        """Nouvelle méthode pour gérer la configuration de tâche avec callback_manager"""
        user_id = query.from_user.id
        task_type = resolved_data.get('task_type')
        agent_name = resolved_data.get('agent_name')
        action_code = resolved_data.get('action_code')
        param_type = resolved_data.get('param_type')
        config_value = resolved_data.get('config_value')
        
        # Récupérer les données actuelles de la session
        current_task_type = session_manager.get_session_data(user_id, 'task_type', task_type)
        current_agent = session_manager.get_session_data(user_id, 'agent_name', agent_name)
        current_action = session_manager.get_session_data(user_id, 'action', action_code)
        current_target = session_manager.get_session_data(user_id, 'target', param_type)
        
        # Traiter la configuration selon le type
        if config_value.isdigit():
            interval = int(config_value)
            session_manager.set_session_data(user_id, 'recurrence_interval', interval)
            session_manager.set_session_data(user_id, 'is_recurring', True)
            
            interval_text = {
                3600: "Toutes les heures",
                86400: "Quotidien",
                604800: "Hebdomadaire"
            }.get(interval, f"Toutes les {interval} secondes")
            
            schedule_info = f"Récurrence : {interval_text}"
            
        elif config_value in ["now", "1h", "24h"]:
            session_manager.set_session_data(user_id, 'is_recurring', False)
            session_manager.set_session_data(user_id, 'recurrence_interval', None)
            
            if config_value == "now":
                session_manager.set_session_data(user_id, 'scheduled_time', datetime.now().isoformat())
                schedule_info = "Exécution immédiate"
            elif config_value == "1h":
                session_manager.set_session_data(user_id, 'scheduled_time', (datetime.now() + timedelta(hours=1)).isoformat())
                schedule_info = "Exécution dans 1 heure"
            elif config_value == "24h":
                session_manager.set_session_data(user_id, 'scheduled_time', (datetime.now() + timedelta(days=1)).isoformat())
                schedule_info = "Exécution dans 24 heures"
                
        elif config_value.startswith("check_"):
            check_interval = int(config_value.replace("check_", ""))
            session_manager.set_session_data(user_id, 'check_interval', check_interval)
            session_manager.set_session_data(user_id, 'is_recurring', True)
            session_manager.set_session_data(user_id, 'recurrence_interval', check_interval)
            
            check_text = {
                3600: "Vérification toutes les heures",
                21600: "Vérification toutes les 6 heures"
            }.get(check_interval, f"Vérification toutes les {check_interval} secondes")
            
            schedule_info = check_text
        else:
            schedule_info = f"Configuration : {config_value}"
        
        # Préparer le résumé
        current_condition = session_manager.get_session_data(user_id, 'condition')
        
        text = safe_formatter.safe_format_html(
            """✅ <b>Résumé de la tâche à créer</b>

🔧 <b>Type :</b> {task_type}
🤖 <b>Agent :</b> {agent_name}
⚙️ <b>Action :</b> {action}
🎯 <b>Cible :</b> {target}
⏰ <b>Planification :</b> {schedule_info}""",
            task_type=current_task_type.upper(),
            agent_name=current_agent,
            action=current_action,
            target=current_target or 'none',
            schedule_info=schedule_info
        )
        
        if current_condition:
            text += safe_formatter.safe_format_html(
                "\n❓ <b>Condition :</b> {condition}",
                condition=current_condition
            )
        
        text += "\n\nConfirmez-vous la création de cette tâche ?"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_final_task_confirmation_keyboard({}),
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_advanced_agent_selection(self, query, callback_data: str):
        """Gère la sélection d'agent dans le workflow avancé (legacy)"""
        user_id = query.from_user.id
        parts = callback_data.replace("select_agent_for_task_", "").split("_", 1)
        
        if len(parts) >= 2:
            task_type, agent_name = parts[0], parts[1]
            
            # Utiliser session_manager
            session_manager.set_session_data(user_id, 'agent_name', agent_name)
            session_manager.set_session_data(user_id, 'task_type', task_type)
            
            text = f"""🤖 **Agent sélectionné**

**Type de tâche :** {task_type.upper()}
**Agent :** {agent_name}

Choisissez l'action que cet agent doit exécuter :"""
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_advanced_agent_actions_keyboard(agent_name, task_type),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_advanced_action_selection(self, query, callback_data: str):
        """Gère la sélection d'action dans le workflow avancé (legacy)"""
        user_id = query.from_user.id
        parts = callback_data.replace("select_action_for_task_", "").split("_")
        
        if len(parts) >= 3:
            task_type, agent_name, action = parts[0], parts[1], parts[2]
            
            # Utiliser session_manager
            session_manager.set_session_data(user_id, 'action', action)
            
            text = f"""⚙️ **Action sélectionnée**

**Type :** {task_type.upper()}
**Agent :** {agent_name}
**Action :** {action}

Configurez les paramètres spécifiques à cette action :"""
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_action_parameters_keyboard(agent_name, action, task_type),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_action_parameters(self, query, callback_data: str):
        """Gère la configuration des paramètres d'action (legacy)"""
        text = "Cette fonctionnalité utilise l'ancien système. Veuillez recommencer."
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("tasks_create"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_condition_selection(self, query, callback_data: str):
        """Gère la sélection de condition pour tâches conditionnelles (legacy)"""
        text = "Cette fonctionnalité utilise l'ancien système. Veuillez recommencer."
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("tasks_create"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_task_configuration(self, query, callback_data: str):
        """Gère la configuration finale selon le type de tâche (legacy)"""
        text = "Cette fonctionnalité utilise l'ancien système. Veuillez recommencer."
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("tasks_create"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _create_final_advanced_task(self, query):
        """Crée la tâche finale avec tous les paramètres avancés"""
        user_id = query.from_user.id
        
        # Récupérer les données de session
        session = session_manager.get_session(user_id)
        
        if not session:
            await query.edit_message_text(
                text=format_error("Session expirée. Veuillez recommencer."),
                reply_markup=get_back_keyboard("tasks_create"),
                parse_mode=ParseMode.HTML
            )
            return
        
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        try:
            # Construire les données de la tâche
            task_data = {
                "name": f"{session.get('action', 'action')}_{session.get('agent_name', 'agent')}",
                "agent": session.get('agent_name'),
                "action": session.get('action'),
                "type": session.get('task_type'),
                "target": session.get('target', 'all'),
                "is_recurring": session.get('is_recurring', False),
                "params": {}
            }
            
            # Ajouter les paramètres selon le type
            if session.get('recurrence_interval'):
                task_data['recurrence_interval'] = session.get('recurrence_interval')
            
            if session.get('scheduled_time'):
                task_data['scheduled_time'] = session.get('scheduled_time')
            
            if session.get('condition'):
                task_data['condition'] = session.get('condition')
            
            if session.get('check_interval'):
                task_data['check_interval'] = session.get('check_interval')
            
            # Mapping des agents vers leurs IDs
            agent_id_mapping = {
                'MessagingAgent': 1,
                'ProspectionSupervisor': 2,
                'PivotStrategyAgent': 3,
                'TaskWatchdogAgent': 4,
                'ScrapingSupervisorAgent': 5,
                'ResponseInterpreterAgent': 6,
                'FollowUpAgent': 7,
                'CleanerAgent': 8,
                'DatabaseQueryAgent': 9,
                'NicheExplorerAgent': 10,
                'OverseerAgent': 11,
                'ScraperAgent': 12,
                'AgentSchedulerAgent': 13
            }
            
            # Récupérer l'ID correct pour l'agent
            agent_id = agent_id_mapping.get(task_data['agent'], 1)
            
            # Appeler l'API pour créer la tâche avec la bonne signature
            result = self.api_client.create_advanced_task(
                task_type=task_data['type'],
                agent_id=agent_id,  # ID correct selon l'agent sélectionné
                action=task_data['action'],
                parameters={
                    'agent_name': task_data['agent'],
                    'target': task_data['target'],
                    **task_data.get('params', {})
                },
                priority=3,
                scheduled_time=task_data.get('scheduled_time'),
                is_recurring=task_data.get('is_recurring', False),
                recurrence_interval=task_data.get('recurrence_interval'),
                condition=task_data.get('condition'),
                auto_cleanup=True,
                cleanup_after_days=30
            )
            
            if result and result.get('status') == 'success':
                text = f"""✅ **Tâche créée avec succès !**

**Type :** {task_data['type'].upper()}
**ID :** {result.get('task_id', 'N/A')}
**Agent :** {session.get('agent_name')}
**Action :** {session.get('action')}"""
            else:
                text = "❌ **Erreur** - Impossible de créer la tâche avancée"
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_back_keyboard("tasks_main"),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Nettoyer la session
            session_manager.clear_session(user_id)
            
        except Exception as e:
            logger.error(f"Erreur création tâche avancée: {e}")
            await query.edit_message_text(
                text=format_error(f"Erreur lors de la création : {str(e)}"),
                reply_markup=get_back_keyboard("tasks_main"),
                parse_mode=ParseMode.HTML
            )
    
    async def _delete_task(self, query, task_id: str):
        """Supprime une tâche"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        try:
            # Appeler l'API pour supprimer la tâche
            result = self.api_client.delete_task(task_id)
            
            if result and result.get('status') == 'success':
                text = f"✅ **Tâche supprimée avec succès !**\n\n**ID :** {task_id}"
            else:
                text = f"❌ **Erreur** - Impossible de supprimer la tâche {task_id}"
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_back_keyboard("tasks_main"),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Erreur suppression tâche: {e}")
            await query.edit_message_text(
                text=format_error(f"Erreur lors de la suppression : {str(e)}"),
                reply_markup=get_back_keyboard("tasks_main"),
                parse_mode=ParseMode.HTML
            )

"""Handler pour le système du bot Telegram"""
import logging
from datetime import datetime, timedelta
from telegram.constants import ParseMode

from services.api_client import BeriniaAPIClient
from utils.keyboards import (
    get_back_keyboard, get_confirmation_keyboard, get_tasks_menu_keyboard,
    get_tasks_list_keyboard, get_task_details_keyboard, get_task_confirmation_keyboard,
    get_agents_selection_keyboard, get_agent_actions_keyboard, get_task_priority_keyboard,
    get_task_schedule_keyboard, get_task_final_confirmation_keyboard,
    get_tasks_to_delete_keyboard, get_tasks_to_execute_keyboard
)
from utils.keyboards_advanced_tasks import (
    get_task_type_selection_keyboard, get_advanced_agents_selection_keyboard,
    get_advanced_agent_actions_keyboard, get_action_parameters_keyboard,
    get_condition_selection_keyboard, get_task_type_configuration_keyboard,
    get_final_task_confirmation_keyboard
)
from utils.formatters import (
    format_agents_status, format_system_logs, format_scheduled_tasks, format_services_status, 
    format_error, format_loading, format_success, format_task_details, format_agent_capabilities
)

logger = logging.getLogger(__name__)

# État de création de tâche global (simplifié pour cette démo)
task_creation_state = {}

class SystemHandler:
    """Gestionnaire du système"""
    
    def __init__(self):
        self.api_client = BeriniaAPIClient()
    
    async def handle_callback(self, query, callback_data: str):
        """Gère les callbacks du système"""
        try:
            if callback_data == "system_agents":
                await self._show_agents_status(query)
            elif callback_data == "system_tasks":
                await self._show_tasks_menu(query)
            elif callback_data == "system_security":
                await self._show_security_logs(query)
            elif callback_data == "system_logs":
                await self._show_system_logs(query)
            elif callback_data == "system_restart":
                await self._show_restart_confirmation(query)
            elif callback_data == "system_services":
                await self._show_services_status(query)
            elif callback_data.startswith("confirm_restart_"):
                await self._restart_system(query)
            elif callback_data.startswith("agent_details_"):
                agent_name = callback_data.replace("agent_details_", "")
                await self._show_agent_details(query, agent_name)
            
            # === GESTION DES TÂCHES ===
            elif callback_data == "tasks_list":
                await self._show_tasks_list(query)
            elif callback_data == "tasks_create":
                await self._show_tasks_create_advanced(query)
            elif callback_data == "tasks_delete":
                await self._show_tasks_delete(query)
            elif callback_data == "tasks_execute":
                await self._show_tasks_execute(query)
            elif callback_data == "tasks_capabilities":
                await self._show_agent_capabilities(query)
            
            # === NOUVEAU WORKFLOW CRÉATION TÂCHES AVANCÉES ===
            elif callback_data.startswith("task_type_"):
                task_type = callback_data.replace("task_type_", "")
                await self._handle_task_type_selection(query, task_type)
            elif callback_data.startswith("select_agent_for_task_"):
                await self._handle_advanced_agent_selection(query, callback_data)
            elif callback_data.startswith("select_action_for_task_"):
                await self._handle_advanced_action_selection(query, callback_data)
            elif callback_data.startswith("param_"):
                await self._handle_action_parameters(query, callback_data)
            elif callback_data.startswith("condition_"):
                await self._handle_condition_selection(query, callback_data)
            elif callback_data.startswith("config_"):
                await self._handle_task_configuration(query, callback_data)
            elif callback_data == "create_final_task":
                await self._create_final_advanced_task(query)
            elif callback_data.startswith("task_details_"):
                task_id = callback_data.replace("task_details_", "")
                await self._show_task_details(query, task_id)
            elif callback_data.startswith("task_execute_"):
                task_id = callback_data.replace("task_execute_", "")
                await self._confirm_task_action(query, "execute", task_id)
            elif callback_data.startswith("task_delete_"):
                task_id = callback_data.replace("task_delete_", "")
                await self._confirm_task_action(query, "delete", task_id)
            elif callback_data.startswith("task_pause_"):
                task_id = callback_data.replace("task_pause_", "")
                await self._confirm_task_action(query, "pause", task_id)
            elif callback_data.startswith("confirm_task_"):
                await self._handle_task_confirmation(query, callback_data)
            elif callback_data.startswith("select_agent_"):
                agent_name = callback_data.replace("select_agent_", "")
                await self._show_agent_actions(query, agent_name)
            elif callback_data.startswith("select_action_"):
                await self._handle_action_selection(query, callback_data)
            elif callback_data.startswith("set_priority_"):
                await self._handle_priority_selection(query, callback_data)
            elif callback_data.startswith("schedule_"):
                await self._handle_schedule_selection(query, callback_data)
            elif callback_data.startswith("create_task_"):
                await self._handle_task_creation(query, callback_data)
            elif callback_data.startswith("confirm_delete_task_"):
                task_id = callback_data.replace("confirm_delete_task_", "")
                await self._delete_task(query, task_id)
            elif callback_data.startswith("confirm_execute_task_"):
                task_id = callback_data.replace("confirm_execute_task_", "")
                await self._execute_task(query, task_id)
            elif callback_data == "tasks_select_agent":
                await self._show_agent_selection(query)
                
        except Exception as e:
            logger.error(f"Erreur dans SystemHandler: {e}")
            await query.edit_message_text(
                text=format_error(str(e)),
                reply_markup=get_back_keyboard("system_main"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_agents_status(self, query):
        """Affiche l'état des agents"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        agents = self.api_client.get_agents_status()
        
        if agents:
            text = format_agents_status(agents)
        else:
            text = "❌ Impossible de récupérer l'état des agents"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # === NOUVELLES MÉTHODES POUR WORKFLOW AVANCÉ DES TÂCHES ===
    
    async def _show_tasks_create_advanced(self, query):
        """Affiche la sélection du type de tâche (workflow avancé)"""
        user_id = query.from_user.id
        # Réinitialiser l'état pour ce user
        task_creation_state[user_id] = {}
        
        text = """🆕 **Créer une nouvelle tâche**

Sélectionnez le type de tâche que vous souhaitez créer :

🔧 **SYSTEM_RECURRING** - Tâche système permanente
💼 **BUSINESS_RECURRING** - Tâche temporaire avec fin automatique  
⚡ **ONE_TIME** - Exécution unique puis suppression
❓ **CONDITIONAL** - Exécution selon condition prédéfinie"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_task_type_selection_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_task_type_selection(self, query, task_type: str):
        """Gère la sélection du type de tâche"""
        user_id = query.from_user.id
        if user_id not in task_creation_state:
            task_creation_state[user_id] = {}
        
        task_creation_state[user_id]['task_type'] = task_type
        
        # Descriptions des types
        type_descriptions = {
            "system_recurring": "Tâche système permanente - Ne sera jamais supprimée automatiquement",
            "business_recurring": "Tâche business temporaire - Avec date de fin et nettoyage automatique",
            "one_time": "Tâche ponctuelle - Exécutée une fois puis supprimée",
            "conditional": "Tâche conditionnelle - Exécutée selon une condition prédéfinie"
        }
        
        text = f"""🆕 **Type de tâche sélectionné**

**Type :** {task_type.upper()}
**Description :** {type_descriptions.get(task_type, 'Description non disponible')}

Sélectionnez maintenant l'agent qui exécutera cette tâche :"""
        
        agents = self.api_client.get_agents_status()
        if agents:
            await query.edit_message_text(
                text=text,
                reply_markup=get_advanced_agents_selection_keyboard(agents, task_type),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text(
                text=format_error("Impossible de récupérer la liste des agents"),
                reply_markup=get_back_keyboard("tasks_create"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_advanced_agent_selection(self, query, callback_data: str):
        """Gère la sélection d'agent dans le workflow avancé"""
        user_id = query.from_user.id
        parts = callback_data.replace("select_agent_for_task_", "").split("_", 1)
        
        if len(parts) >= 2:
            task_type, agent_name = parts[0], parts[1]
            
            if user_id not in task_creation_state:
                task_creation_state[user_id] = {}
            
            task_creation_state[user_id]['agent_name'] = agent_name
            
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
        """Gère la sélection d'action dans le workflow avancé"""
        user_id = query.from_user.id
        parts = callback_data.replace("select_action_for_task_", "").split("_")
        
        if len(parts) >= 3:
            task_type, agent_name, action = parts[0], parts[1], parts[2]
            
            if user_id not in task_creation_state:
                task_creation_state[user_id] = {}
            
            task_creation_state[user_id]['action'] = action
            
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
        """Gère la configuration des paramètres d'action"""
        user_id = query.from_user.id
        parts = callback_data.replace("param_", "").split("_")
        
        if len(parts) >= 4:
            task_type, agent_name, action, param_type = parts[0], parts[1], parts[2], parts[3]
            
            if user_id not in task_creation_state:
                task_creation_state[user_id] = {}
            
            # Traitement selon le type de paramètre
            if param_type == "qualified_leads":
                task_creation_state[user_id]['target'] = "qualified_leads"
                param_summary = "Tous les leads qualifiés"
            elif param_type == "specific_lead":
                # Dans une implémentation complète, on afficherait la liste des leads
                task_creation_state[user_id]['target'] = "specific_lead"
                param_summary = "Lead spécifique (à configurer)"
            elif param_type == "campaign_leads":
                task_creation_state[user_id]['target'] = "campaign_leads"
                param_summary = "Leads d'une campagne (à configurer)"
            elif param_type == "niche_leads":
                task_creation_state[user_id]['target'] = "niche_leads"
                param_summary = "Leads d'une niche (à configurer)"
            elif param_type == "no_params":
                task_creation_state[user_id]['target'] = "none"
                param_summary = "Aucun paramètre spécifique"
            else:
                task_creation_state[user_id]['target'] = param_type
                param_summary = f"Paramètre : {param_type}"
            
            # Si c'est une tâche conditionnelle, demander la condition
            if task_type == "conditional":
                text = f"""❓ **Tâche conditionnelle**

**Paramètres :** {param_summary}

Sélectionnez la condition d'exécution :"""
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=get_condition_selection_keyboard(task_type, agent_name, action),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Passer directement à la configuration du type de tâche
                text = f"""🔧 **Configuration de la tâche**

**Type :** {task_type.upper()}
**Agent :** {agent_name}
**Action :** {action}
**Paramètres :** {param_summary}

Configurez les paramètres spécifiques au type de tâche :"""
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=get_task_type_configuration_keyboard(task_type, agent_name, action, param_type),
                    parse_mode=ParseMode.MARKDOWN
                )
    
    async def _handle_condition_selection(self, query, callback_data: str):
        """Gère la sélection de condition pour tâches conditionnelles"""
        user_id = query.from_user.id
        parts = callback_data.replace("condition_", "").split("_")
        
        if len(parts) >= 4:
            task_type, agent_name, action, condition = parts[0], parts[1], parts[2], "_".join(parts[3:])
            
            if user_id not in task_creation_state:
                task_creation_state[user_id] = {}
            
            task_creation_state[user_id]['condition'] = condition
            
            condition_descriptions = {
                "no_response_24h": "Aucune réponse après 24h",
                "no_response_48h": "Aucune réponse après 48h",
                "low_performance": "Performance campagne faible",
                "no_leads_today": "Aucun nouveau lead aujourd'hui",
                "system_idle": "Système inactif depuis 1h"
            }
            
            text = f"""❓ **Condition sélectionnée**

**Condition :** {condition_descriptions.get(condition, condition)}

Configurez maintenant la fréquence de vérification :"""
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_task_type_configuration_keyboard(task_type, agent_name, action, "configured"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_task_configuration(self, query, callback_data: str):
        """Gère la configuration finale selon le type de tâche"""
        user_id = query.from_user.id
        parts = callback_data.replace("config_", "").split("_")
        
        if len(parts) >= 5:
            task_type, agent_name, action, params, config_value = parts[0], parts[1], parts[2], parts[3], parts[4]
            
            if user_id not in task_creation_state:
                task_creation_state[user_id] = {}
            
            # Traitement de la configuration selon le type
            if config_value.isdigit():
                # C'est un intervalle de récurrence
                interval = int(config_value)
                task_creation_state[user_id]['recurrence_interval'] = interval
                task_creation_state[user_id]['is_recurring'] = True
                
                interval_text = {
                    3600: "Toutes les heures",
                    86400: "Quotidien",
                    604800: "Hebdomadaire"
                }.get(interval, f"Toutes les {interval} secondes")
                
                schedule_info = f"Récurrence : {interval_text}"
                
            elif config_value in ["now", "1h", "24h"]:
                # Tâche ponctuelle
                task_creation_state[user_id]['is_recurring'] = False
                task_creation_state[user_id]['recurrence_interval'] = None
                
                if config_value == "now":
                    task_creation_state[user_id]['scheduled_time'] = datetime.now().isoformat()
                    schedule_info = "Exécution immédiate"
                elif config_value == "1h":
                    task_creation_state[user_id]['scheduled_time'] = (datetime.now() + timedelta(hours=1)).isoformat()
                    schedule_info = "Exécution dans 1 heure"
                elif config_value == "24h":
                    task_creation_state[user_id]['scheduled_time'] = (datetime.now() + timedelta(days=1)).isoformat()
                    schedule_info = "Exécution dans 24 heures"
                    
            elif config_value.startswith("check_"):
                # Tâche conditionnelle - fréquence de vérification
                check_interval = int(config_value.replace("check_", ""))
                task_creation_state[user_id]['check_interval'] = check_interval
                task_creation_state[user_id]['is_recurring'] = True
                task_creation_state[user_id]['recurrence_interval'] = check_interval
                
                check_text = {
                    3600: "Vérification toutes les heures",
                    21600: "Vérification toutes les 6 heures"
                }.get(check_interval, f"Vérification toutes les {check_interval} secondes")
                
                schedule_info = check_text
            else:
                schedule_info = f"Configuration : {config_value}"
            
            # Résumé final
            state = task_creation_state[user_id]
            
            text = f"""✅ **Résumé de la tâche à créer**

🔧 **Type :** {state.get('task_type', 'unknown').upper()}
🤖 **Agent :** {state.get('agent_name', 'unknown')}
⚙️ **Action :** {state.get('action', 'unknown')}
🎯 **Cible :** {state.get('target', 'none')}
⏰ **Planification :** {schedule_info}"""
            
            if state.get('condition'):
                text += f"\n❓ **Condition :** {state.get('condition')}"
            
            text += "\n\nConfirmez-vous la création de cette tâche ?"
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_final_task_confirmation_keyboard(state),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _create_final_advanced_task(self, query):
        """Crée la tâche finale avec tous les paramètres avancés"""
        user_id = query.from_user.id
        
        if user_id not in task_creation_state:
            await query.edit_message_text(
                text=format_error("Session expirée. Veuillez recommencer."),
                reply_markup=get_back_keyboard("tasks_create"),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        state = task_creation_state[user_id]
        
        # Obtenir l'ID de l'agent
        agents = self.api_client.get_agents_status()
        agent_id = 1  # Par défaut
        for agent in agents or []:
            if agent.get('name') == state.get('agent_name'):
                agent_id = agent.get('id', 1)
                break
        
        # Préparer les paramètres
        parameters = {
            "created_via": "telegram_bot_advanced",
            "target": state.get('target', 'none'),
            "task_type": state.get('task_type')
        }
        
        if state.get('condition'):
            parameters['condition'] = state.get('condition')
        
        # Créer la tâche selon le type
        task_type = state.get('task_type', 'one_time')
        
        try:
            if task_type == "system_recurring":
                result = self.api_client.create_advanced_task(
                    task_type=task_type,
                    agent_id=agent_id,
                    action=state.get('action'),
                    parameters=parameters,
                    priority=2,  # Priorité système
                    scheduled_time=state.get('scheduled_time', datetime.now().isoformat()),
                    is_recurring=state.get('is_recurring', True),
                    recurrence_interval=state.get('recurrence_interval', 3600),
                    auto_cleanup=False
                )
            elif task_type == "business_recurring":
                result = self.api_client.create_advanced_task(
                    task_type=task_type,
                    agent_id=agent_id,
                    action=state.get('action'),
                    parameters=parameters,
                    priority=3,
                    scheduled_time=state.get('scheduled_time', datetime.now().isoformat()),
                    is_recurring=state.get('is_recurring', True),
                    recurrence_interval=state.get('recurrence_interval', 86400),
                    end_date=(datetime.now() + timedelta(days=30)).isoformat(),
                    auto_cleanup=True,
                    cleanup_after_days=30
                )
            elif task_type == "one_time":
                result = self.api_client.create_advanced_task(
                    task_type=task_type,
                    agent_id=agent_id,
                    action=state.get('action'),
                    parameters=parameters,
                    priority=3,
                    scheduled_time=state.get('scheduled_time', datetime.now().isoformat()),
                    is_recurring=False,
                    max_executions=1,
                    auto_cleanup=True,
                    cleanup_after_days=1
                )
            elif task_type == "conditional":
                result = self.api_client.create_advanced_task(
                    task_type=task_type,
                    agent_id=agent_id,
                    action=state.get('action'),
                    parameters=parameters,
                    priority=3,
                    scheduled_time=datetime.now().isoformat(),
                    is_recurring=True,
                    recurrence_interval=state.get('check_interval', 3600),
                    condition=state.get('condition'),
                    auto_cleanup=True,
                    cleanup_after_days=7
                )
            else:
                # Fallback vers création basique
                result = self.api_client.create_task(
                    action=state.get('action'),
                    agent_id=agent_id,
                    parameters=parameters,
                    priority=3,
                    scheduled_time=state.get('scheduled_time', datetime.now().isoformat()),
                    is_recurring=state.get('is_recurring', False),
                    recurrence_interval=state.get('recurrence_interval')
                )
            
            if result and result.get('status') == 'success':
                text = format_success(f"""Tâche avancée créée avec succès !

**Type :** {task_type.upper()}
**ID :** {result.get('task_id', 'N/A')}
**Agent :** {state.get('agent_name')}
**Action :** {state.get('action')}""")
            else:
                text = format_error("Impossible de créer la tâche avancée")
            
            # Nettoyer l'état
            if user_id in task_creation_state:
                del task_creation_state[user_id]
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_back_keyboard("system_tasks"),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Erreur création tâche avancée: {e}")
            await query.edit_message_text(
                text=format_error(f"Erreur lors de la création : {str(e)}"),
                reply_markup=get_back_keyboard("system_tasks"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    # === MÉTHODES DE GESTION DES TÂCHES ===
    
    async def _show_tasks_menu(self, query):
        """Affiche le menu de gestion des tâches"""
        text = """📆 **Gestion des tâches planifiées**

Gérez toutes les tâches automatisées du système BerinIA.

**Fonctionnalités disponibles :**
• 📋 Voir toutes les tâches existantes
• ➕ Créer une nouvelle tâche
• 🗑️ Supprimer une tâche
• ▶️ Exécuter une tâche immédiatement
• 🤖 Voir les capacités des agents

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
            keyboard = get_tasks_list_keyboard(tasks)
        else:
            text = "ℹ️ Aucune tâche planifiée trouvée"
            keyboard = get_back_keyboard("system_tasks")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_tasks_create(self, query):
        """Affiche les options de création de tâche"""
        text = """➕ **Créer une nouvelle tâche**

Pour créer une tâche, vous devez :
1. 🤖 Sélectionner un agent
2. ⚙️ Choisir l'action à exécuter  
3. 🎯 Définir la priorité
4. ⏰ Planifier l'exécution

Commencez par sélectionner un agent :"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_tasks"),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Rediriger vers la sélection d'agent
        await self._show_agent_selection(query)
    
    async def _show_agent_selection(self, query):
        """Affiche la sélection d'agents pour création de tâche"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        agents = self.api_client.get_agents_status()
        
        if agents:
            text = """🤖 **Sélectionner un agent**

Choisissez l'agent qui exécutera la tâche :"""
            keyboard = get_agents_selection_keyboard(agents)
        else:
            text = "❌ Impossible de récupérer la liste des agents"
            keyboard = get_back_keyboard("tasks_create")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_agent_actions(self, query, agent_name: str):
        """Affiche les actions disponibles pour un agent"""
        text = f"""⚙️ **Actions disponibles pour {agent_name}**

Sélectionnez l'action que vous souhaitez programmer :"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_agent_actions_keyboard(agent_name),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_action_selection(self, query, callback_data: str):
        """Gère la sélection d'action"""
        parts = callback_data.replace("select_action_", "").split("_", 1)
        if len(parts) >= 2:
            agent_name = parts[0]
            action = parts[1]
            
            text = f"""🎯 **Priorité de la tâche**

**Agent :** {agent_name}
**Action :** {action}

Définissez la priorité d'exécution :"""
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_task_priority_keyboard(agent_name, action),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_priority_selection(self, query, callback_data: str):
        """Gère la sélection de priorité"""
        parts = callback_data.replace("set_priority_", "").split("_")
        if len(parts) >= 3:
            agent_name, action, priority = parts[0], parts[1], int(parts[2])
            
            priority_text = {1: "Haute", 2: "Moyenne", 3: "Basse"}[priority]
            
            text = f"""⏰ **Planification de la tâche**

**Agent :** {agent_name}
**Action :** {action}
**Priorité :** {priority_text}

Choisissez quand exécuter la tâche :"""
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_task_schedule_keyboard(agent_name, action, priority),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_schedule_selection(self, query, callback_data: str):
        """Gère la sélection de planification"""
        parts = callback_data.split("_")
        schedule_type = parts[1]
        agent_name, action, priority = parts[2], parts[3], int(parts[4])
        
        schedule_text = {
            "now": "Exécution immédiate",
            "1h": "Dans 1 heure",
            "24h": "Dans 24 heures", 
            "recurring_1h": "Répétitive toutes les heures",
            "recurring_24h": "Répétitive quotidienne"
        }.get(schedule_type, "Planification personnalisée")
        
        priority_text = {1: "Haute", 2: "Moyenne", 3: "Basse"}[priority]
        
        text = f"""✅ **Confirmation de création**

**Résumé de la tâche :**
🤖 **Agent :** {agent_name}
⚙️ **Action :** {action}
🎯 **Priorité :** {priority_text}
⏰ **Planification :** {schedule_text}

Confirmez-vous la création de cette tâche ?"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_task_final_confirmation_keyboard(agent_name, action, priority, schedule_type),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_task_creation(self, query, callback_data: str):
        """Crée la tâche"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        parts = callback_data.replace("create_task_", "").split("_")
        if len(parts) >= 4:
            agent_name, action, priority, schedule_type = parts[0], parts[1], int(parts[2]), parts[3]
            
            # Calculer l'heure d'exécution
            now = datetime.now()
            if schedule_type == "now":
                scheduled_time = now.isoformat()
                is_recurring = False
                recurrence_interval = None
            elif schedule_type == "1h":
                scheduled_time = (now + timedelta(hours=1)).isoformat()
                is_recurring = False
                recurrence_interval = None
            elif schedule_type == "24h":
                scheduled_time = (now + timedelta(days=1)).isoformat()
                is_recurring = False
                recurrence_interval = None
            elif schedule_type == "recurring_1h":
                scheduled_time = (now + timedelta(hours=1)).isoformat()
                is_recurring = True
                recurrence_interval = 3600  # 1 heure en secondes
            elif schedule_type == "recurring_24h":
                scheduled_time = (now + timedelta(days=1)).isoformat()
                is_recurring = True
                recurrence_interval = 86400  # 24 heures en secondes
            else:
                scheduled_time = now.isoformat()
                is_recurring = False
                recurrence_interval = None
            
            # Obtenir l'ID de l'agent
            agents = self.api_client.get_agents_status()
            agent_id = 1  # Par défaut
            for agent in agents or []:
                if agent.get('name') == agent_name:
                    agent_id = agent.get('id', 1)
                    break
            
            # Créer la tâche
            result = self.api_client.create_task(
                action=action,
                agent_id=agent_id,
                parameters={"created_via": "telegram_bot"},
                priority=priority,
                scheduled_time=scheduled_time,
                is_recurring=is_recurring,
                recurrence_interval=recurrence_interval
            )
            
            if result and result.get('status') == 'success':
                text = format_success(f"Tâche créée avec succès !\n\nID de la tâche : {result.get('task_id', 'N/A')}")
            else:
                text = format_error("Impossible de créer la tâche")
            
            await query.edit_message_text(
                text=text,
                reply_markup=get_back_keyboard("system_tasks"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_tasks_delete(self, query):
        """Affiche les tâches à supprimer"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        tasks = self.api_client.get_scheduled_tasks()
        
        if tasks:
            text = """🗑️ **Supprimer une tâche**

Sélectionnez la tâche à supprimer :

⚠️ **Attention :** Cette action est irréversible."""
            keyboard = get_tasks_to_delete_keyboard(tasks)
        else:
            text = "ℹ️ Aucune tâche trouvée à supprimer"
            keyboard = get_back_keyboard("system_tasks")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_tasks_execute(self, query):
        """Affiche les tâches à exécuter"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        tasks = self.api_client.get_scheduled_tasks()
        pending_tasks = [t for t in (tasks or []) if t.get('status') == 'pending']
        
        if pending_tasks:
            text = """▶️ **Exécuter une tâche**

Sélectionnez la tâche à exécuter immédiatement :"""
            keyboard = get_tasks_to_execute_keyboard(pending_tasks)
        else:
            text = "ℹ️ Aucune tâche en attente trouvée"
            keyboard = get_back_keyboard("system_tasks")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_agent_capabilities(self, query):
        """Affiche les capacités des agents"""
        text = format_agent_capabilities()
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_tasks"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_task_details(self, query, task_id: str):
        """Affiche les détails d'une tâche"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        task = self.api_client.get_task_details(task_id)
        
        if task:
            text = format_task_details(task)
            keyboard = get_task_details_keyboard(task_id)
        else:
            text = f"❌ Tâche {task_id} non trouvée"
            keyboard = get_back_keyboard("tasks_list")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _confirm_task_action(self, query, action: str, task_id: str):
        """Affiche la confirmation pour une action sur tâche"""
        action_text = {
            'delete': 'supprimer',
            'execute': 'exécuter',
            'pause': 'suspendre'
        }.get(action, 'modifier')
        
        text = f"""⚠️ **Confirmation d'action**

Êtes-vous sûr de vouloir {action_text} la tâche {task_id} ?

Cette action sera exécutée immédiatement."""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_task_confirmation_keyboard(action, task_id),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_task_confirmation(self, query, callback_data: str):
        """Gère les confirmations d'actions sur tâches"""
        parts = callback_data.replace("confirm_task_", "").split("_", 1)
        if len(parts) >= 2:
            action, task_id = parts[0], parts[1]
            
            if action == "delete":
                await self._delete_task(query, task_id)
            elif action == "execute":
                await self._execute_task(query, task_id)
            elif action == "pause":
                await self._pause_task(query, task_id)
    
    async def _delete_task(self, query, task_id: str):
        """Supprime une tâche"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        result = self.api_client.delete_task(task_id)
        
        if result and result.get('status') == 'success':
            text = format_success(f"Tâche {task_id} supprimée avec succès")
        else:
            text = format_error(f"Impossible de supprimer la tâche {task_id}")
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_tasks"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _execute_task(self, query, task_id: str):
        """Exécute une tâche immédiatement"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        result = self.api_client.execute_task_now(task_id)
        
        if result and result.get('status') == 'success':
            text = format_success(f"Exécution de la tâche {task_id} démarrée")
        else:
            text = format_error(f"Impossible d'exécuter la tâche {task_id}")
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_tasks"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _pause_task(self, query, task_id: str):
        """Met en pause une tâche"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        result = self.api_client.update_task_status(task_id, "paused")
        
        if result and result.get('status') == 'success':
            text = format_success(f"Tâche {task_id} mise en pause")
        else:
            text = format_error(f"Impossible de mettre en pause la tâche {task_id}")
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_tasks"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_scheduled_tasks(self, query):
        """Affiche les tâches planifiées"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        tasks = self.api_client.get_scheduled_tasks()
        
        if tasks:
            text = format_scheduled_tasks(tasks)
        else:
            text = "ℹ️ Aucune tâche planifiée trouvée"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_security_logs(self, query):
        """Affiche les logs de sécurité"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        logs = self.api_client.get_security_logs()
        
        if logs:
            text = format_system_logs(logs[:10])
        else:
            text = "ℹ️ Aucun log de sécurité trouvé"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_system_logs(self, query):
        """Affiche les logs système"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        logs = self.api_client.get_system_logs(limit=10)
        
        if logs:
            text = format_system_logs(logs)
        else:
            text = "ℹ️ Aucun log système trouvé"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_restart_confirmation(self, query):
        """Affiche la confirmation de redémarrage"""
        text = """🔄 **Redémarrage du système**

⚠️ **ATTENTION** : Cette action va redémarrer tout le système BerinIA.

**Conséquences :**
• Arrêt temporaire de tous les agents
• Interruption des campagnes en cours
• Perte des sessions actives
• Temps d'indisponibilité estimé : 2-3 minutes

**Êtes-vous sûr de vouloir continuer ?**
"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_confirmation_keyboard("restart", "system"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_services_status(self, query):
        """Affiche l'état des services"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        try:
            services_response = self.api_client.get_services_status()
            logger.info(f"DEBUG: Services response type: {type(services_response)}, content: {services_response}")
            
            # Extraire les données des services de la réponse API
            if services_response and isinstance(services_response, dict):
                if services_response.get('status') == 'success' and 'data' in services_response:
                    # Convertir la liste de services en dictionnaire pour le formatteur
                    services_list = services_response['data']
                    services_dict = {}
                    for service in services_list:
                        service_name = service.get('display_name', service.get('name', 'unknown'))
                        # Déterminer le statut réel
                        if service.get('is_active'):
                            status = 'active'
                        elif service.get('is_failing') or service.get('status') == 'activating':
                            status = 'failing'
                        else:
                            status = 'inactive'
                        
                        services_dict[service_name] = {
                            'status': status,
                            'uptime': service.get('uptime', 'N/A'),
                            'raw_status': service.get('status', 'unknown')
                        }
                    text = format_services_status(services_dict)
                else:
                    text = "❌ Réponse API invalide pour les services"
            else:
                text = f"❌ Impossible de récupérer l'état des services\nType reçu: {type(services_response)}"
        except Exception as e:
            logger.error(f"ERROR in _show_services_status: {e}")
            text = f"❌ Erreur lors de la récupération des services: {str(e)}"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _restart_system(self, query):
        """Redémarre le système"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        result = self.api_client.restart_system()
        
        if result:
            text = format_success("Redémarrage du système initié. Le système sera de nouveau opérationnel dans quelques minutes.")
        else:
            text = format_error("Impossible d'initier le redémarrage système")
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_agent_details(self, query, agent_name: str):
        """Affiche les détails d'un agent"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        agent = self.api_client.get_agent_details(agent_name)
        
        if agent:
            text = f"""🧠 **Détails de l'agent : {agent_name}**

📊 **Statut :** {agent.get('status', 'Inconnu')}
📅 **Dernière activité :** {agent.get('last_activity', 'N/A')}
🔄 **Nombre de tâches :** {agent.get('task_count', 0)}
⏱️ **Temps de fonctionnement :** {agent.get('uptime', 'N/A')}
🧮 **Utilisation mémoire :** {agent.get('memory_usage', 'N/A')}
🔧 **Version :** {agent.get('version', 'N/A')}

**Dernières actions :**
{agent.get('recent_actions', 'Aucune action récente')}

**Erreurs récentes :**
{agent.get('recent_errors', 'Aucune erreur')}
"""
        else:
            text = f"❌ Agent {agent_name} non trouvé"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("system_main"),
            parse_mode=ParseMode.MARKDOWN
        )

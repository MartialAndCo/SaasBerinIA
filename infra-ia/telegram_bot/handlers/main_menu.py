"""Handler principal pour les menus du bot Telegram"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from telegram.constants import ParseMode

from config.settings import MESSAGES, TELEGRAM_ADMIN_IDS
from utils.keyboards import (
    get_main_menu_keyboard, get_stats_menu_keyboard, get_campaigns_menu_keyboard,
    get_leads_menu_keyboard, get_niches_menu_keyboard, get_system_menu_keyboard
)
from services.api_client import BeriniaAPIClient
from utils.formatters import format_stats_summary, truncate_text

logger = logging.getLogger(__name__)

class MainMenuHandler:
    """Gestionnaire principal des menus"""
    
    def __init__(self):
        self.api_client = BeriniaAPIClient()
    
    def is_authorized(self, user_id: int) -> bool:
        """Vérifie si l'utilisateur est autorisé"""
        return user_id in TELEGRAM_ADMIN_IDS
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return
        
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            text=MESSAGES['welcome'],
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /help"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return
        
        help_text = """🤖 **Aide BerinIA Bot**

**Commandes disponibles :**
• /start - Menu principal
• /help - Cette aide
• /status - État du système

**Navigation :**
Utilisez les boutons pour naviguer dans les menus.

**Fonctionnalités :**
📊 Statistiques - Voir les métriques
🎯 Campagnes - Gérer les campagnes
👥 Leads - Gestion des leads
📂 Niches - Analyse des niches
🧠 Système - Administration

Contactez l'administrateur en cas de problème.
"""
        
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            text=help_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /status - état rapide du système"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return
        
        # Récupération rapide des stats
        stats = self.api_client.get_general_stats()
        
        if stats:
            response_text = format_stats_summary(stats)
        else:
            response_text = "❌ Impossible de récupérer les statistiques système"
        
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            text=response_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Commandes du menu persistant
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /stats - accès direct aux statistiques"""
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return
        await self._show_stats_menu_direct(update, context)
    
    async def campaigns_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /campagnes - accès direct aux campagnes"""
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return
        await self._show_campaigns_menu_direct(update, context)
    
    async def leads_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /leads - accès direct aux leads"""
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return
        await self._show_leads_menu_direct(update, context)
    
    async def niches_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /niches - accès direct aux niches"""
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return
        await self._show_niches_menu_direct(update, context)
    
    async def system_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /systeme - accès direct au système"""
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text(MESSAGES['unauthorized'])
            return
        await self._show_system_menu_direct(update, context)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère tous les callback queries des menus"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await query.answer("Non autorisé")
            return
        
        await query.answer()  # Répond immédiatement pour éviter le timeout
        
        callback_data = query.data
        logger.info(f"DEBUG: Callback reçu - data={callback_data}, user_id={user_id}")
        
        try:
            # D'abord, essayer de résoudre via CallbackManager pour les nouveaux callbacks courts
            resolved_callback = None
            if callback_data.startswith("cb_"):
                try:
                    import sys
                    import os
                    logger.debug(f"PYTHONPATH in handler: {sys.path}")
                    # Essayer l'import direct
                    try:
                        from core.callback_manager import callback_manager
                    except ImportError:
                        # Ajouter le répertoire telegram_bot au path si nécessaire
                        telegram_bot_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        if telegram_bot_dir not in sys.path:
                            sys.path.insert(0, telegram_bot_dir)
                        from core.callback_manager import callback_manager
                    
                    resolved_callback = callback_manager.resolve(callback_data)
                    logger.debug(f"Callback résolu: {callback_data} -> {resolved_callback}")
                    
                    # Si on a un callback résolu, router selon l'action
                    if resolved_callback:
                        action = resolved_callback.get('action')
                        # Router toutes les actions liées aux tâches
                        if action in ['select_agent_for_task', 'select_action_for_task', 'param_action', 
                                     'condition_selection', 'task_config']:
                            await self._delegate_to_tasks_handler(query, callback_data)
                            return
                        elif action.startswith('campaign_'):
                            await self._delegate_to_campaigns_handler(query, callback_data)
                            return
                        # Pour toutes les autres actions, essayer le tasks handler par défaut
                        else:
                            await self._delegate_to_tasks_handler(query, callback_data)
                            return
                            
                except ImportError as ie:
                    logger.error(f"CallbackManager import failed même avec path fix: {ie}")
                    logger.debug("CallbackManager non disponible, routage standard")
                except Exception as e:
                    logger.warning(f"Impossible de résoudre le callback {callback_data}: {e}")
            
            # Routage classique selon le callback
            if callback_data == "main_menu":
                await self._show_main_menu(query)
            
            elif callback_data == "stats_main":
                await self._show_stats_menu(query)
            
            elif callback_data == "campaigns_main":
                await self._show_campaigns_menu(query)
            
            elif callback_data == "leads_main":
                await self._show_leads_menu(query)
            
            elif callback_data == "niches_main":
                await self._show_niches_menu(query)
            
            elif callback_data == "system_main":
                await self._show_system_menu(query)
            
            elif callback_data == "tasks_main":
                await self._show_tasks_menu(query)
            
            elif callback_data == "billing_main":
                await self._show_billing_menu(query)
            
            else:
                # Déléguer aux handlers spécialisés selon le préfixe
                if callback_data.startswith("stats_"):
                    await self._delegate_to_stats_handler(query, callback_data)
                elif (callback_data.startswith("tasks_") or 
                      callback_data.startswith("task_type_") or
                      callback_data.startswith("select_agent_for_task_") or
                      callback_data.startswith("select_action_for_task_") or
                      callback_data.startswith("param_") or
                      callback_data.startswith("condition_") or
                      callback_data.startswith("config_") or
                      callback_data.startswith("delete_task_") or
                      callback_data.startswith("deletetask_") or
                      callback_data == "create_final_task"):
                    await self._delegate_to_tasks_handler(query, callback_data)
                elif (callback_data.startswith("campaigns_") or 
                      callback_data.startswith("campaign_") or
                      callback_data.startswith("create_campaign_") or
                      callback_data.startswith("select_niche_") or
                      callback_data.startswith("select_city_") or
                      callback_data.startswith("confirm_create_") or
                      callback_data.startswith("confirm_start_") or
                      callback_data.startswith("confirm_stop_") or
                      callback_data.startswith("confirm_restart_")):
                    await self._delegate_to_campaigns_handler(query, callback_data)
                elif (callback_data.startswith("leads_") or 
                      callback_data.startswith("lead_") or
                      callback_data.startswith("meetings_") or
                      callback_data.startswith("meeting_") or
                      callback_data.startswith("convert_") or
                      callback_data.startswith("refuse_") or
                      callback_data.startswith("thinking_") or
                      callback_data.startswith("select_service_") or
                      callback_data.startswith("conversion_stats_") or
                      "bundles" in callback_data):
                    logger.info(f"🔄 Délégation vers LeadsHandler pour: '{callback_data}'")
                    await self._delegate_to_leads_handler(query, callback_data)
                elif callback_data.startswith("niches_") or callback_data.startswith("niche_"):
                    await self._delegate_to_niches_handler(query, callback_data)
                elif (callback_data.startswith("system_") or 
                      callback_data.startswith("agent_") or
                      callback_data.startswith("confirm_restart_")):
                    await self._delegate_to_system_handler(query, callback_data)
                elif (callback_data.startswith("billing_") or 
                      callback_data.startswith("invoice_")):
                    await self._delegate_to_billing_handler(query, callback_data)
                elif callback_data.startswith("daily_"):
                    await self._delegate_to_daily_handler(query, callback_data, context)
                else:
                    # Log pour debugging
                    logger.warning(f"Callback non reconnu: {callback_data}")
                    await query.edit_message_text(
                        text=f"❌ Action non reconnue\\: {callback_data}",
                        reply_markup=get_main_menu_keyboard(),
                        parse_mode=ParseMode.MARKDOWN
                    )
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement du callback {callback_data}: {e}")
            error_text = f"❌ Une erreur s'est produite\\: {str(e)}"
            await query.edit_message_text(
                text=error_text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_main_menu(self, query):
        """Affiche le menu principal"""
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            text=MESSAGES['welcome'],
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_stats_menu(self, query):
        """Affiche le menu statistiques"""
        keyboard = get_stats_menu_keyboard()
        await query.edit_message_text(
            text="📊 **Menu Statistiques**\n\nChoisissez le type de statistiques à consulter :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_campaigns_menu(self, query):
        """Affiche le menu campagnes"""
        keyboard = get_campaigns_menu_keyboard()
        await query.edit_message_text(
            text="🎯 **Menu Campagnes**\n\nGestion et suivi de vos campagnes :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_leads_menu(self, query):
        """Affiche le menu leads"""
        keyboard = get_leads_menu_keyboard()
        await query.edit_message_text(
            text="👥 **Menu Leads**\n\nGestion et analyse de vos leads :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_niches_menu(self, query):
        """Affiche le menu niches"""
        keyboard = get_niches_menu_keyboard()
        await query.edit_message_text(
            text="📂 **Menu Niches**\n\nAnalyse et gestion de vos niches :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_system_menu(self, query):
        """Affiche le menu système"""
        keyboard = get_system_menu_keyboard()
        await query.edit_message_text(
            text="🧠 **Menu Système**\n\nAdministration et monitoring :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_tasks_menu(self, query):
        """Affiche le menu tâches"""
        from utils.keyboards import get_tasks_menu_keyboard
        keyboard = get_tasks_menu_keyboard()
        await query.edit_message_text(
            text="📆 **Menu Tâches**\n\nGestion des tâches planifiées :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _delegate_to_stats_handler(self, query, callback_data):
        """Délègue au handler des statistiques"""
        from handlers.stats import StatsHandler
        handler = StatsHandler()
        await handler.handle_callback(query, callback_data)
    
    async def _delegate_to_campaigns_handler(self, query, callback_data):
        """Délègue au handler des campagnes"""
        from handlers.campaigns import CampaignsHandler
        handler = CampaignsHandler()
        await handler.handle_callback(query, callback_data)
    
    async def _delegate_to_leads_handler(self, query, callback_data):
        """Délègue au handler des leads"""
        from handlers.leads import LeadsHandler
        handler = LeadsHandler()
        await handler.handle_callback(query, callback_data)
    
    async def _delegate_to_niches_handler(self, query, callback_data):
        """Délègue au handler des niches"""
        from handlers.niches import NichesHandler
        handler = NichesHandler()
        await handler.handle_callback(query, callback_data)
    
    async def _delegate_to_system_handler(self, query, callback_data):
        """Délègue au handler du système"""
        from handlers.system import SystemHandler
        handler = SystemHandler()
        await handler.handle_callback(query, callback_data)
    
    async def _delegate_to_tasks_handler(self, query, callback_data):
        """Délègue au handler des tâches"""
        try:
            from handlers.tasks import TasksHandler
            handler = TasksHandler()
            await handler.handle_callback(query, callback_data)
        except ImportError as e:
            logger.error(f"Impossible d'importer TasksHandler: {e}")
            from utils.keyboards import get_back_keyboard
            await query.edit_message_text(
                text="❌ **Erreur**\n\nFonctionnalité temporairement indisponible.",
                reply_markup=get_back_keyboard("main_menu"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_billing_menu(self, query):
        """Affiche le menu facturation"""
        from utils.keyboards import get_billing_menu_keyboard
        keyboard = get_billing_menu_keyboard()
        await query.edit_message_text(
            text="💳 **Menu Facturation**\n\nGestion de la facturation clients :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _delegate_to_billing_handler(self, query, callback_data):
        """Délègue au handler de facturation"""
        logger.info(f"DEBUG: Délégation vers BillingHandler - callback_data={callback_data}")
        handler = get_billing_handler()  # Utiliser l'instance globale
        await handler.handle_callback(query, callback_data)
    
    # Méthodes d'affichage direct pour le menu persistant
    async def _show_stats_menu_direct(self, update, context):
        """Affiche le menu statistiques via message direct"""
        from utils.keyboards import get_stats_menu_keyboard
        keyboard = get_stats_menu_keyboard()
        await update.message.reply_text(
            text="📊 **Menu Statistiques**\n\nVoir les métriques du système :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_campaigns_menu_direct(self, update, context):
        """Affiche le menu campagnes via message direct"""
        from utils.keyboards import get_campaigns_menu_keyboard
        keyboard = get_campaigns_menu_keyboard()
        await update.message.reply_text(
            text="🎯 **Menu Campagnes**\n\nGestion des campagnes de prospection :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_leads_menu_direct(self, update, context):
        """Affiche le menu leads via message direct"""
        from utils.keyboards import get_leads_menu_keyboard
        keyboard = get_leads_menu_keyboard()
        await update.message.reply_text(
            text="👥 **Menu Leads**\n\nGestion des prospects :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_niches_menu_direct(self, update, context):
        """Affiche le menu niches via message direct"""
        from utils.keyboards import get_niches_menu_keyboard
        keyboard = get_niches_menu_keyboard()
        await update.message.reply_text(
            text="📂 **Menu Niches**\n\nAnalyse et gestion des niches :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_system_menu_direct(self, update, context):
        """Affiche le menu système via message direct"""
        from utils.keyboards import get_system_menu_keyboard
        keyboard = get_system_menu_keyboard()
        await update.message.reply_text(
            text="🧠 **Menu Système**\n\nAdministration et gestion :",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _delegate_to_daily_handler(self, query, callback_data, context):
        """Délègue au handler du rapport quotidien"""
        from handlers.daily_report import callback_daily_detail
        
        # Créer un update mock pour le handler
        update = type('Update', (), {
            'callback_query': query,
            'effective_user': query.from_user,
            'effective_chat': query.message.chat
        })()
        
        await callback_daily_detail(update, context)

# Instance globale du handler
main_handler = MainMenuHandler()

# Instance globale du billing handler pour préserver l'état
_billing_handler_instance = None

def get_billing_handler():
    """Retourne l'instance globale du billing handler"""
    global _billing_handler_instance
    if _billing_handler_instance is None:
        from handlers.billing import BillingHandler
        _billing_handler_instance = BillingHandler()
    return _billing_handler_instance

# Export des handlers pour l'application
def get_handlers():
    """Retourne la liste des handlers à enregistrer"""
    from handlers.daily_report import get_daily_report_handlers
    
    # Handlers de base
    base_handlers = [
        CommandHandler("start", main_handler.start_command),
        CommandHandler("help", main_handler.help_command),
        CommandHandler("status", main_handler.status_command),
        CallbackQueryHandler(main_handler.handle_callback_query)
    ]
    
    # Handlers du menu persistant
    persistent_menu_handlers = [
        CommandHandler("stats", main_handler.stats_command),
        CommandHandler("campagnes", main_handler.campaigns_command),
        CommandHandler("leads", main_handler.leads_command),
        CommandHandler("niches", main_handler.niches_command),
        CommandHandler("systeme", main_handler.system_command)
    ]
    
    # Handler pour les commandes meeting
    from telegram.ext import MessageHandler, filters
    import re
    
    async def handle_meeting_command(update, context):
        """Handler pour les commandes /meetingXX"""
        message_text = update.message.text
        match = re.search(r'/meeting(\d+)', message_text)
        if match:
            meeting_id = int(match.group(1))
            from handlers.leads import LeadsHandler
            leads_handler = LeadsHandler()
            # Créer un objet query simulé pour la compatibilité
            class FakeQuery:
                def __init__(self, message):
                    self.message = message
                    self.from_user = message.from_user
                
                async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                    await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            
            fake_query = FakeQuery(update.message)
            await leads_handler._show_meeting_details(fake_query, meeting_id)
    
    async def handle_conversation_command(update, context):
        """Handler pour les commandes /conversationXX"""
        message_text = update.message.text
        match = re.search(r'/conversation(\d+)', message_text)
        if match:
            lead_id = int(match.group(1))
            from handlers.leads import LeadsHandler
            leads_handler = LeadsHandler()
            
            # Récupérer le résumé de conversation
            conversation_data = leads_handler.api_client.get_lead_conversation_summary(lead_id)
            
            if conversation_data and conversation_data.get('summary'):
                summary = conversation_data['summary']
                interest_level = summary.get('interest_level', 'unknown')
                key_points = summary.get('key_points', [])
                conversations_count = conversation_data.get('conversations_count', 0)
                
                # Lead info
                lead_name = conversation_data.get('lead_name', 'Client inconnu')
                lead_company = conversation_data.get('lead_company', 'Non renseignée')
                
                # Emoji selon le niveau d'intérêt
                interest_emojis = {
                    'high': '🔥 Très intéressé',
                    'medium': '🟡 Intérêt modéré', 
                    'low': '🔵 Peu d\'intérêt',
                    'unknown': '❓ Intérêt inconnu'
                }
                interest_text = interest_emojis.get(interest_level, '❓ Intérêt inconnu')
                
                text = f"""💬 **Résumé de la conversation**

👤 **Client :** {lead_name}
🏢 **Entreprise :** {lead_company}
📊 **Niveau d'intérêt :** {interest_text}
💬 **Nombre d'échanges :** {conversations_count}

📋 **Points clés discutés :**"""
                
                if key_points:
                    for point in key_points[:5]:  # Limite à 5 points
                        text += f"\n• {point}"
                else:
                    text += "\n• Aucun point clé enregistré"
                
                # Conseils selon le niveau d'intérêt
                if interest_level == 'high':
                    text += f"\n\n🔥 **Recommandations :**"
                    text += f"\n• Prioriser ce prospect"
                    text += f"\n• Programmer un suivi rapide"
                    text += f"\n• Préparer une proposition"
                elif interest_level == 'medium':
                    text += f"\n\n🟡 **Recommandations :**"
                    text += f"\n• Maintenir le contact régulier"
                    text += f"\n• Apporter plus de valeur"
                    text += f"\n• Identifier les freins"
                elif interest_level == 'low':
                    text += f"\n\n🔵 **Recommandations :**"
                    text += f"\n• Revoir l'approche commerciale"
                    text += f"\n• Chercher de nouveaux angles"
                    text += f"\n• Peut-être espacer les relances"
                
            else:
                text = f"ℹ️ Aucun résumé de conversation disponible pour ce lead (ID: {lead_id})"
            
            await update.message.reply_text(text, parse_mode='Markdown')
    
    meeting_handlers = [
        MessageHandler(filters.Regex(r'^/meeting\d+'), handle_meeting_command),
        MessageHandler(filters.Regex(r'^/conversation\d+'), handle_conversation_command)
    ]
    
    # Handlers du rapport quotidien
    daily_report_handlers = get_daily_report_handlers()
    
    # Handlers pour les tests de paiement
    from handlers.payment_test import get_payment_test_handlers
    payment_test_handlers = get_payment_test_handlers()
    
    # Combinaison de tous les handlers
    return base_handlers + persistent_menu_handlers + meeting_handlers + daily_report_handlers + payment_test_handlers

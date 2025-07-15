"""Routeur simplifié pour callbacks"""

import logging
from typing import Dict, Callable

logger = logging.getLogger(__name__)

class SimpleRouter:
    """Routeur simple et prévisible pour les callbacks"""
    
    def __init__(self):
        self.routes: Dict[str, Callable] = {}
        self.default_handler = None
    
    def add_route(self, prefix: str, handler: Callable):
        """Ajoute une route avec préfixe"""
        self.routes[prefix] = handler
        logger.info(f"Route ajoutée: {prefix} -> {handler.__class__.__name__}")
    
    def set_default(self, handler: Callable):
        """Handler par défaut pour callbacks non reconnus"""
        self.default_handler = handler
    
    async def route(self, query, callback_data: str):
        """Route un callback vers le bon handler"""
        try:
            # Essayer de matcher par préfixe
            for prefix, handler in self.routes.items():
                if callback_data.startswith(prefix):
                    logger.info(f"Routing {callback_data} -> {handler.__class__.__name__}")
                    await handler.handle_callback(query, callback_data)
                    return
            
            # Callbacks spéciaux (sans préfixe)
            special_routes = {
                "main_menu": self._show_main_menu,
                "meetings_quick": self._show_meetings_menu,
                "stats_quick": self._show_stats_menu,
                "campaigns_quick": self._show_campaigns_menu,
                "leads_quick": self._show_leads_menu,
                "tasks_quick": self._show_tasks_menu,
                "system_quick": self._show_system_menu
            }
            
            if callback_data in special_routes:
                await special_routes[callback_data](query)
                return
            
            # Handler par défaut
            if self.default_handler:
                await self.default_handler(query, callback_data)
            else:
                await self._handle_unknown(query, callback_data)
                
        except Exception as e:
            logger.error(f"Erreur routing {callback_data}: {e}")
            await self._handle_error(query, str(e))
    
    async def _show_main_menu(self, query):
        """Menu principal simplifié"""
        from utils.keyboards_simple import get_main_menu_simple
        
        text = """🤖 **BerinIA Dashboard**

Votre interface de gestion simplifiée.
Choisissez une action :"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_main_menu_simple(),
            parse_mode="Markdown"
        )
    
    async def _show_meetings_menu(self, query):
        """Menu meetings simplifié"""
        from utils.keyboards_simple import get_meetings_quick_keyboard
        
        text = """📅 **Gestion Meetings**

Actions rapides disponibles :"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_meetings_quick_keyboard(),
            parse_mode="Markdown"
        )
    
    async def _show_stats_menu(self, query):
        """Menu stats simplifié"""
        from utils.keyboards_simple import get_stats_quick_keyboard
        
        text = """📊 **Statistiques**

Vue d'ensemble des performances :"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_stats_quick_keyboard(),
            parse_mode="Markdown"
        )
    
    async def _show_campaigns_menu(self, query):
        """Menu campagnes (délégué à l'handler existant)"""
        from handlers.campaigns import CampaignsHandler
        handler = CampaignsHandler()
        await handler.handle_callback(query, "campaigns_main")
    
    async def _show_leads_menu(self, query):
        """Menu leads (délégué à l'handler existant)"""
        from handlers.leads import LeadsHandler
        handler = LeadsHandler()
        await handler.handle_callback(query, "leads_main")
    
    async def _show_tasks_menu(self, query):
        """Menu tâches (délégué à l'handler existant)"""
        from handlers.tasks import TasksHandler
        handler = TasksHandler()
        await handler.handle_callback(query, "tasks_main")
    
    async def _show_system_menu(self, query):
        """Menu système (délégué à l'handler existant)"""
        from handlers.system import SystemHandler
        handler = SystemHandler()
        await handler.handle_callback(query, "system_main")
    
    async def _handle_unknown(self, query, callback_data: str):
        """Gère les callbacks non reconnus"""
        logger.warning(f"Callback non reconnu: {callback_data}")
        
        from utils.keyboards_simple import get_back_button
        
        await query.edit_message_text(
            text=f"❌ **Action non reconnue**\\n\\n`{callback_data}`\\n\\nRetour au menu principal ?",
            reply_markup=get_back_button("main_menu"),
            parse_mode="Markdown"
        )
    
    async def _handle_error(self, query, error: str):
        """Gère les erreurs de routing"""
        logger.error(f"Erreur routing: {error}")
        
        from utils.keyboards_simple import get_back_button
        
        await query.edit_message_text(
            text=f"❌ **Erreur technique**\\n\\n{error}\\n\\nRetour au menu principal ?",
            reply_markup=get_back_button("main_menu"),
            parse_mode="Markdown"
        )
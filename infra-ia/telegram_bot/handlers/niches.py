"""Handler pour les niches du bot Telegram"""
import logging
from telegram.constants import ParseMode

from services.api_client import BeriniaAPIClient
from utils.keyboards import get_back_keyboard
from utils.formatters import format_niches_list, format_error, format_loading

logger = logging.getLogger(__name__)

class NichesHandler:
    """Gestionnaire des niches"""
    
    def __init__(self):
        self.api_client = BeriniaAPIClient()
    
    async def handle_callback(self, query, callback_data: str):
        """Gère les callbacks des niches"""
        try:
            if callback_data == "niches_list":
                await self._show_niches_list(query)
            elif callback_data == "niches_performance":
                await self._show_performance_info(query)
            elif callback_data == "niches_stop":
                await self._show_stop_info(query)
            elif callback_data == "niches_new":
                await self._show_new_niche_info(query)
            elif callback_data == "niches_analyze":
                await self._show_analyze_info(query)
            elif callback_data == "niches_campaigns":
                await self._show_campaigns_info(query)
        except Exception as e:
            logger.error(f"Erreur dans NichesHandler: {e}")
            await query.edit_message_text(
                text=format_error(str(e)),
                reply_markup=get_back_keyboard("niches_main"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_niches_list(self, query):
        """Affiche la liste des niches"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        niches = self.api_client.get_niches()
        
        if niches:
            text = format_niches_list(niches)
        else:
            text = "ℹ️ Aucune niche trouvée"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("niches_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_performance_info(self, query):
        """Info sur les performances des niches"""
        text = """📊 **Performances des niches**

Fonctionnalité d'analyse des performances en cours de développement.

Vous pourrez bientôt consulter :
• ROI par niche
• Taux de conversion
• Volume de leads généré
• Évolution temporelle
• Comparaisons entre niches

Contactez l'administrateur pour une analyse détaillée.
"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("niches_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_stop_info(self, query):
        """Info sur l'arrêt des niches"""
        text = """🛑 **Stopper une niche**

Fonctionnalité de gestion des niches en cours de développement.

Cette action permettra de :
• Suspendre les campagnes d'une niche
• Arrêter le scraping pour cette niche
• Analyser les raisons de faible performance
• Proposer des alternatives

Contactez l'administrateur pour stopper une niche spécifique.
"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("niches_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_new_niche_info(self, query):
        """Info sur les nouvelles niches"""
        text = """🆕 **Proposer une nouvelle niche**

Fonctionnalité de suggestion de niches en cours de développement.

Le système pourra :
• Analyser les tendances du marché
• Identifier des niches rentables
• Estimer le potentiel de leads
• Proposer des stratégies d'approche
• Tester automatiquement la viabilité

Contactez l'administrateur pour proposer une niche.
"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("niches_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_analyze_info(self, query):
        """Info sur l'analyse de viabilité"""
        text = """🧠 **Analyser la viabilité d'une niche**

Fonctionnalité d'analyse IA en cours de développement.

L'analyse inclura :
• Potentiel de marché
• Concurrence
• Facilité de prospection
• Taux de conversion estimé
• ROI prévisionnelle
• Recommandations stratégiques

Contactez l'administrateur pour une analyse personnalisée.
"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("niches_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_campaigns_info(self, query):
        """Info sur les campagnes associées"""
        text = """📈 **Campagnes associées aux niches**

Fonctionnalité de liaison campagnes-niches en cours de développement.

Vous pourrez voir :
• Campagnes actives par niche
• Performance comparée
• Allocation des ressources
• Optimisations suggérées
• Historique des campagnes

Contactez l'administrateur pour plus d'informations.
"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("niches_main"),
            parse_mode=ParseMode.MARKDOWN
        )

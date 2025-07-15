"""Handler pour les campagnes du bot Telegram"""
import logging
from telegram.constants import ParseMode

from services.api_client import BeriniaAPIClient
from utils.keyboards import get_back_keyboard, get_campaigns_list_keyboard, get_confirmation_keyboard
from utils.formatters import format_campaign_list, format_campaign_details, format_error, format_loading, format_success

logger = logging.getLogger(__name__)

class CampaignsHandler:
    """Gestionnaire des campagnes"""
    
    def __init__(self):
        self.api_client = BeriniaAPIClient()
    
    async def handle_callback(self, query, callback_data: str):
        """Gère les callbacks des campagnes"""
        try:
            if callback_data == "campaigns_active":
                await self._show_active_campaigns(query)
            elif callback_data == "campaigns_stats":
                await self._show_campaigns_stats(query)
            elif callback_data == "campaigns_start":
                await self._show_create_new_campaign_menu(query)
            elif callback_data == "campaigns_stop":
                await self._show_stop_campaign_menu(query)
            elif callback_data == "campaigns_restart":
                await self._show_restart_campaign_menu(query)
            elif callback_data == "campaigns_export":
                await self._show_export_menu(query)
            elif callback_data.startswith("campaign_details_"):
                campaign_id = callback_data.replace("campaign_details_", "")
                await self._show_campaign_details(query, campaign_id)
            elif callback_data.startswith("confirm_start_"):
                campaign_id = callback_data.replace("confirm_start_", "")
                await self._start_campaign(query, campaign_id)
            elif callback_data.startswith("confirm_stop_"):
                campaign_id = callback_data.replace("confirm_stop_", "")
                await self._stop_campaign(query, campaign_id)
            elif callback_data.startswith("confirm_restart_"):
                campaign_id = callback_data.replace("confirm_restart_", "")
                await self._restart_campaign(query, campaign_id)
            elif callback_data == "create_campaign_select_niche":
                await self._show_niche_selection(query)
            elif callback_data.startswith("select_niche_"):
                niche_id = callback_data.replace("select_niche_", "")
                await self._show_city_selection(query, niche_id)
            elif callback_data.startswith("select_city_"):
                parts = callback_data.replace("select_city_", "").split("_")
                niche_id = parts[0]
                city = "_".join(parts[1:])
                await self._confirm_new_campaign(query, niche_id, city)
            elif callback_data.startswith("confirm_create_"):
                parts = callback_data.replace("confirm_create_", "").split("_")
                niche_id = parts[0]
                city = "_".join(parts[1:])
                await self._create_new_campaign(query, niche_id, city)
        except Exception as e:
            logger.error(f"Erreur dans CampaignsHandler: {e}")
            await query.edit_message_text(
                text=format_error(str(e)),
                reply_markup=get_back_keyboard("campaigns_main"),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_active_campaigns(self, query):
        """Affiche les campagnes actives"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        campaigns = self.api_client.get_active_campaigns()
        
        if campaigns:
            text = format_campaign_list(campaigns)
            keyboard = get_campaigns_list_keyboard(campaigns)
        else:
            text = "ℹ️ Aucune campagne active trouvée"
            keyboard = get_back_keyboard("campaigns_main")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_campaigns_stats(self, query):
        """Affiche les statistiques des campagnes"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        # Récupérer toutes les campagnes (actives et inactives)
        active_campaigns = self.api_client.get_active_campaigns() or []
        inactive_campaigns = self.api_client.get_inactive_campaigns() or []
        all_campaigns = active_campaigns + inactive_campaigns
        
        if all_campaigns:
            active_count = len(active_campaigns)
            total_leads = sum(c.get('leads_count', 0) for c in all_campaigns)
            
            # Calculer conversion moyenne seulement si on a des leads
            campaigns_with_leads = [c for c in all_campaigns if c.get('leads_count', 0) > 0]
            if campaigns_with_leads:
                avg_conversion = sum(c.get('qualified_leads', 0) / c.get('leads_count', 1) * 100 for c in campaigns_with_leads) / len(campaigns_with_leads)
            else:
                avg_conversion = 0
            
            text = f"""📈 **Statistiques des campagnes**

🎯 **Total campagnes :** {len(all_campaigns)}
✅ **Campagnes actives :** {active_count}
❌ **Campagnes inactives :** {len(all_campaigns) - active_count}

👥 **Total leads :** {total_leads}
📊 **Conversion moyenne :** {avg_conversion:.1f}%

**Campagnes actives :**
"""
            # Afficher les campagnes actives avec leurs vraies métriques
            for i, campaign in enumerate(active_campaigns, 1):
                name = campaign.get('name', f'Campagne {i}')
                leads = campaign.get('leads_count', 0)
                qualified = campaign.get('qualified_leads', 0)
                conversion = (qualified / leads * 100) if leads > 0 else 0
                text += f"{i}. {name} ({leads} leads, {conversion:.1f}%)\n"
                
            if not active_campaigns:
                text += "Aucune campagne active.\n"
        else:
            text = "❌ Impossible de récupérer les statistiques des campagnes"
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("campaigns_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    # === NOUVELLES FONCTIONNALITÉS CRÉATION CAMPAGNE ===
    
    async def _show_create_new_campaign_menu(self, query):
        """Affiche le menu de création d'une nouvelle campagne"""
        text = """🚀 **Créer une nouvelle campagne**

Choisissez comment vous souhaitez créer votre campagne :

1️⃣ **Sélectionner une niche existante**
2️⃣ **Créer une nouvelle niche** (bientôt disponible)

Une fois la niche choisie, vous pourrez sélectionner une ville pour votre campagne.
"""
        
        from utils.keyboards import get_create_campaign_keyboard
        await query.edit_message_text(
            text=text,
            reply_markup=get_create_campaign_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_niche_selection(self, query):
        """Affiche la sélection de niche"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        niches = self.api_client.get_available_niches()
        
        if niches:
            text = """📂 **Sélectionnez une niche**

Choisissez la niche pour votre nouvelle campagne :

"""
            from utils.keyboards import get_niches_selection_keyboard
            for i, niche in enumerate(niches[:10], 1):
                name = niche.get('name', f'Niche {i}')
                text += f"{i}️⃣ **{name}**\n"
            
            keyboard = get_niches_selection_keyboard(niches)
        else:
            text = "❌ Aucune niche disponible pour créer une campagne"
            keyboard = get_back_keyboard("campaigns_main")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_city_selection(self, query, niche_id: str):
        """Affiche la sélection de ville"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        cities = self.api_client.get_available_cities()
        
        if cities:
            text = f"""🏙️ **Sélectionnez une ville**

Choisissez la ville pour votre campagne :

"""
            for i, city in enumerate(cities[:10], 1):
                text += f"{i}️⃣ **{city}**\n"
            
            from utils.keyboards import get_cities_selection_keyboard
            keyboard = get_cities_selection_keyboard(cities, niche_id)
        else:
            text = "❌ Aucune ville disponible"
            keyboard = get_back_keyboard("campaigns_main")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _confirm_new_campaign(self, query, niche_id: str, city: str):
        """Confirme la création de la nouvelle campagne"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        # Récupérer les détails de la niche
        niches = self.api_client.get_available_niches() or []
        niche_name = "Niche inconnue"
        for niche in niches:
            if str(niche.get('id')) == str(niche_id):
                niche_name = niche.get('name', 'Niche inconnue')
                break
        
        text = f"""✅ **Confirmation de création**

Vous êtes sur le point de créer une nouvelle campagne :

📂 **Niche :** {niche_name}
🏙️ **Ville :** {city}
🎯 **Objectif leads :** 50 (par défaut)
📊 **Type :** Prospection automatisée

**Voulez-vous confirmer la création ?**

⚠️ Cette action va :
• Créer la campagne dans le système
• L'envoyer à l'OverseerAgent pour traitement
• Commencer la prospection automatiquement
"""
        
        from utils.keyboards import get_confirm_creation_keyboard
        keyboard = get_confirm_creation_keyboard(niche_id, city)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _create_new_campaign(self, query, niche_id: str, city: str):
        """Crée effectivement la nouvelle campagne"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        # Récupérer les détails de la niche
        niches = self.api_client.get_available_niches() or []
        niche_name = "Niche inconnue"
        for niche in niches:
            if str(niche.get('id')) == str(niche_id):
                niche_name = niche.get('name', 'Niche inconnue')
                break
        
        # Créer la campagne via l'API
        result = self.api_client.create_new_campaign(
            niche_id=int(niche_id),
            niche_name=niche_name,
            city=city,
            target_leads=50,
            description=f"Campagne {niche_name} - {city} créée via Telegram"
        )
        
        if result:
            campaign_id = result.get('id', 'N/A')
            text = format_success(f"""🎉 **Campagne créée avec succès !**

📋 **ID :** {campaign_id}
📂 **Niche :** {niche_name}  
🏙️ **Ville :** {city}
🎯 **Objectif :** 50 leads

✅ **La campagne a été envoyée à l'OverseerAgent**
🚀 **La prospection va commencer automatiquement**

Vous pouvez suivre l'évolution dans "Campagnes actives".
""")
        else:
            text = format_error("""❌ **Erreur lors de la création**

Impossible de créer la campagne. Causes possibles :
• Niche non disponible
• Problème de connexion API
• Configuration manquante

Veuillez réessayer ou contacter l'administrateur.
""")
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("campaigns_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_start_campaign_menu(self, query):
        """Affiche le menu pour démarrer une campagne"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        campaigns = self.api_client.get_inactive_campaigns()
        
        if campaigns:
            text = "🚀 **Choisissez une campagne à démarrer :**\n\n"
            text += format_campaign_list(campaigns)
            keyboard = get_campaigns_list_keyboard(campaigns)
        else:
            text = "ℹ️ Aucune campagne inactive à démarrer"
            keyboard = get_back_keyboard("campaigns_main")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_stop_campaign_menu(self, query):
        """Affiche le menu pour arrêter une campagne"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        campaigns = self.api_client.get_active_campaigns()
        
        if campaigns:
            text = "🛑 **Choisissez une campagne à arrêter :**\n\n"
            text += format_campaign_list(campaigns)
            keyboard = get_campaigns_list_keyboard(campaigns)
        else:
            text = "ℹ️ Aucune campagne active à arrêter"
            keyboard = get_back_keyboard("campaigns_main")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_restart_campaign_menu(self, query):
        """Affiche le menu pour relancer une campagne"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        campaigns = self.api_client.get_inactive_campaigns()
        
        if campaigns:
            text = "🔄 **Choisissez une campagne à relancer :**\n\n"
            text += format_campaign_list(campaigns)
            keyboard = get_campaigns_list_keyboard(campaigns)
        else:
            text = "ℹ️ Aucune campagne inactive à relancer"
            keyboard = get_back_keyboard("campaigns_main")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_export_menu(self, query):
        """Affiche le menu d'export"""
        text = """📤 **Export des données**

Fonctionnalité d'export en cours de développement.
Vous pourrez bientôt exporter :
• Données des campagnes
• Listes de leads
• Statistiques détaillées
• Rapports de performance

Contactez l'administrateur pour un export manuel.
"""
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("campaigns_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_campaign_details(self, query, campaign_id: str):
        """Affiche les détails d'une campagne"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        campaign = self.api_client.get_campaign_details(campaign_id)
        
        if campaign:
            text = format_campaign_details(campaign)
            
            # Boutons d'action selon le statut
            if campaign.get('status') == 'active':
                keyboard = get_confirmation_keyboard("stop", campaign_id)
            else:
                keyboard = get_confirmation_keyboard("start", campaign_id)
        else:
            text = "❌ Campagne non trouvée"
            keyboard = get_back_keyboard("campaigns_main")
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _start_campaign(self, query, campaign_id: str):
        """Démarre une campagne"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        result = self.api_client.start_campaign(campaign_id)
        
        if result:
            text = format_success(f"Campagne {campaign_id} démarrée avec succès")
        else:
            text = format_error("Impossible de démarrer la campagne")
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("campaigns_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _stop_campaign(self, query, campaign_id: str):
        """Arrête une campagne"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        result = self.api_client.stop_campaign(campaign_id)
        
        if result:
            text = format_success(f"Campagne {campaign_id} arrêtée avec succès")
        else:
            text = format_error("Impossible d'arrêter la campagne")
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("campaigns_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _restart_campaign(self, query, campaign_id: str):
        """Relance une campagne"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        result = self.api_client.restart_campaign(campaign_id)
        
        if result:
            text = format_success(f"🔄 Campagne {campaign_id} relancée avec succès")
        else:
            text = format_error("Impossible de relancer la campagne")
        
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard("campaigns_main"),
            parse_mode=ParseMode.MARKDOWN
        )

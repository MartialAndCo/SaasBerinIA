"""Handler pour les statistiques du bot Telegram"""
import logging
from telegram.constants import ParseMode

from services.api_client import BeriniaAPIClient
from utils.keyboards import get_back_keyboard, get_stats_menu_keyboard
from utils.formatters import (
    format_stats_summary, format_leads_summary, truncate_text,
    format_error, format_loading
)

logger = logging.getLogger(__name__)

class StatsHandler:
    """Gestionnaire des statistiques"""
    
    def __init__(self):
        self.api_client = BeriniaAPIClient()
    
    async def handle_callback(self, query, callback_data: str):
        """Gère les callbacks des statistiques"""
        try:
            if callback_data == "stats_leads_volume":
                await self._show_leads_volume(query)
            
            elif callback_data == "stats_conversion":
                await self._show_conversion_stats(query)
            
            elif callback_data == "stats_responses":
                await self._show_responses_distribution(query)
            
            elif callback_data == "stats_history":
                await self._show_performance_history(query)
            
            elif callback_data == "stats_compensation":
                await self._show_total_compensation(query)
            
            else:
                await query.edit_message_text(
                    text="❌ Action statistique non reconnue",
                    reply_markup=get_stats_menu_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Erreur dans StatsHandler: {e}")
            await query.edit_message_text(
                text=format_error(str(e)),
                reply_markup=get_stats_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _show_leads_volume(self, query):
        """Affiche le volume total de leads"""
        # Message de chargement
        await query.edit_message_text(
            text=format_loading(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Récupération des données
        leads_count = self.api_client.get_leads_count()
        leads_stats = self.api_client.get_leads_stats()
        
        if leads_count and leads_stats:
            text = f"""📊 **Volume total de leads**

🔢 **Nombre total :** {leads_count.get('total', 0)}
📈 **Nouveaux cette semaine :** {leads_count.get('this_week', 0)}
📅 **Nouveaux ce mois :** {leads_count.get('this_month', 0)}

**Répartition par statut :**
• Nouveaux : {leads_stats.get('new_count', 0)}
• En cours : {leads_stats.get('in_progress_count', 0)}
• Qualifiés : {leads_stats.get('qualified_count', 0)}
• Contactés : {leads_stats.get('contacted_count', 0)}
• Répondus : {leads_stats.get('responded_count', 0)}

📈 **Évolution :** {leads_stats.get('trend', 'stable')}
"""
        else:
            text = "❌ Impossible de récupérer les données de volume des leads"
        
        await query.edit_message_text(
            text=truncate_text(text),
            reply_markup=get_back_keyboard("stats_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_conversion_stats(self, query):
        """Affiche les taux de conversion"""
        await query.edit_message_text(
            text=format_loading(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        stats = self.api_client.get_general_stats()
        
        if stats:
            text = f"""📈 **Taux de conversion globaux**

🎯 **Conversion globale :** {stats.get('conversion_rate', 0)}%
✅ **Taux de qualification :** {stats.get('qualification_rate', 0)}%
💬 **Taux de réponse :** {stats.get('response_rate', 0)}%
📞 **Taux de contact :** {stats.get('contact_rate', 0)}%

**Par canal :**
• Email : {stats.get('email_conversion', 0)}%
• SMS : {stats.get('sms_conversion', 0)}%
• WhatsApp : {stats.get('whatsapp_conversion', 0)}%

**Comparaison période :**
• Cette semaine : {stats.get('weekly_conversion', 0)}%
• Mois dernier : {stats.get('last_month_conversion', 0)}%
• Évolution : {stats.get('conversion_trend', 'stable')}
"""
        else:
            text = "❌ Impossible de récupérer les taux de conversion"
        
        await query.edit_message_text(
            text=truncate_text(text),
            reply_markup=get_back_keyboard("stats_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_responses_distribution(self, query):
        """Affiche la répartition des réponses"""
        await query.edit_message_text(
            text=format_loading(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        stats = self.api_client.get_leads_stats()
        
        if stats:
            total_responses = (
                stats.get('positive_responses', 0) + 
                stats.get('neutral_responses', 0) + 
                stats.get('negative_responses', 0)
            )
            
            if total_responses > 0:
                positive_pct = round((stats.get('positive_responses', 0) / total_responses) * 100, 1)
                neutral_pct = round((stats.get('neutral_responses', 0) / total_responses) * 100, 1)
                negative_pct = round((stats.get('negative_responses', 0) / total_responses) * 100, 1)
            else:
                positive_pct = neutral_pct = negative_pct = 0
            
            text = f"""💬 **Répartition des réponses**

📊 **Total des réponses :** {total_responses}

**Répartition :**
✅ **Positives :** {stats.get('positive_responses', 0)} ({positive_pct}%)
😐 **Neutres :** {stats.get('neutral_responses', 0)} ({neutral_pct}%)
❌ **Négatives :** {stats.get('negative_responses', 0)} ({negative_pct}%)

**Détail des réponses positives :**
• Intéressés : {stats.get('interested_count', 0)}
• RDV pris : {stats.get('meeting_booked', 0)}
• Devis demandés : {stats.get('quote_requested', 0)}

**Motifs de refus principaux :**
• Pas intéressé : {stats.get('not_interested', 0)}
• Mauvais timing : {stats.get('bad_timing', 0)}
• Budget insuffisant : {stats.get('budget_issue', 0)}
"""
        else:
            text = "❌ Impossible de récupérer la répartition des réponses"
        
        await query.edit_message_text(
            text=truncate_text(text),
            reply_markup=get_back_keyboard("stats_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_performance_history(self, query):
        """Affiche l'historique des performances"""
        await query.edit_message_text(
            text=format_loading(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        stats = self.api_client.get_general_stats()
        
        if stats:
            text = f"""📈 **Historique des performances**

**Cette semaine :**
• Leads générés : {stats.get('weekly_leads', 0)}
• Taux de conversion : {stats.get('weekly_conversion', 0)}%
• Revenus : {stats.get('weekly_revenue', 0)}€

**Ce mois :**
• Leads générés : {stats.get('monthly_leads', 0)}
• Taux de conversion : {stats.get('monthly_conversion', 0)}%
• Revenus : {stats.get('monthly_revenue', 0)}€

**Mois dernier :**
• Leads générés : {stats.get('last_month_leads', 0)}
• Taux de conversion : {stats.get('last_month_conversion', 0)}%
• Revenus : {stats.get('last_month_revenue', 0)}€

**Évolutions :**
📊 Leads : {stats.get('leads_trend', 'stable')}
💰 Revenus : {stats.get('revenue_trend', 'stable')}
📈 Conversion : {stats.get('conversion_trend', 'stable')}

**Meilleure performance :**
📅 Date : {stats.get('best_day', 'N/A')}
🎯 Conversion : {stats.get('best_conversion', 0)}%
"""
        else:
            text = "❌ Impossible de récupérer l'historique des performances"
        
        await query.edit_message_text(
            text=truncate_text(text),
            reply_markup=get_back_keyboard("stats_main"),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_total_compensation(self, query):
        """Affiche la compensation totale"""
        await query.edit_message_text(
            text=format_loading(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        stats = self.api_client.get_general_stats()
        
        if stats:
            text = f"""💰 **Compensation totale cumulée**

🏆 **Total général :** {stats.get('total_compensation', 0)}€
📊 **Moyenne par lead :** {stats.get('avg_compensation_per_lead', 0)}€
🎯 **Compensation/campagne :** {stats.get('avg_compensation_per_campaign', 0)}€

**Répartition temporelle :**
• Cette semaine : {stats.get('weekly_compensation', 0)}€
• Ce mois : {stats.get('monthly_compensation', 0)}€
• Mois dernier : {stats.get('last_month_compensation', 0)}€

**Répartition par source :**
• Email : {stats.get('email_compensation', 0)}€
• SMS : {stats.get('sms_compensation', 0)}€
• WhatsApp : {stats.get('whatsapp_compensation', 0)}€

**Top 3 niches rentables :**
1. {stats.get('top_niche_1', 'N/A')} - {stats.get('top_niche_1_comp', 0)}€
2. {stats.get('top_niche_2', 'N/A')} - {stats.get('top_niche_2_comp', 0)}€
3. {stats.get('top_niche_3', 'N/A')} - {stats.get('top_niche_3_comp', 0)}€

📈 **Évolution :** {stats.get('compensation_trend', 'stable')}
🎯 **Objectif du mois :** {stats.get('monthly_target', 0)}€
"""
        else:
            text = "❌ Impossible de récupérer les données de compensation"
        
        await query.edit_message_text(
            text=truncate_text(text),
            reply_markup=get_back_keyboard("stats_main"),
            parse_mode=ParseMode.MARKDOWN
        )

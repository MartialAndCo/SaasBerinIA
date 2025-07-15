"""Handler dédié pour la gestion des meetings et conversions"""

import logging
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from services.api_client import BeriniaAPIClient
from utils.formatters import format_loading, format_error

logger = logging.getLogger(__name__)

class MeetingHandler:
    """Gestionnaire spécialisé pour les meetings"""
    
    def __init__(self):
        self.api_client = BeriniaAPIClient()
    
    async def handle_callback(self, query, callback_data: str):
        """Route les callbacks meetings"""
        try:
            if callback_data.startswith("meeting_quick_"):
                await self._handle_quick_action(query, callback_data)
            elif callback_data.startswith("meeting_details_"):
                meeting_id = int(callback_data.split("_")[-1])
                await self._show_meeting_details(query, meeting_id)
            elif callback_data.startswith("meeting_convert_"):
                meeting_id = int(callback_data.split("_")[-1])
                await self._show_quick_conversion(query, meeting_id)
            else:
                await self._show_meetings_list(query)
        except Exception as e:
            logger.error(f"Erreur MeetingHandler: {e}")
            await query.edit_message_text(
                text=f"❌ Erreur: {str(e)}",
                reply_markup=self._get_back_to_main_keyboard()
            )
    
    async def _handle_quick_action(self, query, callback_data: str):
        """Gère les actions rapides: meeting_quick_MEETINGID_ACTION"""
        parts = callback_data.split("_")
        meeting_id = int(parts[2])
        action = parts[3]
        
        if action == "accept":
            result = self.api_client.convert_meeting(meeting_id, "accepted")
            if result:
                text = "✅ **Client accepté !**\\n\\nSuivi commercial nécessaire."
            else:
                text = "❌ Erreur lors de l'enregistrement"
                
        elif action == "refuse":
            text = "❌ **Raison du refus :**"
            keyboard = self._get_refusal_reasons_keyboard(meeting_id)
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
            return
            
        elif action == "thinking":
            result = self.api_client.convert_meeting(meeting_id, "thinking")
            if result:
                text = "🤔 **Client en réflexion**\\n\\nRelance dans 7 jours."
            else:
                text = "❌ Erreur lors de l'enregistrement"
                
        elif action == "noshow":
            result = self.api_client.convert_meeting(meeting_id, "no_show")
            if result:
                text = "👻 **Client absent**\\n\\nReport nécessaire."
            else:
                text = "❌ Erreur lors de l'enregistrement"
        
        await query.edit_message_text(
            text=text,
            reply_markup=self._get_back_to_meetings_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_quick_conversion(self, query, meeting_id: int):
        """Interface de conversion ultra-simplifiée"""
        # Vérifier si déjà converti
        outcome = self.api_client.get_meeting_outcome(meeting_id)
        if outcome and outcome.get("meeting_outcome"):
            await self._show_existing_outcome(query, outcome)
            return
        
        # Interface rapide pour nouveaux meetings
        text = f"🎯 **Conversion Meeting #{meeting_id}**\\n\\nRésultat du rendez-vous ?"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Accepté", callback_data=f"meeting_quick_{meeting_id}_accept"),
                InlineKeyboardButton("❌ Refusé", callback_data=f"meeting_quick_{meeting_id}_refuse")
            ],
            [
                InlineKeyboardButton("🤔 À réfléchir", callback_data=f"meeting_quick_{meeting_id}_thinking"),
                InlineKeyboardButton("👻 Absent", callback_data=f"meeting_quick_{meeting_id}_noshow")
            ],
            [InlineKeyboardButton("⬅️ Retour", callback_data="meetings_list")]
        ])
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_existing_outcome(self, query, outcome_data):
        """Affiche le résultat existant"""
        outcome = outcome_data["meeting_outcome"]
        
        status_emojis = {
            "accepted": "✅",
            "refused": "❌", 
            "thinking": "🤔",
            "no_show": "👻"
        }
        
        emoji = status_emojis.get(outcome["outcome_type"], "❓")
        text = f"{emoji} **Déjà converti**\\n\\n**Statut:** {outcome['outcome_type']}"
        
        if outcome.get("refusal_reason"):
            reasons = {
                'price_too_high': 'Prix trop élevé',
                'no_budget': 'Pas de budget',
                'bad_timing': 'Mauvais timing'
            }
            text += f"\\n**Raison:** {reasons.get(outcome['refusal_reason'], outcome['refusal_reason'])}"
        
        await query.edit_message_text(
            text=text,
            reply_markup=self._get_back_to_meetings_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _get_refusal_reasons_keyboard(self, meeting_id: int):
        """Clavier simplifié pour les raisons de refus"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Prix trop élevé", callback_data=f"refuse_{meeting_id}_price_too_high")],
            [InlineKeyboardButton("💸 Pas de budget", callback_data=f"refuse_{meeting_id}_no_budget")],
            [InlineKeyboardButton("⏰ Mauvais timing", callback_data=f"refuse_{meeting_id}_bad_timing")],
            [InlineKeyboardButton("⬅️ Retour", callback_data=f"meeting_convert_{meeting_id}")]
        ])
    
    def _get_back_to_meetings_keyboard(self):
        """Bouton retour vers les meetings"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Retour aux meetings", callback_data="meetings_list")]
        ])
    
    def _get_back_to_main_keyboard(self):
        """Bouton retour vers le menu principal"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu")]
        ])
    
    async def _show_meetings_list(self, query):
        """Liste simplifiée des meetings"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        meetings_data = self.api_client.get_upcoming_meetings(days=7)
        
        if not meetings_data or not meetings_data.get('meetings'):
            text = "📅 **Aucun meeting à venir**"
            keyboard = self._get_back_to_main_keyboard()
        else:
            meetings = meetings_data['meetings']
            text = f"📅 **Meetings à venir** ({len(meetings)})\\n\\n"
            
            keyboard_buttons = []
            for meeting in meetings[:5]:  # Limite à 5 pour simplicité
                date_str = meeting['start_time'][:10]
                time_str = meeting['start_time'][11:16]
                client = meeting['client_name']
                
                text += f"• **{client}** - {date_str} à {time_str}\\n"
                
                # Bouton de conversion rapide
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"🎯 {client}", 
                        callback_data=f"meeting_convert_{meeting['id']}"
                    )
                ])
            
            keyboard_buttons.append([InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
"""Wrapper pour le handler de rapport quotidien"""
import logging
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.daily_report import send_daily_report
from utils.keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

class DailyReportHandler:
    """Wrapper pour rendre le rapport quotidien compatible avec le nouveau système"""
    
    async def handle_callback(self, query, callback_data: str):
        """Gère les callbacks du rapport quotidien"""
        try:
            if callback_data == "daily_report_main":
                # Générer et envoyer le rapport
                await send_daily_report(query._bot.application, chat_id=query.from_user.id)
                
                # Ajouter un bouton de retour
                keyboard = [[InlineKeyboardButton("⬅️ Retour menu principal", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    "📊 Rapport quotidien envoyé !",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                
            else:
                # Callback non reconnu, retour au menu
                await query.edit_message_text(
                    text="❌ Action non reconnue",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"❌ Erreur dans DailyReportHandler: {e}")
            await query.edit_message_text(
                text="❌ Une erreur s'est produite lors de la génération du rapport quotidien",
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
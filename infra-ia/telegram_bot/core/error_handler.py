"""Gestionnaire d'erreurs robuste pour le bot Telegram"""
import logging
import traceback
from functools import wraps
from typing import Any, Callable, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class BotErrorHandler:
    """Gestionnaire centralisé des erreurs du bot"""
    
    @staticmethod
    def safe_handler(fallback_message: str = "Une erreur est survenue", 
                    fallback_callback: str = "main_menu"):
        """
        Décorateur pour gérer les erreurs de manière robuste
        
        Args:
            fallback_message: Message à afficher en cas d'erreur
            fallback_callback: Callback de retour en cas d'erreur
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Erreur dans {func.__name__}: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # Essayer de récupérer l'objet query depuis les arguments
                    query = None
                    for arg in args:
                        if hasattr(arg, 'edit_message_text'):
                            query = arg
                            break
                    
                    if query:
                        try:
                            await BotErrorHandler._send_error_response(
                                query, fallback_message, fallback_callback, str(e)
                            )
                        except Exception as nested_e:
                            logger.error(f"Erreur lors de l'envoi du message d'erreur: {nested_e}")
                    
                    return None
            return wrapper
        return decorator
    
    @staticmethod
    async def _send_error_response(query, fallback_message: str, 
                                 fallback_callback: str, error_details: str):
        """Envoie une réponse d'erreur sécurisée"""
        from core.safe_formatter import safe_formatter
        
        # Message d'erreur sécurisé
        safe_error = safe_formatter.sanitize_text(error_details, max_length=100)
        
        text = f"""❌ <b>Erreur</b>

{safe_formatter.escape_html(fallback_message)}

<i>Détails: {safe_formatter.escape_html(safe_error)}</i>"""
        
        # Clavier de retour sécurisé
        keyboard = [[InlineKeyboardButton("🏠 Menu principal", callback_data=fallback_callback)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    @staticmethod
    def log_callback_error(callback_data: str, error: Exception):
        """Log spécialisé pour les erreurs de callback"""
        logger.error(f"Erreur callback '{callback_data}': {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def log_api_error(endpoint: str, error: Exception):
        """Log spécialisé pour les erreurs d'API"""
        logger.error(f"Erreur API '{endpoint}': {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def validate_callback_data(callback_data: str) -> bool:
        """Valide un callback_data avant utilisation"""
        if not callback_data:
            logger.warning("Callback_data vide")
            return False
        
        if len(callback_data) >= 64:
            logger.error(f"Callback_data trop long ({len(callback_data)} chars): {callback_data}")
            return False
        
        # Vérifier les caractères problématiques
        problematic_chars = ['\n', '\r', '\t']
        for char in problematic_chars:
            if char in callback_data:
                logger.warning(f"Caractère problématique dans callback_data: '{char}'")
                return False
        
        return True

# Instance globale
error_handler = BotErrorHandler()

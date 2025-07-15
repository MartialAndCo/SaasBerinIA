"""Handler pour tester les notifications de paiement"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from config.settings import TELEGRAM_ADMIN_IDS

logger = logging.getLogger(__name__)


async def test_payment_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande pour tester les notifications de paiement"""
    
    # Vérifier que l'utilisateur est admin
    if update.effective_user.id not in TELEGRAM_ADMIN_IDS:
        await update.message.reply_text("❌ Vous n'êtes pas autorisé à utiliser cette commande.")
        return
    
    try:
        # Récupérer le service de notification depuis bot_data
        payment_notifier = context.application.bot_data.get('payment_notifier')
        
        if not payment_notifier:
            await update.message.reply_text("❌ Service de notifications de paiement non disponible.")
            return
        
        # Envoyer une notification de test
        success = await payment_notifier.send_test_notification(update.effective_chat.id)
        
        if success:
            await update.message.reply_text("✅ Notification de test envoyée !")
        else:
            await update.message.reply_text("❌ Échec de l'envoi de la notification de test.")
    
    except Exception as e:
        logger.error(f"Erreur lors du test de notification de paiement: {e}")
        await update.message.reply_text(f"❌ Erreur lors du test: {e}")


def get_payment_test_handlers():
    """Retourne les handlers pour les tests de paiement"""
    return [
        CommandHandler("test_payment", test_payment_notification),
        CommandHandler("test_paiement", test_payment_notification),
    ]
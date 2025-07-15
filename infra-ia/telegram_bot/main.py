"""
Bot Telegram pour la gestion du système BerinIA
Point d'entrée principal du bot
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from telegram.ext import Application
from telegram import Bot, BotCommand

# Configuration et handlers
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_IDS, LOG_LEVEL, DEBUG
from handlers.main_menu import get_handlers

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL.upper()),
    handlers=[
        logging.FileHandler('telegram_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def error_handler(update, context):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Exception lors du traitement de l'update {update}: {context.error}")
    
    # Notifier l'utilisateur en cas d'erreur
    if update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Une erreur inattendue s'est produite. Veuillez réessayer."
            )
        except Exception as e:
            logger.error(f"Impossible d'envoyer le message d'erreur: {e}")

async def setup_persistent_menu(bot: Bot):
    """Configure le menu persistant avec les 5 sections principales"""
    try:
        commands = [
            BotCommand(command="stats", description="📊 Statistiques"),
            BotCommand(command="campagnes", description="🎯 Campagnes"), 
            BotCommand(command="leads", description="👥 Leads"),
            BotCommand(command="niches", description="📂 Niches"),
            BotCommand(command="systeme", description="🧠 Système"),
            BotCommand(command="rapport", description="📊 Rapport quotidien"),
            BotCommand(command="help", description="❓ Aide")
        ]
        
        await bot.set_my_commands(commands)
        logger.info("Menu persistant configuré avec 7 commandes")
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du menu persistant: {e}")

async def post_init(application: Application):
    """Actions après l'initialisation du bot"""
    bot = application.bot
    bot_info = await bot.get_me()
    
    logger.info(f"Bot initialisé: @{bot_info.username} (ID: {bot_info.id})")
    logger.info(f"Administrateurs autorisés: {TELEGRAM_ADMIN_IDS}")
    
    # Configurer le menu persistant
    await setup_persistent_menu(bot)
    
    # Initialiser et démarrer le planificateur de rapport quotidien
    try:
        from services.daily_scheduler import initialize_daily_scheduler, start_daily_scheduler
        from datetime import time
        
        # Initialiser le planificateur (envoi à 9h00)
        scheduler = initialize_daily_scheduler(application, scheduled_time=time(9, 0))
        
        # Démarrer le planificateur
        await start_daily_scheduler()
        
        logger.info("Planificateur de rapport quotidien initialisé et démarré")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du planificateur: {e}")
    
    # Initialiser le service de notifications de paiement
    try:
        from services.api_client import APIClient
        from services.payment_notifier import PaymentNotifier
        from config.settings import API_BASE_URL
        
        # Créer l'API client et le notifier
        api_client = APIClient(base_url=API_BASE_URL)
        payment_notifier = PaymentNotifier(bot, api_client)
        
        # Stocker le notifier dans l'application pour pouvoir l'arrêter plus tard
        application.bot_data['payment_notifier'] = payment_notifier
        
        # Démarrer le service
        await payment_notifier.start()
        
        logger.info("Service de notifications de paiement initialisé et démarré")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du service de notifications de paiement: {e}")
    
    # Envoyer un message de démarrage aux admins
    startup_message = """🤖 **BerinIA Bot démarré !**

Le bot de gestion BerinIA est maintenant opérationnel.

📊 **Nouvelles fonctionnalités:**
• Rapport quotidien automatique à 9h00
• Commandes: `/rapport` ou `/daily`
• Intelligence temporelle des campagnes
• 💰 Notifications de paiement Stripe en temps réel

Tapez /start pour accéder au menu principal.
"""
    
    for admin_id in TELEGRAM_ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=startup_message,
                parse_mode='Markdown'
            )
            logger.info(f"Message de démarrage envoyé à l'admin {admin_id}")
        except Exception as e:
            logger.warning(f"Impossible d'envoyer le message de démarrage à {admin_id}: {e}")

async def post_shutdown(application: Application):
    """Actions avant l'arrêt du bot"""
    logger.info("Arrêt du bot BerinIA...")
    
    # Arrêter le planificateur de rapport quotidien
    try:
        from services.daily_scheduler import stop_daily_scheduler
        await stop_daily_scheduler()
        logger.info("Planificateur de rapport quotidien arrêté")
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt du planificateur: {e}")
    
    # Arrêter le service de notifications de paiement
    try:
        payment_notifier = application.bot_data.get('payment_notifier')
        if payment_notifier:
            await payment_notifier.stop()
            logger.info("Service de notifications de paiement arrêté")
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt du service de notifications de paiement: {e}")
    
    # Notifier les admins de l'arrêt
    shutdown_message = "🔴 **BerinIA Bot arrêté**\n\nLe bot de gestion a été arrêté."
    
    for admin_id in TELEGRAM_ADMIN_IDS:
        try:
            await application.bot.send_message(
                chat_id=admin_id,
                text=shutdown_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Impossible d'envoyer le message d'arrêt à {admin_id}: {e}")

def main():
    """Fonction principale"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN manquant !")
        sys.exit(1)
    
    if not TELEGRAM_ADMIN_IDS:
        logger.error("TELEGRAM_ADMIN_IDS manquant !")
        sys.exit(1)
    
    logger.info("Démarrage du bot Telegram BerinIA...")
    logger.info(f"Mode debug: {DEBUG}")
    
    # Créer l'application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Enregistrer le gestionnaire d'erreurs
    application.add_error_handler(error_handler)
    
    # Enregistrer tous les handlers de commandes et callbacks
    handlers = get_handlers()
    for handler in handlers:
        application.add_handler(handler)
        logger.debug(f"Handler enregistré: {type(handler).__name__}")
    
    # Configurer les hooks de démarrage/arrêt
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    
    # Démarrer le bot
    try:
        logger.info("Démarrage du polling...")
        application.run_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur (Ctrl+C)")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)

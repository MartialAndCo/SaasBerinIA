import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import aiohttp
from telegram import Bot
from telegram.constants import ParseMode

from config import settings
from services.api_client import APIClient

logger = logging.getLogger(__name__)


class PaymentNotifier:
    """Service pour gérer les notifications de paiement Telegram"""
    
    def __init__(self, bot: Bot, api_client: APIClient):
        self.bot = bot
        self.api_client = api_client
        self.polling_interval = 30  # Vérifier toutes les 30 secondes
        self.admin_chat_ids = settings.ADMIN_CHAT_IDS
        self.running = False
        self._task = None
        self.last_daily_summary = None
        
    async def start(self):
        """Démarrer le service de notification"""
        if self.running:
            logger.warning("Payment notifier already running")
            return
            
        self.running = True
        self._task = asyncio.create_task(self._polling_loop())
        logger.info("Payment notifier started")
        
    async def stop(self):
        """Arrêter le service de notification"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Payment notifier stopped")
        
    async def _polling_loop(self):
        """Boucle principale de polling"""
        while self.running:
            try:
                # Vérifier les nouvelles notifications
                await self._check_and_send_notifications()
                
                # Envoyer le résumé quotidien si nécessaire
                await self._check_daily_summary()
                
                # Attendre avant la prochaine vérification
                await asyncio.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Error in payment notifier polling loop: {e}")
                await asyncio.sleep(self.polling_interval)
    
    async def _check_and_send_notifications(self):
        """Vérifier et envoyer les notifications en attente"""
        try:
            # Récupérer les notifications non envoyées
            response = await self.api_client.get("/notifications/payments/unsent", params={"limit": 10})
            
            if response and "notifications" in response:
                notifications = response["notifications"]
                
                for notification in notifications:
                    try:
                        # Envoyer la notification à tous les admins
                        await self._send_notification_to_admins(notification)
                        
                        # Marquer comme envoyée
                        await self.api_client.post(
                            f"/notifications/payments/{notification['id']}/mark-sent"
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to send notification {notification['id']}: {e}")
                        # Marquer comme échouée
                        await self.api_client.post(
                            f"/notifications/payments/{notification['id']}/mark-failed",
                            json={"error_message": str(e)}
                        )
        
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
    
    async def _send_notification_to_admins(self, notification: Dict[str, Any]):
        """Envoyer une notification à tous les administrateurs"""
        message = notification.get("message", "")
        
        if not message:
            logger.error("Empty notification message")
            return
            
        # Envoyer à chaque admin
        for chat_id in self.admin_chat_ids:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                logger.info(f"Payment notification sent to admin {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to {chat_id}: {e}")
    
    async def _check_daily_summary(self):
        """Vérifier si le résumé quotidien doit être envoyé"""
        now = datetime.now()
        
        # Envoyer le résumé à 18h00
        if now.hour == 18 and now.minute < 1:
            # Vérifier si on n'a pas déjà envoyé le résumé aujourd'hui
            if self.last_daily_summary is None or self.last_daily_summary.date() < now.date():
                await self._send_daily_summary()
                self.last_daily_summary = now
    
    async def _send_daily_summary(self):
        """Envoyer le résumé quotidien des paiements"""
        try:
            # Récupérer le résumé
            response = await self.api_client.get("/notifications/payments/daily-summary")
            
            if response and "message" in response:
                message = response["message"]
                
                # Envoyer à tous les admins
                for chat_id in self.admin_chat_ids:
                    try:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=message,
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        logger.error(f"Failed to send daily summary to {chat_id}: {e}")
                
                logger.info("Daily payment summary sent")
        
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    async def send_test_notification(self, chat_id: int):
        """Envoyer une notification de test"""
        test_message = (
            "🧪 <b>Test de notification de paiement</b>\n\n"
            "💰 <b>Paiement reçu</b>\n"
            "📄 <b>Facture:</b> #TEST-001\n"
            "💳 <b>Montant:</b> 100.00 EUR\n"
            "👤 <b>Client:</b> Client Test\n"
            "📧 <b>Email:</b> test@example.com\n"
            "\n🕐 <b>Date:</b> " + datetime.now().strftime('%d/%m/%Y %H:%M')
        )
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=test_message,
                parse_mode=ParseMode.HTML
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            return False
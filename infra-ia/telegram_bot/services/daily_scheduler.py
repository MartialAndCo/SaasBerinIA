"""
Service de planification pour le rapport quotidien Telegram
"""
import asyncio
import logging
from datetime import datetime, time
from typing import Optional
from telegram.ext import Application

# Configuration du logger
logger = logging.getLogger(__name__)

class DailyReportScheduler:
    """Planificateur pour l'envoi automatique du rapport quotidien"""
    
    def __init__(self, app: Application, scheduled_time: time = time(9, 0)):
        """
        Initialise le planificateur
        
        Args:
            app: Application Telegram
            scheduled_time: Heure d'envoi quotidien (défaut: 9h00)
        """
        self.app = app
        self.scheduled_time = scheduled_time
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Démarre le planificateur"""
        if self.is_running:
            logger.warning("Le planificateur est déjà en cours d'exécution")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"Planificateur de rapport quotidien démarré (envoi à {self.scheduled_time})")
    
    async def stop(self):
        """Arrête le planificateur"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Planificateur de rapport quotidien arrêté")
    
    async def _scheduler_loop(self):
        """Boucle principale du planificateur"""
        logger.info("Boucle de planification démarrée")
        
        while self.is_running:
            try:
                # Calculer le temps jusqu'au prochain envoi
                now = datetime.now()
                today_scheduled = datetime.combine(now.date(), self.scheduled_time)
                
                # Si l'heure est déjà passée aujourd'hui, programmer pour demain
                if now >= today_scheduled:
                    from datetime import timedelta
                    tomorrow = now.date() + timedelta(days=1)
                    next_scheduled = datetime.combine(tomorrow, self.scheduled_time)
                else:
                    next_scheduled = today_scheduled
                
                # Calculer la durée d'attente
                wait_seconds = (next_scheduled - now).total_seconds()
                
                logger.info(f"Prochain rapport quotidien programmé à {next_scheduled} (dans {wait_seconds/3600:.1f}h)")
                
                # Attendre jusqu'à l'heure programmée
                await asyncio.sleep(wait_seconds)
                
                # Envoyer le rapport si toujours en cours d'exécution
                if self.is_running:
                    await self._send_daily_report()
                
            except asyncio.CancelledError:
                logger.info("Planificateur interrompu")
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle de planification: {e}")
                # Attendre 1 heure avant de réessayer en cas d'erreur
                await asyncio.sleep(3600)
    
    async def _send_daily_report(self):
        """Envoie le rapport quotidien à tous les admins"""
        try:
            logger.info("Envoi du rapport quotidien automatique")
            
            # Import local pour éviter les dépendances circulaires
            from handlers.daily_report import send_daily_report
            
            # Créer un contexte fictif pour l'envoi automatique
            from telegram.ext import ContextTypes
            
            # Utiliser le bot de l'application
            context = ContextTypes.DEFAULT_TYPE(self.app)
            context._bot = self.app.bot
            
            # Envoyer à tous les admins (chat_id=None)
            success = await send_daily_report(context, chat_id=None)
            
            if success:
                logger.info("Rapport quotidien envoyé avec succès")
            else:
                logger.error("Échec de l'envoi du rapport quotidien")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du rapport quotidien: {e}")
    
    async def send_test_report(self, chat_id: int):
        """
        Envoie un rapport de test à un chat spécifique
        
        Args:
            chat_id: ID du chat pour le test
        """
        try:
            logger.info(f"Envoi d'un rapport de test à {chat_id}")
            
            from handlers.daily_report import send_daily_report
            from telegram.ext import ContextTypes
            
            context = ContextTypes.DEFAULT_TYPE(self.app)
            context._bot = self.app.bot
            
            success = await send_daily_report(context, chat_id=chat_id)
            
            if success:
                logger.info("Rapport de test envoyé avec succès")
            else:
                logger.error("Échec de l'envoi du rapport de test")
                
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du rapport de test: {e}")
            return False


# Instance globale du planificateur
_daily_scheduler: Optional[DailyReportScheduler] = None

def initialize_daily_scheduler(app: Application, scheduled_time: time = time(9, 0)) -> DailyReportScheduler:
    """
    Initialise le planificateur de rapport quotidien
    
    Args:
        app: Application Telegram
        scheduled_time: Heure d'envoi quotidien
        
    Returns:
        Instance du planificateur
    """
    global _daily_scheduler
    
    if _daily_scheduler is not None:
        # Arrêter l'ancien planificateur
        asyncio.create_task(_daily_scheduler.stop())
    
    _daily_scheduler = DailyReportScheduler(app, scheduled_time)
    return _daily_scheduler

def get_daily_scheduler() -> Optional[DailyReportScheduler]:
    """
    Retourne l'instance du planificateur quotidien
    
    Returns:
        Instance du planificateur ou None si pas initialisé
    """
    return _daily_scheduler

async def start_daily_scheduler():
    """Démarre le planificateur quotidien"""
    if _daily_scheduler:
        await _daily_scheduler.start()
    else:
        logger.error("Planificateur quotidien non initialisé")

async def stop_daily_scheduler():
    """Arrête le planificateur quotidien"""
    if _daily_scheduler:
        await _daily_scheduler.stop()

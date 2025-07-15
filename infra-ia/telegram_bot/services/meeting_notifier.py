"""
Service de notification Telegram pour les nouveaux rendez-vous
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import telegram
from telegram.constants import ParseMode

from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_IDS
from services.api_client import BeriniaAPIClient
from utils.keyboards import get_meeting_details_keyboard

logger = logging.getLogger(__name__)

class MeetingNotifierService:
    """Service pour envoyer des notifications de nouveaux RDV"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.admin_ids = TELEGRAM_ADMIN_IDS
        self.api_client = BeriniaAPIClient()
        self.bot = None
        
    async def initialize_bot(self):
        """Initialise le bot Telegram"""
        if not self.bot:
            self.bot = telegram.Bot(token=self.bot_token)
    
    async def notify_new_meeting(self, meeting_data: Dict[str, Any]) -> bool:
        """
        Envoie une notification pour un nouveau rendez-vous
        
        Args:
            meeting_data: Données du meeting (depuis l'API ou MeetingAgent)
            
        Returns:
            True si la notification a été envoyée avec succès
        """
        try:
            await self.initialize_bot()
            
            # Formater le message de notification
            notification_message = self._format_meeting_notification(meeting_data)
            
            # Récupérer le résumé de conversation si lead_id disponible (avec timeout court)
            conversation_summary = None
            if meeting_data.get('lead_id'):
                try:
                    # Timeout réduit pour éviter de bloquer la notification
                    import asyncio
                    loop = asyncio.get_event_loop()
                    conversation_data = await asyncio.wait_for(
                        loop.run_in_executor(None, self.api_client.get_lead_conversation_summary, meeting_data['lead_id']),
                        timeout=5  # 5 secondes max
                    )
                    if conversation_data and conversation_data.get('summary'):
                        conversation_summary = conversation_data['summary']
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout récupération résumé conversation pour lead {meeting_data['lead_id']}")
                except Exception as e:
                    logger.warning(f"Erreur récupération résumé conversation: {e}")
            
            # Ajouter le résumé au message
            if conversation_summary:
                notification_message += self._format_conversation_context(conversation_summary)
            
            # Créer le clavier avec bouton pour voir détails
            keyboard = None
            if meeting_data.get('meeting_id'):
                keyboard = get_meeting_details_keyboard(
                    meeting_data['meeting_id'], 
                    meeting_data.get('calendar_event_id')
                )
            
            # Envoyer à tous les admins
            success_count = 0
            for admin_id in self.admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=notification_message,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                    success_count += 1
                    logger.info(f"Notification RDV envoyée à l'admin {admin_id}")
                    
                except Exception as e:
                    logger.error(f"Erreur envoi notification à {admin_id}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification RDV: {e}")
            return False
    
    def _format_meeting_notification(self, meeting_data: Dict[str, Any]) -> str:
        """Formate le message de notification principal"""
        
        client_name = meeting_data.get('client_name', 'Client inconnu')
        client_email = meeting_data.get('client_email', '')
        start_time = meeting_data.get('start_time', '')
        meeting_link = meeting_data.get('meeting_link', '')
        company = meeting_data.get('company_name', '')
        
        # Formatage de la date
        try:
            if start_time:
                if isinstance(start_time, str):
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                else:
                    dt = start_time
                formatted_time = dt.strftime('%d/%m/%Y à %H:%M')
            else:
                formatted_time = 'Date à définir'
        except:
            formatted_time = str(start_time)[:16] if start_time else 'Date à définir'
        
        # Construction du message principal
        message = f"""🔔 **Nouveau Rendez-vous Booké !**

👤 **Client :** {client_name}
📧 **Email :** {client_email}"""

        if company:
            message += f"\n🏢 **Entreprise :** {company}"
        
        message += f"""

📅 **Date/Heure :** {formatted_time}
🔗 **Lien meeting :** {meeting_link[:50]}{'...' if len(meeting_link) > 50 else ''}

"""
        
        return message
    
    def _format_conversation_context(self, conversation_summary: Dict[str, Any]) -> str:
        """Formate le contexte de conversation pour la notification"""
        
        interest_level = conversation_summary.get('interest_level', 'unknown')
        summary_text = conversation_summary.get('summary', '')
        key_points = conversation_summary.get('key_points', [])
        next_actions = conversation_summary.get('next_actions', [])
        
        # Emoji selon le niveau d'intérêt
        interest_emojis = {
            'high': '🔥',
            'medium': '🟡', 
            'low': '🔵',
            'unknown': '❓'
        }
        interest_emoji = interest_emojis.get(interest_level, '❓')
        
        context = f"""💬 **Contexte de la conversation:**

📊 **Niveau d'intérêt :** {interest_emoji} {interest_level.title()}

📝 **Résumé :** {summary_text[:200]}{'...' if len(summary_text) > 200 else ''}"""
        
        # Ajouter les points clés les plus importants
        if key_points:
            context += f"\n\n🔑 **Points clés :**"
            for point in key_points[:3]:  # Max 3 points
                context += f"\n• {point}"
        
        # Ajouter les actions recommandées
        if next_actions:
            context += f"\n\n🎯 **Actions recommandées :**"
            for action in next_actions[:2]:  # Max 2 actions
                context += f"\n• {action}"
        
        return context + "\n"
    
    async def notify_meeting_cancelled(self, meeting_data: Dict[str, Any], reason: str = None) -> bool:
        """Notifie l'annulation d'un rendez-vous"""
        try:
            await self.initialize_bot()
            
            client_name = meeting_data.get('client_name', 'Client inconnu')
            start_time = meeting_data.get('start_time', '')
            
            try:
                if start_time:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%d/%m/%Y à %H:%M')
                else:
                    formatted_time = 'Date inconnue'
            except:
                formatted_time = str(start_time)[:16] if start_time else 'Date inconnue'
            
            message = f"""❌ **Rendez-vous Annulé**

👤 **Client :** {client_name}
📅 **Date/Heure :** {formatted_time}"""
            
            if reason:
                message += f"\n📝 **Raison :** {reason}"
            
            message += f"\n\n🕐 **Annulé le :** {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
            
            # Envoyer à tous les admins
            success_count = 0
            for admin_id in self.admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Erreur envoi notification annulation à {admin_id}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Erreur notification annulation RDV: {e}")
            return False
    
    async def notify_meeting_rescheduled(self, meeting_data: Dict[str, Any], 
                                       old_time: str, new_time: str, reason: str = None) -> bool:
        """Notifie le report d'un rendez-vous"""
        try:
            await self.initialize_bot()
            
            client_name = meeting_data.get('client_name', 'Client inconnu')
            
            # Formatage des dates
            try:
                old_dt = datetime.fromisoformat(old_time.replace('Z', '+00:00'))
                old_formatted = old_dt.strftime('%d/%m/%Y à %H:%M')
            except:
                old_formatted = str(old_time)[:16]
                
            try:
                new_dt = datetime.fromisoformat(new_time.replace('Z', '+00:00'))
                new_formatted = new_dt.strftime('%d/%m/%Y à %H:%M')
            except:
                new_formatted = str(new_time)[:16]
            
            message = f"""📅 **Rendez-vous Reporté**

👤 **Client :** {client_name}
⏰ **Ancienne date :** {old_formatted}
🔄 **Nouvelle date :** {new_formatted}"""
            
            if reason:
                message += f"\n📝 **Raison :** {reason}"
            
            message += f"\n\n🕐 **Modifié le :** {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
            
            # Envoyer à tous les admins
            success_count = 0
            for admin_id in self.admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Erreur envoi notification report à {admin_id}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Erreur notification report RDV: {e}")
            return False

# Instance globale du service
meeting_notifier = MeetingNotifierService()

async def send_meeting_notification(meeting_data: Dict[str, Any]) -> bool:
    """
    Fonction utilitaire pour envoyer une notification de nouveau RDV
    
    Args:
        meeting_data: Données du meeting à notifier
        
    Returns:
        True si la notification a été envoyée avec succès
    """
    return await meeting_notifier.notify_new_meeting(meeting_data)

async def send_meeting_cancellation_notification(meeting_data: Dict[str, Any], reason: str = None) -> bool:
    """Fonction utilitaire pour notifier l'annulation d'un RDV"""
    return await meeting_notifier.notify_meeting_cancelled(meeting_data, reason)

async def send_meeting_reschedule_notification(meeting_data: Dict[str, Any], 
                                             old_time: str, new_time: str, reason: str = None) -> bool:
    """Fonction utilitaire pour notifier le report d'un RDV"""
    return await meeting_notifier.notify_meeting_rescheduled(meeting_data, old_time, new_time, reason)
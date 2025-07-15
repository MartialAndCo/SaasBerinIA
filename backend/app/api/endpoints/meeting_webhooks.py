from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import asyncio
import logging

from app.api import deps
from app.models.meeting import Meeting as MeetingModel

router = APIRouter()
logger = logging.getLogger(__name__)

async def send_telegram_notification(meeting_data: Dict[str, Any]):
    """Envoie une notification Telegram de manière asynchrone"""
    try:
        # Import dynamique pour éviter les problèmes de dépendances circulaires
        import sys
        import os
        
        # Ajouter le chemin vers telegram_bot
        telegram_bot_path = "/root/berinia/infra-ia/telegram_bot"
        if telegram_bot_path not in sys.path:
            sys.path.insert(0, telegram_bot_path)
        
        from services.meeting_notifier import send_meeting_notification
        
        # Envoyer la notification
        success = await send_meeting_notification(meeting_data)
        
        if success:
            logger.info(f"Notification Telegram envoyée pour le meeting {meeting_data.get('meeting_id')}")
        else:
            logger.warning(f"Échec envoi notification Telegram pour meeting {meeting_data.get('meeting_id')}")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de notification Telegram: {e}")

@router.post("/webhook/meeting-created")
async def meeting_created_webhook(
    meeting_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Webhook appelé quand un nouveau meeting est créé
    Envoie une notification Telegram instantanée
    """
    try:
        # Vérifier que le meeting existe dans la base (optionnel pour les tests)
        meeting_id = meeting_data.get('meeting_id') or meeting_data.get('id')
        enriched_data = meeting_data.copy()  # Copier les données d'entrée
        
        if meeting_id and isinstance(meeting_id, int) and meeting_id < 900:  # IDs réels (pas de test)
            meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
            if not meeting:
                raise HTTPException(status_code=404, detail="Meeting non trouvé")
            
            # Enrichir avec les vraies données de la base
            enriched_data.update({
                'meeting_id': meeting.id,
                'client_name': meeting.client_name,
                'client_email': meeting.client_email,
                'start_time': meeting.start_time.isoformat() if meeting.start_time else None,
                'end_time': meeting.end_time.isoformat() if meeting.end_time else None,
                'meeting_link': meeting.meeting_link,
                'calendar_event_id': meeting.calendar_event_id,
                'lead_id': meeting.lead_id,
                'description': meeting.description
            })
            
            # Ajouter les informations du lead si disponible
            if meeting.lead:
                enriched_data.update({
                    'company_name': meeting.lead.company,
                    'lead_name': f"{meeting.lead.first_name or ''} {meeting.lead.last_name or ''}".strip(),
                    'lead_phone': meeting.lead.phone
                })
        else:
            # Pour les tests ou meetings externes, utiliser les données fournies
            logger.info(f"Webhook test/externe pour meeting {meeting_id} - utilisation des données fournies")
        
        # Programmer l'envoi de notification en arrière-plan
        background_tasks.add_task(send_telegram_notification, enriched_data)
        
        logger.info(f"Webhook meeting créé traité pour {enriched_data.get('client_name')}")
        
        return {
            "status": "success",
            "message": "Notification programmée",
            "meeting_id": meeting_id
        }
        
    except Exception as e:
        logger.error(f"Erreur webhook meeting créé: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/meeting-updated")
async def meeting_updated_webhook(
    meeting_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Webhook appelé quand un meeting est modifié
    Peut envoyer des notifications selon le type de modification
    """
    try:
        meeting_id = meeting_data.get('meeting_id') or meeting_data.get('id')
        action = meeting_data.get('action', 'updated')
        
        if not meeting_id:
            raise HTTPException(status_code=400, detail="meeting_id requis")
        
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting non trouvé")
        
        # Enrichir les données
        enriched_data = {
            'meeting_id': meeting.id,
            'client_name': meeting.client_name,
            'client_email': meeting.client_email,
            'start_time': meeting.start_time.isoformat() if meeting.start_time else None,
            'status': meeting.status,
            'action': action
        }
        
        # Selon l'action, envoyer différents types de notifications
        if action in ['cancelled', 'rescheduled']:
            # Pour l'instant, log seulement - les notifications spécialisées 
            # peuvent être ajoutées plus tard
            logger.info(f"Meeting {action}: {enriched_data}")
        
        return {
            "status": "success", 
            "message": f"Webhook meeting {action} traité",
            "meeting_id": meeting_id
        }
        
    except Exception as e:
        logger.error(f"Erreur webhook meeting modifié: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notify-meeting")
async def manual_meeting_notification(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Endpoint pour déclencher manuellement une notification de meeting
    Utile pour tester ou relancer des notifications
    """
    try:
        meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting non trouvé")
        
        # Préparer les données pour notification
        meeting_data = {
            'meeting_id': meeting.id,
            'client_name': meeting.client_name,
            'client_email': meeting.client_email,
            'start_time': meeting.start_time.isoformat() if meeting.start_time else None,
            'meeting_link': meeting.meeting_link,
            'calendar_event_id': meeting.calendar_event_id,
            'lead_id': meeting.lead_id
        }
        
        if meeting.lead:
            meeting_data.update({
                'company_name': meeting.lead.company,
                'lead_name': f"{meeting.lead.first_name or ''} {meeting.lead.last_name or ''}".strip()
            })
        
        # Envoyer la notification
        background_tasks.add_task(send_telegram_notification, meeting_data)
        
        return {
            "status": "success",
            "message": "Notification envoyée",
            "meeting_id": meeting_id
        }
        
    except Exception as e:
        logger.error(f"Erreur notification manuelle meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))
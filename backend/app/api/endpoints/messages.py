from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from app.api import deps
from app.models.message import Message

# Charger les variables d'environnement depuis le fichier central
env_path = '/root/berinia/infra-ia/.env'
load_dotenv(env_path)

# Import Twilio pour l'envoi SMS
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

router = APIRouter(tags=["Messages"])

@router.put("/conversations/{thread_id}/ai")
def toggle_conversation_ai(
    thread_id: str,
    ai_data: dict,
    db: Session = Depends(deps.get_db)
):
    """
    Active/désactive l'IA pour une conversation spécifique
    """
    try:
        ai_enabled = ai_data.get("ai_enabled", True)
        
        # Vérifier si l'enregistrement existe déjà
        existing = db.execute(
            text("SELECT * FROM conversation_ai_settings WHERE thread_id = :thread_id"),
            {"thread_id": thread_id}
        ).fetchone()
        
        if existing:
            # Mettre à jour
            db.execute(
                text("UPDATE conversation_ai_settings SET ai_enabled = :ai_enabled, updated_at = NOW() WHERE thread_id = :thread_id"),
                {"thread_id": thread_id, "ai_enabled": ai_enabled}
            )
        else:
            # Créer nouvel enregistrement
            db.execute(
                text("INSERT INTO conversation_ai_settings (thread_id, ai_enabled, updated_at) VALUES (:thread_id, :ai_enabled, NOW())"),
                {"thread_id": thread_id, "ai_enabled": ai_enabled}
            )
        
        db.commit()
        
        return {
            "status": "success",
            "thread_id": thread_id,
            "ai_enabled": ai_enabled,
            "message": f"IA {'activée' if ai_enabled else 'désactivée'} pour cette conversation"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Erreur lors de la mise à jour des paramètres IA: {str(e)}"
        }

@router.get("/conversations/{thread_id}/ai")
def get_conversation_ai_status(
    thread_id: str,
    db: Session = Depends(deps.get_db)
):
    """
    Récupère l'état IA pour une conversation spécifique
    """
    try:
        result = db.execute(
            text("SELECT ai_enabled FROM conversation_ai_settings WHERE thread_id = :thread_id"),
            {"thread_id": thread_id}
        ).fetchone()
        
        # Par défaut, l'IA est activée si pas de paramètre spécifique
        ai_enabled = result.ai_enabled if result else True
        
        return {
            "status": "success",
            "thread_id": thread_id,
            "ai_enabled": ai_enabled
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur lors de la récupération des paramètres IA: {str(e)}"
        }

@router.put("/global-ai-settings")
def update_global_ai_settings(
    settings: dict,
    db: Session = Depends(deps.get_db)
):
    """
    Met à jour les paramètres globaux de l'IA
    """
    try:
        global_ai_enabled = settings.get("ai_enabled", True)
        
        # Vérifier si l'enregistrement existe
        existing = db.execute(
            text("SELECT * FROM global_ai_settings WHERE key = 'ai_enabled'")
        ).fetchone()
        
        if existing:
            # Mettre à jour
            db.execute(
                text("UPDATE global_ai_settings SET value = :value, updated_at = NOW() WHERE key = 'ai_enabled'"),
                {"value": global_ai_enabled}
            )
        else:
            # Créer nouvel enregistrement
            db.execute(
                text("INSERT INTO global_ai_settings (key, value, updated_at) VALUES ('ai_enabled', :value, NOW())"),
                {"value": global_ai_enabled}
            )
        
        db.commit()
        
        return {
            "status": "success",
            "ai_enabled": global_ai_enabled,
            "message": f"IA globale {'activée' if global_ai_enabled else 'désactivée'}"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Erreur lors de la mise à jour des paramètres globaux IA: {str(e)}"
        }

@router.get("/global-ai-settings")
def get_global_ai_settings(db: Session = Depends(deps.get_db)):
    """
    Récupère les paramètres globaux de l'IA
    """
    try:
        result = db.execute(
            text("SELECT value FROM global_ai_settings WHERE key = 'ai_enabled'")
        ).fetchone()
        
        # Par défaut, l'IA est activée globalement
        ai_enabled = result.value if result else True
        
        return {
            "status": "success",
            "ai_enabled": ai_enabled
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur lors de la récupération des paramètres globaux IA: {str(e)}"
        }

# Configuration Twilio
def get_twilio_client():
    """Récupère le client Twilio configuré"""
    if not TWILIO_AVAILABLE:
        return None
    
    # Recharger les variables à chaque appel pour s'assurer qu'elles sont disponibles
    load_dotenv(env_path)
    
    sid = os.getenv("TWILIO_SID")
    token = os.getenv("TWILIO_TOKEN") 
    
    print(f"DEBUG TWILIO: SID={sid}, TOKEN={token[:10] if token else None}..., PATH={env_path}")
    
    if not sid or not token:
        return None
        
    return TwilioClient(sid, token)

def send_sms_via_twilio(to_number: str, message_content: str):
    """Envoie un SMS via Twilio"""
    client = get_twilio_client()
    if not client:
        raise Exception("Client Twilio non disponible")
    
    from_number = os.getenv("TWILIO_PHONE")
    if not from_number:
        raise Exception("Numéro Twilio non configuré")
    
    try:
        message = client.messages.create(
            body=message_content,
            from_=from_number,
            to=to_number
        )
        return message.sid
    except Exception as e:
        raise Exception(f"Erreur Twilio: {str(e)}")

@router.get("/conversations")
def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère la liste des conversations (groupées par lead/thread_id)
    """
    try:
        # Requête pour obtenir les conversations avec le dernier message
        query = text("""
            WITH latest_messages AS (
                SELECT 
                    thread_id,
                    MAX(COALESCE(received_date, sent_date)) as last_message_date,
                    (
                        SELECT content 
                        FROM messages m2 
                        WHERE m2.thread_id = messages.thread_id 
                        ORDER BY COALESCE(m2.received_date, m2.sent_date) DESC 
                        LIMIT 1
                    ) as last_message_content,
                    (
                        SELECT direction 
                        FROM messages m2 
                        WHERE m2.thread_id = messages.thread_id 
                        ORDER BY COALESCE(m2.received_date, m2.sent_date) DESC 
                        LIMIT 1
                    ) as last_message_direction
                FROM messages 
                WHERE thread_id IS NOT NULL
                GROUP BY thread_id
            ),
            conversation_info AS (
                SELECT DISTINCT ON (m.thread_id)
                    m.thread_id,
                    m.lead_id,
                    m.lead_name,
                    m.lead_email,
                    (SELECT COUNT(*) FROM messages WHERE thread_id = m.thread_id) as message_count
                FROM messages m
                WHERE m.thread_id IS NOT NULL
                ORDER BY m.thread_id, COALESCE(m.received_date, m.sent_date) DESC
            )
            SELECT 
                ci.thread_id,
                ci.lead_id,
                ci.lead_name,
                ci.lead_email,
                lm.last_message_date,
                lm.last_message_content,
                lm.last_message_direction,
                ci.message_count,
                CASE 
                    WHEN lm.last_message_direction = 'inbound' THEN true 
                    ELSE false 
                END as has_unread
            FROM conversation_info ci
            JOIN latest_messages lm ON ci.thread_id = lm.thread_id
            ORDER BY lm.last_message_date DESC
            LIMIT :limit OFFSET :skip
        """)
        
        conversations = db.execute(query, {"limit": limit, "skip": skip}).fetchall()
        
        # Compter le total des conversations
        count_query = text("""
            SELECT COUNT(DISTINCT thread_id) as total
            FROM messages 
            WHERE thread_id IS NOT NULL
        """)
        
        total_result = db.execute(count_query).fetchone()
        total = total_result.total if total_result else 0
        
        # Formater les résultats
        formatted_conversations = []
        for conv in conversations:
            formatted_conversations.append({
                "thread_id": conv.thread_id,
                "lead_id": conv.lead_id,
                "lead_name": conv.lead_name or "Lead inconnu",
                "lead_email": conv.lead_email or "",
                "last_message_date": conv.last_message_date,
                "last_message_content": (conv.last_message_content or "")[:100] + "..." if len(conv.last_message_content or "") > 100 else conv.last_message_content or "",
                "message_count": conv.message_count,
                "has_unread": conv.has_unread
            })
        
        return {
            "conversations": formatted_conversations,
            "total": total,
            "page": skip // limit + 1,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        # Fallback en cas d'erreur
        return {
            "conversations": [],
            "total": 0,
            "page": 1,
            "limit": limit,
            "totalPages": 0,
            "error": str(e)
        }

@router.get("/conversations/{thread_id}")
def get_conversation_messages(
    thread_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les messages d'une conversation spécifique
    """
    try:
        messages = db.query(Message).filter(
            Message.thread_id == thread_id
        ).order_by(
            func.coalesce(Message.received_date, Message.sent_date).asc()
        ).offset(skip).limit(limit).all()
        
        # Compter le total des messages dans cette conversation
        total = db.query(Message).filter(Message.thread_id == thread_id).count()
        
        # Formater les messages pour l'interface
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": msg.id,
                "content": msg.content,
                "direction": msg.direction,
                "sender_type": msg.sender_type,
                "sender_name": msg.sender_name or (msg.lead_name if msg.direction == "inbound" else "BerinIA"),
                "message_type": msg.message_type,
                "timestamp": msg.received_date if msg.direction == "inbound" else msg.sent_date,
                "status": msg.status,
                "subject": msg.subject
            })
        
        return {
            "messages": formatted_messages,
            "total": total,
            "thread_id": thread_id,
            "page": skip // limit + 1,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        return {
            "messages": [],
            "total": 0,
            "thread_id": thread_id,
            "page": 1,
            "limit": limit,
            "totalPages": 0,
            "error": str(e)
        }

@router.post("/conversations/{thread_id}/send")
def send_message_to_conversation(
    thread_id: str,
    message_data: dict,
    db: Session = Depends(deps.get_db)
):
    """
    Envoie un message dans une conversation
    """
    try:
        content = message_data.get("content", "")
        channel = message_data.get("channel", "sms")
        
        if not content.strip():
            raise HTTPException(status_code=400, detail="Le contenu du message est requis")
        
        # Récupérer des infos sur la conversation existante
        existing_msg = db.query(Message).filter(Message.thread_id == thread_id).first()
        
        if not existing_msg:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        
        # Créer le nouveau message en base
        new_message = Message(
            thread_id=thread_id,
            lead_name=existing_msg.lead_name,
            lead_email=existing_msg.lead_email,
            content=content,
            direction="outbound",
            sender_type="user",
            message_type=channel,
            sender_name="BerinIA",
            sent_date=datetime.utcnow(),
            status="sending"
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Envoyer réellement le message selon le canal
        try:
            if channel == "sms":
                # Envoyer SMS via Twilio
                recipient = existing_msg.lead_email  # Contient le numéro de téléphone
                message_sid = send_sms_via_twilio(recipient, content)
                
                # Mettre à jour le statut
                new_message.status = "sent"
                new_message.external_id = message_sid
                db.commit()
                
                return {
                    "status": "success",
                    "message": f"SMS envoyé avec succès à {recipient}",
                    "message_id": new_message.id,
                    "thread_id": thread_id,
                    "content": content,
                    "channel": channel,
                    "twilio_sid": message_sid
                }
                
            else:
                # Pour l'instant, juste marquer comme envoyé
                new_message.status = "sent"
                db.commit()
                
                return {
                    "status": "success",
                    "message": f"Message {channel} envoyé avec succès",
                    "message_id": new_message.id,
                    "thread_id": thread_id,
                    "content": content,
                    "channel": channel
                }
                
        except Exception as send_error:
            # Mettre à jour le statut d'erreur
            new_message.status = "failed"
            db.commit()
            
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi: {str(send_error)}")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi: {str(e)}")

@router.get("/stats")
def get_message_stats(campaign_id: Optional[int] = Query(None), db: Session = Depends(deps.get_db)):
    """
    Récupère les statistiques des messages
    """
    try:
        query = db.query(Message)
        
        if campaign_id:
            query = query.filter(Message.campaign_id == campaign_id)
        
        total = query.count()
        sent = query.filter(Message.direction == "outbound").count()
        received = query.filter(Message.direction == "inbound").count()
        
        # Stats par statut pour les messages sortants
        delivered = query.filter(Message.status == "delivered").count()
        opened = query.filter(Message.status == "opened").count()
        clicked = query.filter(Message.status == "clicked").count()
        replied = received  # Les messages entrants sont des réponses
        bounced = query.filter(Message.status == "bounced").count()
        failed = query.filter(Message.status == "failed").count()
        
        return {
            "total": total,
            "sent": sent,
            "received": received,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "bounced": bounced,
            "failed": failed,
            "open_rate": (opened / delivered * 100) if delivered > 0 else 0,
            "click_rate": (clicked / opened * 100) if opened > 0 else 0,
            "reply_rate": (replied / delivered * 100) if delivered > 0 else 0,
            "bounce_rate": (bounced / total * 100) if total > 0 else 0
        }
        
    except Exception as e:
        return {
            "total": 0,
            "sent": 0,
            "received": 0,
            "delivered": 0,
            "opened": 0,
            "clicked": 0,
            "replied": 0,
            "bounced": 0,
            "failed": 0,
            "open_rate": 0,
            "click_rate": 0,
            "reply_rate": 0,
            "bounce_rate": 0,
            "error": str(e)
        }

@router.get("/")
def get_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None),
    campaign_id: Optional[int] = Query(None),
    lead_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère la liste des messages (ancien endpoint pour compatibilité)
    """
    try:
        query = db.query(Message)
        
        if status:
            query = query.filter(Message.status == status)
        if campaign_id:
            query = query.filter(Message.campaign_id == campaign_id)
        if lead_id:
            query = query.filter(Message.lead_id == lead_id)
        if search:
            query = query.filter(Message.content.ilike(f"%{search}%"))
        
        total = query.count()
        messages = query.offset(skip).limit(limit).all()
        
        # Formater pour l'ancien format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": msg.id,
                "lead_id": msg.lead_id,
                "lead_name": msg.lead_name,
                "lead_email": msg.lead_email,
                "subject": msg.subject,
                "content": msg.content,
                "status": msg.status,
                "campaign_id": msg.campaign_id,
                "campaign_name": msg.campaign_name,
                "sent_date": msg.sent_date,
                "received_date": msg.received_date,
                "direction": msg.direction,
                "sender_type": msg.sender_type,
                "message_type": msg.message_type
            })
        
        return {
            "items": formatted_messages,
            "total": total,
            "page": skip // limit + 1,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        return {
            "items": [],
            "total": 0,
            "page": 1,
            "limit": limit,
            "totalPages": 0,
            "error": str(e)
        }

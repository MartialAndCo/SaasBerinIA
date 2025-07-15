from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, List, Any
from datetime import datetime

from app.api import deps
from app.models.lead import Lead as LeadModel

router = APIRouter()

def get_conversation_by_thread(thread_id: str, db: Session) -> List[Dict]:
    """Récupère tous les messages d'une conversation spécifique"""
    query = text("""
        SELECT 
            direction, sender_name, content, 
            COALESCE(received_date, sent_date) as timestamp,
            message_type, status, lead_name, lead_email
        FROM messages 
        WHERE thread_id = :thread_id 
        ORDER BY timestamp ASC
    """)
    result = db.execute(query, {"thread_id": thread_id})
    return [dict(row._mapping) for row in result.fetchall()]

def get_lead_conversation_history(lead_id: int, db: Session) -> List[Dict]:
    """Récupère l'historique complet des conversations d'un lead"""
    query = text("""
        SELECT 
            m.thread_id,
            m.direction,
            m.content,
            m.message_type,
            m.sender_name,
            m.lead_name,
            COALESCE(m.received_date, m.sent_date) as timestamp,
            COUNT(*) OVER (PARTITION BY m.thread_id) as message_count
        FROM messages m
        WHERE m.lead_id = :lead_id
        ORDER BY timestamp DESC
        LIMIT 500
    """)
    result = db.execute(query, {"lead_id": lead_id})
    return [dict(row._mapping) for row in result.fetchall()]

def get_active_conversations(db: Session, limit: int = 50) -> List[Dict]:
    """Récupère les conversations actives avec statistiques"""
    query = text("""
        SELECT 
            thread_id,
            lead_id,
            lead_name,
            lead_email,
            COUNT(*) as message_count,
            SUM(CASE WHEN direction = 'inbound' THEN 1 ELSE 0 END) as inbound_count,
            SUM(CASE WHEN direction = 'outbound' THEN 1 ELSE 0 END) as outbound_count,
            MAX(COALESCE(received_date, sent_date)) as last_message_date,
            MIN(COALESCE(received_date, sent_date)) as first_message_date
        FROM messages 
        WHERE thread_id IS NOT NULL
        GROUP BY thread_id, lead_id, lead_name, lead_email
        ORDER BY last_message_date DESC
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit})
    return [dict(row._mapping) for row in result.fetchall()]

def format_conversation_for_ai(messages: List[Dict]) -> str:
    """Formate une conversation pour analyse par IA"""
    formatted_messages = []
    
    for msg in messages:
        direction = "CLIENT" if msg['direction'] == 'inbound' else "BERINIA"
        content = msg['content'] or ''
        timestamp = msg['timestamp'].strftime('%d/%m %H:%M') if msg['timestamp'] else ''
        
        formatted_messages.append(f"[{timestamp}] {direction}: {content}")
    
    return "\n".join(formatted_messages)

def generate_conversation_summary(messages: List[Dict]) -> Dict[str, Any]:
    """Génère un résumé intelligent via LLM (version simplifiée pour l'instant)"""
    
    if not messages:
        return {
            "summary": "Aucun message dans cette conversation.",
            "interest_level": "unknown",
            "key_points": [],
            "objections": [],
            "questions": [],
            "next_actions": [],
            "business_context": "Non déterminé"
        }
    
    # Analyse basique en attendant l'intégration LLM complète
    inbound_count = sum(1 for msg in messages if msg['direction'] == 'inbound')
    outbound_count = sum(1 for msg in messages if msg['direction'] == 'outbound')
    total_messages = len(messages)
    
    # Détection de mots-clés d'intérêt
    all_content = " ".join([msg.get('content', '') for msg in messages if msg.get('content')])
    
    interest_keywords = ['intéressé', 'rdv', 'rendez-vous', 'démonstration', 'oui', 'disponible']
    objection_keywords = ['cher', 'prix', 'budget', 'réfléchir', 'plus tard', 'non']
    question_keywords = ['comment', 'combien', 'pourquoi', 'quand', '?']
    
    interest_score = sum(1 for keyword in interest_keywords if keyword.lower() in all_content.lower())
    objection_score = sum(1 for keyword in objection_keywords if keyword.lower() in all_content.lower())
    question_score = sum(1 for keyword in question_keywords if keyword.lower() in all_content.lower())
    
    # Détermination du niveau d'intérêt
    if inbound_count >= 2 and interest_score > objection_score:
        interest_level = "high"
    elif inbound_count >= 1 and interest_score >= objection_score:
        interest_level = "medium"
    elif objection_score > interest_score:
        interest_level = "low"
    else:
        interest_level = "unknown"
    
    # Génération du résumé
    if total_messages == 1:
        summary = f"Premier contact établi. Message {messages[0]['direction']}."
    elif inbound_count > 0:
        summary = f"Conversation active avec {inbound_count} réponse(s) du prospect sur {total_messages} messages."
    else:
        summary = f"Communication unilatérale - {outbound_count} message(s) envoyé(s), aucune réponse."
    
    # Recommandations d'actions
    next_actions = []
    if interest_level == "high":
        next_actions.append("Proposer un rendez-vous rapidement")
        next_actions.append("Envoyer une démonstration")
    elif interest_level == "medium":
        next_actions.append("Relancer avec du contenu personnalisé")
        next_actions.append("Répondre aux questions soulevées")
    elif interest_level == "low":
        next_actions.append("Identifier les objections principales")
        next_actions.append("Reformuler la proposition de valeur")
    else:
        next_actions.append("Relancer avec un angle différent")
        next_actions.append("Vérifier la pertinence du lead")
    
    return {
        "summary": summary,
        "interest_level": interest_level,
        "key_points": [
            f"{inbound_count} réponse(s) du prospect",
            f"{total_messages} messages au total",
            f"Score d'intérêt: {interest_score}",
            f"Score d'objections: {objection_score}"
        ],
        "objections": [msg['content'][:100] + "..." for msg in messages[-3:] 
                      if msg['direction'] == 'inbound' and any(keyword in msg.get('content', '').lower() 
                      for keyword in objection_keywords)],
        "questions": [msg['content'][:100] + "..." for msg in messages[-3:] 
                     if msg['direction'] == 'inbound' and '?' in msg.get('content', '')],
        "next_actions": next_actions,
        "business_context": f"Lead: {messages[0].get('lead_name', 'Inconnu')} - {total_messages} échanges",
        "stats": {
            "total_messages": total_messages,
            "inbound_count": inbound_count, 
            "outbound_count": outbound_count,
            "interest_score": interest_score,
            "objection_score": objection_score,
            "question_score": question_score
        }
    }

@router.get("/conversations")
def get_conversations(
    db: Session = Depends(deps.get_db),
    limit: int = Query(50, le=100),
    lead_id: Optional[int] = Query(None)
):
    """Récupère la liste des conversations actives"""
    if lead_id:
        conversations = get_lead_conversation_history(lead_id, db)
        # Grouper par thread_id pour éviter les doublons
        thread_conversations = {}
        for conv in conversations:
            thread_id = conv['thread_id']
            if thread_id not in thread_conversations:
                thread_conversations[thread_id] = {
                    'thread_id': thread_id,
                    'lead_id': lead_id,
                    'lead_name': conv['lead_name'],
                    'message_count': conv['message_count'],
                    'last_message_date': conv['timestamp']
                }
        return {
            "conversations": list(thread_conversations.values()),
            "total": len(thread_conversations)
        }
    else:
        conversations = get_active_conversations(db, limit)
        return {
            "conversations": conversations,
            "total": len(conversations)
        }

@router.get("/conversations/{thread_id}")
def get_conversation_details(thread_id: str, db: Session = Depends(deps.get_db)):
    """Récupère les détails d'une conversation spécifique"""
    messages = get_conversation_by_thread(thread_id, db)
    
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    return {
        "thread_id": thread_id,
        "messages": messages,
        "message_count": len(messages),
        "lead_name": messages[0].get('lead_name'),
        "lead_email": messages[0].get('lead_email')
    }

@router.get("/conversations/{thread_id}/summary")
def get_conversation_summary(thread_id: str, db: Session = Depends(deps.get_db)):
    """Génère un résumé intelligent de la conversation"""
    
    # Récupérer les messages
    messages = get_conversation_by_thread(thread_id, db)
    
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    # Générer le résumé
    summary = generate_conversation_summary(messages)
    
    return {
        "thread_id": thread_id,
        "lead_name": messages[0].get('lead_name'),
        "lead_email": messages[0].get('lead_email'),
        "message_count": len(messages),
        "summary": summary,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/leads/{lead_id}/conversation-summary")
def get_lead_conversation_summary(lead_id: int, db: Session = Depends(deps.get_db)):
    """Génère un résumé de toutes les conversations d'un lead"""
    
    # Vérifier que le lead existe
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        # Retourner un résumé minimal pour les leads inexistants (évite les timeouts)
        return {
            "lead_id": lead_id,
            "lead_name": "Lead non trouvé",
            "summary": {
                "summary": "Lead non trouvé en base de données.",
                "interest_level": "unknown",
                "key_points": [],
                "next_actions": ["Vérifier l'existence du lead"],
                "business_context": "Lead introuvable"
            },
            "conversations_count": 0
        }
    
    # Récupérer l'historique des conversations avec limite pour éviter les timeouts
    try:
        conversations = get_lead_conversation_history(lead_id, db)
    except Exception as e:
        # Fallback en cas d'erreur de requête
        return {
            "lead_id": lead_id,
            "lead_name": f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
            "summary": {
                "summary": f"Erreur de récupération des conversations: {str(e)[:100]}",
                "interest_level": "unknown",
                "key_points": [],
                "next_actions": ["Réessayer la récupération des conversations"],
                "business_context": f"Entreprise: {lead.company or 'Non renseignée'}"
            },
            "conversations_count": 0
        }
    
    if not conversations:
        return {
            "lead_id": lead_id,
            "lead_name": f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
            "summary": {
                "summary": "Aucune conversation enregistrée avec ce lead.",
                "interest_level": "unknown",
                "key_points": [],
                "next_actions": ["Initier le premier contact"],
                "business_context": f"Lead: {lead.company or 'Entreprise non renseignée'}"
            },
            "conversations_count": 0
        }
    
    # Grouper par thread_id et générer un résumé global
    threads = {}
    for conv in conversations:
        thread_id = conv['thread_id']
        if thread_id not in threads:
            threads[thread_id] = []
        threads[thread_id].append(conv)
    
    # Générer un résumé pour chaque conversation
    thread_summaries = []
    for thread_id, messages in threads.items():
        summary = generate_conversation_summary(messages)
        thread_summaries.append({
            "thread_id": thread_id,
            "message_count": len(messages),
            "summary": summary
        })
    
    # Résumé global du lead
    total_messages = len(conversations)
    total_inbound = sum(1 for c in conversations if c['direction'] == 'inbound')
    
    # Niveau d'engagement global
    if total_inbound >= 3:
        global_interest = "high"
    elif total_inbound >= 1:
        global_interest = "medium"
    else:
        global_interest = "low"
    
    global_summary = {
        "summary": f"Lead avec {len(threads)} conversation(s) et {total_messages} messages total. {total_inbound} réponses du prospect.",
        "interest_level": global_interest,
        "key_points": [
            f"{len(threads)} conversation(s) actives",
            f"{total_messages} messages échangés",
            f"{total_inbound} réponses du prospect"
        ],
        "conversations_detail": thread_summaries,
        "business_context": f"Entreprise: {lead.company or 'Non renseignée'} - Secteur: {lead.industry or 'Non renseigné'}"
    }
    
    return {
        "lead_id": lead_id,
        "lead_name": f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
        "lead_company": lead.company,
        "summary": global_summary,
        "conversations_count": len(threads),
        "generated_at": datetime.utcnow().isoformat()
    }
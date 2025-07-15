from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api import deps
from app.models.lead import Lead as LeadModel

router = APIRouter(tags=["Leads Stats"])

@router.get("/count")
def get_leads_count(db: Session = Depends(deps.get_db)):
    """Récupère le nombre total de leads basé sur vos vraies données"""
    
    # Compter les vraies données
    total = db.query(LeadModel).count()
    
    # Calculer par période avec vraies dates
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    yesterday_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    yesterday_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    try:
        this_week = db.query(LeadModel).filter(LeadModel.created_at >= week_ago).count() if hasattr(LeadModel, 'created_at') else 0
        this_month = db.query(LeadModel).filter(LeadModel.created_at >= month_ago).count() if hasattr(LeadModel, 'created_at') else 0
        yesterday = db.query(LeadModel).filter(
            LeadModel.created_at >= yesterday_start,
            LeadModel.created_at < yesterday_end
        ).count() if hasattr(LeadModel, 'created_at') else 0
    except:
        this_week = this_month = yesterday = 0
    
    return {
        "total": total,
        "this_week": this_week,
        "this_month": this_month,
        "yesterday": yesterday
    }

@router.get("/stats")
def get_leads_stats(db: Session = Depends(deps.get_db)):
    """Statistiques des leads CORRIGÉES avec vos vraies données"""
    
    # Compter les totaux réels
    total_count = db.query(LeadModel).count()
    
    # CORRECTION : Utiliser les VRAIS statuts découverts dans votre base
    qualified_count = db.query(LeadModel).filter(LeadModel.status == "qualified").count()
    new_count = db.query(LeadModel).filter(LeadModel.status == "new").count()
    
    # CORRECTION : Compter les VRAIES réponses depuis la table messages
    from app.models.message import Message
    total_responses_received = db.query(Message).filter(Message.direction == "inbound").count()
    
    # Calculer les taux réels avec les BONNES données
    qualification_rate = (qualified_count / total_count * 100) if total_count > 0 else 0
    
    # Métriques dérivées basées sur vos vraies données
    pending_count = total_count - total_responses_received
    
    # CORRECTION : Analyser les VRAIES conversations positives
    positive_conversations = 0
    
    # Grouper par lead_id pour analyser les conversations complètes
    leads_with_responses = db.query(LeadModel).join(Message, LeadModel.id == Message.lead_id).filter(
        Message.direction == "inbound"
    ).distinct().all()
    
    for lead in leads_with_responses:
        # Récupérer le dernier message de la conversation
        last_message = db.query(Message).filter(
            Message.lead_id == lead.id,
            Message.direction == "inbound"
        ).order_by(Message.sent_date.desc()).first()
        
        if last_message:
            content = (last_message.content or "").lower()
            # Compter seulement les conversations vraiment positives
            if any(word in content for word in ["confirmé", "procédons", "valide", "parfait", "oui", "accepte"]):
                positive_conversations += 1

    # Statistiques d'analyse visuelle
    leads_with_visual = db.query(LeadModel).filter(LeadModel.visual_score.isnot(None)).all()
    visual_analyzed_count = len(leads_with_visual)
    avg_visual_score = 0
    if visual_analyzed_count > 0:
        total_visual_score = sum(lead.visual_score for lead in leads_with_visual if lead.visual_score)
        avg_visual_score = round(total_visual_score / visual_analyzed_count, 1)

    return {
        "total_count": total_count,
        "qualified_count": qualified_count,
        "responded_count": total_responses_received,
        "new_count": new_count,
        "pending_count": pending_count,
        "qualification_rate": round(qualification_rate, 1),
        "positive_responses": positive_conversations,
        "neutral_responses": total_responses_received - positive_conversations,
        "interested_count": positive_conversations,
        "visual_analyzed_count": visual_analyzed_count,
        "avg_visual_score": avg_visual_score
    }

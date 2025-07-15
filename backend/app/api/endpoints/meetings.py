from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from app.api import deps
from app.schemas.meeting import (
    MeetingCreate, Meeting, MeetingUpdate, MeetingStatusUpdate, 
    MeetingFilter, MeetingWithLead, MeetingStats, MeetingActionRequest
)
from app.models.meeting import Meeting as MeetingModel
from app.models.lead import Lead as LeadModel

router = APIRouter()

def meeting_to_dict(meeting: MeetingModel, include_lead: bool = False) -> Dict:
    """Transforme un objet MeetingModel en dictionnaire avec les noms de champs attendus par le frontend"""
    result = {
        "id": meeting.id,
        "nom_client": meeting.client_name,
        "client_name": meeting.client_name,
        "email_client": meeting.client_email,
        "client_email": meeting.client_email,
        "heure_debut": meeting.start_time,
        "start_time": meeting.start_time,
        "heure_fin": meeting.end_time,
        "end_time": meeting.end_time,
        "duree": meeting.duration_minutes,
        "duration_minutes": meeting.duration_minutes,
        "statut": meeting.status,
        "status": meeting.status,
        "lien_meeting": meeting.meeting_link,
        "meeting_link": meeting.meeting_link,
        "calendar_link": meeting.calendar_link,
        "description": meeting.description,
        "date_creation": meeting.created_at,
        "created_at": meeting.created_at,
        "updated_at": meeting.updated_at,
        "lead_id": meeting.lead_id,
        "calendar_event_id": meeting.calendar_event_id,
    }
    
    # Ajouter les informations du lead si demandé et disponible
    if include_lead and meeting.lead:
        result.update({
            "lead_name": f"{meeting.lead.first_name or ''} {meeting.lead.last_name or ''}".strip(),
            "lead_company": meeting.lead.company,
            "lead_phone": meeting.lead.phone,
            "lead_email": meeting.lead.email
        })
    
    return result

@router.post("/")
def create_meeting(meeting: MeetingCreate, db: Session = Depends(deps.get_db)):
    """Crée un nouveau rendez-vous"""
    db_meeting = MeetingModel(
        lead_id=meeting.lead_id,
        calendar_event_id=meeting.calendar_event_id,
        client_name=meeting.client_name,
        client_email=meeting.client_email,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        duration_minutes=meeting.duration_minutes,
        meeting_link=meeting.meeting_link,
        calendar_link=meeting.calendar_link,
        description=meeting.description,
        status=meeting.status or "scheduled"
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return meeting_to_dict(db_meeting)

@router.get("/")
def get_meetings(
    db: Session = Depends(deps.get_db),
    lead_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    include_lead: Optional[bool] = Query(False),
    limit: Optional[int] = Query(100),
    offset: Optional[int] = Query(0)
):
    """Récupère la liste des rendez-vous avec filtres optionnels"""
    query = db.query(MeetingModel)
    
    # Inclure les données du lead si demandé
    if include_lead:
        query = query.options(joinedload(MeetingModel.lead))
    
    # Filtres
    if lead_id:
        query = query.filter(MeetingModel.lead_id == lead_id)
    
    if status:
        query = query.filter(MeetingModel.status == status)
    
    if start_date:
        query = query.filter(MeetingModel.start_time >= start_date)
    
    if end_date:
        query = query.filter(MeetingModel.start_time <= end_date)
    
    # Tri par date de début (plus récents en premier)
    query = query.order_by(MeetingModel.start_time.desc())
    
    # Pagination
    total = query.count()
    meetings = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "meetings": [meeting_to_dict(meeting, include_lead) for meeting in meetings],
        "limit": limit,
        "offset": offset
    }

@router.get("/upcoming")
def get_upcoming_meetings(
    db: Session = Depends(deps.get_db),
    days: Optional[int] = Query(7),
    include_lead: Optional[bool] = Query(True)
):
    """Récupère les rendez-vous à venir dans les N prochains jours"""
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)
    
    query = db.query(MeetingModel).filter(
        and_(
            MeetingModel.start_time >= now,
            MeetingModel.start_time <= end_date,
            MeetingModel.status.in_(["scheduled", "confirmed"])
        )
    )
    
    if include_lead:
        query = query.options(joinedload(MeetingModel.lead))
    
    meetings = query.order_by(MeetingModel.start_time).all()
    
    return {
        "upcoming_meetings": [meeting_to_dict(meeting, include_lead) for meeting in meetings],
        "period_days": days,
        "count": len(meetings)
    }

@router.get("/stats")
def get_meeting_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Récupère les statistiques des rendez-vous"""
    query = db.query(MeetingModel)
    
    # Filtres de date
    if start_date:
        query = query.filter(MeetingModel.start_time >= start_date)
    if end_date:
        query = query.filter(MeetingModel.start_time <= end_date)
    
    # Statistiques générales
    total_meetings = query.count()
    
    # Par statut
    scheduled = query.filter(MeetingModel.status == "scheduled").count()
    completed = query.filter(MeetingModel.status == "completed").count()
    cancelled = query.filter(MeetingModel.status == "cancelled").count()
    no_show = query.filter(MeetingModel.status == "no_show").count()
    
    # Prochains RDV
    now = datetime.utcnow()
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    week_end = now + timedelta(days=7)
    
    upcoming_today = db.query(MeetingModel).filter(
        and_(
            MeetingModel.start_time >= now,
            MeetingModel.start_time <= today_end,
            MeetingModel.status.in_(["scheduled", "confirmed"])
        )
    ).count()
    
    upcoming_week = db.query(MeetingModel).filter(
        and_(
            MeetingModel.start_time >= now,
            MeetingModel.start_time <= week_end,
            MeetingModel.status.in_(["scheduled", "confirmed"])
        )
    ).count()
    
    return {
        "total_meetings": total_meetings,
        "scheduled_meetings": scheduled,
        "completed_meetings": completed,
        "cancelled_meetings": cancelled,
        "no_show_meetings": no_show,
        "upcoming_today": upcoming_today,
        "upcoming_week": upcoming_week,
        "period": {
            "start_date": start_date,
            "end_date": end_date
        }
    }

@router.get("/by-period")
def get_meetings_by_period(
    db: Session = Depends(deps.get_db),
    period: str = Query("today"),  # today, week, month
    include_lead: Optional[bool] = Query(True)
):
    """Récupère les rendez-vous par période (aujourd'hui, cette semaine, ce mois)"""
    now = datetime.utcnow()
    
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "week":
        # Début de la semaine (lundi)
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Dernier jour du mois
        if now.month == 12:
            end_date = start_date.replace(year=now.year + 1, month=1) - timedelta(seconds=1)
        else:
            end_date = start_date.replace(month=now.month + 1) - timedelta(seconds=1)
    else:
        raise HTTPException(status_code=400, detail="Période invalide. Utilisez: today, week, month")
    
    query = db.query(MeetingModel).filter(
        and_(
            MeetingModel.start_time >= start_date,
            MeetingModel.start_time <= end_date
        )
    )
    
    if include_lead:
        query = query.options(joinedload(MeetingModel.lead))
    
    meetings = query.order_by(MeetingModel.start_time).all()
    
    return {
        "meetings": [meeting_to_dict(meeting, include_lead) for meeting in meetings],
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "count": len(meetings)
    }

@router.get("/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(deps.get_db)):
    """Récupère un rendez-vous spécifique avec détails du lead"""
    meeting = db.query(MeetingModel).options(joinedload(MeetingModel.lead)).filter(MeetingModel.id == meeting_id).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    
    result = meeting_to_dict(meeting, include_lead=True)
    
    # Ajouter un résumé de conversation si disponible (à implémenter plus tard)
    # result["conversation_summary"] = get_conversation_summary(meeting.lead_id)
    
    return result

@router.put("/{meeting_id}")
def update_meeting(meeting_id: int, meeting_update: MeetingUpdate, db: Session = Depends(deps.get_db)):
    """Met à jour un rendez-vous"""
    db_meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    
    # Mettre à jour les champs fournis
    update_data = meeting_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_meeting, field, value)
    
    db_meeting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_meeting)
    
    return meeting_to_dict(db_meeting)

@router.patch("/{meeting_id}/status")
def update_meeting_status(meeting_id: int, status_update: MeetingStatusUpdate, db: Session = Depends(deps.get_db)):
    """Met à jour le statut d'un rendez-vous"""
    db_meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    
    db_meeting.status = status_update.status
    db_meeting.updated_at = datetime.utcnow()
    
    # Ajouter les notes si fournies
    if status_update.notes:
        current_desc = db_meeting.description or ""
        db_meeting.description = f"{current_desc}\n\nNotes ({datetime.utcnow().strftime('%d/%m/%Y %H:%M')}): {status_update.notes}"
    
    db.commit()
    db.refresh(db_meeting)
    
    return meeting_to_dict(db_meeting)

@router.post("/{meeting_id}/action")
def perform_meeting_action(meeting_id: int, action_request: MeetingActionRequest, db: Session = Depends(deps.get_db)):
    """Effectue une action sur un rendez-vous (reporter, annuler, etc.)"""
    db_meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    
    if action_request.action == "reschedule":
        if not action_request.new_start_time:
            raise HTTPException(status_code=400, detail="Nouvelle heure requise pour reporter")
        
        # Calculer la nouvelle heure de fin
        duration = action_request.new_duration or db_meeting.duration_minutes or 30
        new_end_time = action_request.new_start_time + timedelta(minutes=duration)
        
        db_meeting.start_time = action_request.new_start_time
        db_meeting.end_time = new_end_time
        db_meeting.duration_minutes = duration
        db_meeting.status = "scheduled"
        
        # Ajouter une note
        note = f"RDV reporté le {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}"
        if action_request.reason:
            note += f" - Raison: {action_request.reason}"
        
        current_desc = db_meeting.description or ""
        db_meeting.description = f"{current_desc}\n\n{note}"
        
    elif action_request.action == "cancel":
        db_meeting.status = "cancelled"
        
        # Ajouter une note d'annulation
        note = f"RDV annulé le {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}"
        if action_request.reason:
            note += f" - Raison: {action_request.reason}"
        
        current_desc = db_meeting.description or ""
        db_meeting.description = f"{current_desc}\n\n{note}"
        
    else:
        raise HTTPException(status_code=400, detail=f"Action non supportée: {action_request.action}")
    
    db_meeting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_meeting)
    
    # TODO: Si notify_client est True, envoyer une notification au client via MeetingAgent
    # if action_request.notify_client:
    #     notify_client_of_meeting_change(db_meeting, action_request.action)
    
    return {
        "success": True,
        "action": action_request.action,
        "meeting": meeting_to_dict(db_meeting),
        "message": f"Action '{action_request.action}' effectuée avec succès"
    }

@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(deps.get_db)):
    """Supprime un rendez-vous"""
    db_meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    
    db.delete(db_meeting)
    db.commit()
    
    return {"success": True, "message": "Rendez-vous supprimé avec succès"}
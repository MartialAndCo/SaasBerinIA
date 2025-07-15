from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func, or_
from fastapi.encoders import jsonable_encoder

from app.api import deps
from app.models.lead import Lead as LeadModel
from app.models.campaign import Campaign as CampaignModel
from app.models.niche import Niche as NicheModel
from app.models.message import Message

router = APIRouter(tags=["Leads Management"])

@router.get("/list", response_model=List[dict])
def get_leads_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """
    Liste détaillée des leads avec pagination et filtres
    """
    query = db.query(LeadModel)

    # Filtrer par statut si spécifié
    if status:
        query = query.filter(LeadModel.status == status)

    # Recherche par nom, email ou entreprise
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                LeadModel.first_name.ilike(search_term),
                LeadModel.last_name.ilike(search_term),
                LeadModel.email.ilike(search_term),
                LeadModel.company.ilike(search_term),
                LeadModel.entreprise.ilike(search_term)
            )
        )

    leads = query.offset(skip).limit(limit).all()

    # Enrichir avec données des campagnes et messages
    result = []
    for lead in leads:
        # Récupérer la campagne associée
        campaign = None
        if lead.campagne_id:
            campaign = db.query(CampaignModel).filter(CampaignModel.id == lead.campagne_id).first()

        # Compter les messages pour ce lead
        messages_sent = db.query(Message).filter(
            Message.lead_id == lead.id,
            Message.direction == "outbound"
        ).count()
        
        messages_received = db.query(Message).filter(
            Message.lead_id == lead.id,
            Message.direction == "inbound"
        ).count()

        result.append({
            "id": lead.id,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "email": lead.email,
            "phone": lead.phone,
            "company": lead.company or lead.entreprise,
            "status": lead.status,
            "campaign_name": campaign.name if campaign else "Aucune",
            "messages_sent": messages_sent,
            "messages_received": messages_received,
            "created_at": lead.created_at,
            "last_contact": lead.last_contact
        })

    return result

@router.get("/by-status", response_model=dict)
def get_leads_by_status(db: Session = Depends(deps.get_db)):
    """
    Compter les leads par statut pour afficher les boutons
    """
    # Compter tous les statuts
    status_counts = db.query(
        LeadModel.status, 
        func.count(LeadModel.id)
    ).group_by(LeadModel.status).all()

    result = {"total": db.query(LeadModel).count()}
    
    for status, count in status_counts:
        result[status] = count

    return result

@router.get("/search/{query}", response_model=List[dict])
def search_leads(
    query: str,
    limit: int = Query(10, le=50),
    db: Session = Depends(deps.get_db)
):
    """
    Recherche rapide de leads
    """
    search_term = f"%{query}%"
    
    leads = db.query(LeadModel).filter(
        or_(
            LeadModel.first_name.ilike(search_term),
            LeadModel.last_name.ilike(search_term),
            LeadModel.email.ilike(search_term),
            LeadModel.company.ilike(search_term),
            LeadModel.entreprise.ilike(search_term)
        )
    ).limit(limit).all()

    result = []
    for lead in leads:
        result.append({
            "id": lead.id,
            "name": f"{lead.first_name} {lead.last_name or ''}".strip(),
            "email": lead.email,
            "company": lead.company or lead.entreprise,
            "status": lead.status
        })

    return result

@router.get("/{lead_id}/compensation", response_model=dict)
def get_lead_compensation(lead_id: int, db: Session = Depends(deps.get_db)):
    """
    Calculer la compensation pour un lead spécifique
    """
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Pour l'instant, compensation basique selon le statut
    compensation = 0
    if lead.status == "qualified":
        compensation = 50  # 50€ pour un lead qualifié
    elif lead.status == "new":
        compensation = 10   # 10€ pour un nouveau lead

    # Compter les messages échangés
    messages_sent = db.query(Message).filter(
        Message.lead_id == lead.id,
        Message.direction == "outbound"
    ).count()
    
    messages_received = db.query(Message).filter(
        Message.lead_id == lead.id,
        Message.direction == "inbound"
    ).count()

    return {
        "lead_id": lead.id,
        "lead_name": f"{lead.first_name} {lead.last_name or ''}".strip(),
        "status": lead.status,
        "base_compensation": compensation,
        "messages_bonus": messages_received * 5,  # 5€ par réponse reçue
        "total_compensation": compensation + (messages_received * 5),
        "messages_sent": messages_sent,
        "messages_received": messages_received
    }

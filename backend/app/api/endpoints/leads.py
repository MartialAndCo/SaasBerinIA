from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, List
from datetime import datetime

from app.api import deps
from app.schemas.lead import LeadCreate, Lead, LeadUpdate, LeadStatusUpdateRequest
from pydantic import BaseModel
from typing import Union
from app.models.lead import Lead as LeadModel

router = APIRouter()

def lead_to_dict(lead: LeadModel) -> Dict:
    """Transforme un objet LeadModel en dictionnaire avec les noms de champs attendus par le frontend"""
    return {
        "id": lead.id,
        "nom": f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "Sans nom",
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "email": lead.email,
        "telephone": lead.phone,
        "phone": lead.phone,
        # Priorité à la colonne entreprise puis company
        "entreprise": lead.entreprise or lead.company,
        "company": lead.company,
        "position": lead.position,
        "industry": lead.industry,
        "source": lead.source,
        "linkedin_url": lead.linkedin_url,
        "website": lead.website,
        "niche_id": lead.niche_id,
        "score": lead.score,
        "score_details": lead.score_details,
        "validation_status": lead.validation_status,
        "last_contact": lead.last_contact,
        "statut": lead.status or "new",
        "status": lead.status or "new",
        "date_creation": lead.created_at,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
        "campagne_id": lead.campagne_id,
        "notes": lead.notes,
        "visual_score": lead.visual_score,
        "has_popup": lead.has_popup,
        "popup_removed": lead.popup_removed,
        "screenshot_path": lead.screenshot_path,
        "enhanced_screenshot_path": lead.enhanced_screenshot_path,
        "visual_analysis_date": lead.visual_analysis_date,
        "site_type": lead.site_type,
        "visual_quality": lead.visual_quality,
        "website_maturity": lead.website_maturity,
        "design_strengths": lead.design_strengths,
        "design_weaknesses": lead.design_weaknesses,
        "visual_analysis_data": lead.visual_analysis_data,
        # Ajout des champs de facturation
        "billing_address": lead.billing_address,
        "billing_city": lead.billing_city,
        "billing_postal_code": lead.billing_postal_code,
        "billing_country": lead.billing_country,
        "vat_number": lead.vat_number,
        "billing_email": lead.billing_email,
        "billing_contact_name": lead.billing_contact_name,
        "stripe_customer_id": lead.stripe_customer_id,
    }

@router.post("/")
def create_lead(lead: LeadCreate, db: Session = Depends(deps.get_db)):
    """Crée un nouveau lead"""
    db_lead = LeadModel(
        first_name=lead.nom.split()[0] if lead.nom else "",
        last_name=" ".join(lead.nom.split()[1:]) if len(lead.nom.split()) > 1 else "",
        email=lead.email,
        phone=lead.telephone,
        company=lead.entreprise,
        status=lead.statut or "new",
        campagne_id=lead.campagne_id
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return lead_to_dict(db_lead)

# Routes spécifiques AVANT les routes avec paramètres
@router.get("/kanban")
def get_leads_kanban(
    db: Session = Depends(deps.get_db),
    campagne_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None)
):
    """Récupère les leads groupés par statut pour le kanban"""
    query = db.query(LeadModel)
    
    # Filtres
    if campagne_id:
        query = query.filter(LeadModel.campagne_id == campagne_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            LeadModel.first_name.ilike(search_term) |
            LeadModel.last_name.ilike(search_term) |
            LeadModel.email.ilike(search_term) |
            LeadModel.company.ilike(search_term)
        )
    
    leads = query.all()
    
    # Grouper par statut
    kanban_data = {
        "new": [],
        "qualification": [],
        "presentation": [],
        "negotiation": [],
        "evaluation": [],
        "won": [],
        "lost": []
    }
    
    # Mapping pour normaliser les statuts incohérents
    status_mapping = {
        "qualified": "qualification",  # Normaliser "qualified" vers "qualification"
        "qualify": "qualification",    # Autres variantes possibles
        "qualifié": "qualification",   # Version française
    }
    
    for lead in leads:
        status = lead.status or "new"
        # Appliquer le mapping si nécessaire
        normalized_status = status_mapping.get(status, status)
        
        lead_dict = lead_to_dict(lead)
        if normalized_status in kanban_data:
            kanban_data[normalized_status].append(lead_dict)
        else:
            kanban_data["new"].append(lead_dict)  # Fallback pour les statuts inconnus
    
    return kanban_data

@router.get("/stats")
def get_leads_stats(
    db: Session = Depends(deps.get_db),
    campagne_id: Optional[int] = Query(None)
):
    """Récupère les statistiques des leads"""
    query = db.query(LeadModel)
    
    if campagne_id:
        query = query.filter(LeadModel.campagne_id == campagne_id)
    
    # Total des leads
    total = query.count()
    
    # Statistiques par statut
    status_stats = db.query(
        LeadModel.status,
        func.count(LeadModel.id).label('count')
    )
    
    if campagne_id:
        status_stats = status_stats.filter(LeadModel.campagne_id == campagne_id)
    
    status_stats = status_stats.group_by(LeadModel.status).all()
    
    by_status = {stat.status or "new": stat.count for stat in status_stats}
    
    # Statistiques par campagne
    campaign_stats = db.query(
        LeadModel.campagne_id,
        func.count(LeadModel.id).label('count')
    ).filter(LeadModel.campagne_id.isnot(None)).group_by(LeadModel.campagne_id).all()
    
    by_campaign = {f"campaign_{stat.campagne_id}": stat.count for stat in campaign_stats}
    
    return {
        "total": total,
        "by_status": by_status,
        "by_campaign": by_campaign
    }

@router.get("/export")
def export_leads(
    db: Session = Depends(deps.get_db),
    status: Optional[str] = Query(None),
    campagne_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None)
):
    """Exporte les leads au format CSV"""
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    query = db.query(LeadModel)
    
    # Filtres
    if status and status != "all":
        query = query.filter(LeadModel.status == status)
    
    if campagne_id:
        query = query.filter(LeadModel.campagne_id == campagne_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            LeadModel.first_name.ilike(search_term) |
            LeadModel.last_name.ilike(search_term) |
            LeadModel.email.ilike(search_term) |
            LeadModel.company.ilike(search_term)
        )
    
    leads = query.all()
    
    # Créer le CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow([
        "ID", "Nom", "Email", "Téléphone", "Entreprise", 
        "Statut", "Date de création", "Campagne ID", "Notes"
    ])
    
    # Données
    for lead in leads:
        writer.writerow([
            lead.id,
            f"{lead.first_name} {lead.last_name}".strip(),
            lead.email,
            lead.phone or "",
            lead.company or "",
            lead.status or "new",
            lead.created_at.strftime("%Y-%m-%d %H:%M:%S") if lead.created_at else "",
            lead.campagne_id or "",
            lead.notes or ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"}
    )

@router.get("/")
def get_leads(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    campagne_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("newest", description="newest, oldest")
):
    """Récupère la liste des leads avec pagination et filtres"""
    query = db.query(LeadModel)
    
    # Filtres
    if status and status != "all":
        query = query.filter(LeadModel.status == status)
    
    if campagne_id:
        query = query.filter(LeadModel.campagne_id == campagne_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            LeadModel.first_name.ilike(search_term) |
            LeadModel.last_name.ilike(search_term) |
            LeadModel.email.ilike(search_term) |
            LeadModel.company.ilike(search_term)
        )
    
    # Tri par date de création
    if sort_by == "oldest":
        query = query.order_by(LeadModel.created_at.asc())
    else:  # newest par défaut
        query = query.order_by(LeadModel.created_at.desc())
    
    # Compter le total pour la pagination
    total = query.count()
    
    # Pagination
    offset = (page - 1) * limit
    leads = query.offset(offset).limit(limit).all()
    
    # Transformer en dictionnaires avec les bons noms de champs
    leads_data = [lead_to_dict(lead) for lead in leads]
    
    return {
        "leads": leads_data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }

@router.get("/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(deps.get_db)):
    """Récupère un lead spécifique"""
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead_to_dict(lead)

@router.put("/{lead_id}")
def update_lead(lead_id: int, lead_data: LeadUpdate, db: Session = Depends(deps.get_db)):
    """Met à jour un lead"""
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    
    # Mettre à jour les champs
    if lead_data.nom:
        parts = lead_data.nom.split()
        lead.first_name = parts[0] if parts else ""
        lead.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    
    if lead_data.email:
        lead.email = lead_data.email
    
    if lead_data.telephone:
        lead.phone = lead_data.telephone
    
    if lead_data.entreprise:
        lead.company = lead_data.entreprise
    
    if lead_data.statut:
        lead.status = lead_data.statut
    
    if lead_data.campagne_id is not None:
        lead.campagne_id = lead_data.campagne_id
    
    db.commit()
    db.refresh(lead)
    return lead_to_dict(lead)

@router.patch("/{lead_id}/status")
def update_lead_status(lead_id: int, status_data: LeadStatusUpdateRequest, db: Session = Depends(deps.get_db)):
    """Met à jour le statut d'un lead (pour le kanban)"""
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    
    # Valider le statut
    valid_statuses = ["new", "qualification", "presentation", "negotiation", "evaluation", "won", "lost"]
    if status_data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    lead.status = status_data.status
    
    # Ajouter une note si fournie
    if status_data.notes:
        if lead.notes:
            lead.notes += f"\n{status_data.notes}"
        else:
            lead.notes = status_data.notes
    
    db.commit()
    db.refresh(lead)
    return lead_to_dict(lead)

@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(deps.get_db)):
    """Supprime un lead"""
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    
    db.delete(lead)
    db.commit()
    return {"message": "Lead deleted successfully"}

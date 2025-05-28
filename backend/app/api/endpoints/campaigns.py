from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.api import deps
from app.models.campaign import Campaign as CampaignModel
from app.models.lead import Lead as LeadModel
from app.schemas.campaign import Campaign, CampaignCreate, CampaignUpdate
from app.crud import campaign as crud
from app.models.user import User as UserModel

router = APIRouter()

# Schéma pour la mise à jour du statut
class StatusUpdate(BaseModel):
    status: str

@router.get("/", response_model=List[Campaign])
def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    niche_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """
    Récupérer toutes les campagnes avec filtrage optionnel.
    """
    query = db.query(CampaignModel)

    if search:
        query = query.filter(CampaignModel.nom.ilike(f"%{search}%"))

    if status:
        query = query.filter(CampaignModel.statut == status)

    if niche_id:
        query = query.filter(CampaignModel.niche_id == niche_id)

    campaigns = query.offset(skip).limit(limit).all()

    # Enrichir les campagnes avec des données calculées
    for campaign in campaigns:
        # Progression
        if campaign.target_leads and campaign.target_leads > 0:
            lead_count = db.query(func.count(LeadModel.id)).filter(LeadModel.campagne_id == campaign.id).scalar() or 0
            campaign.progress = min(int((lead_count / campaign.target_leads) * 100), 100)
        else:
            campaign.progress = 0

        # Taux de conversion
        total_leads = db.query(func.count(LeadModel.id)).filter(LeadModel.campagne_id == campaign.id).scalar() or 0
        converted_leads = db.query(func.count(LeadModel.id)).filter(
            LeadModel.campagne_id == campaign.id,
            LeadModel.statut == "converted"
        ).scalar() or 0

        if total_leads > 0:
            campaign.conversion = round((converted_leads / total_leads) * 100, 1)
        else:
            campaign.conversion = 0.0

    return jsonable_encoder(campaigns)

@router.get("/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: int, db: Session = Depends(deps.get_db)):
    """
    Récupérer une campagne spécifique par son ID.
    """
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Enrichir la campagne avec des données calculées
    if campaign.target_leads and campaign.target_leads > 0:
        lead_count = db.query(func.count(LeadModel.id)).filter(LeadModel.campagne_id == campaign.id).scalar() or 0
        campaign.progress = min(int((lead_count / campaign.target_leads) * 100), 100)
    else:
        campaign.progress = 0
    
    # Taux de conversion
    total_leads = db.query(func.count(LeadModel.id)).filter(LeadModel.campagne_id == campaign.id).scalar() or 0
    converted_leads = db.query(func.count(LeadModel.id)).filter(
        LeadModel.campagne_id == campaign.id,
        LeadModel.statut == "converted"
    ).scalar() or 0

    if total_leads > 0:
        campaign.conversion = round((converted_leads / total_leads) * 100, 1)
    else:
        campaign.conversion = 0.0
    
    return jsonable_encoder(campaign)

@router.post("/", response_model=Campaign)
def create_campaign(
    campaign_in: CampaignCreate,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
):
    campaign = crud.campaign.create(db=db, obj_in=campaign_in)
    return jsonable_encoder(campaign)

@router.put("/{id}", response_model=Campaign)
def update_campaign(
    id: int,
    campaign_in: CampaignUpdate,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
):
    campaign = crud.campaign.get(db=db, id=id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = crud.campaign.update(db=db, db_obj=campaign, obj_in=campaign_in)
    return jsonable_encoder(campaign)

@router.put("/{campaign_id}/status", response_model=Campaign)
def update_campaign_status(
    campaign_id: int, 
    status_data: StatusUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Mettre à jour le statut d'une campagne.
    """
    db_campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    
    # Valider le statut
    valid_statuses = ["active", "paused", "completed", "archived"]
    if status_data.status not in valid_statuses:
        raise HTTPException(
            status_code=422, 
            detail=f"Statut invalide. Valeurs autorisées: {', '.join(valid_statuses)}"
        )
    
    db_campaign.status = status_data.status
    db.commit()
    db.refresh(db_campaign)
    return jsonable_encoder(db_campaign)

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: int, db: Session = Depends(deps.get_db)):
    """
    Supprimer une campagne en gérant les contraintes de clés étrangères.
    """
    db_campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Vérifier s'il y a des leads associés
    leads_count = db.query(func.count(LeadModel.id)).filter(LeadModel.campagne_id == campaign_id).scalar() or 0
    
    if leads_count > 0:
        # Option 1: Dissocier les leads (mettre campagne_id à NULL)
        db.query(LeadModel).filter(LeadModel.campagne_id == campaign_id).update(
            {"campagne_id": None}, synchronize_session=False
        )
        
        # Option 2: Alternative - Empêcher la suppression
        # raise HTTPException(
        #     status_code=400, 
        #     detail=f"Impossible de supprimer la campagne. {leads_count} leads y sont associés."
        # )
    
    try:
        db.delete(db_campaign)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

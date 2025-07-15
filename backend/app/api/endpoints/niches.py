from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func
from fastapi.encoders import jsonable_encoder

from app.api import deps
from app.models.niche import Niche as NicheModel
from app.models.campaign import Campaign as CampaignModel
from app.models.lead import Lead as LeadModel
from app.schemas.niche import NicheResponse, NicheCreate, NicheUpdate

router = APIRouter(tags=["Niches"])

@router.get("/", response_model=List[dict])
def get_niches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = Query(None),
    statut: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère la liste des niches CORRIGÉE avec vrais noms de champs
    """
    query = db.query(NicheModel)

    # CORRECTION : Utiliser les VRAIS noms de champs
    if search:
        query = query.filter(NicheModel.name.ilike(f"%{search}%"))

    if statut:
        query = query.filter(NicheModel.status == statut)

    niches = query.offset(skip).limit(limit).all()

    # Enrichir avec données calculées
    result = []
    for niche in niches:
        campaigns_count = db.query(CampaignModel).filter(CampaignModel.niche_id == niche.id).count()
        leads_count = db.query(LeadModel).join(CampaignModel).filter(CampaignModel.niche_id == niche.id).count()
        
        result.append({
            "id": niche.id,
            "name": niche.name,
            "description": niche.description,
            "status": niche.status,
            "campaigns_count": campaigns_count,
            "leads_count": leads_count,
            "created_at": niche.created_at
        })
        
    return result

@router.get("/{niche_id}", response_model=dict)
def get_niche(niche_id: int, db: Session = Depends(deps.get_db)):
    """
    Récupère une niche spécifique CORRIGÉE
    """
    niche = db.query(NicheModel).filter(NicheModel.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")

    # Charger données associées
    campaigns = db.query(CampaignModel).filter(CampaignModel.niche_id == niche.id).all()
    leads_count = db.query(LeadModel).join(CampaignModel).filter(CampaignModel.niche_id == niche.id).count()
    
    return {
        "id": niche.id,
        "name": niche.name,
        "description": niche.description,
        "status": niche.status,
        "campaigns": [jsonable_encoder(c) for c in campaigns],
        "leads_count": leads_count,
        "created_at": niche.created_at
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_niche(niche: NicheCreate, db: Session = Depends(deps.get_db)):
    """
    Crée une nouvelle niche CORRIGÉE
    """
    # CORRECTION : Utiliser les vrais noms de champs du schéma
    db_niche = NicheModel(
        name=niche.nom,  # Le schéma utilise 'nom' avec alias 'name'
        description=niche.description,
        status=niche.statut if hasattr(niche, 'statut') else 'active'
    )
    db.add(db_niche)
    db.commit()
    db.refresh(db_niche)
    return jsonable_encoder(db_niche)

@router.put("/{niche_id}")
def update_niche(niche_id: int, niche: NicheUpdate, db: Session = Depends(deps.get_db)):
    """
    Met à jour une niche CORRIGÉE
    """
    db_niche = db.query(NicheModel).filter(NicheModel.id == niche_id).first()
    if not db_niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    update_data = niche.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_niche, key, value)
    
    db.commit()
    db.refresh(db_niche)
    return jsonable_encoder(db_niche)

@router.delete("/{niche_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_niche(niche_id: int, db: Session = Depends(deps.get_db)):
    """
    Supprime une niche
    """
    db_niche = db.query(NicheModel).filter(NicheModel.id == niche_id).first()
    if not db_niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    db.delete(db_niche)
    db.commit()
    return None

@router.get("/stats", response_model=List[dict])
def get_niches_stats(period: str = Query("30d"), db: Session = Depends(deps.get_db)):
    """
    Statistiques des niches SIMPLIFIÉES et CORRIGÉES
    """
    niches = db.query(NicheModel).all()
    
    result = []
    for niche in niches:
        # Compter campagnes et leads
        campaigns_count = db.query(CampaignModel).filter(CampaignModel.niche_id == niche.id).count()
        leads_count = db.query(LeadModel).join(CampaignModel).filter(CampaignModel.niche_id == niche.id).count()
        qualified_leads = db.query(LeadModel).join(CampaignModel).filter(
            CampaignModel.niche_id == niche.id,
            LeadModel.status == "qualified"  # CORRECTION : vrai statut
        ).count()
        
        conversion_rate = (qualified_leads / leads_count * 100) if leads_count > 0 else 0
        
        result.append({
            "niche": niche.name,  # CORRECTION : name pas nom
            "campaigns": campaigns_count,
            "leads": leads_count,
            "conversion": round(conversion_rate, 1),
            "trend": [0] * 7  # Trend simplifié pour l'instant
        })
    
    return result

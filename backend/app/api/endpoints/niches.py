from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func, cast, text
import sqlalchemy as sa

from app.api import deps
from app.models.niche import Niche as NicheModel
from app.models.campaign import Campaign as CampaignModel
from app.models.lead import Lead as LeadModel
from app.schemas.niche import NicheResponse, NicheCreate, NicheUpdate

from fastapi.encoders import jsonable_encoder
router = APIRouter(tags=["Niches"])


@router.get("/", response_model=List[NicheResponse])
def get_niches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = Query(None),
    statut: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère la liste des niches avec filtres optionnels
    """
    query = db.query(NicheModel)

    if search:
        query = query.filter(NicheModel.nom.ilike(f"%{search}%"))

    if statut:
        query = query.filter(NicheModel.statut == statut)

    niches = query.offset(skip).limit(limit).all()

    # Enrichir les niches avec des données calculées si nécessaire
    for niche in niches:
        # Si vous avez besoin de charger les campagnes associées
        campaigns = db.query(CampaignModel).filter(CampaignModel.niche_id == niche.id).all()
        niche.campagnes = campaigns
        
    # Utiliser jsonable_encoder pour sérialiser les objets SQLAlchemy
    result = jsonable_encoder(niches)
    return result

@router.get("/{niche_id}", response_model=NicheResponse)
def get_niche(niche_id: int, db: Session = Depends(deps.get_db)):
    """
    Récupère une niche spécifique par son ID
    """
    niche = db.query(NicheModel).filter(NicheModel.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")

    # Charger les campagnes associées
    campaigns = db.query(CampaignModel).filter(CampaignModel.niche_id == niche.id).all()
    niche.campagnes = campaigns
    
    # Utiliser jsonable_encoder pour sérialiser l'objet SQLAlchemy
    result = jsonable_encoder(niche)
    return result

@router.post("/", response_model=NicheResponse, status_code=status.HTTP_201_CREATED)
def create_niche(niche: NicheCreate, db: Session = Depends(deps.get_db)):
    """
    Crée une nouvelle niche
    """
    db_niche = NicheModel(
        nom=niche.nom,
        description=niche.description,
        statut=niche.statut,
        taux_conversion=niche.taux_conversion,
        cout_par_lead=niche.cout_par_lead,
        recommandation=niche.recommandation
    )
    db.add(db_niche)
    db.commit()
    db.refresh(db_niche)
    return jsonable_encoder(db_niche)

@router.get("/{niche_id}", response_model=NicheResponse)
def get_niche(niche_id: int, db: Session = Depends(deps.get_db)):
    """
    Récupère une niche spécifique par son ID
    """
    niche = db.query(NicheModel).filter(NicheModel.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    # Enrichir la niche avec des données calculées
    niche.campagnes = db.query(CampaignModel).filter(CampaignModel.niche_id == niche.id).all()
    
    # Compter les leads
    # Préparation des données pour la sérialisation
    from fastapi.encoders import jsonable_encoder
    # Utiliser des objets dict avec uniquement les attributs nécessaires
    # Préparer la niche pour la sérialisation
        # Préparer les données pour la sérialisation pour jsonable_encoder
    lead_count = 0
    for campagne in niche.campagnes:
        campagne_leads = db.query(LeadModel).filter(LeadModel.campagne_id == campagne.id).all()
        lead_count += len(campagne_leads)
        
    niche.leads = []  # Nous ne renvoyons pas les leads individuels, juste le compte
    
    return jsonable_encoder(jsonable_encoder)(niche)

@router.put("/{niche_id}", response_model=NicheResponse)
def update_niche(niche_id: int, niche: NicheUpdate, db: Session = Depends(deps.get_db)):
    """
    Met à jour une niche existante
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
    Récupère les statistiques des niches
    """
    days = int(period.replace("d", ""))
    start_date = func.now() - cast(f"{days} days", sa.Interval)

    subquery = (
        db.query(
            CampaignModel.niche_id.label("niche_id"),
            func.date_trunc("day", LeadModel.date_creation).label("day"),
            func.count(LeadModel.id).label("leads_count"),
            func.avg(func.case((LeadModel.statut == "converted", 1), else_=0)).label("conversion_rate")
        )
        .join(LeadModel, CampaignModel.id == LeadModel.campagne_id)
        .filter(LeadModel.date_creation >= start_date)
        .group_by("niche_id", "day")
        .subquery()
    )
    # Préparation des données pour la sérialisation
    from fastapi.encoders import jsonable_encoder
    # Utiliser des objets dict avec uniquement les attributs nécessaires
                    # Créer des copies des leads avec uniquement les attributs nécessaires
                        # Ajouter d'autres attributs selon le schéma

    results = (
        db.query(
            NicheModel.nom.label("niche"),
            func.array_agg(
                subquery.c.leads_count.op("ORDER BY")(text("day"))
            ).label("trend"),
            func.avg(subquery.c.conversion_rate).label("conversion")
        )
        .join(subquery, subquery.c.niche_id == NicheModel.id)
        .group_by(NicheModel.nom)
        .all()
    )

    return [
        {
            "niche": row.niche,
            "trend": row.trend,
            "conversion": float(row.conversion or 0)
        }
        for row in results
    ]
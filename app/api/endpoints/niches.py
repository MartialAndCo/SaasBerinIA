from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Niche])
def get_niches(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    statut: Optional[str] = None,
    db: Session = Depends(deps.get_db)
):
    """
    Récupère la liste des niches avec filtres optionnels
    """
    niches = crud.niche.get_multi_with_filters(
        db, 
        skip=skip, 
        limit=limit, 
        search=search,
        statut=statut
    )
    
    # Formater les niches pour le frontend
    result = []
    for niche in niches:
        # Calculer le nombre de campagnes
        campagnes_count = len(niche.campagnes)
        
        # Calculer le nombre total de leads
        leads_count = sum(len(campagne.leads) for campagne in niche.campagnes)
        
        result.append({
            "id": niche.id,
            "nom": niche.nom,
            "description": niche.description,
            "date_creation": niche.date_creation.strftime("%d/%m/%Y"),
            "statut": niche.statut,
            "taux_conversion": niche.taux_conversion,
            "cout_par_lead": niche.cout_par_lead,
            "recommandation": niche.recommandation,
            "campagnes": campagnes_count,
            "leads": leads_count
        })
    
    return result


@router.post("/", response_model=schemas.Niche)
def create_niche(
    niche_in: schemas.NicheCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Crée une nouvelle niche
    """
    # Vérifier si une niche avec le même nom existe déjà
    existing_niche = crud.niche.get_by_name(db, name=niche_in.nom)
    if existing_niche:
        raise HTTPException(status_code=400, detail="Une niche avec ce nom existe déjà")
    
    # Créer la niche
    niche = crud.niche.create(db, obj_in=niche_in)
    
    return {
        "id": niche.id,
        "nom": niche.nom,
        "description": niche.description,
        "date_creation": niche.date_creation.strftime("%d/%m/%Y"),
        "statut": niche.statut,
        "taux_conversion": niche.taux_conversion,
        "cout_par_lead": niche.cout_par_lead,
        "recommandation": niche.recommandation,
        "campagnes": 0,
        "leads": 0
    }


@router.put("/{niche_id}", response_model=schemas.Niche)
def update_niche(
    niche_id: int,
    niche_in: schemas.NicheUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Met à jour une niche existante
    """
    # Vérifier si la niche existe
    niche = crud.niche.get(db, niche_id)
    if not niche:
        raise HTTPException(status_code=404, detail="Niche non trouvée")
    
    # Si le nom est modifié, vérifier qu'il n'existe pas déjà
    if niche_in.nom and niche_in.nom != niche.nom:
        existing_niche = crud.niche.get_by_name(db, name=niche_in.nom)
        if existing_niche:
            raise HTTPException(status_code=400, detail="Une niche avec ce nom existe déjà")
    
    # Mettre à jour la niche
    niche = crud.niche.update(db, db_obj=niche, obj_in=niche_in)
    
    # Calculer le nombre de campagnes
    campagnes_count = len(niche.campagnes)
    
    # Calculer le nombre total de leads
    leads_count = sum(len(campagne.leads) for campagne in niche.campagnes)
    
    return {
        "id": niche.id,
        "nom": niche.nom,
        "description": niche.description,
        "date_creation": niche.date_creation.strftime("%d/%m/%Y"),
        "statut": niche.statut,
        "taux_conversion": niche.taux_conversion,
        "cout_par_lead": niche.cout_par_lead,
        "recommandation": niche.recommandation,
        "campagnes": campagnes_count,
        "leads": leads_count
    }


@router.delete("/{niche_id}", response_model=dict)
def delete_niche(
    niche_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Supprime une niche
    """
    # Vérifier si la niche existe
    niche = crud.niche.get(db, niche_id)
    if not niche:
        raise HTTPException(status_code=404, detail="Niche non trouvée")
    
    # Vérifier si la niche a des campagnes
    if niche.campagnes:
        raise HTTPException(
            status_code=400, 
            detail="Impossible de supprimer cette niche car elle contient des campagnes. Supprimez d'abord les campagnes."
        )
    
    # Supprimer la niche
    crud.niche.remove(db, id=niche_id)
    
    return {"success": True, "message": "Niche supprimée avec succès"} 
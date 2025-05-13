from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import csv
import os
from typing import List, Optional
from datetime import datetime

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Lead])
def get_leads(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    campaign_id: Optional[int] = None,
    db: Session = Depends(deps.get_db)
):
    """
    Récupère la liste des leads avec filtres optionnels
    """
    leads = crud.lead.get_multi_with_filters(
        db, 
        skip=skip, 
        limit=limit, 
        search=search,
        status=status,
        campaign_id=campaign_id
    )
    
    # Formater les leads pour le frontend
    result = []
    for lead in leads:
        result.append({
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "company": lead.company,
            "campaign": lead.campaign.name,
            "status": lead.status,
            "date": lead.date.strftime("%d/%m/%Y")
        })
    
    return result


@router.post("/", response_model=schemas.Lead)
def create_lead(
    lead_in: schemas.LeadCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Crée un nouveau lead
    """
    # Vérifier si la campagne existe
    campaign = crud.campaign.get(db, lead_in.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    
    # Créer le lead
    lead = crud.lead.create(db, obj_in=lead_in)
    
    return {
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "company": lead.company,
        "campaign": campaign.name,
        "status": lead.status,
        "date": lead.date.strftime("%d/%m/%Y")
    }


@router.put("/{lead_id}", response_model=schemas.Lead)
def update_lead(
    lead_id: int,
    lead_in: schemas.LeadUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Met à jour un lead existant
    """
    # Vérifier si le lead existe
    lead = crud.lead.get(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    
    # Mettre à jour le lead
    lead = crud.lead.update(db, db_obj=lead, obj_in=lead_in)
    
    return {
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "company": lead.company,
        "campaign": lead.campaign.name,
        "status": lead.status,
        "date": lead.date.strftime("%d/%m/%Y")
    }


@router.delete("/{lead_id}", response_model=dict)
def delete_lead(
    lead_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Supprime un lead
    """
    # Vérifier si le lead existe
    lead = crud.lead.get(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    
    # Supprimer le lead
    crud.lead.remove(db, id=lead_id)
    
    return {"success": True, "message": "Lead supprimé avec succès"}


@router.get("/export/csv", response_model=dict)
def export_leads_to_csv(
    background_tasks: BackgroundTasks,
    campaign_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(deps.get_db)
):
    """
    Exporte les leads au format CSV
    """
    # Générer le fichier CSV en tâche de fond
    background_tasks.add_task(
        generate_leads_csv,
        db=db,
        campaign_id=campaign_id,
        status=status
    )
    
    return {"success": True, "message": "Export des leads en cours. Le fichier sera disponible prochainement."}


@router.post("/sync-ghl", response_model=dict)
def sync_leads_to_ghl(
    lead_ids: List[int],
    db: Session = Depends(deps.get_db)
):
    """
    Synchronise les leads sélectionnés avec Go High Level
    """
    # Vérifier si les leads existent
    for lead_id in lead_ids:
        lead = crud.lead.get(db, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} non trouvé")
    
    # Simuler la synchronisation avec GHL
    # Dans une implémentation réelle, on appellerait l'API GHL ici
    
    return {"success": True, "message": f"{len(lead_ids)} leads synchronisés avec Go High Level"}


def generate_leads_csv(db: Session, campaign_id: Optional[int] = None, status: Optional[str] = None):
    """
    Génère un fichier CSV avec les leads filtrés
    """
    # Récupérer les leads avec les filtres
    leads = crud.lead.get_multi_with_filters(
        db, 
        skip=0, 
        limit=1000,  # Limiter à 1000 leads pour l'export
        campaign_id=campaign_id,
        status=status
    )
    
    # Créer le répertoire d'export si nécessaire
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    
    # Générer un nom de fichier unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{export_dir}/leads_export_{timestamp}.csv"
    
    # Écrire les données dans le fichier CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Écrire l'en-tête
        writer.writerow(['ID', 'Nom', 'Email', 'Téléphone', 'Entreprise', 'Campagne', 'Statut', 'Date'])
        
        # Écrire les données
        for lead in leads:
            writer.writerow([
                lead.id,
                lead.name,
                lead.email,
                lead.phone,
                lead.company,
                lead.campaign.name,
                lead.status,
                lead.date.strftime("%d/%m/%Y")
            ])
    
    return filename 
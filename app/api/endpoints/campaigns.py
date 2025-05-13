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


@router.get("/", response_model=List[schemas.Campaign])
def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    niche_id: Optional[int] = None,
    db: Session = Depends(deps.get_db)
):
    """
    Récupère la liste des campagnes avec filtres optionnels
    """
    campaigns = crud.campaign.get_multi_with_filters(
        db, 
        skip=skip, 
        limit=limit, 
        search=search,
        status=status,
        niche_id=niche_id
    )
    
    # Formater les campagnes pour le frontend
    result = []
    for campaign in campaigns:
        # Calculer le nombre de leads et le taux de conversion
        leads_count = len(campaign.leads)
        conversion_rate = 0
        if leads_count > 0:
            # Simuler un taux de conversion basé sur le statut des leads
            converted_leads = sum(1 for lead in campaign.leads if lead.status == "converted")
            conversion_rate = (converted_leads / leads_count) * 100
        
        # Calculer la progression
        progress = 0
        if hasattr(campaign, 'targetLeads') and campaign.targetLeads > 0:
            progress = min(100, int((leads_count / campaign.targetLeads) * 100))
        
        result.append({
            "id": campaign.id,
            "name": campaign.name,
            "niche": campaign.niche.nom,
            "status": campaign.status,
            "leads": leads_count,
            "conversion": round(conversion_rate, 1),
            "date": campaign.date.strftime("%d/%m/%Y"),
            "agent": campaign.agent if hasattr(campaign, 'agent') and campaign.agent else "Scraper Agent",
            "progress": progress,
            "description": campaign.description,
            "targetLeads": campaign.targetLeads if hasattr(campaign, 'targetLeads') else 500
        })
    
    return result


@router.post("/", response_model=schemas.Campaign)
def create_campaign(
    campaign_in: schemas.CampaignCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Crée une nouvelle campagne
    """
    # Vérifier si la niche existe
    niche = crud.niche.get_by_name(db, name=campaign_in.niche)
    if not niche:
        raise HTTPException(status_code=404, detail="Niche non trouvée")
    
    # Créer la campagne
    campaign_data = {
        "name": campaign_in.name,
        "description": campaign_in.description,
        "niche_id": niche.id,
        "status": "active",
        "agent": campaign_in.agent,
        "targetLeads": campaign_in.targetLeads
    }
    
    campaign = crud.campaign.create(db, obj_in=campaign_data)
    
    return {
        "id": campaign.id,
        "name": campaign.name,
        "niche": niche.nom,
        "status": campaign.status,
        "leads": 0,
        "conversion": 0,
        "date": campaign.date.strftime("%d/%m/%Y"),
        "agent": campaign.agent,
        "progress": 0,
        "description": campaign.description,
        "targetLeads": campaign.targetLeads
    }


@router.put("/{campaign_id}", response_model=schemas.Campaign)
def update_campaign(
    campaign_id: int,
    campaign_in: schemas.CampaignUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Met à jour une campagne existante
    """
    # Vérifier si la campagne existe
    campaign = crud.campaign.get(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    
    # Mettre à jour la campagne
    campaign = crud.campaign.update(db, db_obj=campaign, obj_in=campaign_in)
    
    # Calculer le nombre de leads et le taux de conversion
    leads_count = len(campaign.leads)
    conversion_rate = 0
    if leads_count > 0:
        converted_leads = sum(1 for lead in campaign.leads if lead.status == "converted")
        conversion_rate = (converted_leads / leads_count) * 100
    
    # Calculer la progression
    progress = 0
    if hasattr(campaign, 'targetLeads') and campaign.targetLeads > 0:
        progress = min(100, int((leads_count / campaign.targetLeads) * 100))
    
    return {
        "id": campaign.id,
        "name": campaign.name,
        "niche": campaign.niche.nom,
        "status": campaign.status,
        "leads": leads_count,
        "conversion": round(conversion_rate, 1),
        "date": campaign.date.strftime("%d/%m/%Y"),
        "agent": campaign.agent if hasattr(campaign, 'agent') and campaign.agent else "Scraper Agent",
        "progress": progress,
        "description": campaign.description,
        "targetLeads": campaign.targetLeads if hasattr(campaign, 'targetLeads') else 500
    }


@router.delete("/{campaign_id}", response_model=dict)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Supprime une campagne
    """
    # Vérifier si la campagne existe
    campaign = crud.campaign.get(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    
    # Supprimer la campagne
    crud.campaign.remove(db, id=campaign_id)
    
    return {"success": True, "message": "Campagne supprimée avec succès"}


@router.get("/{campaign_id}/export", response_model=dict)
def export_campaign_leads(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Exporte les leads d'une campagne au format CSV
    """
    # Vérifier si la campagne existe
    campaign = crud.campaign.get(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    
    # Générer le fichier CSV en tâche de fond
    background_tasks.add_task(
        generate_campaign_leads_csv,
        db=db,
        campaign_id=campaign_id
    )
    
    return {"success": True, "message": f"Export des leads de la campagne '{campaign.name}' en cours. Le fichier sera disponible prochainement."}


def generate_campaign_leads_csv(db: Session, campaign_id: int):
    """
    Génère un fichier CSV avec les leads d'une campagne
    """
    # Récupérer la campagne et ses leads
    campaign = crud.campaign.get(db, campaign_id)
    if not campaign:
        return None
    
    # Créer le répertoire d'export si nécessaire
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    
    # Générer un nom de fichier unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{export_dir}/campaign_{campaign_id}_leads_{timestamp}.csv"
    
    # Écrire les données dans le fichier CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Écrire l'en-tête
        writer.writerow(['ID', 'Nom', 'Email', 'Téléphone', 'Entreprise', 'Statut', 'Date'])
        
        # Écrire les données
        for lead in campaign.leads:
            writer.writerow([
                lead.id,
                lead.name,
                lead.email,
                lead.phone,
                lead.company,
                lead.status,
                lead.date.strftime("%d/%m/%Y")
            ])
    
    return filename 
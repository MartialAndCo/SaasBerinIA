from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import logging
import os
import sys

from app.api import deps
from app.models.campaign import Campaign as CampaignModel
from app.models.lead import Lead as LeadModel
from app.models.niche import Niche as NicheModel

# Import du client Instantly depuis infra-ia
sys.path.append('/root/berinia/infra-ia')
from utils.api_clients.instantly_client import InstantlyClient

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Campaigns Management"])

class CampaignLaunchRequest(BaseModel):
    niche_id: int
    city: str
    target_leads: Optional[int] = 100
    description: Optional[str] = None

@router.get("/active", response_model=List[dict])
def get_active_campaigns(db: Session = Depends(deps.get_db)):
    """
    Récupérer les campagnes actives
    """
    campaigns = db.query(CampaignModel).filter(CampaignModel.status == "active").all()
    
    if not campaigns:
        return []

    result = []
    for campaign in campaigns:
        # Récupérer la niche associée
        niche = db.query(NicheModel).filter(NicheModel.id == campaign.niche_id).first()
        
        # Compter les leads
        leads_count = db.query(LeadModel).filter(LeadModel.campagne_id == campaign.id).count()
        qualified_leads = db.query(LeadModel).filter(
            LeadModel.campagne_id == campaign.id,
            LeadModel.status == "qualified"
        ).count()

        progress = 0
        if campaign.target_leads and campaign.target_leads > 0:
            progress = min(int((leads_count / campaign.target_leads) * 100), 100)

        result.append({
            "id": campaign.id,
            "name": campaign.name,
            "description": campaign.description,
            "niche_name": niche.name if niche else "Inconnue",
            "status": campaign.status,
            "leads_count": leads_count,
            "qualified_leads": qualified_leads,
            "target_leads": campaign.target_leads,
            "progress": progress,
            "created_at": campaign.created_at
        })

    return result

@router.get("/inactive", response_model=List[dict])
def get_inactive_campaigns(db: Session = Depends(deps.get_db)):
    """
    Récupérer les campagnes inactives (draft, paused, completed)
    """
    campaigns = db.query(CampaignModel).filter(
        CampaignModel.status.in_(["draft", "paused", "completed"])
    ).all()
    
    if not campaigns:
        return []

    result = []
    for campaign in campaigns:
        niche = db.query(NicheModel).filter(NicheModel.id == campaign.niche_id).first()
        leads_count = db.query(LeadModel).filter(LeadModel.campagne_id == campaign.id).count()

        result.append({
            "id": campaign.id,
            "name": campaign.name,
            "niche_name": niche.name if niche else "Inconnue",
            "status": campaign.status,
            "leads_count": leads_count,
            "created_at": campaign.created_at
        })

    return result

@router.get("/stats/{campaign_id}", response_model=dict)
def get_campaign_stats(campaign_id: int, db: Session = Depends(deps.get_db)):
    """
    Statistiques détaillées d'une campagne
    """
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Récupérer la niche
    niche = db.query(NicheModel).filter(NicheModel.id == campaign.niche_id).first()

    # Statistiques des leads
    total_leads = db.query(LeadModel).filter(LeadModel.campagne_id == campaign.id).count()
    qualified_leads = db.query(LeadModel).filter(
        LeadModel.campagne_id == campaign.id,
        LeadModel.status == "qualified"
    ).count()
    new_leads = db.query(LeadModel).filter(
        LeadModel.campagne_id == campaign.id,
        LeadModel.status == "new"
    ).count()

    # Calculer les taux
    qualification_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
    progress = 0
    if campaign.target_leads and campaign.target_leads > 0:
        progress = min(int((total_leads / campaign.target_leads) * 100), 100)

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "niche_name": niche.name if niche else "Inconnue",
        "status": campaign.status,
        "total_leads": total_leads,
        "qualified_leads": qualified_leads,
        "new_leads": new_leads,
        "target_leads": campaign.target_leads,
        "progress": progress,
        "qualification_rate": round(qualification_rate, 1),
        "created_at": campaign.created_at
    }

@router.post("/launch", response_model=dict)
def launch_campaign(
    request: CampaignLaunchRequest,
    db: Session = Depends(deps.get_db)
):
    """
    Lancer une nouvelle campagne
    """
    # Vérifier que la niche existe
    niche = db.query(NicheModel).filter(NicheModel.id == request.niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")

    # Créer le nom de la campagne
    campaign_name = f"Campagne {niche.name} - {request.city}"
    
    # Vérifier qu'une campagne similaire n'existe pas déjà
    existing = db.query(CampaignModel).filter(
        CampaignModel.name == campaign_name,
        CampaignModel.status == "active"
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Une campagne active existe déjà pour {niche.name} à {request.city}"
        )

    # Créer la campagne BerinIA
    new_campaign = CampaignModel(
        name=campaign_name,
        ville=request.city,  # Ajouter la ville
        description=request.description or f"Prospection {niche.name} dans la ville de {request.city}",
        niche_id=request.niche_id,
        target_leads=request.target_leads,
        status="active",
        agent="MessagingAgent"
    )

    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)

    # Créer la campagne Instantly correspondante
    instantly_campaign_id = None
    instantly_error = None
    
    try:
        instantly_client = InstantlyClient()
        
        # Template de base pour les emails
        email_subject = f"Opportunité business pour {niche.name} à {request.city}"
        email_template = f"""
        Bonjour {{{{first_name}}}},

        J'ai identifié votre entreprise comme un acteur majeur dans le secteur {niche.name} à {request.city}.

        Je serais ravi de discuter avec vous d'une opportunité qui pourrait significativement impacter votre croissance.

        Seriez-vous disponible pour un échange de 15 minutes cette semaine ?

        Cordialement,
        L'équipe BerinIA
        """
        
        # Créer la campagne Instantly
        instantly_response = instantly_client.create_instantly_campaign(
            name=campaign_name,
            subject=email_subject,
            html_content=email_template,
            daily_limit=50
        )
        
        instantly_campaign_id = instantly_response.get("id")
        
        if instantly_campaign_id:
            # Mettre à jour la campagne BerinIA avec l'ID Instantly
            new_campaign.instantly_campaign_id = instantly_campaign_id
            db.commit()
            logger.info(f"Campagne Instantly créée avec ID: {instantly_campaign_id}")
        else:
            logger.warning("Réponse Instantly invalide - pas d'ID de campagne")
            instantly_error = "Réponse Instantly invalide"
            
    except Exception as e:
        logger.error(f"Erreur lors de la création de la campagne Instantly: {str(e)}")
        instantly_error = str(e)

    response = {
        "success": True,
        "campaign_id": new_campaign.id,
        "campaign_name": new_campaign.name,
        "instantly_campaign_id": instantly_campaign_id,
        "message": f"Campagne lancée avec succès pour {niche.name} à {request.city}"
    }
    
    if instantly_error:
        response["instantly_warning"] = f"Campagne BerinIA créée mais erreur Instantly: {instantly_error}"
    
    return response

@router.put("/{campaign_id}/stop", response_model=dict)
def stop_campaign(campaign_id: int, db: Session = Depends(deps.get_db)):
    """
    Arrêter une campagne active
    """
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status != "active":
        raise HTTPException(
            status_code=400, 
            detail=f"La campagne est déjà {campaign.status}, ne peut pas l'arrêter"
        )

    # Mettre à jour le statut
    campaign.status = "paused"
    db.commit()

    return {
        "success": True,
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "message": f"Campagne '{campaign.name}' arrêtée avec succès"
    }

@router.put("/{campaign_id}/restart", response_model=dict)
def restart_campaign(campaign_id: int, db: Session = Depends(deps.get_db)):
    """
    Redémarrer une campagne pausée
    """
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status not in ["paused", "draft"]:
        raise HTTPException(
            status_code=400, 
            detail=f"La campagne est {campaign.status}, ne peut pas la redémarrer"
        )

    # Redémarrer
    campaign.status = "active"
    db.commit()

    return {
        "success": True,
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "message": f"Campagne '{campaign.name}' redémarrée avec succès"
    }

@router.get("/export/{campaign_id}", response_model=dict)
def export_campaign_data(campaign_id: int, db: Session = Depends(deps.get_db)):
    """
    Exporter les données d'une campagne
    """
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Récupérer tous les leads de cette campagne
    leads = db.query(LeadModel).filter(LeadModel.campagne_id == campaign.id).all()

    leads_data = []
    for lead in leads:
        leads_data.append({
            "id": lead.id,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "email": lead.email,
            "phone": lead.phone,
            "company": lead.company or lead.entreprise,
            "status": lead.status,
            "created_at": str(lead.created_at)
        })

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "total_leads": len(leads_data),
        "export_date": str(func.now()),
        "leads": leads_data
    }

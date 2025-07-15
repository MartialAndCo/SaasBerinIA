from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import SessionLocal
from app.schemas.sandbox import SandboxLeadCreate, SandboxLead, SandboxMessageRequest, SandboxMessageResponse
from app.models.sandbox import SandboxLead as SandboxLeadModel, SandboxConversation
from app.models.niche import Niche
import json
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/api/sandbox/templates")
def get_templates():
    """Récupère les templates prédéfinis pour créer des profils de test"""
    templates = {
        "restaurant_traditionnel": {
            "name": "Restaurant Traditionnel",
            "data": {
                "first_name": "Jean",
                "last_name": "Dupont",
                "email": "jean.dupont@legourmand.fr",
                "phone": "0123456789",
                "company": "Le Gourmand",
                "position": "Propriétaire",
                "website": "www.legourmand-lyon.fr",
                "industry": "Restauration",
                "score": 65,
                "visual_score": 45,
                "site_type": "vitrine",
                "visual_quality": 6,
                "website_maturity": "basique"
            }
        }
    }
    return templates

@router.post("/api/sandbox/leads", response_model=SandboxLead)
def create_sandbox_lead(lead: SandboxLeadCreate, db: Session = Depends(get_db)):
    """Crée un lead de test pour le sandbox"""
    db_lead = SandboxLeadModel(**lead.dict())
    db_lead.created_by_user = "sandbox_user"
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@router.get("/api/sandbox/leads", response_model=List[SandboxLead])
def get_sandbox_leads(db: Session = Depends(get_db)):
    """Récupère tous les leads de test"""
    return db.query(SandboxLeadModel).all()

@router.post("/api/sandbox/conversation", response_model=SandboxMessageResponse)
def handle_sandbox_conversation(request: SandboxMessageRequest, db: Session = Depends(get_db)):
    """Gère les conversations dans le sandbox"""
    # Récupérer le lead de test
    lead = db.query(SandboxLeadModel).filter(SandboxLeadModel.id == request.sandbox_lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead de test non trouvé")
    
    # TODO: Intégrer avec le MessagingAgent
    # Pour l'instant, réponse simulée
    response = SandboxMessageResponse(
        success=True,
        message="Conversation initiée avec succès",
        ai_response="Bonjour, ceci est une réponse simulée de l'agent IA",
        conversation_id=1
    )
    
    return response

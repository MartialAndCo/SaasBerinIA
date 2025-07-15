from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import SessionLocal
from app.schemas.sandbox import (
    SandboxLeadCreate, 
    SandboxLead, 
    SandboxMessageRequest, 
    SandboxMessageResponse
)
from app.models.sandbox import SandboxLead as SandboxLeadModel, SandboxConversation
from app.models.niche import Niche
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Ajouter le chemin vers infra-ia pour importer le MessagingAgent
# __file__ = backend/app/api/endpoints/sandbox.py
# .parent = backend/app/api/endpoints/
# .parent.parent = backend/app/api/
# .parent.parent.parent = backend/app/
# .parent.parent.parent.parent = backend/
# .parent.parent.parent.parent.parent = / (racine berinia)
berinia_root = Path(__file__).parent.parent.parent.parent.parent
infra_ia_path = berinia_root / "infra-ia"
sys.path.insert(0, str(infra_ia_path))
sys.path.insert(0, str(berinia_root))

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/templates")
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
        },
        "ecommerce_moderne": {
            "name": "E-commerce Moderne",
            "data": {
                "first_name": "Marie",
                "last_name": "Martin",
                "email": "marie@boutique-tendance.com",
                "phone": "0987654321",
                "company": "Boutique Tendance",
                "position": "Directrice",
                "website": "www.boutique-tendance.com",
                "industry": "Commerce",
                "score": 85,
                "visual_score": 90,
                "site_type": "e-commerce",
                "visual_quality": 9,
                "website_maturity": "avancé"
            }
        },
        "artisan_local": {
            "name": "Artisan Local",
            "data": {
                "first_name": "Pierre",
                "last_name": "Moreau",
                "email": "contact@plomberie-moreau.fr",
                "phone": "0456789123",
                "company": "Plomberie Moreau",
                "position": "Artisan plombier",
                "website": "www.plomberie-moreau.fr",
                "industry": "Artisanat",
                "score": 70,
                "visual_score": 55,
                "site_type": "vitrine",
                "visual_quality": 7,
                "website_maturity": "intermédiaire"
            }
        }
    }
    return templates

@router.post("/leads", response_model=SandboxLead)
def create_sandbox_lead(lead: SandboxLeadCreate, db: Session = Depends(get_db)):
    """Crée un lead de test pour le sandbox"""
    db_lead = SandboxLeadModel(**lead.dict())
    db_lead.created_by_user = "sandbox_user"
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@router.get("/leads", response_model=List[SandboxLead])
def get_sandbox_leads(db: Session = Depends(get_db)):
    """Récupère tous les leads de test"""
    return db.query(SandboxLeadModel).all()

@router.post("/conversation", response_model=SandboxMessageResponse)
def handle_sandbox_conversation(request: SandboxMessageRequest, db: Session = Depends(get_db)):
    """Gère les conversations dans le sandbox avec le VRAI MessagingAgent"""
    
    # Récupérer le lead de test
    lead = db.query(SandboxLeadModel).filter(SandboxLeadModel.id == request.sandbox_lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead de test non trouvé")
    
    try:
        # Import dynamique du MessagingAgent avec chemin complet
        import importlib.util
        
        # Chemin complet vers le MessagingAgent
        messaging_agent_path = infra_ia_path / "agents" / "messaging" / "messaging_agent.py"
        
        if not messaging_agent_path.exists():
            raise ImportError(f"MessagingAgent non trouvé: {messaging_agent_path}")
        
        # Import dynamique avec importlib
        spec = importlib.util.spec_from_file_location("messaging_agent", messaging_agent_path)
        messaging_agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(messaging_agent_module)
        
        MessagingAgent = messaging_agent_module.MessagingAgent
        
        # Créer une instance du MessagingAgent en mode test
        messaging_agent = MessagingAgent()
        messaging_agent.config["test_mode"] = True  # Force le mode test pour le sandbox
        
        # 🔥 RÉCUPÉRER LES DIRECTIVES DEPUIS L'ENDPOINT MESSENGER
        try:
            import requests
            directives_response = requests.get("http://localhost:8000/api/messenger/directives", timeout=5)
            
            if directives_response.status_code == 200:
                directives = directives_response.json()
                
                # Injecter les directives dans la configuration du MessagingAgent
                messaging_agent.persona_config = {
                    "identity": {
                        "name": "Louise",
                        "entity": "BerinIA", 
                        "role": "Assistante commerciale"
                    },
                    "sms_instructions": directives.get("sms_instructions", ""),
                    "email_instructions": directives.get("email_instructions", ""),
                    "directives_loaded": True
                }
                
                print(f"[SANDBOX] Directives chargées: SMS={len(directives.get('sms_instructions', ''))} chars, Email={len(directives.get('email_instructions', ''))} chars")
                
            else:
                print(f"[SANDBOX] Erreur récupération directives: {directives_response.status_code}")
                
        except Exception as e:
            print(f"[SANDBOX] Erreur chargement directives: {e}")
        
        # Conversion du lead sandbox en format attendu par MessagingAgent
        lead_data = {
            "lead_id": lead.id,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "email": lead.email,
            "phone": lead.phone,
            "company": lead.company,
            "position": lead.position,
            "industry": lead.industry,
            "score": lead.score,
            "visual_score": lead.visual_score,
            "site_type": lead.site_type,
            "visual_quality": lead.visual_quality,
            "website_maturity": lead.website_maturity
        }
        
        ai_response = ""
        
        if request.action == "start_conversation":
            # 🎯 GÉNÉRATION INTELLIGENTE DU PREMIER MESSAGE
            print(f"[SANDBOX] Génération du premier message pour {lead.first_name}")
            
            # Utiliser la méthode _generate_auto_message du MessagingAgent
            message_data = messaging_agent._generate_auto_message(lead_data)
            
            if message_data:
                if request.platform == "sms":
                    # Pour SMS, prendre seulement le contenu (pas de sujet)
                    ai_response = message_data.get("content", "")
                else:  # email
                    # Pour email, inclure le sujet et le contenu
                    subject = message_data.get("subject", "")
                    content = message_data.get("content", "")
                    ai_response = f"Sujet: {subject}\n\n{content}"
            else:
                # Fallback en cas d'échec de génération
                ai_response = f"Bonjour {lead.first_name}, j'ai découvert votre entreprise {lead.company} et je pense que nous pourrions vous aider. Seriez-vous disponible pour en discuter ?"
                
        else:
            # 🤖 RÉPONSE INTELLIGENTE AVEC LE VRAI MESSAGINGAGENT
            print(f"[SANDBOX] Génération de réponse contextuelle pour: {request.user_message}")
            
            # Préparer les données pour generate_contextual_response
            input_data = {
                "lead_data": lead_data,
                "message": request.user_message,
                "channel": request.platform,
                "campaign_id": "sandbox_test",
                "subject": f"Re: Discussion avec {lead.company}"
            }
            
            # 🔥 INTÉGRER LES DIRECTIVES DANS LE PROMPT
            if hasattr(messaging_agent, 'persona_config') and messaging_agent.persona_config.get('directives_loaded'):
                # Ajouter les directives spécifiques selon la plateforme
                if request.platform == "sms":
                    input_data["custom_instructions"] = messaging_agent.persona_config.get('sms_instructions', '')
                else:  # email
                    input_data["custom_instructions"] = messaging_agent.persona_config.get('email_instructions', '')
                
                print(f"[SANDBOX] Instructions {request.platform} intégrées dans le prompt")
            
            # Utiliser la vraie méthode de génération de réponse contextuelle
            ai_response = messaging_agent.generate_contextual_response(input_data)
        
        # 📝 LOG POUR DEBUGGING
        print(f"[SANDBOX] Réponse générée ({len(ai_response)} chars): {ai_response[:100]}...")
        
        # Sauvegarder la conversation dans le sandbox (optionnel)
        try:
            conversation = SandboxConversation(
                sandbox_lead_id=lead.id,
                user_message=request.user_message if request.action != "start_conversation" else "",
                ai_response=ai_response,
                platform=request.platform,
                action=request.action,
                created_at=datetime.now()
            )
            db.add(conversation)
            db.commit()
            conversation_id = conversation.id
        except Exception as e:
            print(f"[SANDBOX] Erreur sauvegarde conversation: {e}")
            conversation_id = 1  # ID par défaut
        
        return SandboxMessageResponse(
            success=True,
            message="Réponse générée par le vrai MessagingAgent",
            ai_response=ai_response,
            conversation_id=conversation_id
        )
        
    except ImportError as e:
        # Erreur d'import du MessagingAgent
        error_msg = f"Impossible d'importer MessagingAgent: {str(e)}"
        print(f"[SANDBOX ERROR] {error_msg}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur système: {error_msg}"
        )
        
    except Exception as e:
        # Autres erreurs
        error_msg = f"Erreur lors de la génération de réponse: {str(e)}"
        print(f"[SANDBOX ERROR] {error_msg}")
        
        # Fallback avec réponse basique en cas d'erreur
        if request.action == "start_conversation":
            fallback_response = f"Bonjour {lead.first_name}, j'ai découvert votre entreprise {lead.company} et je pense que nous pourrions vous aider. Seriez-vous disponible pour en discuter ?"
        else:
            fallback_response = f"Merci pour votre message, {lead.first_name}. Je prends note de vos informations et reviendrai vers vous."
        
        return SandboxMessageResponse(
            success=True,
            message=f"Réponse fallback (erreur: {error_msg})",
            ai_response=fallback_response,
            conversation_id=1
        )

@router.delete("/leads/{lead_id}")
def delete_sandbox_lead(lead_id: int, db: Session = Depends(get_db)):
    """Supprime un lead de test"""
    lead = db.query(SandboxLeadModel).filter(SandboxLeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead de test non trouvé")
    
    db.delete(lead)
    db.commit()
    return {"message": "Lead de test supprimé avec succès"}

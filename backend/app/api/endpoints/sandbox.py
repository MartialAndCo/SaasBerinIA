from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List
from app.database.session import SessionLocal
from app.schemas.sandbox import (
    SandboxLeadCreate, 
    SandboxLead, 
    SandboxMessageRequest, 
    SandboxMessageResponse,
    SandboxConversationHistoryResponse,
    SandboxConversationListResponse,
    SandboxResetRequest,
    SandboxResetResponse
)
from app.models.sandbox import SandboxLead as SandboxLeadModel, SandboxConversation
from app.models.niche import Niche
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Ajouter le chemin vers infra-ia pour importer le MessagingAgent
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
                "website_maturity": "basique",
                "test_platform": "sms"
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
                "website_maturity": "avancé",
                "test_platform": "email"
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
                "website_maturity": "intermédiaire",
                "test_platform": "sms"
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

# 🆕 NOUVEAU SYSTÈME DE CONVERSATIONS AVEC SESSIONS

@router.post("/conversation", response_model=SandboxMessageResponse)
def handle_sandbox_conversation(request: SandboxMessageRequest, db: Session = Depends(get_db)):
    """Gère les conversations dans le sandbox avec système de sessions"""
    
    # Récupérer le lead de test
    lead = db.query(SandboxLeadModel).filter(SandboxLeadModel.id == request.sandbox_lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead de test non trouvé")
    
    # 🔄 GESTION DES ACTIONS
    if request.action == "reset_conversation":
        return reset_conversation_internal(request.sandbox_lead_id, request.platform, db)
    
    # 📝 RÉCUPÉRER OU CRÉER UNE SESSION
    session_id = request.conversation_session_id
    
    if request.action == "start_conversation" or not session_id:
        # Créer une nouvelle session
        session_id = SandboxConversation.generate_session_id()
        message_order = 1
        print(f"[SANDBOX] Nouvelle session créée: {session_id}")
    else:
        # Continuer une session existante
        last_message = db.query(SandboxConversation).filter(
            and_(
                SandboxConversation.conversation_session_id == session_id,
                SandboxConversation.sandbox_lead_id == request.sandbox_lead_id
            )
        ).order_by(SandboxConversation.message_order.desc()).first()
        
        message_order = (last_message.message_order + 1) if last_message else 1
        print(f"[SANDBOX] Continuation session {session_id}, message #{message_order}")
    
    try:
        # 🤖 GÉNÉRER LA RÉPONSE IA
        ai_response, ai_subject, ai_content = generate_ai_response(lead, request, session_id, db)
        
        # 💾 SAUVEGARDER LE MESSAGE
        conversation_entry = SandboxConversation(
            sandbox_lead_id=lead.id,
            conversation_session_id=session_id,
            message_order=message_order,
            message_type="start" if request.action == "start_conversation" else "exchange",
            messages={
                "user": request.user_message if request.user_message else "",
                "ai": ai_response,
                "ai_subject": ai_subject,
                "ai_content": ai_content,
                "timestamp": datetime.now().isoformat(),
                "platform": request.platform,
                "action": request.action
            },
            platform=request.platform,
            status="active"
        )
        
        db.add(conversation_entry)
        db.commit()
        db.refresh(conversation_entry)
        
        # 📜 RÉCUPÉRER L'HISTORIQUE POUR LA RÉPONSE
        conversation_history = get_conversation_history_internal(session_id, db)
        
        return SandboxMessageResponse(
            success=True,
            message="Réponse générée par le vrai MessagingAgent avec sessions",
            ai_response=ai_response,
            ai_subject=ai_subject,
            ai_content=ai_content,
            conversation_session_id=session_id,
            message_order=message_order,
            conversation_history=conversation_history
        )
        
    except Exception as e:
        error_msg = f"Erreur lors de la génération: {str(e)}"
        print(f"[SANDBOX ERROR] {error_msg}")
        
        # Fallback
        fallback_response = f"Désolé {lead.first_name}, une erreur technique s'est produite. Pouvez-vous reformuler votre demande ?"
        
        return SandboxMessageResponse(
            success=False,
            message=f"Erreur technique: {error_msg}",
            ai_response=fallback_response,
            conversation_session_id=session_id,
            error=error_msg
        )

@router.get("/conversations/{lead_id}", response_model=SandboxConversationListResponse)
def get_lead_conversations(lead_id: int, db: Session = Depends(get_db)):
    """Récupère la liste des conversations d'un lead"""
    
    # Vérifier que le lead existe
    lead = db.query(SandboxLeadModel).filter(SandboxLeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead de test non trouvé")
    
    # Récupérer les sessions de conversation
    conversations_query = db.query(
        SandboxConversation.conversation_session_id,
        func.min(SandboxConversation.created_at).label('start_time'),
        func.max(SandboxConversation.created_at).label('last_activity'),
        func.count(SandboxConversation.id).label('message_count'),
        SandboxConversation.platform
    ).filter(
        SandboxConversation.sandbox_lead_id == lead_id
    ).group_by(
        SandboxConversation.conversation_session_id,
        SandboxConversation.platform
    ).order_by(func.max(SandboxConversation.created_at).desc()).all()
    
    conversations = []
    for conv in conversations_query:
        conversations.append({
            "session_id": conv.conversation_session_id,
            "start_time": conv.start_time.isoformat(),
            "last_activity": conv.last_activity.isoformat(),
            "message_count": conv.message_count,
            "platform": conv.platform,
            "display_name": f"Conversation {conv.platform.upper()} - {conv.start_time.strftime('%d/%m %H:%M')}"
        })
    
    return SandboxConversationListResponse(
        sandbox_lead_id=lead_id,
        conversations=conversations,
        total_conversations=len(conversations)
    )

@router.get("/conversations/{lead_id}/{session_id}", response_model=SandboxConversationHistoryResponse)
def get_conversation_history(lead_id: int, session_id: str, db: Session = Depends(get_db)):
    """Récupère l'historique complet d'une conversation"""
    
    messages = db.query(SandboxConversation).filter(
        and_(
            SandboxConversation.sandbox_lead_id == lead_id,
            SandboxConversation.conversation_session_id == session_id
        )
    ).order_by(SandboxConversation.message_order).all()
    
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    # Infos du lead
    lead = db.query(SandboxLeadModel).filter(SandboxLeadModel.id == lead_id).first()
    lead_info = {
        "name": f"{lead.first_name} {lead.last_name}".strip(),
        "company": lead.company,
        "platform": messages[0].platform
    } if lead else None
    
    return SandboxConversationHistoryResponse(
        conversation_session_id=session_id,
        sandbox_lead_id=lead_id,
        platform=messages[0].platform,
        total_messages=len(messages),
        conversation_start=messages[0].created_at,
        conversation_end=messages[-1].created_at if len(messages) > 1 else None,
        messages=messages,
        lead_info=lead_info
    )

@router.post("/conversation/reset", response_model=SandboxResetResponse)
def reset_conversation(request: SandboxResetRequest, db: Session = Depends(get_db)):
    """Réinitialise une conversation (crée une nouvelle session)"""
    return reset_conversation_internal(request.sandbox_lead_id, request.platform, db, request.keep_lead)

@router.delete("/leads/{lead_id}")
def delete_sandbox_lead(lead_id: int, db: Session = Depends(get_db)):
    """Supprime un lead de test et toutes ses conversations"""
    lead = db.query(SandboxLeadModel).filter(SandboxLeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead de test non trouvé")
    
    # Supprimer toutes les conversations associées
    db.query(SandboxConversation).filter(SandboxConversation.sandbox_lead_id == lead_id).delete()
    
    # Supprimer le lead
    db.delete(lead)
    db.commit()
    
    return {"message": "Lead de test et conversations supprimés avec succès"}

# 🔧 FONCTIONS UTILITAIRES

def reset_conversation_internal(lead_id: int, platform: str, db: Session, keep_lead: bool = True):
    """Fonction interne pour réinitialiser une conversation"""
    
    # Vérifier que le lead existe
    lead = db.query(SandboxLeadModel).filter(SandboxLeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead de test non trouvé")
    
    # Archiver les conversations précédentes (optionnel)
    previous_conversations = db.query(SandboxConversation).filter(
        and_(
            SandboxConversation.sandbox_lead_id == lead_id,
            SandboxConversation.platform == platform,
            SandboxConversation.status == "active"
        )
    ).all()
    
    archived_count = 0
    for conv in previous_conversations:
        conv.status = "archived"
        archived_count += 1
    
    if archived_count > 0:
        db.commit()
    
    # Créer une nouvelle session
    new_session_id = SandboxConversation.generate_session_id()
    
    return SandboxResetResponse(
        success=True,
        message=f"Conversation réinitialisée pour {lead.first_name}. Nouvelle session créée.",
        new_conversation_session_id=new_session_id,
        previous_session_archived=archived_count > 0
    )

def get_conversation_history_internal(session_id: str, db: Session):
    """Récupère l'historique d'une session pour transmission à l'IA - FORMAT COMPATIBLE MESSAGING_AGENT"""
    
    messages = db.query(SandboxConversation).filter(
        SandboxConversation.conversation_session_id == session_id
    ).order_by(SandboxConversation.message_order).all()
    
    history = []
    for msg in messages:
        if msg.messages and isinstance(msg.messages, dict):
            # Format compatible avec get_conversation_history du MessagingAgent
            user_msg = msg.messages.get("user", "")
            ai_msg = msg.messages.get("ai", "")
            
            # Ajouter le message user s'il existe
            if user_msg and user_msg.strip():
                history.append({
                    "id": f"{msg.id}_user", 
                    "content": user_msg,
                    "sent_at": msg.messages.get("timestamp", msg.created_at.isoformat()),
                    "direction": "inbound",
                    "type": "reply"
                })
            
            # Ajouter le message AI s'il existe
            if ai_msg and ai_msg.strip():
                history.append({
                    "id": f"{msg.id}_ai",
                    "content": ai_msg, 
                    "subject": msg.messages.get("ai_subject"),
                    "content_only": msg.messages.get("ai_content", ai_msg),
                    "sent_at": msg.messages.get("timestamp", msg.created_at.isoformat()),
                    "direction": "outbound",
                    "type": "sms"
                })
    
    print(f"[SANDBOX] Historique formaté: {len(history)} messages pour session {session_id}")
    return history

def generate_ai_response(lead, request, session_id, db):
    """Génère une réponse IA avec le vrai MessagingAgent"""
    
    try:
        # Import dynamique du MessagingAgent
        import importlib.util
        
        messaging_agent_path = infra_ia_path / "agents" / "messaging" / "messaging_agent.py"
        
        if not messaging_agent_path.exists():
            raise ImportError(f"MessagingAgent non trouvé: {messaging_agent_path}")
        
        spec = importlib.util.spec_from_file_location("messaging_agent", messaging_agent_path)
        messaging_agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(messaging_agent_module)
        
        MessagingAgent = messaging_agent_module.MessagingAgent
        
        # Créer l'instance
        messaging_agent = MessagingAgent()
        messaging_agent.config["test_mode"] = True
        
        # 🔥 CHARGER LES DIRECTIVES
        try:
            import requests
            directives_response = requests.get("http://localhost:8000/api/messenger/directives", timeout=5)
            
            if directives_response.status_code == 200:
                directives = directives_response.json()
                messaging_agent.persona_config = {
                    "identity": {"name": "Louise", "entity": "BerinIA", "role": "Assistante commerciale"},
                    "sms_instructions": directives.get("sms_instructions", ""),
                    "email_instructions": directives.get("email_instructions", ""),
                    "email_subject_instructions": directives.get("email_subject_instructions", ""),
                    "directives_loaded": True
                }
                print(f"[SANDBOX] Directives chargées pour session {session_id}: SMS={len(directives.get('sms_instructions', ''))} chars, Email={len(directives.get('email_instructions', ''))} chars, Subject={len(directives.get('email_subject_instructions', ''))} chars")
        except Exception as e:
            print(f"[SANDBOX] Erreur chargement directives: {e}")
        
        # 📜 RÉCUPÉRER L'HISTORIQUE DE LA CONVERSATION
        conversation_history = get_conversation_history_internal(session_id, db)
        print(f"[SANDBOX DEBUG] Historique récupéré: {len(conversation_history)} messages")
        for i, msg in enumerate(conversation_history):
            print(f"[SANDBOX DEBUG] Message {i+1}: direction={msg.get('direction')}, content={msg.get('content', '')[:50]}...")
        
        # Préparer les données du lead
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
            # Premier message automatique avec directives API
            print(f"[SANDBOX] Génération premier message pour {lead.first_name}")
            message_data = messaging_agent._generate_message(lead_data, "auto_intro", "sandbox_campaign", request.platform)
            
            if message_data:
                print(f"[SANDBOX DEBUG] Message data reçu: {message_data}")
                print(f"[SANDBOX DEBUG] Type: {type(message_data)}")
                
                if request.platform == "sms":
                    ai_response = message_data.get("content", "")
                    ai_subject = None
                    ai_content = ai_response
                else:  # email
                    ai_subject = message_data.get("subject", "")
                    ai_content = message_data.get("content", "")
                    print(f"[SANDBOX DEBUG] Objet extrait: '{ai_subject}'")
                    print(f"[SANDBOX DEBUG] Contenu extrait: '{ai_content}'")
                    # Pour compatibilité, garder aussi ai_response avec le format ancien
                    ai_response = f"Sujet: {ai_subject}\n\n{ai_content}"
            else:
                ai_response = f"Bonjour {lead.first_name}, j'ai découvert votre entreprise {lead.company} et je pense que nous pourrions vous aider. Seriez-vous disponible pour en discuter ?"
                ai_subject = None
                ai_content = ai_response
        else:
            # Réponse contextuelle avec historique
            print(f"[SANDBOX] Génération réponse contextuelle avec historique ({len(conversation_history)} messages)")
            
            input_data = {
                "lead_data": lead_data,
                "message": request.user_message,
                "channel": request.platform,
                "campaign_id": "sandbox_test",
                "subject": f"Re: Discussion avec {lead.company}",
                "conversation_history": conversation_history  # 🔥 HISTORIQUE TRANSMIS
            }
            
            # Intégrer les directives
            if hasattr(messaging_agent, 'persona_config') and messaging_agent.persona_config.get('directives_loaded'):
                if request.platform == "sms":
                    input_data["custom_instructions"] = messaging_agent.persona_config.get('sms_instructions', '')
                else:
                    input_data["custom_instructions"] = messaging_agent.persona_config.get('email_instructions', '')
                print(f"[SANDBOX] Instructions {request.platform} intégrées avec historique")
            
            ai_response = messaging_agent.generate_contextual_response(input_data)
            
            # Pour les réponses contextuelles, extraire subject/content si c'est un email
            if request.platform == "email" and isinstance(ai_response, dict):
                ai_subject = ai_response.get("subject", "")
                ai_content = ai_response.get("content", "")
                # Format ancien pour compatibilité
                ai_response = f"Sujet: {ai_subject}\n\n{ai_content}"
            else:
                ai_subject = None
                ai_content = ai_response if isinstance(ai_response, str) else str(ai_response)
                ai_response = ai_content
        
        print(f"[SANDBOX] Réponse générée: {ai_response[:100]}...")
        return ai_response, ai_subject, ai_content
        
    except Exception as e:
        print(f"[SANDBOX] Erreur génération IA: {e}")
        fallback_response = f"Bonjour {lead.first_name}, merci pour votre message. Je prends note et reviendrai vers vous."
        return fallback_response, None, fallback_response

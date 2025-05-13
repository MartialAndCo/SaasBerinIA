from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from app.database.base import get_db
from app.models.messenger import MessengerDirectives
from app.schemas.messenger import MessengerDirectivesSchema

router = APIRouter(prefix="/api/messenger", tags=["messenger"])

@router.get("/directives", response_model=MessengerDirectivesSchema)
def get_messenger_directives(db: Session = Depends(get_db)):
    """
    Récupère les directives actuelles du Messenger Agent
    """
    directives = db.query(MessengerDirectives).first()
    
    if not directives:
        # Créer des directives par défaut si aucune n'existe
        default_directives = MessengerDirectives(
            sms_instructions="Instructions générales pour les SMS",
            email_instructions="Instructions générales pour les emails"
        )
        db.add(default_directives)
        db.commit()
        db.refresh(default_directives)
        return default_directives

    return directives

@router.post("/directives", response_model=MessengerDirectivesSchema)
def update_messenger_directives(
    directives_data: Dict[str, str], 
    db: Session = Depends(get_db)
):
    """
    Met à jour les directives du Messenger Agent
    """
    existing_directives = db.query(MessengerDirectives).first()

    if not existing_directives:
        # Créer de nouvelles directives si aucune n'existe
        new_directives = MessengerDirectives(
            sms_instructions=directives_data.get('sms_instructions', ''),
            email_instructions=directives_data.get('email_instructions', '')
        )
        db.add(new_directives)
    else:
        # Mettre à jour les directives existantes
        existing_directives.sms_instructions = directives_data.get('sms_instructions', existing_directives.sms_instructions)
        existing_directives.email_instructions = directives_data.get('email_instructions', existing_directives.email_instructions)

    db.commit()
    db.refresh(existing_directives or new_directives)
    
    return existing_directives or new_directives

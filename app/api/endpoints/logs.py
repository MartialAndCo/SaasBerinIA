from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/recent", response_model=List[schemas.RecentActivity])
def get_recent_logs(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les logs d'activité récents
    """
    # Récupérer les logs récents
    logs = crud.log.get_recent(db, limit=limit)
    
    # Formater les logs pour le frontend
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "type": log.type,
            "action": log.action,
            "description": log.description,
            "timestamp": log.timestamp.strftime("%d/%m/%Y %H:%M")
        })
    
    return result 
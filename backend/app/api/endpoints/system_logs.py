from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import math

from app.api import deps
from app.crud.system_log import system_log
from app.schemas.system_log import (
    SystemLog, 
    SystemLogCreate, 
    SystemLogResponse, 
    SystemLogStats
)

router = APIRouter()

@router.get("/", response_model=SystemLogResponse)
def get_system_logs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    module: Optional[str] = Query(None, description="Filter by module"),
    context_id: Optional[str] = Query(None, description="Filter by context ID"),
    search: Optional[str] = Query(None, description="Search in messages"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    db: Session = Depends(deps.get_db)
):
    """
    Récupérer les logs système avec pagination et filtres
    """
    # Calcul de l'offset
    skip = (page - 1) * per_page
    
    # Récupération des logs
    logs = system_log.get_multi(
        db=db,
        skip=skip,
        limit=per_page,
        level=level,
        source=source,
        agent_name=agent_name,
        module=module,
        context_id=context_id,
        search=search,
        start_date=start_date,
        end_date=end_date
    )
    
    # Comptage total
    total = system_log.count(
        db=db,
        level=level,
        source=source,
        agent_name=agent_name,
        module=module,
        context_id=context_id,
        search=search,
        start_date=start_date,
        end_date=end_date
    )
    
    # Calcul du nombre total de pages
    total_pages = math.ceil(total / per_page)
    
    return SystemLogResponse(
        logs=logs,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.post("/", response_model=SystemLog)
def create_system_log(
    log_in: SystemLogCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Créer un nouveau log système
    """
    return system_log.create(db=db, obj_in=log_in)

@router.get("/stats", response_model=SystemLogStats)
def get_system_logs_stats(db: Session = Depends(deps.get_db)):
    """
    Obtenir les statistiques des logs système
    """
    stats = system_log.get_stats(db=db)
    return SystemLogStats(**stats)

@router.get("/errors", response_model=List[SystemLog])
def get_recent_errors(
    limit: int = Query(50, ge=1, le=200, description="Number of errors to retrieve"),
    db: Session = Depends(deps.get_db)
):
    """
    Récupérer les erreurs récentes
    """
    return system_log.get_recent_errors(db=db, limit=limit)

@router.get("/agents/{agent_name}", response_model=List[SystemLog])
def get_agent_logs(
    agent_name: str,
    limit: int = Query(100, ge=1, le=500, description="Number of logs to retrieve"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    db: Session = Depends(deps.get_db)
):
    """
    Récupérer les logs d'un agent spécifique
    """
    return system_log.get_agent_logs(
        db=db, 
        agent_name=agent_name, 
        limit=limit, 
        level=level
    )

@router.delete("/cleanup")
def cleanup_old_logs(
    days_to_keep: int = Query(30, ge=1, le=365, description="Number of days to keep"),
    db: Session = Depends(deps.get_db)
):
    """
    Nettoyer les anciens logs (supprimer les logs plus anciens que X jours)
    """
    deleted_count = system_log.delete_old_logs(db=db, days_to_keep=days_to_keep)
    
    return {
        "message": f"Nettoyage terminé",
        "deleted_logs": deleted_count,
        "days_kept": days_to_keep
    }

@router.get("/levels")
def get_available_levels(db: Session = Depends(deps.get_db)):
    """
    Obtenir la liste des niveaux de logs disponibles
    """
    from sqlalchemy import distinct
    from app.models.system_log import SystemLog
    
    levels = db.query(distinct(SystemLog.level)).all()
    return {"levels": [level[0] for level in levels]}

@router.get("/sources")
def get_available_sources(db: Session = Depends(deps.get_db)):
    """
    Obtenir la liste des sources disponibles
    """
    from sqlalchemy import distinct
    from app.models.system_log import SystemLog
    
    sources = db.query(distinct(SystemLog.source)).all()
    return {"sources": [source[0] for source in sources]}

@router.get("/agents")
def get_available_agents(db: Session = Depends(deps.get_db)):
    """
    Obtenir la liste des agents qui ont des logs
    """
    from sqlalchemy import distinct
    from app.models.system_log import SystemLog
    
    agents = db.query(distinct(SystemLog.agent_name)).filter(
        SystemLog.agent_name.isnot(None)
    ).all()
    return {"agents": [agent[0] for agent in agents]}

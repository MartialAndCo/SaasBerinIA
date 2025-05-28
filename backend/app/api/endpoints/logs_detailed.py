from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import List, Optional
from datetime import datetime, timedelta
from app.api import deps
from app.models.log import Log
from app.models.agent_log import AgentLog
from app.models.agent import Agent

router = APIRouter()

@router.get("/system")
def get_system_logs(
    limit: int = Query(50, ge=1, le=200),
    level: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """Récupère les logs système de la table logs"""
    
    query = db.query(Log)
    
    # Filtrer par niveau si spécifié
    if level and level != "all":
        query = query.filter(Log.level == level)
    
    # Récupérer les logs les plus récents
    logs = query.order_by(desc(Log.timestamp)).limit(limit).all()
    
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.utcnow().isoformat(),
            "level": log.level,
            "source": "system",
            "module": log.module,
            "message": log.message,
            "details": log.details
        })
    
    return result

@router.get("/agents")
def get_agent_logs(
    limit: int = Query(50, ge=1, le=200),
    agent_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """Récupère les logs des agents de la table agent_logs"""
    
    query = db.query(AgentLog, Agent).join(Agent, AgentLog.agent_id == Agent.id)
    
    # Filtrer par agent si spécifié
    if agent_id:
        query = query.filter(AgentLog.agent_id == agent_id)
    
    # Filtrer par statut si spécifié
    if status and status != "all":
        query = query.filter(AgentLog.status == status)
    
    # Récupérer les logs les plus récents
    logs = query.order_by(desc(AgentLog.timestamp)).limit(limit).all()
    
    result = []
    for agent_log, agent in logs:
        # Convertir status en level pour compatibilité frontend
        level = "error" if agent_log.status == "error" else "warning" if agent_log.status == "warning" else "success" if agent_log.status == "completed" else "info"
        
        result.append({
            "id": agent_log.id,
            "timestamp": agent_log.timestamp.isoformat() if agent_log.timestamp else datetime.utcnow().isoformat(),
            "level": level,
            "source": "agent",
            "agent_id": agent.id,
            "agent_name": agent.name,
            "action": agent_log.action,
            "status": agent_log.status,
            "message": agent_log.message or f"Action: {agent_log.action}",
            "details": agent_log.details
        })
    
    return result

@router.get("/errors")
def get_error_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db)
):
    """Récupère tous les logs d'erreur (système + agents)"""
    
    result = []
    
    # Logs système avec erreurs
    system_errors = db.query(Log).filter(Log.level == "error").order_by(desc(Log.timestamp)).limit(limit//2).all()
    
    for log in system_errors:
        result.append({
            "id": f"sys_{log.id}",
            "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.utcnow().isoformat(),
            "level": "error",
            "source": "system",
            "module": log.module,
            "message": log.message,
            "details": log.details
        })
    
    # Logs agents avec erreurs
    agent_errors = db.query(AgentLog, Agent).join(Agent, AgentLog.agent_id == Agent.id).filter(
        AgentLog.status == "error"
    ).order_by(desc(AgentLog.timestamp)).limit(limit//2).all()
    
    for agent_log, agent in agent_errors:
        result.append({
            "id": f"agent_{agent_log.id}",
            "timestamp": agent_log.timestamp.isoformat() if agent_log.timestamp else datetime.utcnow().isoformat(),
            "level": "error",
            "source": "agent",
            "agent_id": agent.id,
            "agent_name": agent.name,
            "action": agent_log.action,
            "message": agent_log.message or f"Erreur lors de l'action: {agent_log.action}",
            "details": agent_log.details
        })
    
    # Trier par timestamp décroissant
    result.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return result[:limit]

@router.get("/all")
def get_all_logs(
    limit: int = Query(100, ge=1, le=500),
    level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """Récupère tous les logs (système + agents) mélangés"""
    
    result = []
    
    # Récupérer les logs système
    system_query = db.query(Log)
    if level and level != "all" and level in ["info", "warning", "error"]:
        system_query = system_query.filter(Log.level == level)
    
    if not source or source == "all" or source == "system":
        system_logs = system_query.order_by(desc(Log.timestamp)).limit(limit//2).all()
        
        for log in system_logs:
            result.append({
                "id": f"sys_{log.id}",
                "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.utcnow().isoformat(),
                "level": log.level,
                "source": "system",
                "module": log.module,
                "message": log.message,
                "details": log.details
            })
    
    # Récupérer les logs agents
    if not source or source == "all" or source == "agent":
        agent_query = db.query(AgentLog, Agent).join(Agent, AgentLog.agent_id == Agent.id)
        
        if level and level != "all":
            if level == "error":
                agent_query = agent_query.filter(AgentLog.status == "error")
            elif level == "warning":
                agent_query = agent_query.filter(AgentLog.status == "warning")
            elif level == "info":
                agent_query = agent_query.filter(AgentLog.status.in_(["info", "running", "waiting"]))
            # Pour "success", on cherche "completed"
            elif level == "success":
                agent_query = agent_query.filter(AgentLog.status == "completed")
        
        agent_logs = agent_query.order_by(desc(AgentLog.timestamp)).limit(limit//2).all()
        
        for agent_log, agent in agent_logs:
            # Convertir status en level pour compatibilité frontend
            level_converted = "error" if agent_log.status == "error" else "warning" if agent_log.status == "warning" else "success" if agent_log.status == "completed" else "info"
            
            result.append({
                "id": f"agent_{agent_log.id}",
                "timestamp": agent_log.timestamp.isoformat() if agent_log.timestamp else datetime.utcnow().isoformat(),
                "level": level_converted,
                "source": "agent",
                "agent_id": agent.id,
                "agent_name": agent.name,
                "action": agent_log.action,
                "status": agent_log.status,
                "message": agent_log.message or f"Action: {agent_log.action}",
                "details": agent_log.details
            })
    
    # Trier par timestamp décroissant
    result.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return result[:limit]

@router.get("/stats")
def get_logs_stats(db: Session = Depends(deps.get_db)):
    """Récupère les statistiques des logs"""
    
    # Stats système
    total_system_logs = db.query(Log).count()
    system_errors = db.query(Log).filter(Log.level == "error").count()
    system_warnings = db.query(Log).filter(Log.level == "warning").count()
    
    # Stats agents
    total_agent_logs = db.query(AgentLog).count()
    agent_errors = db.query(AgentLog).filter(AgentLog.status == "error").count()
    agent_warnings = db.query(AgentLog).filter(AgentLog.status == "warning").count()
    
    # Logs récents (dernière heure)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_system = db.query(Log).filter(Log.timestamp >= one_hour_ago).count() if total_system_logs > 0 else 0
    recent_agents = db.query(AgentLog).filter(AgentLog.timestamp >= one_hour_ago).count() if total_agent_logs > 0 else 0
    
    return {
        "system": {
            "total": total_system_logs,
            "errors": system_errors,
            "warnings": system_warnings,
            "recent_hour": recent_system
        },
        "agents": {
            "total": total_agent_logs,
            "errors": agent_errors,
            "warnings": agent_warnings,
            "recent_hour": recent_agents
        },
        "totals": {
            "all_logs": total_system_logs + total_agent_logs,
            "all_errors": system_errors + agent_errors,
            "all_warnings": system_warnings + agent_warnings,
            "recent_hour": recent_system + recent_agents
        }
    }

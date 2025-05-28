from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.api import deps
from app.models.agent import Agent
from app.models.agent_log import AgentLog

router = APIRouter()

@router.get("/detailed")
def get_agents_detailed(db: Session = Depends(deps.get_db)):
    """Récupère les détails complets des agents avec leurs vraies métriques"""
    
    agents = db.query(Agent).all()
    
    result = []
    for agent in agents:
        # Calculer les vraies métriques pour chaque agent
        last_log = db.query(AgentLog).filter(
            AgentLog.agent_id == agent.id
        ).order_by(AgentLog.timestamp.desc()).first()
        
        # Compter les leads traités par cet agent (si applicable)
        leads_count = 0  # À adapter selon votre logique métier
        
        # Calculer le dernier run
        last_run = None
        if last_log:
            time_diff = datetime.utcnow() - last_log.timestamp
            if time_diff.total_seconds() < 60:
                last_run = f"Il y a {int(time_diff.total_seconds())} secondes"
            elif time_diff.total_seconds() < 3600:
                last_run = f"Il y a {int(time_diff.total_seconds() / 60)} minutes"
            else:
                last_run = f"Il y a {int(time_diff.total_seconds() / 3600)} heures"
        else:
            last_run = "Jamais exécuté"
        
        result.append({
            "name": agent.name,
            "status": agent.status,  # active, warning, error
            "lastRun": last_run,
            "leads": leads_count if leads_count > 0 else None,
            "type": agent.type if hasattr(agent, 'type') else "worker",
            "id": agent.id
        })
    
    return result

@router.get("/activity")
def get_agents_activity(db: Session = Depends(deps.get_db)):
    """Récupère l'activité récente des agents pour les notifications"""
    
    # Récupérer les logs récents des agents
    recent_logs = db.query(AgentLog).filter(
        AgentLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).order_by(AgentLog.timestamp.desc()).limit(10).all()
    
    notifications = []
    for log in recent_logs:
        agent = db.query(Agent).filter(Agent.id == log.agent_id).first()
        if agent:
            if log.status == "error":
                notifications.append({
                    "type": "error",
                    "title": f"{agent.name} en erreur",
                    "description": f"L'agent {agent.name} a rencontré une erreur. Détails: {log.operation}",
                    "timestamp": log.timestamp.isoformat(),
                    "agent_id": agent.id
                })
            elif log.status == "warning":
                notifications.append({
                    "type": "warning", 
                    "title": f"{agent.name}: Avertissement",
                    "description": f"L'agent {agent.name} signale: {log.operation}",
                    "timestamp": log.timestamp.isoformat(),
                    "agent_id": agent.id
                })
    
    return notifications

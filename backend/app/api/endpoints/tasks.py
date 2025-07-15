"""
API Endpoints pour la gestion des tâches planifiées BerinIA - VERSION DATABASE
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import os
import logging
import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Task, Log

router = APIRouter()
logger = logging.getLogger(__name__)

class TaskCreate(BaseModel):
    action: str
    agent_id: Optional[int] = 1
    parameters: Optional[Dict[str, Any]] = {}
    priority: Optional[int] = 3
    scheduled_time: Optional[str] = None
    is_recurring: Optional[bool] = False
    recurrence_interval: Optional[int] = None

class TaskUpdate(BaseModel):
    action: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    scheduled_time: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_interval: Optional[int] = None

class TaskResponse(BaseModel):
    id: int
    agent_id: int
    action: str
    parameters: Dict[str, Any]
    status: str
    priority: int
    scheduled_time: str
    execution_time: Optional[str]
    is_recurring: bool
    recurrence_interval: Optional[int]
    last_run: Optional[str]
    result: Optional[Dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]

class TaskStats(BaseModel):
    total_tasks: int
    active_tasks: int
    completed_today: int
    next_execution: Optional[str]
    security_analysis: Dict[str, Any]

# ROUTES SPÉCIFIQUES D'ABORD (avant les routes avec paramètres)

@router.get("/tasks/stats", response_model=TaskStats)
async def get_tasks_stats_simple(db: Session = Depends(get_db)):
    """Récupère les statistiques des tâches (endpoint simplifié pour le frontend)"""
    try:
        # Calculs statistiques depuis la base
        total_tasks = db.query(Task).count()
        pending_tasks = db.query(Task).filter(Task.status == "pending").count()
        completed_tasks = db.query(Task).filter(Task.status == "completed").count()
        failed_tasks = db.query(Task).filter(Task.status == "failed").count()
        
        # Prochaine exécution
        next_task = db.query(Task).filter(
            Task.status == "pending",
            Task.scheduled_time > datetime.datetime.now()
        ).order_by(Task.scheduled_time.asc()).first()
        
        next_execution = next_task.scheduled_time.isoformat() if next_task else None
        
        # Calcul des vraies statistiques de sécurité depuis les logs
        try:
            threats_blocked = db.query(Log).filter(
                Log.module == 'TaskWatchdog',
                Log.level == 'WARNING'
            ).count()
            
            security_alerts = db.query(Log).filter(
                Log.level == 'ERROR'
            ).count()
            
            suspicious_activities = db.query(Log).filter(
                Log.level == 'WARNING'
            ).count()
        except Exception as log_error:
            logger.warning(f'Erreur lors du calcul des stats de sécurité: {log_error}')
            threats_blocked = 0
            security_alerts = 0
            suspicious_activities = 0
        
        return TaskStats(
            total_tasks=total_tasks,
            active_tasks=pending_tasks,
            completed_today=completed_tasks,
            next_execution=next_execution,
            security_analysis={
                "total_analyses": security_alerts,
                "threats_blocked": threats_blocked,
                "false_positives": 0,
                "last_analysis": None,
                "patterns_learned": suspicious_activities
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des statistiques"
        )

@router.get("/tasks/stats/overview", response_model=TaskStats)
async def get_tasks_stats_detailed(db: Session = Depends(get_db)):
    """Récupère les statistiques des tâches (endpoint détaillé)"""
    return await get_tasks_stats_simple(db)

@router.post("/tasks/{task_id}/execute", response_model=Dict[str, str])
async def execute_task_now(task_id: int, db: Session = Depends(get_db)):
    """Exécute immédiatement une tâche spécifique"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche {task_id} non trouvée"
            )
        
        # Marquer comme en cours d'exécution
        task.status = "running"
        task.execution_time = datetime.datetime.now()
        task.updated_at = datetime.datetime.now()
        db.commit()
        
        # TODO: Implémenter l'exécution réelle via le scheduler
        # Pour l'instant, simulation
        
        return {
            "status": "success", 
            "message": f"Exécution de la tâche {task_id} démarrée"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur exécution tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'exécution de la tâche"
        )

# ROUTES GÉNÉRALES

@router.get("/tasks")
async def get_tasks(db: Session = Depends(get_db)):
    """Récupère toutes les tâches planifiées depuis la base de données (format frontend)"""
    try:
        tasks = db.query(Task).all()
        
        # Mapping des IDs agents vers les noms
        agent_names = {
            1: "MessagingAgent",
            2: "ProspectionSupervisor", 
            3: "PivotStrategyAgent",
            4: "TaskWatchdogAgent"
        }
        
        result = []
        for task in tasks:
            # Créer un nom de tâche basé sur l'action
            task_name = f"{task.action}_{task.id}" if task.action else f"task_{task.id}"
            
            # Convertir la récurrence en format lisible
            if task.is_recurring and task.recurrence_interval:
                if task.recurrence_interval == 3600:
                    schedule = "Toutes les heures"
                elif task.recurrence_interval == 86400:
                    schedule = "Quotidien"
                elif task.recurrence_interval == 604800:
                    schedule = "Hebdomadaire"
                else:
                    schedule = f"Toutes les {task.recurrence_interval}s"
            else:
                schedule = "Une fois"
            
            result.append({
                "task_id": str(task.id),
                "name": task_name,
                "schedule": schedule,
                "agent": agent_names.get(task.agent_id, f"Agent_{task.agent_id}"),
                "params": task.parameters or {},
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.scheduled_time.isoformat() if task.scheduled_time else "",
                "status": task.status or "pending",
                "priority": task.priority or 3
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur récupération tâches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des tâches"
        )

@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle tâche planifiée"""
    try:
        # Créer la tâche en base
        new_task = Task(
            agent_id=task_data.agent_id,
            action=task_data.action,
            parameters=task_data.parameters,
            status="pending",
            priority=task_data.priority,
            scheduled_time=datetime.datetime.fromisoformat(task_data.scheduled_time) if task_data.scheduled_time else datetime.datetime.now(),
            is_recurring=task_data.is_recurring,
            recurrence_interval=task_data.recurrence_interval,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        return {
            "status": "success",
            "message": "Tâche créée avec succès",
            "task_id": new_task.id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur création tâche: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la tâche: {str(e)}"
        )

# ROUTES AVEC PARAMÈTRES (À LA FIN)

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Récupère une tâche spécifique par son ID"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche {task_id} non trouvée"
            )
        
        return TaskResponse(
            id=task.id,
            agent_id=task.agent_id or 1,
            action=task.action,
            parameters=task.parameters or {},
            status=task.status or "pending",
            priority=task.priority or 3,
            scheduled_time=task.scheduled_time.isoformat() if task.scheduled_time else "",
            execution_time=task.execution_time.isoformat() if task.execution_time else None,
            is_recurring=task.is_recurring or False,
            recurrence_interval=task.recurrence_interval,
            last_run=task.last_run.isoformat() if task.last_run else None,
            result=task.result or {},
            created_at=task.created_at.isoformat() if task.created_at else None,
            updated_at=task.updated_at.isoformat() if task.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de la tâche"
        )

@router.put("/tasks/{task_id}", response_model=Dict[str, str])
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Met à jour une tâche existante"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche {task_id} non trouvée"
            )
        
        # Mise à jour des champs fournis
        if task_update.action is not None:
            task.action = task_update.action
        if task_update.status is not None:
            task.status = task_update.status
        if task_update.priority is not None:
            task.priority = task_update.priority
        if task_update.scheduled_time is not None:
            task.scheduled_time = datetime.datetime.fromisoformat(task_update.scheduled_time)
        if task_update.is_recurring is not None:
            task.is_recurring = task_update.is_recurring
        if task_update.recurrence_interval is not None:
            task.recurrence_interval = task_update.recurrence_interval
        
        task.updated_at = datetime.datetime.now()
        
        db.commit()
        
        return {"status": "success", "message": "Tâche mise à jour avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur mise à jour tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de la tâche"
        )

@router.delete("/tasks/{task_id}", response_model=Dict[str, str])
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Supprime une tâche planifiée"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche {task_id} non trouvée"
            )
        
        db.delete(task)
        db.commit()
        
        return {"status": "success", "message": "Tâche supprimée avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur suppression tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de la tâche"
        )

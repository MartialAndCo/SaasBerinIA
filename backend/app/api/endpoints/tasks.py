"""
API Endpoints pour la gestion des tâches planifiées BerinIA
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import os
import logging
import datetime
from pathlib import Path

router = APIRouter()
logger = logging.getLogger(__name__)

# Chemin vers le fichier de tâches
TASKS_FILE = "/root/berinia/infra-ia/data/tasks.json"

class TaskCreate(BaseModel):
    name: str
    schedule: str  # 'daily', 'weekly', 'hourly', ou datetime ISO
    agent: str
    params: Optional[Dict[str, Any]] = {}

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    schedule: Optional[str] = None
    agent: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    task_id: str
    name: str
    schedule: str
    agent: str
    params: Dict[str, Any]
    last_run: Optional[str]
    next_run: Optional[str]

class TaskStats(BaseModel):
    total_tasks: int
    active_tasks: int
    completed_today: int
    next_execution: Optional[str]
    security_analysis: Dict[str, Any]

def load_tasks() -> List[Dict[str, Any]]:
    """Charge les tâches depuis le fichier JSON"""
    try:
        if not os.path.exists(TASKS_FILE):
            return []
        
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur chargement tâches: {e}")
        return []

def save_tasks(tasks: List[Dict[str, Any]]) -> bool:
    """Sauvegarde les tâches dans le fichier JSON"""
    try:
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
        
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erreur sauvegarde tâches: {e}")
        return False

def call_scheduler_api(action: str, task_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Appelle l'API du scheduler pour les opérations en temps réel"""
    try:
        # Import du scheduler pour interaction directe
        import sys
        sys.path.append('/root/berinia/infra-ia')
        from scheduler import TaskScheduler
        
        scheduler = TaskScheduler()
        
        if action == "add_task":
            return scheduler.add_task(
                name=task_data["name"],
                schedule=task_data["schedule"],
                agent=task_data["agent"],
                params=task_data.get("params", {}),
                requesting_agent="admin_api"
            )
        elif action == "remove_task":
            return {"status": "success" if scheduler.remove_task(task_data["task_id"]) else "error"}
        else:
            return {"status": "error", "message": f"Action non supportée: {action}"}
            
    except Exception as e:
        logger.error(f"Erreur appel scheduler: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks():
    """Récupère toutes les tâches planifiées"""
    try:
        tasks = load_tasks()
        return [TaskResponse(**task) for task in tasks]
    except Exception as e:
        logger.error(f"Erreur récupération tâches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des tâches"
        )

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Récupère une tâche spécifique par son ID"""
    try:
        tasks = load_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche {task_id} non trouvée"
            )
        
        return TaskResponse(**task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de la tâche"
        )

@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(task: TaskCreate):
    """Crée une nouvelle tâche planifiée"""
    try:
        # Validation des données
        valid_schedules = ["hourly", "daily", "weekly"]
        if task.schedule not in valid_schedules:
            # Vérifier si c'est une date ISO
            try:
                datetime.datetime.fromisoformat(task.schedule)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Schedule invalide. Utilisez: {', '.join(valid_schedules)} ou une date ISO"
                )
        
        # Appel du scheduler pour créer la tâche avec analyse de sécurité
        result = call_scheduler_api("add_task", {
            "name": task.name,
            "schedule": task.schedule,
            "agent": task.agent,
            "params": task.params
        })
        
        if result.get("status") == "blocked":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tâche bloquée par sécurité: {result.get('message', '')}"
            )
        elif result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur création tâche: {result.get('message', '')}"
            )
        
        return {
            "status": "success",
            "message": "Tâche créée avec succès",
            "task_id": result.get("task_id"),
            "security_analysis": result.get("analysis")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur création tâche: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création de la tâche"
        )

@router.put("/tasks/{task_id}", response_model=Dict[str, str])
async def update_task(task_id: str, task_update: TaskUpdate):
    """Met à jour une tâche existante"""
    try:
        tasks = load_tasks()
        task_index = next((i for i, t in enumerate(tasks) if t["task_id"] == task_id), None)
        
        if task_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche {task_id} non trouvée"
            )
        
        # Mise à jour des champs fournis
        task = tasks[task_index]
        if task_update.name is not None:
            task["name"] = task_update.name
        if task_update.schedule is not None:
            task["schedule"] = task_update.schedule
        if task_update.agent is not None:
            task["agent"] = task_update.agent
        if task_update.params is not None:
            task["params"] = task_update.params
        
        # Sauvegarde
        if not save_tasks(tasks):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la sauvegarde"
            )
        
        return {"status": "success", "message": "Tâche mise à jour avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur mise à jour tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de la tâche"
        )

@router.delete("/tasks/{task_id}", response_model=Dict[str, str])
async def delete_task(task_id: str):
    """Supprime une tâche planifiée"""
    try:
        # Appel du scheduler pour suppression avec validation
        result = call_scheduler_api("remove_task", {"task_id": task_id})
        
        if result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Impossible de supprimer la tâche {task_id}"
            )
        
        return {"status": "success", "message": "Tâche supprimée avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de la tâche"
        )

@router.get("/tasks/stats/overview", response_model=TaskStats)
async def get_tasks_stats():
    """Récupère les statistiques des tâches"""
    try:
        tasks = load_tasks()
        
        # Calculs statistiques
        total_tasks = len(tasks)
        active_tasks = len([t for t in tasks if t.get("next_run")])
        
        # Prochaine exécution
        next_runs = [t.get("next_run") for t in tasks if t.get("next_run")]
        next_execution = min(next_runs) if next_runs else None
        
        # Récupérer les stats de sécurité du TaskWatchdogAgent
        security_analysis = {}
        try:
            import sys
            sys.path.append('/root/berinia/infra-ia')
            from agents.task_watchdog.task_watchdog_agent import TaskWatchdogAgent
            
            watchdog = TaskWatchdogAgent()
            security_result = watchdog.run({"action": "get_stats"})
            if security_result.get("status") == "success":
                security_analysis = security_result.get("stats", {})
        except Exception as e:
            logger.warning(f"Impossible de récupérer les stats de sécurité: {e}")
            security_analysis = {"error": "Stats de sécurité indisponibles"}
        
        return TaskStats(
            total_tasks=total_tasks,
            active_tasks=active_tasks,
            completed_today=0,  # TODO: Calculer depuis les logs
            next_execution=next_execution,
            security_analysis=security_analysis
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des statistiques"
        )

@router.post("/tasks/{task_id}/execute", response_model=Dict[str, str])
async def execute_task_now(task_id: str):
    """Exécute immédiatement une tâche spécifique"""
    try:
        tasks = load_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche {task_id} non trouvée"
            )
        
        # TODO: Implémenter l'exécution immédiate via le scheduler
        # Pour l'instant, simulation
        
        return {
            "status": "success", 
            "message": f"Exécution de la tâche {task_id} programmée"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur exécution tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'exécution de la tâche"
        )

@router.get("/security/watchdog/report")
async def get_security_report():
    """Récupère le rapport de sécurité TaskWatchdogAgent"""
    try:
        import sys
        sys.path.append('/root/berinia/infra-ia')
        from agents.task_watchdog.task_watchdog_agent import TaskWatchdogAgent
        
        watchdog = TaskWatchdogAgent()
        report = watchdog.run({"action": "get_threat_report"})
        
        if report.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur génération rapport de sécurité"
            )
        
        return report
        
    except Exception as e:
        logger.error(f"Erreur rapport sécurité: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du rapport de sécurité"
        )

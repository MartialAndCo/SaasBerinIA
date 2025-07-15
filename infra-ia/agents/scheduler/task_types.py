"""
Types de tâches avancés pour AgentSchedulerAgent - Phase 2
Architecture générique permettant aux agents de décider du comportement des tâches
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time

class TaskType(Enum):
    """Types de tâches disponibles"""
    SYSTEM_RECURRING = "system_recurring"      # Tâches système permanentes
    BUSINESS_RECURRING = "business_recurring"  # Tâches business avec fin possible
    ONE_TIME = "one_time"                      # Exécution unique puis suppression
    CONDITIONAL = "conditional"                # Exécution conditionnelle

class TaskBehavior:
    """Classe définissant le comportement d'une tâche selon son type"""
    
    def __init__(self, task_type: TaskType, **kwargs):
        self.task_type = task_type
        self.auto_cleanup = kwargs.get("auto_cleanup", True)
        self.end_date = kwargs.get("end_date")  # timestamp ou None
        self.cleanup_after_days = kwargs.get("cleanup_after_days", 30)
        self.condition = kwargs.get("condition")  # Pour conditional tasks
        self.max_executions = kwargs.get("max_executions")  # Limite d'exécutions
        self.priority_decay = kwargs.get("priority_decay", False)  # Baisse priorité dans le temps
        
    def should_auto_cleanup(self, task_creation_time: float, last_execution: Optional[float] = None) -> bool:
        """Détermine si la tâche doit être nettoyée automatiquement"""
        now = time.time()
        
        # Tâches système : jamais de nettoyage automatique
        if self.task_type == TaskType.SYSTEM_RECURRING:
            return False
        
        # Vérifier end_date si définie
        if self.end_date and now > self.end_date:
            return True
        
        # Tâches one_time : nettoyer SEULEMENT après exécution
        if self.task_type == TaskType.ONE_TIME:
            if last_execution:  # A été exécutée
                return True
            else:  # Pas encore exécutée = NE PAS SUPPRIMER
                return False
        
        # Nettoyage basé sur l'âge SEULEMENT pour les autres types
        if self.auto_cleanup and self.cleanup_after_days:
            age_days = (now - task_creation_time) / (24 * 3600)
            if age_days > self.cleanup_after_days:
                return True
        
        return False
    
    def is_execution_allowed(self, execution_count: int = 0) -> bool:
        """Vérifie si l'exécution est autorisée"""
        # Vérifier limite d'exécutions
        if self.max_executions and execution_count >= self.max_executions:
            return False
        
        # Pour les tâches conditionnelles, vérifier la condition
        if self.task_type == TaskType.CONDITIONAL:
            return self._check_condition()
        
        return True
    
    def _check_condition(self) -> bool:
        """Vérifie la condition pour les tâches conditionnelles"""
        if not self.condition:
            return True
        
        # Ici on pourrait implémenter une logique plus complexe
        # Pour l'instant, on considère la condition comme toujours vraie
        # sauf si explicitement False
        return self.condition != False
    
    def calculate_next_execution(self, current_time: float, recurrence_interval: Optional[int]) -> Optional[float]:
        """Calcule la prochaine exécution selon le type de tâche"""
        if not recurrence_interval:
            return None
        
        # Tâches one_time : pas de prochaine exécution
        if self.task_type == TaskType.ONE_TIME:
            return None
        
        # Vérifier si pas dépassé end_date
        if self.end_date and current_time + recurrence_interval > self.end_date:
            return None
        
        return current_time + recurrence_interval
    
    def get_effective_priority(self, original_priority: int, creation_time: float) -> int:
        """Calcule la priorité effective (avec decay possible)"""
        if not self.priority_decay:
            return original_priority
        
        # Décroissance de priorité : +1 toutes les 24h pour les tâches anciennes
        age_days = (time.time() - creation_time) / (24 * 3600)
        if age_days > 7:  # Après 7 jours, commencer la décroissance
            decay = int((age_days - 7) / 1)  # +1 priorité par jour après 7 jours
            return min(original_priority + decay, 10)  # Max priorité 10
        
        return original_priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le comportement en dictionnaire"""
        return {
            "task_type": self.task_type.value,
            "auto_cleanup": self.auto_cleanup,
            "end_date": self.end_date,
            "cleanup_after_days": self.cleanup_after_days,
            "condition": self.condition,
            "max_executions": self.max_executions,
            "priority_decay": self.priority_decay
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskBehavior':
        """Désérialise le comportement depuis un dictionnaire"""
        task_type = TaskType(data.get("task_type", TaskType.ONE_TIME.value))
        return cls(
            task_type=task_type,
            auto_cleanup=data.get("auto_cleanup", True),
            end_date=data.get("end_date"),
            cleanup_after_days=data.get("cleanup_after_days", 30),
            condition=data.get("condition"),
            max_executions=data.get("max_executions"),
            priority_decay=data.get("priority_decay", False)
        )

class TaskFactory:
    """Factory pour créer des tâches avec le bon comportement selon le type"""
    
    @staticmethod
    def create_system_recurring(**kwargs) -> TaskBehavior:
        """Crée une tâche système récurrente (permanente)"""
        # Filtrer les kwargs pour éviter les conflits
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['task_type', 'auto_cleanup', 'cleanup_after_days', 'priority_decay']}
        return TaskBehavior(
            task_type=TaskType.SYSTEM_RECURRING,
            auto_cleanup=False,  # Jamais de nettoyage automatique
            cleanup_after_days=None,
            priority_decay=False,
            **filtered_kwargs
        )
    
    @staticmethod
    def create_business_recurring(**kwargs) -> TaskBehavior:
        """Crée une tâche business récurrente (temporaire)"""
        # Extraire les paramètres spécifiques
        auto_cleanup = kwargs.get("auto_cleanup", True)
        cleanup_after_days = kwargs.get("cleanup_after_days", 30)
        priority_decay = kwargs.get("priority_decay", True)
        
        # Filtrer les kwargs pour éviter les conflits
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['task_type', 'auto_cleanup', 'cleanup_after_days', 'priority_decay']}
        
        return TaskBehavior(
            task_type=TaskType.BUSINESS_RECURRING,
            auto_cleanup=auto_cleanup,
            cleanup_after_days=cleanup_after_days,
            priority_decay=priority_decay,
            **filtered_kwargs
        )
    
    @staticmethod
    def create_one_time(**kwargs) -> TaskBehavior:
        """Crée une tâche ponctuelle"""
        # Filtrer les kwargs pour éviter les conflits
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['task_type', 'auto_cleanup', 'cleanup_after_days', 'max_executions']}
        
        return TaskBehavior(
            task_type=TaskType.ONE_TIME,
            auto_cleanup=True,  # Toujours nettoyer après exécution
            cleanup_after_days=1,  # Nettoyage rapide
            max_executions=1,  # Une seule exécution
            **filtered_kwargs
        )
    
    @staticmethod
    def create_conditional(**kwargs) -> TaskBehavior:
        """Crée une tâche conditionnelle"""
        # Extraire les paramètres spécifiques
        auto_cleanup = kwargs.get("auto_cleanup", True)
        cleanup_after_days = kwargs.get("cleanup_after_days", 7)
        
        # Filtrer les kwargs pour éviter les conflits
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['task_type', 'auto_cleanup', 'cleanup_after_days']}
        
        return TaskBehavior(
            task_type=TaskType.CONDITIONAL,
            auto_cleanup=auto_cleanup,
            cleanup_after_days=cleanup_after_days,  # Nettoyage plus rapide
            **filtered_kwargs
        )
    
    @staticmethod
    def create_from_agent_request(agent_request: Dict[str, Any]) -> TaskBehavior:
        """Crée le comportement de tâche à partir d'une demande d'agent"""
        task_type_str = agent_request.get("task_type", "one_time")
        
        try:
            task_type = TaskType(task_type_str)
        except ValueError:
            # Type non reconnu, par défaut one_time
            task_type = TaskType.ONE_TIME
        
        # Factory selon le type
        if task_type == TaskType.SYSTEM_RECURRING:
            return TaskFactory.create_system_recurring(**agent_request)
        elif task_type == TaskType.BUSINESS_RECURRING:
            return TaskFactory.create_business_recurring(**agent_request)
        elif task_type == TaskType.ONE_TIME:
            return TaskFactory.create_one_time(**agent_request)
        elif task_type == TaskType.CONDITIONAL:
            return TaskFactory.create_conditional(**agent_request)
        else:
            return TaskFactory.create_one_time(**agent_request)

# Exemples d'utilisation pour la documentation
TASK_TYPE_EXAMPLES = {
    "system_recurring": {
        "description": "Tâche système permanente (jamais supprimée)",
        "example": {
            "task_type": "system_recurring",
            "auto_cleanup": False,
            "agent": "ProspectionSupervisor",
            "action": "daily_monitoring",
            "recurrence_interval": 86400
        }
    },
    "business_recurring": {
        "description": "Tâche business temporaire avec fin automatique",
        "example": {
            "task_type": "business_recurring",
            "auto_cleanup": True,
            "end_date": "2025-12-31T23:59:59",
            "cleanup_after_days": 30,
            "agent": "CampaignAgent",
            "action": "run_campaign",
            "recurrence_interval": 604800
        }
    },
    "one_time": {
        "description": "Tâche ponctuelle, supprimée après exécution",
        "example": {
            "task_type": "one_time",
            "auto_cleanup": True,
            "max_executions": 1,
            "agent": "MessagingAgent",
            "action": "send_urgent_email"
        }
    },
    "conditional": {
        "description": "Tâche conditionnelle, exécutée si condition remplie",
        "example": {
            "task_type": "conditional",
            "condition": "no_response_after_48h",
            "auto_cleanup": True,
            "cleanup_after_days": 7,
            "agent": "FollowUpAgent",
            "action": "send_reminder"
        }
    }
}

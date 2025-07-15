"""
Méthodes avancées pour AgentSchedulerAgent - Phase 2
Support des 4 types de tâches et système de turnover automatique
"""

import time
import datetime
import heapq
from typing import Dict, Any

from .task_types import TaskType, TaskBehavior, TaskFactory, TASK_TYPE_EXAMPLES

class AdvancedSchedulerMethods:
    """Mixin contenant les méthodes avancées pour AgentSchedulerAgent"""
    
    def schedule_advanced_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        NOUVEAU : Planifie une tâche avec les types avancés
        
        Args:
            input_data: Données contenant task_type et autres paramètres
            
        Returns:
            Résultat de la planification avancée
        """
        try:
            # Extraction des paramètres
            task_type = input_data.get("task_type", "one_time")
            task_data = input_data.get("task_data", {})
            execution_time = input_data.get("execution_time")
            priority = input_data.get("priority", 1)
            task_id = input_data.get("task_id")
            
            # Conversion du moment d'exécution
            if isinstance(execution_time, datetime.datetime):
                timestamp = execution_time.timestamp()
            elif isinstance(execution_time, str):
                timestamp = datetime.datetime.fromisoformat(execution_time).timestamp()
            else:
                timestamp = float(execution_time)
            
            # Génération d'un ID unique si non fourni
            if task_id is None:
                task_id = f"{task_type}_{int(time.time())}_{self.stats['total_tasks_scheduled']}"
            
            # Création du comportement de tâche selon le type
            task_behavior = TaskFactory.create_from_agent_request(input_data)
            
            # Détermination de la récurrence selon le type
            recurring = task_behavior.task_type in [TaskType.SYSTEM_RECURRING, TaskType.BUSINESS_RECURRING]
            recurrence_interval = input_data.get("recurrence_interval")
            
            # Analyse de sécurité
            security_analysis = self._analyze_task_security(
                task_id=task_id,
                task_data=task_data,
                execution_time=datetime.datetime.fromtimestamp(timestamp).isoformat(),
                recurring=recurring,
                recurrence_interval=recurrence_interval
            )
            
            # Vérification sécurité
            if security_analysis.get("threat_level") == "CRITICAL":
                error_message = f"Tâche {task_id} bloquée par TaskWatchdogAgent: {security_analysis.get('reason', 'Menace critique')}"
                self.speak(error_message, target="OverseerAgent")
                return {
                    "status": "blocked",
                    "message": error_message,
                    "security_analysis": security_analysis
                }
            
            # Calcul de la priorité effective
            effective_priority = task_behavior.get_effective_priority(priority, timestamp)
            
            # Création de la tâche avancée
            from .agent_scheduler_agent import ScheduledTask
            task = ScheduledTask(
                timestamp=timestamp,
                priority=effective_priority,
                task_id=task_id,
                task_data=task_data,
                recurring=recurring,
                recurrence_interval=recurrence_interval,
                task_behavior=task_behavior
            )
            
            # Vérification d'autorisation d'exécution
            if not task_behavior.is_execution_allowed():
                return {
                    "status": "rejected",
                    "message": f"Exécution non autorisée pour le type {task_type}",
                    "task_id": task_id
                }
            
            # Ajout à la file
            with self.queue_lock:
                heapq.heappush(self.task_queue, task)
                self.tasks_by_id[task_id] = task
                self.stats["tasks_in_queue"] = len(self.task_queue)
                self.stats["total_tasks_scheduled"] += 1
            
            # Sauvegarde
            self._save_tasks()
            
            # Message de log
            exec_time_str = datetime.datetime.fromtimestamp(timestamp).isoformat()
            self.speak(
                f"Tâche avancée {task_id} ({task_type}) planifiée pour {exec_time_str}",
                target="OverseerAgent"
            )
            
            return {
                "status": "success",
                "message": f"Tâche {task_type} planifiée avec succès",
                "task_id": task_id,
                "task_type": task_type,
                "execution_time": exec_time_str,
                "security_analysis": security_analysis,
                "effective_priority": effective_priority,
                "behavior_info": task_behavior.to_dict()
            }
            
        except Exception as e:
            error_message = f"Erreur lors de la planification avancée: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def cleanup_expired_tasks(self) -> Dict[str, Any]:
        """
        NOUVEAU : Nettoie automatiquement les tâches expirées selon leur comportement
        
        Returns:
            Résultat du nettoyage
        """
        try:
            now = time.time()
            tasks_to_remove = []
            cleanup_count = 0
            
            with self.queue_lock:
                # Identifier les tâches à nettoyer
                for task_id, task in list(self.tasks_by_id.items()):
                    if task.task_behavior.should_auto_cleanup(task.creation_time, task.last_execution):
                        tasks_to_remove.append(task_id)
                        
                        # Marquer la tâche comme invalide
                        task.timestamp = 0
                        cleanup_count += 1
                
                # Supprimer les références
                for task_id in tasks_to_remove:
                    if task_id in self.tasks_by_id:
                        del self.tasks_by_id[task_id]
                
                # Reconstruire la file
                if tasks_to_remove:
                    self._rebuild_queue()
                    
                # Mise à jour statistiques
                self.stats["tasks_in_queue"] = len(self.task_queue)
            
            # Sauvegarde si des tâches ont été supprimées
            if cleanup_count > 0:
                self._save_tasks()
                self.speak(f"Nettoyage automatique: {cleanup_count} tâches expirées supprimées", target="OverseerAgent")
            
            return {
                "status": "success",
                "message": f"Nettoyage terminé: {cleanup_count} tâches supprimées",
                "cleaned_tasks": cleanup_count,
                "remaining_tasks": len(self.task_queue)
            }
            
        except Exception as e:
            error_message = f"Erreur lors du nettoyage des tâches: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def get_task_types_info(self) -> Dict[str, Any]:
        """
        NOUVEAU : Retourne les informations sur les types de tâches disponibles
        
        Returns:
            Informations détaillées sur les types de tâches
        """
        try:
            # Statistiques par type de tâche
            type_stats = {}
            
            with self.queue_lock:
                for task in self.task_queue:
                    if task.timestamp > 0:  # Tâche valide
                        task_type = task.task_behavior.task_type.value
                        if task_type not in type_stats:
                            type_stats[task_type] = 0
                        type_stats[task_type] += 1
            
            return {
                "status": "success",
                "available_types": {
                    "system_recurring": "Tâches système permanentes (jamais supprimées)",
                    "business_recurring": "Tâches business temporaires avec fin automatique", 
                    "one_time": "Tâches ponctuelles, supprimées après exécution",
                    "conditional": "Tâches conditionnelles, exécutées si condition remplie"
                },
                "current_distribution": type_stats,
                "examples": TASK_TYPE_EXAMPLES,
                "api_usage": {
                    "endpoint": "schedule_advanced_task",
                    "required_fields": ["task_type", "task_data", "execution_time"],
                    "optional_fields": ["priority", "task_id", "end_date", "cleanup_after_days", "max_executions"]
                }
            }
            
        except Exception as e:
            error_message = f"Erreur récupération infos types: {str(e)}"
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }

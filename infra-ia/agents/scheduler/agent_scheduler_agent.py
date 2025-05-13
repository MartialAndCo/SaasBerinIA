"""
Module de l'AgentSchedulerAgent - Planificateur des tâches du système BerinIA
"""
import os
import json
import time
import logging
import datetime
import threading
import queue
from typing import Dict, Any, Optional, List, Tuple, Union
import heapq
import sched
from pathlib import Path

from core.agent_base import Agent
from utils.llm import LLMService

class ScheduledTask:
    """
    Classe représentant une tâche planifiée avec sa priorité
    """
    def __init__(self, timestamp: float, priority: int, task_id: str, 
                 task_data: Dict[str, Any], recurring: bool = False, 
                 recurrence_interval: int = None):
        self.timestamp = timestamp
        self.priority = priority
        self.task_id = task_id
        self.task_data = task_data
        self.recurring = recurring
        self.recurrence_interval = recurrence_interval  # en secondes
    
    def __lt__(self, other):
        # Tri d'abord par timestamp, puis par priorité (plus petit = plus prioritaire)
        if self.timestamp == other.timestamp:
            return self.priority < other.priority
        return self.timestamp < other.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la tâche en dictionnaire pour la sérialisation"""
        return {
            "timestamp": self.timestamp,
            "priority": self.priority,
            "task_id": self.task_id,
            "task_data": self.task_data,
            "recurring": self.recurring,
            "recurrence_interval": self.recurrence_interval
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        """Crée une instance à partir d'un dictionnaire"""
        return cls(
            timestamp=data["timestamp"],
            priority=data["priority"],
            task_id=data["task_id"],
            task_data=data["task_data"],
            recurring=data.get("recurring", False),
            recurrence_interval=data.get("recurrence_interval")
        )

class AgentSchedulerAgent(Agent):
    """
    AgentSchedulerAgent - Agent responsable de la planification et de l'exécution des tâches
    
    Cet agent est responsable de:
    - Maintenir une file des tâches planifiées
    - Exécuter les tâches au moment prévu
    - Gérer les tâches récurrentes
    - Coordonner les actions dans le temps
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation de l'AgentSchedulerAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("AgentSchedulerAgent", config_path)
        
        # Logger dédié
        self.logger = logging.getLogger("BerinIA-Scheduler")
        
        # File de priorité des tâches (heap)
        self.task_queue = []
        
        # Dictionnaire des tâches par ID pour accès rapide
        self.tasks_by_id = {}
        
        # Verrou pour la synchronisation entre threads
        self.queue_lock = threading.Lock()
        
        # Chemin vers le fichier de sauvegarde des tâches
        self.tasks_file = Path(self.config.get("tasks_file", "data/scheduled_tasks.json"))
        
        # Scheduler pour la planification des tâches
        self.scheduler = sched.scheduler(time.time, time.sleep)
        
        # Thread pour l'exécution du scheduler en arrière-plan
        self.scheduler_thread = None
        self.running = False
        
        # Statistiques de l'agent
        self.stats = {
            "total_tasks_scheduled": 0,
            "total_tasks_executed": 0,
            "tasks_in_queue": 0,
            "last_execution": None
        }
        
        # Chargement des tâches existantes
        self._load_tasks()
    
    def _get_overseer_agent(self):
        """
        Récupère une instance de l'OverseerAgent
        
        Cette méthode peut être remplacée dans les tests
        
        Returns:
            Instance de l'OverseerAgent
        """
        # Importation dynamique pour éviter les dépendances circulaires
        from agents.overseer.overseer_agent import OverseerAgent
        return OverseerAgent()
    
    def _load_tasks(self) -> None:
        """Charge les tâches planifiées depuis le fichier de sauvegarde"""
        if not self.tasks_file.exists():
            # Création du répertoire parent si nécessaire
            if not self.tasks_file.parent.exists():
                self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
            return
        
        try:
            with open(self.tasks_file, "r") as f:
                tasks_data = json.load(f)
            
            with self.queue_lock:
                self.task_queue = []
                self.tasks_by_id = {}
                
                for task_data in tasks_data:
                    task = ScheduledTask.from_dict(task_data)
                    
                    # Ne pas charger les tâches déjà expirées
                    if task.timestamp > time.time():
                        heapq.heappush(self.task_queue, task)
                        self.tasks_by_id[task.task_id] = task
                
                self.stats["tasks_in_queue"] = len(self.task_queue)
                
                self.speak(f"Chargement de {len(self.task_queue)} tâches planifiées.", target="OverseerAgent")
        except Exception as e:
            error_message = f"Erreur lors du chargement des tâches: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
    
    def _save_tasks(self) -> None:
        """Sauvegarde les tâches planifiées dans le fichier"""
        try:
            with self.queue_lock:
                tasks_data = [task.to_dict() for task in self.task_queue]
            
            # Création du répertoire parent si nécessaire
            if not self.tasks_file.parent.exists():
                self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.tasks_file, "w") as f:
                json.dump(tasks_data, f, indent=2)
        except Exception as e:
            error_message = f"Erreur lors de la sauvegarde des tâches: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
    
    def schedule_task(self, task_data: Dict[str, Any], execution_time: Union[datetime.datetime, str, float], 
                      priority: int = 1, task_id: Optional[str] = None, 
                      recurring: bool = False, recurrence_interval: Optional[int] = None) -> Dict[str, Any]:
        """
        Planifie une tâche pour exécution à un moment donné
        
        Args:
            task_data: Les données de la tâche
            execution_time: Moment d'exécution (datetime, timestamp, ou chaîne ISO)
            priority: Priorité de la tâche (1 = haute, 5 = basse)
            task_id: Identifiant unique de la tâche (généré si non fourni)
            recurring: Si la tâche est récurrente
            recurrence_interval: Intervalle de récurrence en secondes
            
        Returns:
            Résultat de la planification
        """
        try:
            # Conversion du moment d'exécution en timestamp si nécessaire
            if isinstance(execution_time, datetime.datetime):
                timestamp = execution_time.timestamp()
            elif isinstance(execution_time, str):
                timestamp = datetime.datetime.fromisoformat(execution_time).timestamp()
            else:
                timestamp = float(execution_time)
            
            # Génération d'un ID unique si non fourni
            if task_id is None:
                task_id = f"task_{int(time.time())}_{self.stats['total_tasks_scheduled']}"
            
            # Création de la tâche
            task = ScheduledTask(
                timestamp=timestamp,
                priority=priority,
                task_id=task_id,
                task_data=task_data,
                recurring=recurring,
                recurrence_interval=recurrence_interval
            )
            
            # Ajout de la tâche à la file
            with self.queue_lock:
                heapq.heappush(self.task_queue, task)
                self.tasks_by_id[task_id] = task
                self.stats["tasks_in_queue"] = len(self.task_queue)
                self.stats["total_tasks_scheduled"] += 1
            
            # Sauvegarde des tâches
            self._save_tasks()
            
            # Message de log
            exec_time_str = datetime.datetime.fromtimestamp(timestamp).isoformat()
            self.speak(
                f"Tâche {task_id} planifiée pour {exec_time_str}",
                target="OverseerAgent"
            )
            
            return {
                "status": "success",
                "message": "Tâche planifiée avec succès",
                "task_id": task_id,
                "execution_time": exec_time_str
            }
            
        except Exception as e:
            error_message = f"Erreur lors de la planification de la tâche: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Annule une tâche planifiée
        
        Args:
            task_id: Identifiant de la tâche à annuler
            
        Returns:
            Résultat de l'annulation
        """
        try:
            with self.queue_lock:
                if task_id in self.tasks_by_id:
                    # Marquage de la tâche pour suppression
                    # (ne peut pas être retirée directement du heap)
                    task = self.tasks_by_id[task_id]
                    task.timestamp = 0  # Marque la tâche comme invalide
                    
                    # Suppression de la référence
                    del self.tasks_by_id[task_id]
                    
                    # Mise à jour des statistiques
                    self.stats["tasks_in_queue"] = len(self.tasks_by_id)
                    
                    # Message de log
                    self.speak(f"Tâche {task_id} annulée", target="OverseerAgent")
                    
                    # Réorganisation de la file et sauvegarde
                    self._rebuild_queue()
                    self._save_tasks()
                    
                    return {
                        "status": "success",
                        "message": f"Tâche {task_id} annulée"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Tâche {task_id} non trouvée"
                    }
        except Exception as e:
            error_message = f"Erreur lors de l'annulation de la tâche {task_id}: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def _rebuild_queue(self) -> None:
        """Reconstruit la file de priorité en supprimant les tâches marquées comme invalides"""
        valid_tasks = [task for task in self.task_queue if task.timestamp > 0]
        self.task_queue = []
        for task in valid_tasks:
            heapq.heappush(self.task_queue, task)
    
    def get_pending_tasks(self) -> Dict[str, Any]:
        """
        Récupère la liste des tâches en attente
        
        Returns:
            Liste des tâches en attente
        """
        try:
            with self.queue_lock:
                tasks = []
                
                for task in self.task_queue:
                    if task.timestamp > 0:  # Tâche valide
                        tasks.append({
                            "task_id": task.task_id,
                            "execution_time": datetime.datetime.fromtimestamp(task.timestamp).isoformat(),
                            "priority": task.priority,
                            "recurring": task.recurring,
                            "agent": task.task_data.get("agent", "unknown"),
                            "action": task.task_data.get("action", "unknown")
                        })
                
                return {
                    "status": "success",
                    "pending_tasks": sorted(tasks, key=lambda t: t["execution_time"])
                }
        except Exception as e:
            error_message = f"Erreur lors de la récupération des tâches en attente: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def start_scheduler(self) -> Dict[str, Any]:
        """
        Démarre le thread du scheduler en arrière-plan
        
        Returns:
            Statut du démarrage
        """
        if self.running:
            return {
                "status": "info",
                "message": "Le scheduler est déjà en cours d'exécution"
            }
        
        try:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            self.speak("Scheduler démarré en arrière-plan", target="OverseerAgent")
            
            return {
                "status": "success",
                "message": "Scheduler démarré avec succès"
            }
        except Exception as e:
            error_message = f"Erreur lors du démarrage du scheduler: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            self.running = False
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def stop_scheduler(self) -> Dict[str, Any]:
        """
        Arrête le thread du scheduler
        
        Returns:
            Statut de l'arrêt
        """
        if not self.running:
            return {
                "status": "info",
                "message": "Le scheduler n'est pas en cours d'exécution"
            }
        
        try:
            self.running = False
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5.0)
            
            self.speak("Scheduler arrêté", target="OverseerAgent")
            
            return {
                "status": "success",
                "message": "Scheduler arrêté avec succès"
            }
        except Exception as e:
            error_message = f"Erreur lors de l'arrêt du scheduler: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def _scheduler_loop(self) -> None:
        """Boucle principale du scheduler exécutée dans un thread séparé"""
        self.logger.info("Démarrage de la boucle du scheduler")
        
        check_interval = self.config.get("check_interval_seconds", 60)
        
        while self.running:
            try:
                # Vérification des tâches à exécuter
                self._check_tasks()
                
                # Attente avant la prochaine vérification
                time.sleep(check_interval)
            except Exception as e:
                error_message = f"Erreur dans la boucle du scheduler: {str(e)}"
                self.logger.error(error_message)
                
                # En cas d'erreur, attente courte pour éviter une boucle d'erreurs
                time.sleep(5)
        
        self.logger.info("Arrêt de la boucle du scheduler")
    
    def _check_tasks(self) -> None:
        """Vérifie les tâches à exécuter et les exécute si nécessaire"""
        now = time.time()
        tasks_to_execute = []
        
        with self.queue_lock:
            # Extraction des tâches à exécuter
            while self.task_queue and self.task_queue[0].timestamp <= now and self.task_queue[0].timestamp > 0:
                task = heapq.heappop(self.task_queue)
                tasks_to_execute.append(task)
                
                # Si tâche récurrente, reprogrammation
                if task.recurring and task.recurrence_interval:
                    next_execution = now + task.recurrence_interval
                    new_task = ScheduledTask(
                        timestamp=next_execution,
                        priority=task.priority,
                        task_id=f"{task.task_id}_next_{int(now)}",
                        task_data=task.task_data.copy(),
                        recurring=True,
                        recurrence_interval=task.recurrence_interval
                    )
                    heapq.heappush(self.task_queue, new_task)
                    self.tasks_by_id[new_task.task_id] = new_task
                
                # Suppression de la référence
                if task.task_id in self.tasks_by_id:
                    del self.tasks_by_id[task.task_id]
            
            # Mise à jour des statistiques
            self.stats["tasks_in_queue"] = len(self.task_queue)
        
        # Exécution des tâches extraites
        for task in tasks_to_execute:
            self._execute_task(task)
        
        # Sauvegarde de l'état actuel
        if tasks_to_execute:
            self._save_tasks()
    
    def _execute_task(self, task: ScheduledTask, overseer=None) -> None:
        """
        Exécute une tâche planifiée

        Args:
            task: La tâche à exécuter
            overseer: Instance d'OverseerAgent (pour tests)
        """
        try:
            # Log de l'exécution
            self.logger.info(f"Exécution de la tâche {task.task_id}")
            self.speak(f"Exécution de la tâche {task.task_id}", target="OverseerAgent")
            
            # Utiliser l'overseer fourni ou en obtenir un
            if overseer is None:
                overseer = self._get_overseer_agent()
            
            # Création de l'événement à transmettre
            event = {
                "action": "handle_event",
                "event_type": "scheduled_task",
                "event_data": {
                    "task_id": task.task_id,
                    "task_data": task.task_data,
                    "scheduled_time": task.timestamp,
                    "execution_time": time.time()
                }
            }
            
            # Exécution de la tâche
            result = overseer.run(event)
            
            # Mise à jour des statistiques
            self.stats["total_tasks_executed"] += 1
            self.stats["last_execution"] = datetime.datetime.now().isoformat()
            
            # Log du résultat
            status = result.get("status", "unknown")
            self.speak(f"Tâche {task.task_id} exécutée avec statut: {status}", target="OverseerAgent")
            
        except Exception as e:
            error_message = f"Erreur lors de l'exécution de la tâche {task.task_id}: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "")
        
        # Traitement selon l'action demandée
        if action == "schedule_task":
            # Planification d'une tâche
            return self.schedule_task(
                task_data=input_data.get("task_data", {}),
                execution_time=input_data.get("execution_time"),
                priority=input_data.get("priority", 1),
                task_id=input_data.get("task_id"),
                recurring=input_data.get("recurring", False),
                recurrence_interval=input_data.get("recurrence_interval")
            )
        
        elif action == "cancel_task":
            # Annulation d'une tâche
            return self.cancel_task(input_data.get("task_id"))
        
        elif action == "get_pending_tasks":
            # Récupération des tâches en attente
            return self.get_pending_tasks()
        
        elif action == "start_scheduler":
            # Démarrage du scheduler
            return self.start_scheduler()
        
        elif action == "stop_scheduler":
            # Arrêt du scheduler
            return self.stop_scheduler()
        
        elif action == "get_stats":
            # Récupération des statistiques
            return {
                "status": "success",
                "stats": self.stats
            }
        
        else:
            # Action non reconnue
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Création d'une instance de l'AgentSchedulerAgent
    scheduler = AgentSchedulerAgent()
    
    # Démarrage du scheduler
    scheduler.start_scheduler()
    
    # Exemple de planification d'une tâche
    scheduler.schedule_task(
        task_data={
            "agent": "MessagingAgent",
            "action": "send_message",
            "params": {
                "recipient": "test@example.com",
                "subject": "Test planifié",
                "body": "Ceci est un message de test planifié"
            }
        },
        execution_time=datetime.datetime.now() + datetime.timedelta(minutes=1),
        priority=1,
        recurring=True,
        recurrence_interval=3600  # Toutes les heures
    )
    
    # Boucle principale pour maintenir le script actif
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        # Arrêt propre
        scheduler.stop_scheduler()
        print("Scheduler arrêté")

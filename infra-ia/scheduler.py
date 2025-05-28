#!/usr/bin/env python3
"""
Planificateur de tâches pour BerinIA.

Ce script exécute un service de planification qui gère les tâches périodiques
et les tâches programmées dans le système BerinIA.
"""
import os
import sys
import time
import logging
import datetime
import json
import signal
import threading
from pathlib import Path

# Import TaskWatchdogAgent pour analyse de sécurité
try:
    from agents.task_watchdog.task_watchdog_agent import TaskWatchdogAgent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("TaskWatchdogAgent non disponible - Sécurité désactivée")

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'scheduler.log'))
    ]
)
logger = logging.getLogger("BerinIA.Scheduler")

# Créer le répertoire de logs s'il n'existe pas
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Chemin vers le fichier de tâches
TASKS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'tasks.json')

# S'assurer que le répertoire de données existe
data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)

# Variable pour contrôler l'exécution
running = True

class Task:
    """Représente une tâche planifiée."""
    
    def __init__(self, task_id, name, schedule, agent, params=None):
        self.task_id = task_id
        self.name = name
        self.schedule = schedule  # 'daily', 'weekly', 'hourly', ou datetime ISO
        self.agent = agent
        self.params = params or {}
        self.last_run = None
        self.next_run = self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calcule la prochaine exécution prévue."""
        now = datetime.datetime.now()
        
        if isinstance(self.schedule, str):
            if self.schedule == 'hourly':
                # Prochaine heure pleine
                return now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
            elif self.schedule == 'daily':
                # Demain même heure
                return now.replace(hour=9, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            elif self.schedule == 'weekly':
                # Prochain lundi à 9h
                days_ahead = 0 - now.weekday() if now.weekday() == 0 and now.hour < 9 else 7 - now.weekday()
                return now.replace(hour=9, minute=0, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
            else:
                try:
                    # Essayer de parser comme datetime ISO
                    return datetime.datetime.fromisoformat(self.schedule)
                except ValueError:
                    # Par défaut, exécuter dans une heure
                    return now + datetime.timedelta(hours=1)
        else:
            # Par défaut, exécuter dans une heure
            return now + datetime.timedelta(hours=1)
    
    def should_run(self):
        """Vérifie si la tâche doit être exécutée maintenant."""
        now = datetime.datetime.now()
        return self.next_run and now >= self.next_run
    
    def run(self):
        """Exécute la tâche."""
        from agents.registry import registry
        
        logger.info(f"Exécution de la tâche {self.name} (ID: {self.task_id})")
        
        try:
            # Obtenir l'agent
            agent_instance = registry.get_or_create(self.agent)
            
            if not agent_instance:
                logger.error(f"Agent {self.agent} non trouvé")
                return False
            
            # Exécuter l'agent avec les paramètres
            result = agent_instance.run(self.params)
            
            # Mettre à jour le statut
            self.last_run = datetime.datetime.now().isoformat()
            self.next_run = self._calculate_next_run()
            
            logger.info(f"Tâche {self.name} exécutée avec succès. Prochaine exécution: {self.next_run}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la tâche {self.name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def to_dict(self):
        """Convertit l'objet Task en dictionnaire."""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'schedule': self.schedule,
            'agent': self.agent,
            'params': self.params,
            'last_run': self.last_run,
            'next_run': self.next_run.isoformat() if isinstance(self.next_run, datetime.datetime) else self.next_run
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crée un objet Task à partir d'un dictionnaire."""
        task = cls(
            task_id=data['task_id'],
            name=data['name'],
            schedule=data['schedule'],
            agent=data['agent'],
            params=data['params']
        )
        task.last_run = data.get('last_run')
        if 'next_run' in data and data['next_run']:
            try:
                task.next_run = datetime.datetime.fromisoformat(data['next_run'])
            except (ValueError, TypeError):
                # En cas d'erreur, recalculer
                task.next_run = task._calculate_next_run()
        return task

class TaskScheduler:
    """Gestionnaire de tâches planifiées."""
    
    def __init__(self):
        self.tasks = []
        self.load_tasks()
    
    def load_tasks(self):
        """Charge les tâches depuis le fichier tasks.json."""
        if not os.path.exists(TASKS_FILE):
            logger.info(f"Fichier de tâches {TASKS_FILE} non trouvé. Création d'un nouveau fichier.")
            self.save_tasks()
            return
        
        try:
            with open(TASKS_FILE, 'r') as f:
                tasks_data = json.load(f)
            
            self.tasks = [Task.from_dict(task_data) for task_data in tasks_data]
            logger.info(f"{len(self.tasks)} tâches chargées depuis {TASKS_FILE}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des tâches: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def save_tasks(self):
        """Sauvegarde les tâches dans le fichier tasks.json."""
        try:
            tasks_data = [task.to_dict() for task in self.tasks]
            
            with open(TASKS_FILE, 'w') as f:
                json.dump(tasks_data, f, indent=2)
            
            logger.info(f"{len(self.tasks)} tâches sauvegardées dans {TASKS_FILE}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des tâches: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def add_task(self, name, schedule, agent, params=None, requesting_agent="scheduler"):
        """Ajoute une nouvelle tâche au planificateur avec analyse de sécurité."""
        # Générer un ID unique
        task_id = str(int(time.time()))
        
        # SÉCURITÉ : Analyse TaskWatchdogAgent
        if WATCHDOG_AVAILABLE:
            try:
                watchdog = TaskWatchdogAgent()
                
                # Construire les données pour l'analyse de sécurité
                security_analysis_data = {
                    "action": "analyze_new_task",
                    "task_id": task_id,
                    "task_data": {
                        "agent": agent,
                        "action": params.get("action", "unknown") if params else "unknown",
                        "params": params.get("params", {}) if params else {}
                    },
                    "execution_time": datetime.datetime.now().isoformat(),
                    "recurring": schedule in ['daily', 'weekly', 'hourly'],
                    "recurrence_interval": {
                        'hourly': 3600,
                        'daily': 86400, 
                        'weekly': 604800
                    }.get(schedule, None),
                    "requesting_agent": requesting_agent
                }
                
                # Analyse de sécurité
                security_result = watchdog.run(security_analysis_data)
                
                if security_result.get("status") == "success":
                    analysis = security_result.get("analysis", {})
                    threat_level = analysis.get("threat_level", "NORMAL")
                    
                    if threat_level == "CRITICAL":
                        logger.error(f"🚨 SÉCURITÉ CRITIQUE: Tâche {name} bloquée - {analysis.get('reason', 'Menace critique détectée')}")
                        return {
                            "status": "blocked", 
                            "message": f"Tâche bloquée par TaskWatchdogAgent: {analysis.get('reason', '')}",
                            "threat_level": threat_level,
                            "analysis": analysis
                        }
                    elif threat_level == "SUSPECT":
                        logger.warning(f"⚠️ TÂCHE SUSPECTE: {name} - {analysis.get('reason', '')} - Surveillance renforcée")
                    else:
                        logger.info(f"✅ Tâche {name} validée par sécurité (niveau: {threat_level})")
                else:
                    logger.warning(f"Erreur analyse sécurité pour tâche {name}: {security_result.get('message', 'unknown')}")
                    
            except Exception as e:
                logger.error(f"Erreur TaskWatchdogAgent pour tâche {name}: {e}")
                # En cas d'erreur, on continue (fail-safe)
        else:
            logger.warning(f"Tâche {name} ajoutée sans analyse de sécurité (TaskWatchdogAgent indisponible)")
        
        # Créer et ajouter la tâche
        task = Task(
            task_id=task_id,
            name=name,
            schedule=schedule,
            agent=agent,
            params=params
        )
        
        self.tasks.append(task)
        self.save_tasks()
        
        logger.info(f"Tâche {name} ajoutée avec ID {task_id}")
        return {"status": "success", "task_id": task_id}
    
    def remove_task(self, task_id):
        """Supprime une tâche du planificateur."""
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                del self.tasks[i]
                self.save_tasks()
                logger.info(f"Tâche avec ID {task_id} supprimée")
                return True
        
        logger.warning(f"Tâche avec ID {task_id} non trouvée")
        return False
    
    def run_scheduler(self):
        """Exécute le planificateur en continu."""
        logger.info("Démarrage du planificateur de tâches")
        
        while running:
            # Vérifier si des tâches doivent être exécutées
            for task in self.tasks:
                if task.should_run():
                    # Exécuter la tâche dans un thread séparé
                    thread = threading.Thread(target=task.run)
                    thread.start()
            
            # Sauvegarder les tâches
            self.save_tasks()
            
            # Attendre avant la prochaine vérification
            time.sleep(60)  # Vérifier toutes les minutes

# Gestionnaire de signal pour arrêter proprement
def signal_handler(sig, frame):
    global running
    logger.info("Signal d'arrêt reçu. Arrêt du planificateur...")
    running = False
    sys.exit(0)

# Enregistrer le gestionnaire de signal
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Démarrer le planificateur
    scheduler = TaskScheduler()
    try:
        scheduler.run_scheduler()
    except KeyboardInterrupt:
        logger.info("Interruption clavier. Arrêt du planificateur...")
    except Exception as e:
        logger.error(f"Erreur fatale dans le planificateur: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

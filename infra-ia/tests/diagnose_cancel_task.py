#!/usr/bin/env python3
"""
Script de diagnostic pour identifier précisément où le blocage se produit
dans la méthode cancel_task de l'AgentSchedulerAgent.
"""
import sys
import time
import datetime
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CancelTaskDiagnostic")

logger.info("=== DÉMARRAGE DU DIAGNOSTIC DE CANCEL_TASK ===")

# Ajout du répertoire courant au chemin de recherche
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Importation des modules avec gestion d'erreur explicite
try:
    logger.info("Importation des modules...")
    from agents.scheduler.agent_scheduler_agent import AgentSchedulerAgent, ScheduledTask
    from agents.logger.logger_agent import LoggerAgent
    logger.info("Modules importés avec succès")
except ImportError as e:
    logger.error(f"ERREUR D'IMPORTATION: {e}")
    sys.exit(1)

# Inspection de l'implémentation de cancel_task
logger.info("\n=== CODE SOURCE DE CANCEL_TASK ===")
import inspect
cancel_task_source = inspect.getsource(AgentSchedulerAgent.cancel_task)
logger.info(cancel_task_source)

# Inspection de l'implémentation de speak
logger.info("\n=== CODE SOURCE DE SPEAK ===")
from core.agent_base import Agent
speak_source = inspect.getsource(Agent.speak)
logger.info(speak_source)

# Injection de points de trace dans la méthode cancel_task
original_cancel_task = AgentSchedulerAgent.cancel_task

def traced_cancel_task(self, task_id):
    """Wrapper avec traces pour cancel_task"""
    logger.info(f"TRACE: Entrée dans cancel_task({task_id})")
    
    try:
        # Simulation étape par étape
        logger.info("TRACE: Acquisition du verrou...")
        with self.queue_lock:
            logger.info("TRACE: Verrou acquis")
            
            if task_id in self.tasks_by_id:
                logger.info(f"TRACE: Tâche {task_id} trouvée dans tasks_by_id")
                
                # Marquage de la tâche
                task = self.tasks_by_id[task_id]
                task.timestamp = 0
                logger.info("TRACE: Tâche marquée comme invalide (timestamp=0)")
                
                # Suppression de la référence
                del self.tasks_by_id[task_id]
                logger.info("TRACE: Référence supprimée de tasks_by_id")
                
                # Mise à jour des statistiques
                old_count = self.stats["tasks_in_queue"]
                self.stats["tasks_in_queue"] = len(self.tasks_by_id)
                logger.info(f"TRACE: Statistiques mises à jour ({old_count} -> {self.stats['tasks_in_queue']})")
                
                # POINT CRITIQUE: Appel à speak
                logger.info("TRACE: AVANT appel à self.speak()")
                with patch.object(LoggerAgent, 'log_interaction', MagicMock()):
                    logger.info("TRACE: LoggerAgent.log_interaction patché")
                    # Patch de speak pour éviter les effets de bord
                    old_speak = self.speak
                    self.speak = MagicMock()
                    logger.info("TRACE: self.speak remplacé par un mock")
                    
                    # Tentative d'appel à speak (ne devrait pas bloquer maintenant)
                    try:
                        self.speak(f"Tâche {task_id} annulée", target="OverseerAgent")
                        logger.info("TRACE: Appel à self.speak() réussi!")
                    except Exception as speak_error:
                        logger.error(f"TRACE: ERREUR dans self.speak(): {speak_error}")
                    
                    # Restauration de speak
                    self.speak = old_speak
                    logger.info("TRACE: self.speak restauré")
                
                # Réorganisation et sauvegarde
                logger.info("TRACE: AVANT appel à self._rebuild_queue()")
                self._rebuild_queue()
                logger.info("TRACE: File reconstruite avec succès")
                
                logger.info("TRACE: AVANT appel à self._save_tasks()")
                # Patch de _save_tasks pour éviter les effets de bord
                old_save = self._save_tasks
                self._save_tasks = MagicMock()
                try:
                    self._save_tasks()
                    logger.info("TRACE: Appel à self._save_tasks() réussi!")
                except Exception as save_error:
                    logger.error(f"TRACE: ERREUR dans self._save_tasks(): {save_error}")
                # Restauration de _save_tasks
                self._save_tasks = old_save
                
                logger.info("TRACE: Préparation du résultat de succès")
                return {
                    "status": "success",
                    "message": f"Tâche {task_id} annulée"
                }
            else:
                logger.info(f"TRACE: Tâche {task_id} NON trouvée dans tasks_by_id")
                return {
                    "status": "error",
                    "message": f"Tâche {task_id} non trouvée"
                }
    except Exception as e:
        logger.error(f"TRACE: EXCEPTION GLOBALE dans cancel_task: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Message de log (avec speak patché)
        error_message = f"Erreur lors de l'annulation de la tâche {task_id}: {str(e)}"
        with patch.object(LoggerAgent, 'log_interaction', MagicMock()):
            # Patch de speak
            old_speak = self.speak
            self.speak = MagicMock()
            try:
                self.speak(error_message, target="OverseerAgent")
            except:
                pass
            # Restauration de speak
            self.speak = old_speak
                
        self.logger.error(error_message)
        
        return {
            "status": "error",
            "message": error_message
        }

# Remplacer temporairement la méthode par notre version instrumentée
AgentSchedulerAgent.cancel_task = traced_cancel_task
logger.info("Méthode cancel_task remplacée par version instrumentée")

# Test de la fonction cancel_task avec isolation maximale
logger.info("\n=== TEST ISOLÉ DE CANCEL_TASK ===")

try:
    # Création de l'agent avec minimal de dépendances
    logger.info("Création de l'instance d'AgentSchedulerAgent...")
    
    # Patch tous les appels problématiques
    with patch('agents.logger.logger_agent.LoggerAgent', MagicMock()):
        with patch.object(LoggerAgent, 'log_interaction', MagicMock()):
            with patch.object(AgentSchedulerAgent, 'load_config', return_value={"tasks_file": "diagnostic_tasks.json"}):
                # Création de l'agent
                scheduler = AgentSchedulerAgent()
                logger.info("Instance créée avec succès")
                
                # Réinitialisation des structures de données
                scheduler.task_queue = []
                scheduler.tasks_by_id = {}
                logger.info("Structures de données réinitialisées")
                
                # Création d'une tâche de test
                task_id = "diagnostic_task"
                task = ScheduledTask(
                    timestamp=time.time() + 3600,  # Dans une heure
                    priority=1,
                    task_id=task_id,
                    task_data={"diagnostic": True}
                )
                
                # Ajout manuel à la file et au dictionnaire
                scheduler.task_queue.append(task)
                scheduler.tasks_by_id[task_id] = task
                logger.info(f"Tâche de test '{task_id}' ajoutée manuellement")
                
                # Vérification que la tâche est bien présente
                logger.info(f"État avant annulation: {len(scheduler.task_queue)} tâches, IDs={list(scheduler.tasks_by_id.keys())}")
                
                # Test de l'annulation
                logger.info("EXÉCUTION DE CANCEL_TASK...")
                result = scheduler.cancel_task(task_id)
                
                # Analyse du résultat
                logger.info(f"Résultat: {result}")
                logger.info(f"État après annulation: {len(scheduler.task_queue)} tâches, IDs={list(scheduler.tasks_by_id.keys())}")
                
                # Vérification du succès
                if result["status"] == "success" and task_id not in scheduler.tasks_by_id:
                    logger.info("TEST RÉUSSI: La tâche a été correctement annulée")
                else:
                    logger.error("TEST ÉCHOUÉ: Problème lors de l'annulation")

except Exception as e:
    logger.error(f"ERREUR GLOBALE: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Restauration de la méthode originale
AgentSchedulerAgent.cancel_task = original_cancel_task
logger.info("Méthode cancel_task restaurée à sa version originale")

logger.info("\n=== DIAGNOSTIC TERMINÉ ===")

#!/usr/bin/env python3
"""
Script d'initialisation du système BerinIA.

Ce script initialise tous les agents du système, configure les connexions
entre eux et démarre les services nécessaires.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
import importlib
import datetime
import time

from agents.registry import registry
from utils.agent_definitions import AGENT_DEFINITIONS, ALL_AGENT_NAMES

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/berinia_init.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("BerinIA-Init")

def ensure_directories():
    """Assure que les répertoires nécessaires existent."""
    dirs = ["logs", "data", "db"]
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        logger.info(f"Répertoire {dir_name} vérifié/créé.")

def load_env_variables():
    """Charge les variables d'environnement depuis le fichier .env."""
    env_path = Path(".env")
    if not env_path.exists():
        logger.error("Fichier .env non trouvé. Veuillez créer un fichier .env avec les variables nécessaires.")
        sys.exit(1)
    
    logger.info("Chargement des variables d'environnement...")
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                key, value = line.split('=', 1)
                os.environ[key] = value
        
        # Vérification des variables critiques
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
            sys.exit(1)
            
        logger.info("Variables d'environnement chargées avec succès.")
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement des variables d'environnement: {e}")
        sys.exit(1)

def import_agent_class(agent_path):
    """
    Importe dynamiquement une classe d'agent depuis son chemin.
    
    Args:
        agent_path: Chemin vers la classe d'agent (format: "agents.agent_type.agent_name.AgentClass")
        
    Returns:
        La classe d'agent
    """
    try:
        module_path, class_name = agent_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except Exception as e:
        logger.error(f"Erreur lors de l'importation de l'agent {agent_path}: {e}")
        return None

def initialize_agents():
    """
    Initialise tous les agents du système à partir des définitions centralisées.
    
    Returns:
        Dict avec les instances d'agents initialisées
    """
    logger.info("Initialisation des agents...")
    
    # Réinitialiser le registre si nécessaire
    if registry.initialized:
        logger.warning("Le registre d'agents est déjà initialisé. Réutilisation des agents existants.")
        return registry.list_agents()
    
    # Utiliser la méthode create_all_agents du registre qui se base sur les définitions centralisées
    agents = registry.create_all_agents()
    
    # Marquer le registre comme initialisé
    registry.initialized = True
    logger.info(f"Registre d'agents initialisé avec {len(agents)} agents")
    
    # Vérifier que tous les agents ont été initialisés correctement
    missing_agents = [name for name in ALL_AGENT_NAMES if name not in agents]
    if missing_agents:
        logger.warning(f"Agents manquants après initialisation: {', '.join(missing_agents)}")
    
    return agents

def start_scheduler(agents):
    """
    Démarre l'agent de planification.
    
    Args:
        agents: Dictionnaire contenant les instances d'agents
    """
    if "AgentSchedulerAgent" not in agents:
        logger.warning("AgentSchedulerAgent non trouvé, impossible de démarrer le planificateur.")
        return False
    
    try:
        scheduler = agents["AgentSchedulerAgent"]
        logger.info("Démarrage de l'AgentSchedulerAgent...")
        
        # Démarrage du scheduler
        result = scheduler.run({"action": "start_scheduler"})
        
        if result.get("status") == "success":
            logger.info("AgentSchedulerAgent démarré avec succès.")
            return True
        else:
            logger.error(f"Échec du démarrage de l'AgentSchedulerAgent: {result.get('message')}")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'AgentSchedulerAgent: {e}")
        return False

def setup_initial_tasks(agents):
    """
    Configure les tâches initiales dans le système.
    
    Args:
        agents: Dictionnaire contenant les instances d'agents
    """
    if "AgentSchedulerAgent" not in agents:
        logger.warning("AgentSchedulerAgent non trouvé, impossible de configurer les tâches initiales.")
        return
    
    logger.info("Configuration des tâches initiales...")
    
    scheduler = agents["AgentSchedulerAgent"]
    
    # Configuration des tâches récurrentes
    tasks = [
        # Analyse hebdomadaire des performances du système
        {
            "agent": "PivotStrategyAgent",
            "action": "recommend_optimizations",  # Action existante dans PivotStrategyAgent
            "params": {
                "target": "all",
                "optimization_type": "all",
                "days_back": 7,
                "include_details": True
            },
            "scheduled_time": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat(),
            "recurrent": True,
            "interval_seconds": 7 * 24 * 60 * 60  # 7 jours
        },
        
        # Vérification quotidienne des campagnes
        {
            "agent": "ProspectionSupervisor",
            "action": "list",  # Action existante dans ProspectionSupervisor
            "params": {},
            "scheduled_time": (datetime.datetime.now() + datetime.timedelta(hours=12)).isoformat(),
            "recurrent": True,
            "interval_seconds": 24 * 60 * 60  # 1 jour
        }
    ]
    
    for task in tasks:
        try:
            result = scheduler.run({
                "action": "schedule_task",
                "task_data": {
                    "agent": task["agent"],
                    "action": task["action"],
                    "params": task.get("params", {})
                },
                "execution_time": task["scheduled_time"],
                "recurring": task.get("recurrent", False),
                "recurrence_interval": task.get("interval_seconds")
            })
            
            if result.get("status") == "success":
                logger.info(f"Tâche planifiée avec succès: {task['agent']}.{task['action']}")
            else:
                logger.warning(f"Échec de la planification de la tâche: {result.get('message')}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la planification de la tâche: {e}")

def register_handlers():
    """
    Enregistre les gestionnaires d'événements et de signaux.
    """
    def shutdown_handler(signum, frame):
        logger.info("Signal d'arrêt reçu. Arrêt propre du système...")
        # TODO: Implémentation de l'arrêt propre
        sys.exit(0)
    
    # Enregistrement des gestionnaires pour SIGINT et SIGTERM
    import signal
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    logger.info("Gestionnaires d'événements enregistrés.")

def main():
    """Fonction principale d'initialisation du système."""
    parser = argparse.ArgumentParser(description="Initialisation du système BerinIA")
    parser.add_argument("--no-scheduler", action="store_true", help="Ne pas démarrer l'agent de planification")
    args = parser.parse_args()
    
    logger.info("===== DÉMARRAGE DE BERINIA =====")
    start_time = time.time()
    
    # Création des répertoires nécessaires
    ensure_directories()
    
    # Chargement des variables d'environnement
    load_env_variables()
    
    # Initialisation des agents
    agents = initialize_agents()
    
    if not agents:
        logger.error("Aucun agent n'a pu être initialisé. Arrêt du système.")
        sys.exit(1)
    
    # Enregistrement des gestionnaires d'événements
    register_handlers()
    
    # Démarrage du planificateur si demandé
    if not args.no_scheduler:
        scheduler_started = start_scheduler(agents)
        
        # Configuration des tâches initiales si le scheduler a démarré
        if scheduler_started:
            setup_initial_tasks(agents)
    else:
        logger.info("Démarrage de l'agent de planification ignoré (--no-scheduler).")
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    logger.info(f"===== BERINIA DÉMARRÉ EN {elapsed:.2f} SECONDES =====")
    logger.info(f"Agents initialisés: {', '.join(agents.keys())}")
    
    # L'OverseerAgent est maintenant prêt à recevoir des instructions
    if "OverseerAgent" in agents:
        agents["OverseerAgent"].speak("Système BerinIA initialisé et prêt à recevoir des instructions.")
    
    return agents

if __name__ == "__main__":
    main()

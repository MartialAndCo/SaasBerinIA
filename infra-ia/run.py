#!/usr/bin/env python3
"""
Point d'entrée principal du système BerinIA.

Ce script constitue le lanceur automatisé du système complet avec les modules suivants:
- Initialisation des agents
- Exécution du scheduler en arrière-plan
- Démarrage du serveur de webhooks
- Supervision et monitoring du système

Usage:
    python run.py                      # Démarrage normal avec tous les composants
    python run.py --no-webhook         # Sans serveur de webhooks
    python run.py --no-scheduler       # Sans démarrage du scheduler
    python run.py --debug              # Mode debug avec logs détaillés
"""
import os
import sys
import time
import signal
import argparse
import logging
import threading
import json
from pathlib import Path
import importlib
import uvicorn
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/berinia.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("BerinIA-Main")

# Chemins importants
CURRENT_DIR = Path(__file__).parent.absolute()
CONFIG_PATH = CURRENT_DIR / "config.json"

def load_config():
    """Charge la configuration globale du système."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        logger.info("Configuration globale chargée avec succès")
        return config
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        sys.exit(1)

def setup_environment():
    """Prépare l'environnement d'exécution."""
    # Chargement des variables d'environnement
    load_dotenv()
    
    # Vérification des variables critiques
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Création des répertoires nécessaires
    dirs = ["logs", "data", "db"]
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
    
    logger.info("Environnement configuré avec succès")

def import_from_path(module_path, attribute=None):
    """
    Importe dynamiquement un module ou un attribut de module.
    
    Args:
        module_path: Chemin vers le module
        attribute: Attribut à extraire (optionnel)
        
    Returns:
        Module ou attribut importé
    """
    try:
        module = importlib.import_module(module_path)
        if attribute:
            return getattr(module, attribute)
        return module
    except Exception as e:
        logger.error(f"Erreur lors de l'importation de {module_path}: {e}")
        return None

def start_webhook_server(config):
    """
    Démarre le serveur de webhooks dans un thread séparé.
    
    Args:
        config: Configuration du système
    """
    logger.info("Démarrage du serveur de webhooks...")
    
    webhook_config = config["webhook"]
    host = webhook_config["host"]
    port = webhook_config["port"]
    
    # Import du module FastAPI pour le webhook
    try:
        webhook_app = import_from_path("webhook.run_webhook", "app")
        
        if not webhook_app:
            logger.error("Impossible d'importer l'application webhook")
            return False
        
        # Démarrage dans un thread séparé pour ne pas bloquer
        def run_server():
            uvicorn.run(webhook_app, host=host, port=port)
        
        webhook_thread = threading.Thread(target=run_server, daemon=True)
        webhook_thread.start()
        
        logger.info(f"Serveur de webhooks démarré sur {host}:{port}")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur de webhooks: {e}")
        return False

def initialize_agents():
    """
    Initialise les agents du système en utilisant init_system.py.
    
    Returns:
        Dict d'agents initialisés
    """
    logger.info("Initialisation des agents...")
    
    try:
        init_system = import_from_path("init_system", "main")
        
        if not init_system:
            logger.error("Impossible d'importer le module d'initialisation")
            return {}
        
        agents = init_system()
        
        if not agents:
            logger.error("Échec de l'initialisation des agents")
            return {}
        
        agent_names = ", ".join(agents.keys())
        logger.info(f"Agents initialisés avec succès: {agent_names}")
        
        return agents
    
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation des agents: {e}")
        return {}

def start_scheduler(agents, config):
    """
    Démarre l'agent scheduler en mode continu.
    
    Args:
        agents: Dict d'agents initialisés
        config: Configuration du système
    """
    if "AgentSchedulerAgent" not in agents:
        logger.error("AgentSchedulerAgent non trouvé, impossible de démarrer le scheduler")
        return False
    
    logger.info("Démarrage du scheduler...")
    
    scheduler = agents["AgentSchedulerAgent"]
    scheduler_config = config["agents"]["scheduler"]
    check_interval = scheduler_config["check_interval_seconds"]
    
    try:
        # Démarrage du scheduler
        result = scheduler.run({"action": "start_scheduler"})
        
        if result.get("status") != "success":
            logger.error(f"Échec du démarrage du scheduler: {result.get('message')}")
            return False
        
        logger.info(f"Scheduler démarré avec succès (intervalle: {check_interval}s)")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du scheduler: {e}")
        return False

def setup_signal_handlers(agents):
    """
    Configure les gestionnaires de signaux pour un arrêt propre.
    
    Args:
        agents: Dict d'agents initialisés
    """
    def signal_handler(sig, frame):
        logger.info("Signal d'arrêt reçu. Arrêt propre du système...")
        
        # Arrêt du scheduler si présent
        if "AgentSchedulerAgent" in agents:
            try:
                agents["AgentSchedulerAgent"].run({"action": "stop_scheduler"})
                logger.info("Scheduler arrêté")
            except Exception as e:
                logger.error(f"Erreur lors de l'arrêt du scheduler: {e}")
        
        # Informer l'OverseerAgent de l'arrêt du système
        if "OverseerAgent" in agents:
            try:
                agents["OverseerAgent"].speak("Arrêt du système BerinIA en cours...")
            except Exception:
                pass
        
        logger.info("Système BerinIA arrêté proprement")
        sys.exit(0)
    
    # Capture des signaux d'arrêt
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Gestionnaires de signaux configurés")

def monitor_system(agents, config):
    """
    Surveille l'état de santé du système en continu.
    
    Args:
        agents: Dict d'agents initialisés
        config: Configuration du système
    """
    monitoring_config = config["monitoring"]
    check_interval = monitoring_config["health_check_interval_minutes"] * 60
    
    logger.info(f"Démarrage du monitoring (intervalle: {check_interval}s)")
    
    while True:
        try:
            # Vérification de l'état des agents
            for name, agent in agents.items():
                # Si l'agent a une méthode health_check
                if hasattr(agent, "health_check") and callable(getattr(agent, "health_check")):
                    health = agent.health_check()
                    if not health["healthy"]:
                        logger.warning(f"Agent {name} signale un problème: {health['message']}")
            
            # Collecte des métriques si tracking activé
            if monitoring_config["performance_tracking"]["response_times"]:
                # TODO: Implémenter la collecte de métriques
                pass
                
        except Exception as e:
            logger.error(f"Erreur lors du monitoring: {e}")
        
        # Attente avant la prochaine vérification
        time.sleep(check_interval)

def main():
    """Fonction principale du système."""
    parser = argparse.ArgumentParser(description="Système BerinIA - Lanceur principal")
    parser.add_argument("--no-webhook", action="store_true", help="Ne pas démarrer le serveur de webhooks")
    parser.add_argument("--no-scheduler", action="store_true", help="Ne pas démarrer l'agent scheduler")
    parser.add_argument("--debug", action="store_true", help="Activer le mode debug")
    args = parser.parse_args()
    
    # Configuration du niveau de log
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Mode DEBUG activé")
    
    logger.info("===== DÉMARRAGE DU SYSTÈME BERINIA =====")
    start_time = time.time()
    
    # Préparation de l'environnement
    setup_environment()
    
    # Chargement de la configuration
    config = load_config()
    
    # Initialisation des agents
    agents = initialize_agents()
    
    if not agents:
        logger.error("Échec critique: aucun agent initialisé. Arrêt du système.")
        sys.exit(1)
    
    # Configuration des gestionnaires de signaux
    setup_signal_handlers(agents)
    
    # Démarrage du scheduler si demandé
    if not args.no_scheduler:
        scheduler_started = start_scheduler(agents, config)
        if not scheduler_started:
            logger.warning("Le scheduler n'a pas pu démarrer correctement")
    else:
        logger.info("Démarrage du scheduler ignoré (--no-scheduler)")
    
    # Démarrage du serveur de webhooks si demandé
    if not args.no_webhook:
        webhook_started = start_webhook_server(config)
        if not webhook_started:
            logger.warning("Le serveur de webhooks n'a pas pu démarrer correctement")
    else:
        logger.info("Démarrage du serveur de webhooks ignoré (--no-webhook)")
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    logger.info(f"===== SYSTÈME BERINIA DÉMARRÉ EN {elapsed:.2f} SECONDES =====")
    
    # Information de démarrage via l'OverseerAgent
    if "OverseerAgent" in agents:
        agents["OverseerAgent"].speak("Système BerinIA démarré et opérationnel.")
    
    # Monitoring continu du système
    try:
        monitor_system(agents, config)
    except KeyboardInterrupt:
        logger.info("Arrêt manuel du système")
        sys.exit(0)

if __name__ == "__main__":
    main()

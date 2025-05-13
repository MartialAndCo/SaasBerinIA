#!/usr/bin/env python3
"""
Configuration des agents pour le webhook
Utilise le système centralisé de définition des agents et le nouveau système de logs
"""
import sys
import os
import traceback

# Ajout du répertoire parent au path pour les imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import du registre d'agents et des définitions
from agents.registry import registry
from utils.agent_definitions import get_all_agent_names
from utils.logging_config import get_logger

# Logger
logger = get_logger("webhook.config")

# Fonction pour créer les instances d'agents
def get_webhook_agents():
    """
    Crée et retourne les instances d'agents nécessaires pour le webhook
    Utilise la liste complète des agents disponibles
    
    Returns:
        Dictionnaire contenant les instances d'agents
    """
    agents = {}
    
    # Obtenir la liste de tous les agents disponibles
    all_agent_names = get_all_agent_names()
    
    # Vérifier si le registre est déjà initialisé
    if registry.initialized:
        logger.info("Registre d'agents déjà initialisé, récupération des agents existants")

        # Récupérer les agents existants
        for agent_name in all_agent_names:
            agent = registry.get(agent_name)
            if agent:
                agents[agent_name] = agent
                logger.info(f"Agent {agent_name} récupéré du registre")
            else:
                # Créer l'agent s'il n'existe pas déjà
                logger.warning(f"Agent {agent_name} non trouvé dans le registre, création...")
                try:
                    agent = registry.get_or_create(agent_name)
                    if agent:
                        agents[agent_name] = agent
                        logger.info(f"Agent {agent_name} créé avec succès")
                    else:
                        logger.error(f"Impossible de créer l'agent {agent_name}")
                except Exception as e:
                    logger.error(f"Erreur lors de la création de l'agent {agent_name}: {str(e)}")
                    logger.error(traceback.format_exc())

    else:
        logger.info("Initialisation de tous les agents pour le webhook...")

        # Créer tous les agents disponibles
        for agent_name in all_agent_names:
            try:
                logger.info(f"Initialisation de l'agent {agent_name}...")
                agent = registry.get_or_create(agent_name)

                if agent:
                    agents[agent_name] = agent
                    logger.info(f"Agent {agent_name} initialisé avec succès")
                else:
                    logger.error(f"Échec de l'initialisation de l'agent {agent_name}")

            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation de l'agent {agent_name}: {str(e)}")
                logger.error(traceback.format_exc())

    # Marquer le registre comme initialisé
    registry.initialized = True
    logger.info(f"Registre d'agents initialisé avec {len(agents)} agents")

    # Vérifier que les agents principaux sont disponibles
    # Cette liste contient les agents absolument nécessaires au fonctionnement du webhook
    core_agents = ["LoggerAgent", "OverseerAgent", "MessagingAgent"]
    missing_core_agents = [name for name in core_agents if name not in agents]
    
    if missing_core_agents:
        logger.error(f"Agents principaux manquants pour le webhook: {', '.join(missing_core_agents)}")
    else:
        logger.info("Tous les agents principaux pour le webhook sont disponibles")
        logger.info(f"Total des agents chargés: {len(agents)}")

    return agents

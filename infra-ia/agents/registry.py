"""
Module de registre d'agents pour le système BerinIA.

Ce module fournit un singleton de registre d'agents partagé entre tous les composants
du système, permettant ainsi un accès centralisé aux instances d'agents.
"""
import logging
import importlib
from typing import Dict, Any, Optional, Type, List

from core.agent_base import Agent
from utils.agent_definitions import (
    AGENT_DEFINITIONS, 
    ALL_AGENT_NAMES, 
    get_agent_definition,
    get_agent_import_info
)

logger = logging.getLogger("BerinIA.AgentRegistry")

class AgentRegistry:
    """
    Registre singleton pour stocker et accéder aux instances d'agents.
    
    Cette classe implémente le design pattern Singleton pour garantir
    qu'un seul registre d'agents existe dans tout le système.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance._agents = {}
            cls._instance._initialized = False
        return cls._instance
    
    def register(self, name: str, agent: Agent) -> None:
        """
        Enregistre une instance d'agent dans le registre.
        
        Args:
            name: Nom de l'agent
            agent: Instance de l'agent
        """
        self._agents[name] = agent
        logger.info(f"Agent {name} enregistré dans le registre")
    
    def get(self, name: str) -> Optional[Agent]:
        """
        Récupère une instance d'agent à partir de son nom.
        
        Args:
            name: Nom de l'agent à récupérer
            
        Returns:
            L'instance d'agent ou None si non trouvée
        """
        agent = self._agents.get(name)
        if not agent:
            logger.warning(f"Agent {name} non trouvé dans le registre")
        return agent
    
    def get_or_create(self, name: str, config_path: Optional[str] = None) -> Optional[Agent]:
        """
        Récupère une instance d'agent ou la crée si non existante.
        Utilise les définitions centralisées pour trouver la classe d'agent.
        
        Args:
            name: Nom de l'agent
            config_path: Chemin optionnel vers la configuration
            
        Returns:
            L'instance d'agent ou None en cas d'erreur
        """
        # Vérifier si l'agent existe déjà
        agent = self.get(name)
        if agent:
            return agent
        
        # Récupérer la définition de l'agent depuis le fichier centralisé
        agent_def = get_agent_definition(name)
        
        if agent_def:
            # Utiliser les informations de la définition
            module_path = agent_def["module_path"]
            class_name = agent_def["class_name"]
            config_path = config_path or agent_def["config_path"]
            
            logger.info(f"Création de l'agent {name} depuis les définitions centralisées")
            
            try:
                # Importation du module
                module = importlib.import_module(module_path)
                AgentClass = getattr(module, class_name)
                
                # Création de l'instance
                agent = AgentClass(config_path=config_path)
                
                # Enregistrement de l'instance
                self.register(name, agent)
                
                return agent
                
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'agent {name}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return None
        else:
            # Fallback à l'ancienne méthode si nécessaire pour compatibilité
            try:
                # Import dynamique pour éviter les dépendances circulaires
                from utils.agent_finder import load_agent_class
                
                # Tentative de chargement de la classe avec le finder robuste
                logger.info(f"Agent {name} non trouvé dans les définitions, tentative avec finder")
                AgentClass = load_agent_class(name)
                
                if AgentClass:
                    # Création de l'instance
                    agent = AgentClass(config_path=config_path)
                    
                    # Enregistrement de l'instance
                    self.register(name, agent)
                    
                    logger.warning(f"Agent {name} créé avec le fallback, mais il est absent des définitions centralisées")
                    return agent
                else:
                    logger.error(f"Agent {name} introuvable, ni dans les définitions ni via finder")
                    return None
            except Exception as e:
                logger.error(f"Erreur lors du fallback pour l'agent {name}: {str(e)}")
                return None
    
    def list_agents(self) -> Dict[str, Agent]:
        """
        Liste tous les agents enregistrés.
        
        Returns:
            Dictionnaire des agents enregistrés
        """
        return self._agents.copy()
        
    def create_all_agents(self, categories: Optional[List[str]] = None) -> Dict[str, Agent]:
        """
        Crée des instances de tous les agents définis dans les catégories spécifiées.
        
        Args:
            categories: Liste des catégories d'agents à créer (None = toutes)
            
        Returns:
            Dictionnaire des agents créés {nom: instance}
        """
        created_agents = {}
        
        # Filtrer les définitions par catégorie si spécifié
        if categories:
            defs_to_process = [
                agent for agent in AGENT_DEFINITIONS 
                if agent.get("category") in categories
            ]
        else:
            defs_to_process = AGENT_DEFINITIONS
            
        # Créer chaque agent
        for agent_def in defs_to_process:
            name = agent_def["name"]
            if name not in self._agents:
                try:
                    logger.info(f"Création de l'agent {name}")
                    agent = self.get_or_create(name, agent_def["config_path"])
                    if agent:
                        created_agents[name] = agent
                except Exception as e:
                    logger.error(f"Erreur lors de la création de l'agent {name}: {str(e)}")
            else:
                # L'agent existe déjà
                created_agents[name] = self._agents[name]
                
        logger.info(f"Création de {len(created_agents)} agents terminée")
        return created_agents
    
    def clear(self) -> None:
        """
        Vide le registre (utile pour les tests).
        """
        self._agents.clear()
        logger.info("Registre d'agents vidé")
    
    @property
    def initialized(self) -> bool:
        """
        Indique si le registre a été initialisé avec les agents de base.
        """
        return self._initialized
    
    @initialized.setter
    def initialized(self, value: bool) -> None:
        """
        Définit l'état d'initialisation du registre.
        """
        self._initialized = value
        
    def __contains__(self, name: str) -> bool:
        """
        Vérifie si un agent existe dans le registre.
        
        Args:
            name: Nom de l'agent à vérifier
            
        Returns:
            True si l'agent existe, False sinon
        """
        return name in self._agents

# Export d'une instance du registre pour un accès global
registry = AgentRegistry()

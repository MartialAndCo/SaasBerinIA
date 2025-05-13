"""
Module de recherche avancée d'agents pour BerinIA

Ce module fournit des fonctions avancées pour trouver et charger des agents 
indépendamment des variations de noms et de chemins.
"""

import os
import re
import sys
import logging
import inspect
import importlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set, Union

logger = logging.getLogger("BerinIA.AgentFinder")

# Cache global des chemins d'agents découverts
# {nom normalisé: (module_path, class_name)}
AGENT_PATHS_CACHE = {}

def normalize_agent_name(agent_name: str) -> str:
    """
    Normalise un nom d'agent pour la recherche
    
    Args:
        agent_name: Nom de l'agent à normaliser
        
    Returns:
        Nom normalisé (lowercase, sans underscore, sans 'agent' à la fin)
    """
    # Supprimer les underscores et mettre en minuscules
    normalized = agent_name.lower().replace("_", "")
    
    # Supprimer le suffixe "agent" s'il existe
    if normalized.endswith("agent"):
        normalized = normalized[:-5]
        
    return normalized

def find_agent_file(agent_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Trouve le fichier et le nom de classe d'un agent, quelle que soit la structure
    
    Args:
        agent_name: Nom de l'agent (avec ou sans "Agent")
        
    Returns:
        Tuple (module_path, class_name) ou (None, None) si non trouvé
    """
    normalized_name = normalize_agent_name(agent_name)
    
    # Vérifier d'abord dans le cache
    if normalized_name in AGENT_PATHS_CACHE:
        return AGENT_PATHS_CACHE[normalized_name]
        
    # Construire la liste des chemins de modules possibles à vérifier
    base_dir = Path("/root/berinia/infra-ia/agents")
    potential_dirs = []
    
    # 1. Essayer le format standard (snake_case)
    snake_case = "_".join(re.findall(r'[a-z]+|[A-Z][a-z]*', normalized_name)).lower()
    potential_dirs.append(base_dir / snake_case)
    
    # 2. Essayer avec "agent" suffixé
    potential_dirs.append(base_dir / f"{snake_case}_agent")
    
    # 3. Essayer agent collé
    potential_dirs.append(base_dir / f"{snake_case}agent")
    
    # 4. Essayer le nom exact
    potential_dirs.append(base_dir / normalized_name)
    
    # 5. Essayer le nom normalisé sans "agent"
    if normalized_name.endswith("agent"):
        potential_dirs.append(base_dir / normalized_name[:-5])
    
    # Parcourir tous les dossiers potentiels
    logger.info(f"Recherche de l'agent '{agent_name}' (normalisé: '{normalized_name}')")
    
    found_module_path = None
    found_class_name = None
    
    for agent_dir in potential_dirs:
        if not agent_dir.exists() or not agent_dir.is_dir():
            continue
            
        logger.info(f"Dossier trouvé: {agent_dir}")
        
        # Chercher les fichiers Python
        for py_file in agent_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # Lire le contenu pour trouver les classes
            with open(py_file, "r") as f:
                content = f.read()
                
            # Rechercher les classes qui héritent de Agent
            class_matches = re.findall(r'class\s+(\w+)\s*\([^)]*Agent', content)
            
            if not class_matches:
                continue
                
            # Vérifier si l'une des classes correspond à notre agent
            for class_name in class_matches:
                class_normalized = normalize_agent_name(class_name)
                
                # Si le nom normalisé correspond
                if class_normalized == normalized_name or (class_normalized.endswith("agent") and class_normalized[:-5] == normalized_name):
                    # Construire le chemin du module
                    rel_path = agent_dir.relative_to(base_dir.parent)
                    module_path = str(rel_path).replace("/", ".").replace("\\", ".")
                    
                    # Ajouter ".{filename sans extension}"
                    module_path += f".{py_file.stem}"
                    
                    logger.info(f"Agent trouvé! Module: {module_path}, Classe: {class_name}")
                    
                    # Mettre en cache et retourner
                    AGENT_PATHS_CACHE[normalized_name] = (module_path, class_name)
                    return module_path, class_name
    
    # Pas trouvé, recherche générique dans tous les dossiers d'agents
    logger.info("Recherche avancée dans tous les dossiers d'agents...")
    
    for agent_dir in base_dir.iterdir():
        if not agent_dir.is_dir() or agent_dir.name.startswith("__"):
            continue
            
        for py_file in agent_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # Lire le contenu pour trouver les classes
            with open(py_file, "r") as f:
                content = f.read()
                
            # Rechercher les classes qui héritent de Agent
            class_matches = re.findall(r'class\s+(\w+)\s*\([^)]*Agent', content)
            
            if not class_matches:
                continue
                
            # Vérifier si l'une des classes correspond à notre agent
            for class_name in class_matches:
                class_normalized = normalize_agent_name(class_name)
                
                # Si le nom normalisé correspond
                if class_normalized == normalized_name or (class_normalized.endswith("agent") and class_normalized[:-5] == normalized_name):
                    # Construire le chemin du module
                    rel_path = agent_dir.relative_to(base_dir.parent)
                    module_path = str(rel_path).replace("/", ".").replace("\\", ".")
                    
                    # Ajouter ".{filename sans extension}"
                    module_path += f".{py_file.stem}"
                    
                    logger.info(f"Agent trouvé dans la recherche avancée! Module: {module_path}, Classe: {class_name}")
                    
                    # Mettre en cache et retourner
                    AGENT_PATHS_CACHE[normalized_name] = (module_path, class_name)
                    return module_path, class_name
    
    # Toujours pas trouvé
    logger.warning(f"Agent '{agent_name}' introuvable après recherche approfondie")
    AGENT_PATHS_CACHE[normalized_name] = (None, None)
    return None, None

def load_agent_class(agent_name: str) -> Optional[type]:
    """
    Charge la classe d'un agent de manière robuste
    
    Args:
        agent_name: Nom de l'agent à charger
        
    Returns:
        Classe d'agent ou None si non trouvée
    """
    module_path, class_name = find_agent_file(agent_name)
    
    if not module_path or not class_name:
        return None
        
    try:
        module = importlib.import_module(module_path)
        if not hasattr(module, class_name):
            logger.error(f"Module {module_path} trouvé mais ne contient pas la classe {class_name}")
            return None
            
        agent_class = getattr(module, class_name)
        logger.info(f"Classe {class_name} chargée depuis {module_path}")
        return agent_class
        
    except ImportError as e:
        logger.error(f"Erreur lors de l'importation du module {module_path}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'agent {agent_name}: {str(e)}")
        return None

def get_all_agent_classes() -> Dict[str, type]:
    """
    Découvre et charge toutes les classes d'agents disponibles
    
    Returns:
        Dictionnaire {nom_agent: classe_agent}
    """
    base_dir = Path("/root/berinia/infra-ia/agents")
    agents = {}
    
    # Parcourir tous les dossiers d'agents
    for agent_dir in base_dir.iterdir():
        if not agent_dir.is_dir() or agent_dir.name.startswith("__"):
            continue
            
        # Parcourir tous les fichiers Python
        for py_file in agent_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # Lire le contenu pour trouver les classes
            with open(py_file, "r") as f:
                content = f.read()
                
            # Rechercher les classes qui héritent de Agent
            class_matches = re.findall(r'class\s+(\w+)\s*\([^)]*Agent', content)
            
            if not class_matches:
                continue
                
            # Traiter chaque classe
            for class_name in class_matches:
                # Construire le chemin du module
                rel_path = agent_dir.relative_to(base_dir.parent)
                module_path = str(rel_path).replace("/", ".").replace("\\", ".")
                
                # Ajouter ".{filename sans extension}"
                module_path += f".{py_file.stem}"
                
                # Tenter de charger la classe
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, class_name):
                        agent_class = getattr(module, class_name)
                        agents[class_name] = agent_class
                        logger.info(f"Agent découvert: {class_name} dans {module_path}")
                        
                        # Mettre en cache
                        normalized_name = normalize_agent_name(class_name)
                        AGENT_PATHS_CACHE[normalized_name] = (module_path, class_name)
                except ImportError:
                    logger.warning(f"Impossible d'importer {module_path}")
                except Exception as e:
                    logger.warning(f"Erreur lors du chargement de {class_name} depuis {module_path}: {str(e)}")
    
    return agents

def create_agent_instance(agent_name: str) -> Optional[Any]:
    """
    Crée une instance d'agent de manière robuste
    
    Args:
        agent_name: Nom de l'agent à instancier
        
    Returns:
        Instance de l'agent ou None en cas d'échec
    """
    agent_class = load_agent_class(agent_name)
    
    if not agent_class:
        return None
        
    try:
        agent_instance = agent_class()
        logger.info(f"Instance de {agent_name} créée avec succès")
        return agent_instance
    except Exception as e:
        logger.error(f"Erreur lors de l'instanciation de {agent_name}: {str(e)}")
        return None

# Initialisation automatique du cache au chargement du module
def _init_cache():
    """Initialise le cache des agents"""
    try:
        get_all_agent_classes()
        logger.info(f"Cache d'agents initialisé avec {len(AGENT_PATHS_CACHE)} entrées")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du cache d'agents: {str(e)}")

# À décommenter pour initialiser automatiquement le cache
# _init_cache()

"""
Décorateur de persistance automatique - Intercepte et sauvegarde automatiquement les données des agents
"""
import functools
import logging
from typing import Dict, Any, Callable
from datetime import datetime

from core.persistence_service import persistence_service


def persist_automatically(func: Callable) -> Callable:
    """
    Décorateur qui intercepte automatiquement les résultats des agents et les persiste
    
    Usage:
        @persist_automatically
        def run(self, input_data):
            return result
    
    Args:
        func: Fonction à décorer (généralement la méthode run() d'un agent)
        
    Returns:
        Fonction wrappée avec persistance automatique
    """
    @functools.wraps(func)
    def wrapper(agent_instance, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Informations sur l'agent
        agent_name = getattr(agent_instance, 'name', 'UnknownAgent')
        action = input_data.get('action', 'run')
        
        # Log de démarrage
        logger = logging.getLogger("BerinIA-AutoPersistence")
        logger.info(f"[{agent_name}] Exécution avec auto-persistance: {action}")
        
        try:
            # Exécution de la fonction originale
            result = func(agent_instance, input_data)
            
            # Vérification si le résultat est valide pour la persistance
            if not isinstance(result, dict):
                logger.warning(f"[{agent_name}] Résultat non-dict, persistance ignorée")
                return result
            
            # Vérification si l'agent a désactivé l'auto-persistance
            agent_config = getattr(agent_instance, 'config', {})
            if agent_config.get('disable_auto_persistence', False):
                logger.info(f"[{agent_name}] Auto-persistance désactivée par configuration")
                return result
            
            # Vérification si le résultat indique un succès
            status = result.get('status', '')
            if status in ['error', 'failed', 'not_implemented']:
                logger.info(f"[{agent_name}] Pas de persistance pour status: {status}")
                return result
            
            # Persistance automatique
            try:
                enriched_result = persistence_service.persist_agent_data(
                    agent_name=agent_name,
                    action=action,
                    input_data=input_data,
                    result_data=result
                )
                
                # Log du succès de persistance
                persistence_info = enriched_result.get('persistence', {})
                if persistence_info.get('status') == 'success':
                    count = persistence_info.get('count', 0)
                    logger.info(f"[{agent_name}] ✅ Persistance réussie: {count} éléments sauvegardés")
                else:
                    logger.warning(f"[{agent_name}] ⚠️ Persistance partielle ou échec")
                
                return enriched_result
                
            except Exception as e:
                logger.error(f"[{agent_name}] ❌ Erreur persistance: {e}")
                # Retour du résultat original en cas d'erreur de persistance
                return result
                
        except Exception as e:
            logger.error(f"[{agent_name}] Erreur dans l'exécution: {e}")
            raise
    
    return wrapper


def enable_auto_persistence_for_agent(agent_class):
    """
    Décorateur de classe qui active automatiquement la persistance pour un agent
    
    Usage:
        @enable_auto_persistence_for_agent
        class MonAgent(Agent):
            def run(self, input_data):
                return result
    
    Args:
        agent_class: Classe d'agent à modifier
        
    Returns:
        Classe modifiée avec auto-persistance
    """
    # Sauvegarde de la méthode run originale
    original_run = agent_class.run
    
    # Application du décorateur
    agent_class.run = persist_automatically(original_run)
    
    # Ajout d'une méthode pour désactiver temporairement la persistance
    def disable_persistence_temporarily(self):
        """Désactive temporairement l'auto-persistance pour cet agent"""
        self.config['disable_auto_persistence'] = True
    
    def enable_persistence_temporarily(self):
        """Réactive l'auto-persistance pour cet agent"""
        self.config['disable_auto_persistence'] = False
    
    agent_class.disable_persistence_temporarily = disable_persistence_temporarily
    agent_class.enable_persistence_temporarily = enable_persistence_temporarily
    
    return agent_class


class PersistenceControl:
    """Contrôleur global de la persistance automatique"""
    
    def __init__(self):
        self.global_enabled = True
        self.agent_overrides = {}
        self.logger = logging.getLogger("BerinIA-PersistenceControl")
    
    def disable_globally(self):
        """Désactive la persistance automatique pour tous les agents"""
        self.global_enabled = False
        self.logger.info("🔒 Persistance automatique désactivée globalement")
    
    def enable_globally(self):
        """Active la persistance automatique pour tous les agents"""
        self.global_enabled = True
        self.logger.info("🔓 Persistance automatique activée globalement")
    
    def disable_for_agent(self, agent_name: str):
        """Désactive la persistance pour un agent spécifique"""
        self.agent_overrides[agent_name] = False
        self.logger.info(f"🔒 Persistance désactivée pour {agent_name}")
    
    def enable_for_agent(self, agent_name: str):
        """Active la persistance pour un agent spécifique"""
        self.agent_overrides[agent_name] = True
        self.logger.info(f"🔓 Persistance activée pour {agent_name}")
    
    def is_enabled_for_agent(self, agent_name: str) -> bool:
        """Vérifie si la persistance est activée pour un agent"""
        # Override spécifique à l'agent
        if agent_name in self.agent_overrides:
            return self.agent_overrides[agent_name]
        
        # Configuration globale
        return self.global_enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut de la persistance"""
        return {
            'global_enabled': self.global_enabled,
            'agent_overrides': self.agent_overrides.copy(),
            'persistence_stats': persistence_service.get_stats()
        }


# Instance globale du contrôleur
persistence_control = PersistenceControl()


def conditional_persist_automatically(func: Callable) -> Callable:
    """
    Version conditionnelle du décorateur qui respecte les configurations globales
    
    Args:
        func: Fonction à décorer
        
    Returns:
        Fonction wrappée avec persistance conditionnelle
    """
    @functools.wraps(func)
    def wrapper(agent_instance, input_data: Dict[str, Any]) -> Dict[str, Any]:
        agent_name = getattr(agent_instance, 'name', 'UnknownAgent')
        
        # Vérification si la persistance est activée pour cet agent
        if not persistence_control.is_enabled_for_agent(agent_name):
            # Exécution sans persistance
            return func(agent_instance, input_data)
        
        # Exécution avec persistance
        return persist_automatically(func)(agent_instance, input_data)
    
    return wrapper


# Fonction utilitaire pour appliquer rétroactivement la persistance
def apply_auto_persistence_to_existing_agents():
    """
    Applique la persistance automatique aux agents existants
    Cette fonction peut être appelée pour mettre à jour les agents déjà créés
    """
    import importlib
    import pkgutil
    from core.agent_base import Agent
    
    logger = logging.getLogger("BerinIA-AutoPersistence")
    
    try:
        # Import dynamique de tous les modules d'agents
        agents_package = importlib.import_module('agents')
        
        applied_count = 0
        
        for importer, modname, ispkg in pkgutil.iter_modules(agents_package.__path__, agents_package.__name__ + "."):
            try:
                module = importlib.import_module(modname)
                
                # Recherche des classes d'agents dans le module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    if (isinstance(attr, type) and 
                        issubclass(attr, Agent) and 
                        attr != Agent and
                        hasattr(attr, 'run')):
                        
                        # Application du décorateur si pas déjà appliqué
                        if not hasattr(attr.run, '__wrapped__'):
                            attr.run = conditional_persist_automatically(attr.run)
                            applied_count += 1
                            logger.info(f"✅ Auto-persistance appliquée à {attr.__name__}")
                        
            except Exception as e:
                logger.warning(f"Erreur lors du traitement du module {modname}: {e}")
        
        logger.info(f"🎯 Auto-persistance appliquée à {applied_count} agents")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'application automatique: {e}")

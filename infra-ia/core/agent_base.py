"""
Module de définition de la classe de base pour tous les agents du système BerinIA
"""
import os
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Import pour accéder aux définitions d'agents centralisées
try:
    from utils.agent_definitions import get_agent_definition
except ImportError:
    # Fallback si l'import échoue
    def get_agent_definition(agent_name: str) -> Optional[Dict[str, Any]]:
        return None

class Agent:
    """
    Classe de base pour tous les agents du système BerinIA
    
    Tous les agents héritent de cette classe et implémentent leur logique
    spécifique en surchargeant la méthode run().
    """
    
    def __init__(self, agent_name: str, config_path: Optional[str] = None):
        """
        Initialise un agent avec son nom et sa configuration
        
        Args:
            agent_name: Le nom unique de l'agent
            config_path: Le chemin vers le fichier de configuration JSON
        """
        self.name = agent_name
        self.agent_id = str(uuid.uuid4())
        
        # CORRECTION : Utiliser les définitions centralisées au lieu de générer automatiquement
        if config_path:
            self.config_path = config_path
        else:
            # Tenter de récupérer le chemin depuis les définitions centralisées
            agent_def = get_agent_definition(agent_name)
            if agent_def and agent_def.get("config_path"):
                self.config_path = agent_def["config_path"]
            else:
                # Fallback avec conversion intelligente du nom
                folder_name = self._convert_agent_name_to_folder(agent_name)
                self.config_path = f"agents/{folder_name}/config.json"
        
        # Dériver le prompt_path depuis le config_path
        config_path_obj = Path(self.config_path)
        self.prompt_path = str(config_path_obj.parent / "prompt.txt")
        
        # Création du timestamp de démarrage
        self.start_timestamp = datetime.now().isoformat()
        
        # Chargement de la configuration
        self.config = self.load_config()
    
    def _convert_agent_name_to_folder(self, agent_name: str) -> str:
        """
        Convertit intelligemment un nom d'agent en nom de dossier
        
        Args:
            agent_name: Nom de l'agent (ex: "LoggerAgent", "FollowUpAgent")
            
        Returns:
            Nom de dossier approprié (ex: "logger", "follow_up")
        """
        # Supprimer le suffixe "Agent" s'il existe
        name = agent_name
        if name.endswith("Agent"):
            name = name[:-5]
        
        # Convertir PascalCase en snake_case
        import re
        # Insérer un underscore avant chaque majuscule qui suit une minuscule
        name = re.sub(r'(?<!^)(?=[A-Z][a-z])', '_', name)
        # Convertir en minuscules
        name = name.lower()
        
        return name
        
    def load_config(self) -> Dict[str, Any]:
        """
        Charge la configuration de l'agent depuis le fichier JSON
        
        Returns:
            Dictionnaire de configuration
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                # CORRECTION : Ne plus créer automatiquement de dossiers
                # Utiliser une configuration par défaut en mémoire uniquement
                print(f"ATTENTION: Fichier de configuration manquant pour {self.name}: {self.config_path}")
                print(f"L'agent fonctionnera avec une configuration par défaut en mémoire.")
                return {"name": self.name}
                
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration de {self.name}: {e}")
            return {"name": self.name}
    
    def update_config(self, key: str, value: Any) -> None:
        """
        Met à jour une valeur dans la configuration et sauvegarde
        
        Args:
            key: La clé à modifier
            value: La nouvelle valeur
        """
        self.config[key] = value
        
        try:
            config_file = Path(self.config_path)
            
            # CORRECTION : Seulement créer le dossier si le fichier config existe déjà
            # ou si on est dans un agent défini officiellement
            agent_def = get_agent_definition(self.name)
            if config_file.exists() or agent_def:
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, "w") as f:
                    json.dump(self.config, f, indent=2)
            else:
                print(f"ATTENTION: Tentative de sauvegarde pour un agent non défini officiellement: {self.name}")
                print(f"Configuration sauvegardée en mémoire uniquement.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration de {self.name}: {e}")
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        """
        Construit le prompt pour le LLM en utilisant le template et les variables
        
        Args:
            context: Contexte spécifique pour le prompt
            
        Returns:
            Le prompt formaté
        """
        try:
            prompt_file = Path(self.prompt_path)
            if not prompt_file.exists():
                return f"Tu es un agent nommé {self.name}. Réponds en JSON."
                
            with open(prompt_file, "r") as f:
                template = f.read()
                
            # Fusion du contexte et de la configuration pour le format
            format_vars = {**self.config, **context}
            
            return template.format(**format_vars)
        except Exception as e:
            print(f"Erreur lors de la construction du prompt de {self.name}: {e}")
            return f"Tu es un agent nommé {self.name}. Réponds en JSON."
    
    def speak(self, message: str, target: Optional[str] = None, context_id: Optional[str] = None, level: str = "INFO") -> None:
        """
        Envoie un message dans le canal de communication des agents - NOUVEAU SYSTÈME UNIFIÉ

        Args:
            message: Le message à envoyer
            target: L'agent destinataire (None pour broadcast)
            context_id: ID de contexte (campagne, niche, etc.)
            level: Niveau de log (INFO, WARNING, ERROR, DEBUG)
        """
        try:
            # Utilisation du nouveau système unifié PostgreSQL + fichiers avec rotation
            from utils.unified_logging import unified_logger
            
            unified_logger.agent_message(
                agent_name=self.name,
                message=message,
                target=target,
                level=level,
                context_id=context_id
            )
            
        except Exception as e:
            # Fallback vers le print en cas d'erreur critique
            print(f"[{self.name}] → {target or 'ALL'}: {message} (Logging error: {e})")
    
    def log_system(self, message: str, level: str = "INFO", details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log un message système de l'agent
        
        Args:
            message: Message à logger
            level: Niveau du log (INFO, WARNING, ERROR, DEBUG)
            details: Détails supplémentaires en JSON
        """
        try:
            from utils.unified_logging import unified_logger
            
            unified_logger.system_message(
                module=self.name,
                message=message,
                level=level,
                details=details
            )
            
        except Exception as e:
            print(f"[{self.name}] System log error: {e}")
    
    def log_error(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Méthode de convenance pour logger une erreur"""
        self.log_system(message, "ERROR", details)
    
    def log_warning(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Méthode de convenance pour logger un avertissement"""
        self.log_system(message, "WARNING", details)
    
    def log_info(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Méthode de convenance pour logger une information"""
        self.log_system(message, "INFO", details)
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Méthode principale qui exécute la logique de l'agent
        
        À surcharger dans chaque agent concret.
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        # Implémentation par défaut - à surcharger
        return {
            "status": "not_implemented",
            "agent": self.name,
            "message": "Méthode run() non implémentée dans cet agent."
        }

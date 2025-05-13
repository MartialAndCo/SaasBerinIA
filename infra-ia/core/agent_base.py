"""
Module de définition de la classe de base pour tous les agents du système BerinIA
"""
import os
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from utils.logger import agent_message

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
        self.config_path = config_path or f"agents/{agent_name.lower()}/config.json"
        self.prompt_path = f"agents/{agent_name.lower()}/prompt.txt"
        
        # Création du timestamp de démarrage
        self.start_timestamp = datetime.now().isoformat()
        
        # Chargement de la configuration
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """
        Charge la configuration de l'agent depuis le fichier JSON
        
        Returns:
            Dictionnaire de configuration
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                # Création d'une configuration par défaut
                default_config = {"name": self.name}
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, "w") as f:
                    json.dump(default_config, f, indent=2)
                return default_config
                
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
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w") as f:
                json.dump(self.config, f, indent=2)
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
        Envoie un message dans le canal de communication des agents

        Args:
            message: Le message à envoyer
            target: L'agent destinataire (None pour broadcast)
            context_id: ID de contexte (campagne, niche, etc.)
            level: Niveau de log (INFO, WARNING, ERROR, DEBUG)
        """
        from agents.logger.logger_agent import LoggerAgent
        from utils.logger import agent_message as new_agent_message

        # Log via l'ancien système (compatibilité)
        LoggerAgent.log_interaction(
            from_agent=self.name,
            to_agent=target,
            message=message,
            context_id=context_id,
            metadata={"level": level}
        )
        
        # Log via le nouveau système directement
        try:
            new_agent_message(self.name, message, target, level)
        except Exception as e:
            print(f"Erreur lors du logging via le nouveau système: {str(e)}")
    
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

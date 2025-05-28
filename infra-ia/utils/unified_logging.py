"""
Système de logging unifié pour BerinIA
Écrit simultanément dans PostgreSQL ET dans les fichiers avec rotation

Ce module remplace le système défaillant et unifie tous les logs.
"""
import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from utils.logging_config import get_logger, CustomRotatingFileHandler

class UnifiedLogger:
    """
    Logger unifié qui écrit dans PostgreSQL + fichiers avec rotation
    """
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000/api"
        self.fallback_logger = get_logger("UnifiedLogger")
        
        # Configuration pour les fichiers avec rotation
        self.logs_dir = "/root/berinia/infra-ia/logs"
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Configuration du logger avec rotation
        self._setup_file_logging()
    
    def _setup_file_logging(self):
        """Configure le logging avec rotation pour les fichiers"""
        
        # Logger pour les agents avec rotation
        self.agents_logger = logging.getLogger("BerinIA.UnifiedAgents")
        if not self.agents_logger.handlers:
            agents_handler = CustomRotatingFileHandler(
                os.path.join(self.logs_dir, "agents.log"),
                maxBytes=150*1024,  # 150KB ~1000 lignes
                backupCount=5
            )
            agents_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s"
            ))
            self.agents_logger.addHandler(agents_handler)
            self.agents_logger.setLevel(logging.INFO)
        
        # Logger pour le système avec rotation
        self.system_logger = logging.getLogger("BerinIA.UnifiedSystem")
        if not self.system_logger.handlers:
            system_handler = CustomRotatingFileHandler(
                os.path.join(self.logs_dir, "system.log"),
                maxBytes=150*1024,  # 150KB ~1000 lignes
                backupCount=5
            )
            system_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s"
            ))
            self.system_logger.addHandler(system_handler)
            self.system_logger.setLevel(logging.INFO)
        
        # Logger pour les erreurs avec rotation
        self.error_logger = logging.getLogger("BerinIA.UnifiedErrors")
        if not self.error_logger.handlers:
            error_handler = CustomRotatingFileHandler(
                os.path.join(self.logs_dir, "error.log"),
                maxBytes=150*1024,  # 150KB ~1000 lignes
                backupCount=5
            )
            error_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s"
            ))
            self.error_logger.addHandler(error_handler)
            self.error_logger.setLevel(logging.ERROR)
    
    def _write_to_postgresql(
        self, 
        level: str, 
        source: str, 
        message: str,
        agent_name: Optional[str] = None,
        module: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context_id: Optional[str] = None
    ) -> bool:
        """Écrit un log dans PostgreSQL via l'API"""
        try:
            log_data = {
                "level": level,
                "source": source,
                "agent_name": agent_name,
                "module": module,
                "message": message,
                "details": details,
                "context_id": context_id
            }
            
            response = requests.post(
                f"{self.api_base_url}/system-logs/",
                json=log_data,
                timeout=5
            )
            
            return response.status_code == 200
            
        except Exception as e:
            # Fallback en cas d'erreur API
            self.fallback_logger.error(f"Erreur PostgreSQL logging: {e}")
            return False
    
    def _write_to_file(self, level: str, source: str, message: str, agent_name: Optional[str] = None):
        """Écrit un log dans les fichiers avec rotation"""
        try:
            # Format du message
            if agent_name:
                formatted_message = f"[{agent_name}] {message}"
            else:
                formatted_message = message
            
            # Sélection du logger selon le niveau et la source
            if level == "ERROR":
                self.error_logger.error(formatted_message)
            
            if source == "agent" or agent_name:
                if level == "ERROR":
                    self.agents_logger.error(formatted_message)
                elif level == "WARNING":
                    self.agents_logger.warning(formatted_message)
                elif level == "DEBUG":
                    self.agents_logger.debug(formatted_message)
                else:
                    self.agents_logger.info(formatted_message)
            else:
                if level == "ERROR":
                    self.system_logger.error(formatted_message)
                elif level == "WARNING":
                    self.system_logger.warning(formatted_message)
                elif level == "DEBUG":
                    self.system_logger.debug(formatted_message)
                else:
                    self.system_logger.info(formatted_message)
                    
        except Exception as e:
            self.fallback_logger.error(f"Erreur file logging: {e}")
    
    def log(
        self,
        level: str,
        source: str,
        message: str,
        agent_name: Optional[str] = None,
        module: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context_id: Optional[str] = None
    ):
        """
        Méthode principale de logging unifié
        
        Args:
            level: Niveau du log (INFO, WARNING, ERROR, DEBUG)
            source: Source du log (agent, system, api, webhook, etc.)
            message: Message du log
            agent_name: Nom de l'agent (si applicable)
            module: Module/composant qui émet le log
            details: Détails supplémentaires en JSON
            context_id: ID de contexte (campagne, session, etc.)
        """
        
        # 1. Écriture dans PostgreSQL (prioritaire)
        postgresql_success = self._write_to_postgresql(
            level=level,
            source=source,
            message=message,
            agent_name=agent_name,
            module=module,
            details=details,
            context_id=context_id
        )
        
        # 2. Écriture dans les fichiers avec rotation (toujours)
        self._write_to_file(level, source, message, agent_name)
        
        # 3. Fallback si PostgreSQL échoue
        if not postgresql_success:
            self.fallback_logger.warning(f"PostgreSQL logging failed for: {message[:100]}...")
    
    def agent_message(
        self,
        agent_name: str,
        message: str,
        target: Optional[str] = None,
        level: str = "INFO",
        context_id: Optional[str] = None
    ):
        """
        Log un message d'agent (remplace l'ancien speak())
        
        Args:
            agent_name: Nom de l'agent qui émet
            message: Message de l'agent
            target: Agent destinataire (optionnel)
            level: Niveau du log
            context_id: ID de contexte
        """
        
        # Format du message avec destinataire
        if target:
            formatted_message = f"{agent_name} → {target}: {message}"
        else:
            formatted_message = f"{agent_name}: {message}"
        
        # Détails supplémentaires
        details = {
            "from_agent": agent_name,
            "to_agent": target,
            "interaction_type": "agent_communication"
        }
        
        self.log(
            level=level,
            source="agent",
            message=formatted_message,
            agent_name=agent_name,
            module="communication",
            details=details,
            context_id=context_id
        )
    
    def system_message(
        self,
        module: str,
        message: str,
        level: str = "INFO",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log un message système
        
        Args:
            module: Module système qui émet
            message: Message système
            level: Niveau du log
            details: Détails supplémentaires
        """
        
        self.log(
            level=level,
            source="system",
            message=message,
            module=module,
            details=details
        )
    
    def error(self, message: str, module: str = "system", details: Optional[Dict[str, Any]] = None):
        """Log une erreur"""
        self.log("ERROR", "system", message, module=module, details=details)
    
    def warning(self, message: str, module: str = "system", details: Optional[Dict[str, Any]] = None):
        """Log un avertissement"""
        self.log("WARNING", "system", message, module=module, details=details)
    
    def info(self, message: str, module: str = "system", details: Optional[Dict[str, Any]] = None):
        """Log une information"""
        self.log("INFO", "system", message, module=module, details=details)
    
    def debug(self, message: str, module: str = "system", details: Optional[Dict[str, Any]] = None):
        """Log un message de debug"""
        self.log("DEBUG", "system", message, module=module, details=details)

# Instance unique du logger unifié
unified_logger = UnifiedLogger()

# Fonctions de convenance pour compatibilité
def agent_message(agent_name: str, message: str, target: Optional[str] = None, level: str = "INFO"):
    """Fonction de convenance pour les messages d'agents"""
    unified_logger.agent_message(agent_name, message, target, level)

def system_message(module: str, message: str, level: str = "INFO", details: Optional[Dict[str, Any]] = None):
    """Fonction de convenance pour les messages système"""
    unified_logger.system_message(module, message, level, details)

def log_error(message: str, module: str = "system", details: Optional[Dict[str, Any]] = None):
    """Fonction de convenance pour les erreurs"""
    unified_logger.error(message, module, details)

def log_warning(message: str, module: str = "system", details: Optional[Dict[str, Any]] = None):
    """Fonction de convenance pour les avertissements"""
    unified_logger.warning(message, module, details)

def log_info(message: str, module: str = "system", details: Optional[Dict[str, Any]] = None):
    """Fonction de convenance pour les informations"""
    unified_logger.info(message, module, details)

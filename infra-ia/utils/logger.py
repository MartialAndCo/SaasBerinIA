"""
Module de logging centralisé pour le système BerinIA.

Ce module fournit une interface unifiée pour le logging dans tout le système
avec support pour:
- Colorisation des logs en console
- Rotation automatique des fichiers
- Séparation par niveau de log
- Formatage standardisé
"""
import os
import sys
import logging
import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any, Optional, List, Union

# Configuration par défaut
DEFAULT_CONFIG = {
    "logs_dir": "logs",
    "console_level": "INFO",
    "file_level": "DEBUG",
    "max_file_size_mb": 10,
    "backup_count": 5,
    "enable_colors": True
}

# ANSI color codes for terminal coloring
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GREY = "\033[90m"
    
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

class ColoredFormatter(logging.Formatter):
    """
    Formateur personnalisé qui ajoute des couleurs aux logs en console
    """
    
    # Mapping des niveaux de log aux couleurs
    COLORS = {
        logging.DEBUG: Colors.GREY,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BG_RED + Colors.WHITE
    }
    
    def __init__(self, fmt=None, datefmt=None, style='%', use_colors=True):
        super().__init__(fmt, datefmt, style)
        self.use_colors = use_colors
    
    def format(self, record):
        # Backup du formatMessage original
        orig_msg = record.msg
        orig_levelname = record.levelname
        
        if self.use_colors:
            # Ajouter des couleurs au niveau
            color = self.COLORS.get(record.levelno, Colors.RESET)
            record.levelname = f"{color}{record.levelname:8}{Colors.RESET}"
            
            # Si c'est un message d'un agent, formater spécialement 
            if hasattr(record, 'agent_message') and record.agent_message:
                if hasattr(record, 'target_agent') and record.target_agent:
                    record.msg = f"{Colors.CYAN}{record.agent_name}{Colors.RESET} → " + \
                                f"{Colors.MAGENTA}{record.target_agent}{Colors.RESET}: {record.msg}"
                else:
                    record.msg = f"{Colors.CYAN}{record.agent_name}{Colors.RESET}: {record.msg}"
        
        # Appel au formateur standard
        result = super().format(record)
        
        # Restauration des valeurs originales
        record.msg = orig_msg
        record.levelname = orig_levelname
        
        return result

class AgentFilter(logging.Filter):
    """
    Filtre pour sélectionner uniquement les logs venant des agents
    """
    def filter(self, record):
        return hasattr(record, 'agent_message') and record.agent_message

class WebhookFilter(logging.Filter):
    """
    Filtre pour sélectionner uniquement les logs liés aux webhooks
    """
    def filter(self, record):
        return hasattr(record, 'webhook') and record.webhook

class BeriniLogger:
    """
    Service centralisé de logging pour BerinIA
    """
    
    # Stockage de l'instance unique (singleton pattern)
    _instance = None
    
    @classmethod
    def get_instance(cls, config=None):
        """
        Récupère l'instance unique du logger
        
        Args:
            config: Configuration optionnelle
            
        Returns:
            Instance unique du logger
        """
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def __init__(self, config=None):
        """
        Initialisation du logger
        
        Args:
            config: Configuration optionnelle
        """
        # Fusionner avec la configuration par défaut
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # Créer le dossier de logs s'il n'existe pas
        self.logs_dir = self.config.get("logs_dir", "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(os.path.join(self.logs_dir, "archives"), exist_ok=True)
        
        # Configuration du logger principal
        self.logger = logging.getLogger("BerinIA")
        self.logger.setLevel(logging.DEBUG)  # Niveau le plus bas, filtrage par handlers
        
        # Éviter les logs en double si déjà configuré
        if not self.logger.handlers:
            self._setup_logging()
    
    def _setup_logging(self):
        """
        Configure tous les handlers de logs
        """
        # Niveaux de log
        console_level = getattr(logging, self.config.get("console_level", "INFO"))
        file_level = getattr(logging, self.config.get("file_level", "DEBUG"))
        
        # Taille maximale des fichiers et nombre de backups
        max_size = self.config.get("max_file_size_mb", 10) * 1024 * 1024  # En octets
        backup_count = self.config.get("backup_count", 5)
        enable_colors = self.config.get("enable_colors", True)
        
        # 1. Handler console avec couleurs
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_format = "%(asctime)s | %(levelname)-8s | %(message)s"
        console_formatter = ColoredFormatter(
            console_format, 
            datefmt="%H:%M:%S",
            use_colors=enable_colors
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 2. Handler fichier principal (system.log)
        system_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        system_formatter = logging.Formatter(system_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        system_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, "system.log"),
            maxBytes=max_size,
            backupCount=backup_count
        )
        system_handler.setLevel(file_level)
        system_handler.setFormatter(system_formatter)
        self.logger.addHandler(system_handler)
        
        # 3. Handler pour les erreurs (error.log)
        error_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, "error.log"),
            maxBytes=max_size,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(system_formatter)
        self.logger.addHandler(error_handler)
        
        # 4. Handler pour les agents (agents.log)
        agent_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, "agents.log"),
            maxBytes=max_size,
            backupCount=backup_count
        )
        agent_handler.setLevel(file_level)
        agent_handler.setFormatter(system_formatter)
        agent_handler.addFilter(AgentFilter())
        self.logger.addHandler(agent_handler)
        
        # 5. Handler pour les webhooks (webhook.log)
        webhook_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, "webhook.log"),
            maxBytes=max_size,
            backupCount=backup_count
        )
        webhook_handler.setLevel(file_level)
        webhook_handler.setFormatter(system_formatter)
        webhook_handler.addFilter(WebhookFilter())
        self.logger.addHandler(webhook_handler)
    
    def get_logger(self, name=None):
        """
        Récupère un logger nommé qui hérite de la configuration principale
        
        Args:
            name: Nom du logger (optionnel)
            
        Returns:
            Logger configuré
        """
        if name:
            return logging.getLogger(f"BerinIA.{name}")
        return self.logger
    
    def debug(self, message, *args, **kwargs):
        """Log un message DEBUG"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """Log un message INFO"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """Log un message WARNING"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """Log un message ERROR"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """Log un message CRITICAL"""
        self.logger.critical(message, *args, **kwargs)
    
    def agent_message(self, agent_name, message, target_agent=None, level="INFO"):
        """
        Log un message d'agent
        
        Args:
            agent_name: Nom de l'agent émetteur
            message: Message à logger
            target_agent: Agent destinataire (optionnel)
            level: Niveau de log (INFO par défaut)
        """
        level_func = getattr(self.logger, level.lower(), self.logger.info)
        extra = {
            "agent_message": True,
            "agent_name": agent_name,
            "target_agent": target_agent
        }
        level_func(message, extra=extra)
    
    def webhook_event(self, source, event_type, message, level="INFO"):
        """
        Log un événement webhook
        
        Args:
            source: Source du webhook (Twilio, Mailgun, etc.)
            event_type: Type d'événement
            message: Description de l'événement
            level: Niveau de log (INFO par défaut)
        """
        full_message = f"[{source}] {event_type}: {message}"
        level_func = getattr(self.logger, level.lower(), self.logger.info)
        extra = {
            "webhook": True,  # Correction ici: ajout de l'attribut webhook=True
            "webhook_source": source,
            "webhook_event": event_type
        }
        level_func(full_message, extra=extra)

# Fonction d'accès global au logger
def get_logger(name=None, config=None):
    """
    Récupère une instance du logger
    
    Args:
        name: Nom du logger (optionnel)
        config: Configuration optionnelle
        
    Returns:
        Instance du logger
    """
    instance = BeriniLogger.get_instance(config)
    return instance.get_logger(name)

# Fonctions d'aide globales
def debug(message, *args, **kwargs):
    """Log un message DEBUG"""
    get_logger().debug(message, *args, **kwargs)

def info(message, *args, **kwargs):
    """Log un message INFO"""
    get_logger().info(message, *args, **kwargs)

def warning(message, *args, **kwargs):
    """Log un message WARNING"""
    get_logger().warning(message, *args, **kwargs)

def error(message, *args, **kwargs):
    """Log un message ERROR"""
    get_logger().error(message, *args, **kwargs)

def critical(message, *args, **kwargs):
    """Log un message CRITICAL"""
    get_logger().critical(message, *args, **kwargs)

def agent_message(agent_name, message, target_agent=None, level="INFO"):
    """Log un message d'agent"""
    instance = BeriniLogger.get_instance()
    instance.agent_message(agent_name, message, target_agent, level)

def webhook_event(source, event_type, message, level="INFO"):
    """Log un événement webhook"""
    instance = BeriniLogger.get_instance()
    instance.webhook_event(source, event_type, message, level)

# Initialisation du logger par défaut
logger = get_logger()

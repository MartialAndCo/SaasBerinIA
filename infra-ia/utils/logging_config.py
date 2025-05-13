"""
Configuration centralisée du système de logs pour BerinIA.

Ce module définit une configuration de logging unifiée pour tout le système,
évitant la duplication et la confusion entre différents fichiers de logs.
"""
import os
import logging
import shutil
from logging.handlers import RotatingFileHandler
from datetime import datetime

class CustomRotatingFileHandler(RotatingFileHandler):
    """
    Gestionnaire de fichiers de logs personnalisé qui déplace les fichiers
    rotés dans un sous-dossier 'archives' plutôt que de les conserver 
    dans le même dossier que le fichier actif.
    """
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, 
                 encoding=None, delay=False, errors=None):
        # Créer le dossier archives s'il n'existe pas
        self.base_dir = os.path.dirname(filename)
        self.archive_dir = os.path.join(self.base_dir, "archives")
        os.makedirs(self.archive_dir, exist_ok=True)
        
        # Initialiser le handler parent
        super().__init__(filename, mode, maxBytes, backupCount, 
                         encoding, delay, errors)
    
    def doRollover(self):
        """
        Redéfinition de la méthode de rotation pour déplacer les fichiers
        dans le sous-dossier archives au lieu de les conserver dans le
        dossier principal.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
            
        # Rotation du fichier principal
        if self.backupCount > 0:
            # Gérer les anciens fichiers d'abord (ceux qui sont déjà dans le dossier archives)
            for i in range(self.backupCount - 1, 0, -1):
                # Chemins dans le dossier archives
                sfn_archive = os.path.join(self.archive_dir, f"{os.path.basename(self.baseFilename)}.{i}")
                dfn_archive = os.path.join(self.archive_dir, f"{os.path.basename(self.baseFilename)}.{i+1}")
                
                if os.path.exists(sfn_archive):
                    if os.path.exists(dfn_archive):
                        os.remove(dfn_archive)
                    os.rename(sfn_archive, dfn_archive)
            
            # Gérer ensuite les fichiers dans le dossier principal (ceux de précédentes rotations qui n'ont pas été déplacés)
            for i in range(self.backupCount - 1, 0, -1):
                sfn_main = f"{self.baseFilename}.{i}"
                if os.path.exists(sfn_main):
                    # Si le fichier existe dans le dossier principal, le déplacer vers archives
                    dfn_archive = os.path.join(self.archive_dir, f"{os.path.basename(self.baseFilename)}.{i+1}")
                    if os.path.exists(dfn_archive):
                        os.remove(dfn_archive)
                    # Déplacer le fichier vers archives avec le nouveau numéro
                    shutil.move(sfn_main, dfn_archive)
            
            # Créer le nouveau fichier .1 dans le dossier archives à partir du fichier courant
            dfn_archive_1 = os.path.join(self.archive_dir, f"{os.path.basename(self.baseFilename)}.1")
            if os.path.exists(dfn_archive_1):
                os.remove(dfn_archive_1)
            
            # Copier le fichier courant vers archives/.1
            shutil.copy2(self.baseFilename, dfn_archive_1)
            
            # Tronquer le fichier courant
            with open(self.baseFilename, 'w'):
                pass
                
        # Recréer le stream
        if not self.delay:
            self.stream = self._open()

# Chemin racine pour les logs (un seul dossier)
LOGS_DIR = "/root/berinia/infra-ia/logs"

# S'assurer que le dossier existe
os.makedirs(LOGS_DIR, exist_ok=True)

# Noms des fichiers de logs principaux
SYSTEM_LOG = os.path.join(LOGS_DIR, "system.log")
AGENTS_LOG = os.path.join(LOGS_DIR, "agents.log")
ERROR_LOG = os.path.join(LOGS_DIR, "error.log")
WEBHOOK_LOG = os.path.join(LOGS_DIR, "webhook.log") 
WHATSAPP_LOG = os.path.join(LOGS_DIR, "whatsapp.log")
AGENT_INTERACTIONS_LOG = os.path.join(LOGS_DIR, "agent_interactions.jsonl")

# Format des logs
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
VERBOSE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

def setup_logging(service_name, log_level=logging.INFO):
    """
    Configure le système de logging pour un service spécifique.
    
    Args:
        service_name: Nom du service (ex: 'webhook', 'whatsapp', etc.)
        log_level: Niveau de logging (default: INFO)
        
    Returns:
        Logger configuré
    """
    # Réinitialiser les handlers existants
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configurer le logger racine
    root_logger.setLevel(log_level)
    
    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(console_handler)
    
    # Handler pour le fichier système avec rotation (~1000 lignes)
    system_handler = CustomRotatingFileHandler(
        SYSTEM_LOG,
        maxBytes=150*1024,  # ~150 KB (~1000 lignes)
        backupCount=5       # Garder 5 fichiers de backup
    )
    system_handler.setLevel(log_level)
    system_handler.setFormatter(logging.Formatter(VERBOSE_FORMAT))
    root_logger.addHandler(system_handler)
    
    # Handler pour les erreurs avec rotation (~1000 lignes)
    error_handler = CustomRotatingFileHandler(
        ERROR_LOG,
        maxBytes=150*1024,  # ~150 KB (~1000 lignes)
        backupCount=5       # Garder 5 fichiers de backup
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(VERBOSE_FORMAT))
    root_logger.addHandler(error_handler)
    
    # Fichier de log spécifique au service
    if service_name == 'webhook':
        service_log = WEBHOOK_LOG
    elif service_name == 'whatsapp':
        service_log = WHATSAPP_LOG
    elif service_name in ['agent', 'agents']:
        service_log = AGENTS_LOG
    else:
        # Pour les autres services, créer un fichier dédié
        service_log = os.path.join(LOGS_DIR, f"{service_name}.log")
    
    # Handler pour le service spécifique avec rotation (~1000 lignes)
    service_handler = CustomRotatingFileHandler(
        service_log,
        maxBytes=150*1024,  # ~150 KB (~1000 lignes)
        backupCount=5       # Garder 5 fichiers de backup
    )
    service_handler.setLevel(log_level)
    service_handler.setFormatter(logging.Formatter(VERBOSE_FORMAT))
    root_logger.addHandler(service_handler)
    
    # Créer et renvoyer un logger nommé
    logger = logging.getLogger(f"BerinIA.{service_name}")
    logger.setLevel(log_level)
    
    return logger

def get_logger(name, log_level=logging.INFO):
    """
    Récupère un logger déjà configuré ou en crée un nouveau.
    
    Args:
        name: Nom du logger (ex: 'webhook.processor')
        log_level: Niveau de logging (default: INFO)
        
    Returns:
        Logger configuré
    """
    # Si c'est la première partie du nom, configurer le système
    parts = name.split('.')
    service = parts[0]
    
    logger = logging.getLogger(f"BerinIA.{name}")
    logger.setLevel(log_level)
    
    # Si aucun handler n'est configuré, configurer le système
    if not logging.getLogger().handlers:
        setup_logging(service, log_level)
    
    return logger

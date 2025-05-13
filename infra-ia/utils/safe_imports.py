"""
Utilitaires pour l'importation sécurisée de modules optionnels.

Ce module fournit des fonctions permettant d'importer des modules
qui peuvent être absents du système, sans que cela ne provoque d'erreur.
"""
import importlib
import logging
from typing import Any, Optional

logger = logging.getLogger("BerinIA.SafeImports")

def safe_import(module_name: str) -> Optional[Any]:
    """
    Importe un module de manière sécurisée.
    
    Args:
        module_name: Nom du module à importer
        
    Returns:
        Le module importé ou None s'il n'est pas disponible
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        logger.warning(f"Module optionnel {module_name} non disponible. Certaines fonctionnalités seront limitées.")
        return None

# Imports sécurisés des modules optionnels utilisés par les agents
tldextract = safe_import("tldextract")
twilio = safe_import("twilio.rest")
playwright = safe_import("playwright.async_api")

# Vérifier quels modules optionnels sont disponibles
TLDEXTRACT_AVAILABLE = tldextract is not None
TWILIO_AVAILABLE = twilio is not None
PLAYWRIGHT_AVAILABLE = playwright is not None

def check_optional_dependencies() -> dict:
    """
    Vérifie quelles dépendances optionnelles sont disponibles.
    
    Returns:
        Dictionnaire des dépendances et leur disponibilité
    """
    return {
        "tldextract": TLDEXTRACT_AVAILABLE,
        "twilio": TWILIO_AVAILABLE,
        "playwright": PLAYWRIGHT_AVAILABLE
    }

def get_missing_dependencies() -> list:
    """
    Retourne la liste des dépendances optionnelles manquantes.
    
    Returns:
        Liste des noms de modules manquants
    """
    missing = []
    
    if not TLDEXTRACT_AVAILABLE:
        missing.append("tldextract")
    if not TWILIO_AVAILABLE:
        missing.append("twilio")
    if not PLAYWRIGHT_AVAILABLE:
        missing.append("playwright")
        
    return missing

def print_dependencies_status():
    """
    Affiche l'état des dépendances optionnelles dans les logs.
    """
    status = check_optional_dependencies()
    for name, available in status.items():
        logger.info(f"Dépendance {name}: {'DISPONIBLE' if available else 'MANQUANTE'}")
        
    if missing := get_missing_dependencies():
        logger.warning("Dépendances manquantes détectées. Pour les installer:")
        logger.warning("source venv/bin/activate && pip install " + " ".join(missing))

"""
Handlers pour le bot Telegram BerinIA
Ce module contient tous les gestionnaires de commandes et callbacks du bot
"""

# Import des handlers principaux
from .main_menu import get_handlers

# Les handlers spécifiques seront importés directement quand nécessaire
# pour éviter les erreurs d'import circulaire

__all__ = [
    'get_handlers',
]
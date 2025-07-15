"""Configuration pour le bot Telegram BerinIA"""
import os
from dotenv import load_dotenv
from typing import List

# Charger les variables d'environnement
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

# Configuration Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN manquant dans le fichier .env")

# IDs des administrateurs autorisés
ADMIN_IDS_STR = os.getenv('TELEGRAM_ADMIN_IDS', '')
TELEGRAM_ADMIN_IDS: List[int] = []
if ADMIN_IDS_STR:
    try:
        TELEGRAM_ADMIN_IDS = [int(id_str.strip()) for id_str in ADMIN_IDS_STR.split(',') if id_str.strip()]
    except ValueError:
        raise ValueError("Format incorrect pour TELEGRAM_ADMIN_IDS dans le fichier .env")

# Pour les notifications de paiement
ADMIN_CHAT_IDS = TELEGRAM_ADMIN_IDS

# URL de base de l'API BerinIA
API_BASE_URL = os.getenv('TELEGRAM_API_BASE_URL', 'http://localhost:8000/api')

# Configuration du logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Émojis pour les menus
EMOJIS = {
    'stats': '📊',
    'campaigns': '🎯',
    'leads': '👥',
    'niches': '📂',
    'system': '🧠',
    'back': '⬅️',
    'active': '✅',
    'inactive': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'success': '✅',
    'error': '❌',
    'loading': '⏳',
    'view': '🔍',
    'export': '📤',
    'start': '🚀',
    'stop': '🛑',
    'restart': '🔄',
    'add': '➕',
    'delete': '🗑️',
    'edit': '✏️'
}

# Messages par défaut
MESSAGES = {
    'welcome': """🤖 **Bienvenue sur BerinIA Bot !**

Votre interface de gestion du système BerinIA. 
Choisissez une option dans le menu ci-dessous :""",
    
    'unauthorized': "❌ Vous n'êtes pas autorisé à utiliser ce bot.",
    'error': "❌ Une erreur s'est produite : {error}",
    'loading': "⏳ Chargement en cours...",
    'no_data': "ℹ️ Aucune donnée disponible.",
    'action_confirmed': "✅ Action exécutée avec succès.",
    'action_cancelled': "❌ Action annulée.",
}

# Configuration des timeouts
REQUEST_TIMEOUT = 30  # secondes
CACHE_TIMEOUT = 300   # 5 minutes

print(f"Configuration chargée - Admin IDs: {TELEGRAM_ADMIN_IDS}")

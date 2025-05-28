"""
Script pour initialiser les paramètres système par défaut dans la base de données.
Ce script s'assure que tous les paramètres requis existent et ont des valeurs par défaut.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.system_setting import SystemSetting
from app.services.system_settings_service import SystemSettingsService

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Définition des paramètres système par défaut
DEFAULT_INTEGRATIONS = [
    # Twilio
    {
        "name": "twilio_account_sid",
        "value": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "data_type": "string",
        "category": "integrations",
        "description": "SID du compte Twilio pour l'intégration SMS"
    },
    {
        "name": "twilio_auth_token",
        "value": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "data_type": "string",
        "category": "integrations",
        "description": "Token d'authentification Twilio pour l'intégration SMS"
    },
    {
        "name": "twilio_integration_active",
        "value": os.getenv("TWILIO_INTEGRATION_ACTIVE", "false").lower(),
        "data_type": "boolean",
        "category": "integrations",
        "description": "Indique si l'intégration Twilio est active"
    },
    
    # Instantly.ai
    {
        "name": "instantly_api_key",
        "value": os.getenv("INSTANTLY_API_KEY", ""),
        "data_type": "string",
        "category": "integrations",
        "description": "Clé API Instantly.ai pour l'intégration email"
    },
    {
        "name": "instantly_integration_active",
        "value": os.getenv("INSTANTLY_INTEGRATION_ACTIVE", "false").lower(),
        "data_type": "boolean",
        "category": "integrations",
        "description": "Indique si l'intégration Instantly.ai est active"
    },
    
    # WhatsApp
    {
        "name": "whatsapp_integration_active",
        "value": os.getenv("WHATSAPP_INTEGRATION_ACTIVE", "false").lower(),
        "data_type": "boolean",
        "category": "integrations",
        "description": "Indique si l'intégration WhatsApp est active"
    },
    {
        "name": "whatsapp_notification_group",
        "value": os.getenv("WHATSAPP_NOTIFICATION_GROUP", ""),
        "data_type": "string",
        "category": "integrations",
        "description": "ID du groupe WhatsApp pour les notifications"
    }
]

DEFAULT_SCHEDULING = [
    {
        "name": "agent_frequency",
        "value": os.getenv("AGENT_FREQUENCY", "daily"),
        "data_type": "string",
        "category": "scheduling",
        "description": "Fréquence d'exécution des agents IA (manual, daily, weekly, custom-hours)"
    },
    {
        "name": "agent_execution_time",
        "value": os.getenv("AGENT_EXECUTION_TIME", "00:00"),
        "data_type": "string",
        "category": "scheduling",
        "description": "Heure d'exécution des agents IA (format HH:MM)"
    },
    {
        "name": "agent_active",
        "value": os.getenv("AGENT_ACTIVE", "false").lower(),
        "data_type": "boolean",
        "category": "scheduling",
        "description": "Indique si l'exécution automatique des agents est active"
    },
    {
        "name": "custom_hours_interval",
        "value": os.getenv("CUSTOM_HOURS_INTERVAL", "3"),
        "data_type": "integer",
        "category": "scheduling",
        "description": "Intervalle en heures pour l'exécution des agents (si frequency=custom-hours)"
    },
    {
        "name": "daily_report_active",
        "value": os.getenv("DAILY_REPORT_ACTIVE", "false").lower(),
        "data_type": "boolean",
        "category": "scheduling",
        "description": "Indique si les rapports quotidiens sont actifs"
    },
    {
        "name": "daily_report_time",
        "value": os.getenv("DAILY_REPORT_TIME", "08:00"),
        "data_type": "string",
        "category": "scheduling",
        "description": "Heure d'envoi des rapports quotidiens (format HH:MM)"
    },
    {
        "name": "report_channel_email",
        "value": os.getenv("REPORT_CHANNEL_EMAIL", "true").lower(),
        "data_type": "boolean",
        "category": "scheduling",
        "description": "Indique si les rapports sont envoyés par email"
    },
    {
        "name": "report_channel_slack",
        "value": os.getenv("REPORT_CHANNEL_SLACK", "false").lower(),
        "data_type": "boolean",
        "category": "scheduling",
        "description": "Indique si les rapports sont envoyés sur Slack"
    },
    {
        "name": "report_channel_whatsapp",
        "value": os.getenv("REPORT_CHANNEL_WHATSAPP", "true").lower(),
        "data_type": "boolean",
        "category": "scheduling",
        "description": "Indique si les rapports sont envoyés sur WhatsApp"
    }
]

def init_system_settings():
    """
    Initialise les paramètres système dans la base de données.
    Vérifie si chaque paramètre existe déjà avant de l'ajouter.
    """
    db = SessionLocal()
    try:
        # Initialiser les paramètres d'intégration
        logger.info("Initialisation des paramètres d'intégration...")
        init_settings(db, DEFAULT_INTEGRATIONS)
        
        # Initialiser les paramètres de planification
        logger.info("Initialisation des paramètres de planification...")
        init_settings(db, DEFAULT_SCHEDULING)
        
        logger.info("Paramètres système initialisés avec succès!")
    finally:
        db.close()

def init_settings(db: Session, settings_list: List[Dict[str, Any]]):
    """
    Initialise une liste de paramètres dans la base de données.
    
    Args:
        db: Session de base de données
        settings_list: Liste des paramètres à initialiser
    """
    service = SystemSettingsService(db)
    
    for setting in settings_list:
        # Vérifier si le paramètre existe déjà
        existing = db.query(SystemSetting).filter(SystemSetting.name == setting["name"]).first()
        
        if existing:
            logger.debug(f"Le paramètre {setting['name']} existe déjà.")
            # Mettre à jour la description si nécessaire
            if existing.description != setting["description"]:
                existing.description = setting["description"]
                db.commit()
        else:
            # Créer le paramètre s'il n'existe pas
            logger.info(f"Création du paramètre {setting['name']}.")
            try:
                new_setting = SystemSetting(
                    name=setting["name"],
                    value=setting["value"],
                    data_type=setting["data_type"],
                    category=setting["category"],
                    description=setting["description"]
                )
                db.add(new_setting)
                db.commit()
            except Exception as e:
                logger.error(f"Erreur lors de la création du paramètre {setting['name']}: {str(e)}")
                db.rollback()

# Exécuter si le script est lancé directement
if __name__ == "__main__":
    init_system_settings()

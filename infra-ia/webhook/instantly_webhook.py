"""
Module pour la gestion des webhooks Instantly.ai.

Ce module reçoit et traite les webhooks d'Instantly.ai, puis les transmet au ResponseListenerAgent
pour analyse et action.
"""
import json
import datetime
from typing import Dict, Any, Optional

from utils.logging_config import get_logger

# Configuration du logger
logger = get_logger("webhook.instantly")

async def handle_instantly_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Traite un webhook reçu d'Instantly.ai.
    
    Args:
        data: Données du webhook reçu
    
    Returns:
        Résultat du traitement
    """
    # Log des données reçues
    event_type = data.get("event_type", "unknown")
    lead_email = data.get("lead_email", "unknown")
    timestamp = data.get("timestamp", datetime.datetime.now().isoformat())
    
    logger.info(f"Webhook Instantly reçu: {event_type} pour {lead_email}")
    
    # Import dynamique pour éviter les dépendances circulaires
    try:
        # Import du registre d'agents
        from agents.registry import registry
        
        # Obtenir ou créer l'instance de ResponseListenerAgent
        listener_agent = registry.get_or_create("ResponseListenerAgent")
        
        if not listener_agent:
            logger.error("Impossible de charger le ResponseListenerAgent")
            return {
                "status": "error",
                "message": "Agent non disponible"
            }
        
        # Transmission du webhook au ResponseListenerAgent
        logger.info(f"Transmission du webhook Instantly au ResponseListenerAgent")
        
        # Appel de l'agent avec les données du webhook
        result = listener_agent.run({
            "action": "process_email_response",
            "data": data
        })
        
        logger.info(f"Résultat du traitement par ResponseListenerAgent: {result.get('status', 'unknown')}")
        
        # Retour du résultat
        return {
            "status": "success",
            "message": "Webhook traité",
            "agent_response": result.get("status", "unknown")
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de la transmission au ResponseListenerAgent: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            "status": "error",
            "message": f"Erreur: {str(e)}"
        }

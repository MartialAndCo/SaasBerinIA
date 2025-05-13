#!/usr/bin/env python3
"""
Script de test pour le webhook WhatsApp.

Ce script simule l'envoi d'un message WhatsApp au webhook
pour vérifier que le traitement fonctionne correctement.
"""
import os
import sys
import json
import asyncio
import requests
from datetime import datetime

# Ajout du répertoire parent au path pour les imports
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import de la nouvelle configuration de logging
from utils.logging_config import setup_logging

# Initialiser le logger
logger = setup_logging("test_webhook")

# URL du webhook (en local pour le test)
WEBHOOK_URL = "http://localhost:8888/webhook/whatsapp"

async def test_whatsapp_webhook():
    """
    Envoie un message de test au webhook WhatsApp
    """
    logger.info("Envoi d'un message de test au webhook WhatsApp")
    
    # Message de test simulant un webhook Twilio WhatsApp
    test_message = {
        "sender": "+33612345678",
        "profile_name": "Test User",
        "timestamp": datetime.now().isoformat(),
        "message": {
            "text": "Bonjour, ceci est un message de test pour le webhook WhatsApp",
            "type": "text"
        }
    }
    
    try:
        # Envoyer la requête au webhook
        logger.info(f"Envoi du message: {json.dumps(test_message)}")
        response = requests.post(WEBHOOK_URL, json=test_message)
        
        # Vérifier la réponse
        if response.status_code == 200:
            logger.info(f"Réponse reçue avec succès (200 OK)")
            logger.info(f"Contenu de la réponse: {json.dumps(response.json())}")
            return True
        else:
            logger.error(f"Erreur lors de l'envoi du message: {response.status_code}")
            logger.error(f"Contenu de l'erreur: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Exception lors de l'envoi du message: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Point d'entrée du script de test
    """
    logger.info("=== DÉBUT DU TEST DU WEBHOOK WHATSAPP ===")
    
    # Vérifier si le serveur webhook est en cours d'exécution
    try:
        response = requests.get("http://localhost:8888/health")
        if response.status_code != 200:
            logger.error("Le serveur webhook n'est pas en cours d'exécution ou ne répond pas")
            logger.error("Lancez le serveur avec: python webhook/run_webhook.py")
            return
    except Exception:
        logger.error("Le serveur webhook n'est pas en cours d'exécution")
        logger.error("Lancez le serveur avec: python webhook/run_webhook.py")
        return
    
    # Exécuter le test du webhook
    asyncio.run(test_whatsapp_webhook())
    
    logger.info("=== FIN DU TEST DU WEBHOOK WHATSAPP ===")

if __name__ == "__main__":
    main()

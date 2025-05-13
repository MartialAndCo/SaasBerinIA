#!/usr/bin/env python3
"""
Script de test temporaire pour vérifier la réception SMS du webhook.
Ce script simule l'envoi d'une requête au webhook sans modifier les agents existants.
"""
import os
import sys
import json
import requests
import logging
from datetime import datetime

# Configuration du logging
log_dir = "/root/berinia/infra-ia/tests/temp_webhook_test"
log_file = f"{log_dir}/test_sms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("SMS-Test")

def test_sms_webhook():
    """Test du webhook SMS en mode simulation"""
    logger.info("=== TEST DE WEBHOOK SMS - MODE SIMULATION ===")
    
    # URL du webhook
    webhook_url = "http://127.0.0.1:8001/webhook/sms-response"
    
    # Données de test (simulant un webhook Twilio)
    payload = {
        "From": "+33695472227",
        "To": "+33757594999",
        "Body": "Ceci est un test de SMS",
        "MessageSid": "TEST12345"
    }
    
    # En-têtes de la requête
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Twilio-Signature": "dummy_signature"
    }
    
    logger.info(f"Envoi d'une requête à {webhook_url}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Test basique de connexion au serveur
        logger.info("Test de connexion au serveur webhook...")
        try:
            root_response = requests.get("http://127.0.0.1:8001/", timeout=3)
            logger.info(f"Réponse racine: {root_response.status_code} - {root_response.text[:100]}...")
        except Exception as e:
            logger.error(f"Erreur de connexion au serveur: {str(e)}")
            return False
        
        # Envoi de la requête POST
        logger.info("Envoi de la requête POST au webhook SMS...")
        response = requests.post(webhook_url, data=payload, headers=headers, timeout=10)
        
        # Affichage des informations de réponse
        logger.info(f"Code de statut: {response.status_code}")
        logger.info(f"Réponse: {response.text}")
        
        # Test terminé
        logger.info("Test terminé!")
        return response.status_code < 400
        
    except Exception as e:
        logger.error(f"Erreur pendant le test: {str(e)}")
        return False

if __name__ == "__main__":
    # Exécution du test
    success = test_sms_webhook()
    
    # Affichage du résultat
    if success:
        logger.info("✅ Test réussi!")
        print(f"\n✅ TEST RÉUSSI! Log: {log_file}")
        sys.exit(0)
    else:
        logger.error("❌ Test échoué!")
        print(f"\n❌ TEST ÉCHOUÉ! Log: {log_file}")
        sys.exit(1)

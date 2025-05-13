#!/usr/bin/env python3
"""
Script de test pour le webhook SMS de BerinIA.
"""
import os
import sys
import json
import requests
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger("SMS-Webhook-Test")

def test_sms_webhook(verbose=False):
    """Test du webhook SMS"""
    # URL du webhook
    webhook_url = "http://127.0.0.1:8001/webhook/sms-response"
    
    # Données de test (simulant un webhook Twilio)
    payload = {
        "From": "+33695472227",
        "To": "+33757594999",
        "Body": "Ceci est un test de SMS depuis le script Python",
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
        # Envoi de la requête POST
        response = requests.post(webhook_url, data=payload, headers=headers)
        
        # Affichage des informations de réponse
        logger.info(f"Code de statut: {response.status_code}")
        logger.info(f"Réponse: {response.text}")
        
        # En cas d'erreur, afficher des informations supplémentaires
        if response.status_code >= 400:
            logger.error(f"ERREUR: Le webhook a retourné un code d'erreur {response.status_code}")
            
            # Essayer de parser le corps de la réponse comme JSON
            try:
                error_data = response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Corps de la réponse: {response.text}")
        
        # Tentative de vérification des logs
        try:
            log_path = "/root/berinia/infra-ia/logs/berinia_webhook.log"
            if os.path.exists(log_path):
                logger.info(f"Dernières lignes du log webhook:")
                os.system(f"tail -n 10 {log_path}")
            else:
                logger.warning(f"Fichier de log {log_path} non trouvé")
        except Exception as e:
            logger.warning(f"Impossible de lire les logs: {str(e)}")
            
        return response.status_code < 400
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la requête: {str(e)}")
        return False

if __name__ == "__main__":
    # Exécution du test
    verbose = "--verbose" in sys.argv
    success = test_sms_webhook(verbose)
    
    # Affichage du résultat final
    if success:
        logger.info("✅ Test de webhook SMS réussi!")
        sys.exit(0)
    else:
        logger.error("❌ Test de webhook SMS échoué!")
        sys.exit(1)

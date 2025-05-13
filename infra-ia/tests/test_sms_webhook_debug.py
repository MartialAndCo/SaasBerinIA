#!/usr/bin/env python3
"""
Script de test pour le webhook SMS de BerinIA avec débogage amélioré.
"""
import os
import sys
import json
import requests
import logging
import traceback
from datetime import datetime

# Configuration du logging vers un fichier et la console
log_file = f"/root/berinia/infra-ia/logs/sms_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("SMS-Webhook-Test")

def test_sms_webhook():
    """Test du webhook SMS avec débogage amélioré"""
    logger.info("=== DÉBUT DU TEST DE WEBHOOK SMS ===")
    logger.info(f"Log file: {log_file}")
    
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
    logger.info(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        # Diagnostic du serveur webhook
        logger.info("Vérification du serveur webhook...")
        try:
            health_response = requests.get("http://127.0.0.1:8001/health")
            logger.info(f"État de santé du webhook: {health_response.status_code}")
            logger.info(f"Réponse: {health_response.text}")
        except Exception as e:
            logger.warning(f"Impossible de vérifier l'état de santé: {str(e)}")
        
        # Envoi de la requête POST
        logger.info("Envoi de la requête POST au webhook...")
        response = requests.post(webhook_url, data=payload, headers=headers)
        
        # Affichage des informations de réponse
        logger.info(f"Code de statut: {response.status_code}")
        logger.info(f"Réponse: {response.text}")
        logger.info(f"En-têtes de réponse: {dict(response.headers)}")
        
        # En cas d'erreur, afficher des informations supplémentaires
        if response.status_code >= 400:
            logger.error(f"ERREUR: Le webhook a retourné un code d'erreur {response.status_code}")
            
            # Essayer de parse le corps de la réponse comme JSON
            try:
                error_data = response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Corps de la réponse: {response.text}")
        
        # Tentative de vérification des logs
        webhook_log_path = "/root/berinia/infra-ia/logs/berinia_webhook.log"
        logger.info(f"Vérification des logs webhook: {webhook_log_path}")
        
        if os.path.exists(webhook_log_path):
            with open(webhook_log_path, 'r') as f:
                try:
                    last_lines = f.readlines()[-20:]  # Dernières 20 lignes
                    logger.info("Dernières lignes du log webhook:")
                    for line in last_lines:
                        logger.info(f"LOG: {line.strip()}")
                except Exception as e:
                    logger.warning(f"Erreur lors de la lecture des logs: {str(e)}")
        else:
            logger.warning(f"Fichier de log {webhook_log_path} non trouvé")
            
        logger.info("=== FIN DU TEST ===")
        return response.status_code < 400
    
    except Exception as e:
        logger.error(f"Exception lors du test: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Création du répertoire de logs si nécessaire
    os.makedirs("/root/berinia/infra-ia/logs", exist_ok=True)
    
    print(f"Exécution du test de webhook SMS. Logs dans: {log_file}")
    
    # Exécution du test
    success = test_sms_webhook()
    
    # Affichage du résultat final
    if success:
        logger.info("✅ Test de webhook SMS réussi!")
        print("✅ Test de webhook SMS réussi!")
        sys.exit(0)
    else:
        logger.error("❌ Test de webhook SMS échoué!")
        print("❌ Test de webhook SMS échoué!")
        sys.exit(1)

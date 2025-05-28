#!/usr/bin/env python3
"""
Script de test pour envoyer un email via Instantly.ai en utilisant le MessagingAgent.
"""
import os
import sys
import logging
import json
from datetime import datetime

# Configurer le logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-instantly")

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importer le MessagingAgent
from agents.messaging.messaging_agent import MessagingAgent

def send_test_email(recipient_email):
    """
    Envoie un email de test via le MessagingAgent
    
    Args:
        recipient_email: Adresse email du destinataire
    """
    logger.info(f"Envoi d'un email de test à {recipient_email}")
    
    # Créer une instance du MessagingAgent
    agent = MessagingAgent()
    
    # ID de campagne unique basé sur l'horodatage
    campaign_id = f"test-{int(datetime.now().timestamp())}"
    
    # Création des données de test
    test_lead = {
        "lead_id": f"lead-{int(datetime.now().timestamp())}",
        "email": recipient_email,
        "first_name": "Test",
        "last_name": "Utilisateur",
        "company": "BerinIA Test",
        "position": "Testeur"
    }
    
    # Préparer le message
    message_data = {
        "subject": "Test d'intégration Instantly.ai",
        "content": """
        <p>Bonjour,</p>
        <p>Ceci est un email de test envoyé via l'intégration Instantly.ai dans BerinIA.</p>
        <p>Si vous recevez cet email, l'intégration fonctionne correctement.</p>
        <p>Vous pouvez répondre à cet email pour tester la réception des réponses via le webhook.</p>
        <p><a href="https://example.com/test-click">Cliquez ici</a> pour tester la détection des clics.</p>
        <p>Cordialement,<br/>L'équipe BerinIA</p>
        """,
        "campaign_id": campaign_id
    }
    
    # Appeler le MessagingAgent pour envoyer l'email
    result = agent.run({
        "action": "send_email",
        "parameters": {
            "to": recipient_email,
            "subject": message_data["subject"],
            "body": message_data["content"]
        }
    })
    
    # Afficher le résultat
    logger.info(f"Résultat de l'envoi: {json.dumps(result, indent=2)}")
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_instantly_email.py <email_destinataire>")
        sys.exit(1)
        
    recipient = sys.argv[1]
    send_test_email(recipient)

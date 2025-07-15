#!/usr/bin/env python3
"""
Test final après suppression du cache Python
"""
import requests
import json
import time

# Simulation d'un webhook Instantly avec un ID de campagne Instantly
webhook_payload = {
    "event_type": "reply_received",
    "campaign_id": "eeb6ff44-f64c-42da-9fd4-5e7f76a543db",  # ID Instantly
    "campaign_name": "Test Final Cache Fix",
    "lead": "test.cache.fixed@example.com",
    "lead_email": "test.cache.fixed@example.com", 
    "subject": "Re: Test cache Python corrigé",
    "body": {
        "text": "Excellent ! J'ai hâte de découvrir votre solution. Quand pouvons-nous nous rencontrer ?"
    },
    "message_id": "msg_test_cache_fixed",
    "timestamp": int(time.time())
}

print("Test final après suppression du cache Python...")
print(f"Payload: {json.dumps(webhook_payload, indent=2)}")

# Envoi du webhook
response = requests.post(
    "http://localhost:8001/webhook/instantly",
    json=webhook_payload,
    headers={'Content-Type': 'application/json'}
)

print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

# Attendre un moment pour que le traitement soit terminé
time.sleep(3)

print("\n" + "="*50)
print("Vérifiez les logs pour voir si le message 'NOUVELLE VERSION _save_message_to_db UTILISÉE' apparaît.")
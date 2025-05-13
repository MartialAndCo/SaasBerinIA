#!/usr/bin/env python3
"""
Script de test pour le webhook WhatsApp
Simule l'envoi d'un message WhatsApp vers le webhook BerinIA
"""

import sys
import os
import json
import requests
import argparse
from datetime import datetime

def send_test_webhook(group_name, message, webhook_url=None):
    """
    Envoie un message de test au webhook WhatsApp
    """
    if webhook_url is None:
        webhook_url = "http://localhost:8000/webhook/whatsapp"
    
    print(f"Envoi d'un message de test au webhook: {webhook_url}")
    
    # Préparer les données du message
    data = {
        "source": "whatsapp",
        "type": "group",
        "group": group_name,
        "author": "TestUser",
        "content": message,
        "timestamp": datetime.now().isoformat(),
        "messageId": f"test-{datetime.now().timestamp()}"
    }
    
    print(f"Données à envoyer: {json.dumps(data, indent=2)}")
    
    try:
        # Envoyer la requête
        response = requests.post(
            webhook_url,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        # Vérifier la réponse
        if response.status_code == 200:
            print(f"✅ Message envoyé avec succès! Code: {response.status_code}")
            print(f"Réponse: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"❌ Échec de l'envoi. Code: {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {str(e)}")
        return False

def main():
    """Point d'entrée du script"""
    parser = argparse.ArgumentParser(description="Test du webhook WhatsApp pour BerinIA")
    parser.add_argument("--group", type=str, default="🤖 Support IA / Chatbot", 
                        help="Nom du groupe WhatsApp")
    parser.add_argument("--message", type=str, default="Ceci est un message de test depuis le script de test webhook",
                        help="Message à envoyer")
    parser.add_argument("--url", type=str, default="http://localhost:8001/webhook/whatsapp",
                        help="URL du webhook")
    
    args = parser.parse_args()
    
    print("=== Test du webhook WhatsApp BerinIA ===")
    print(f"Groupe: {args.group}")
    print(f"Message: {args.message}")
    print(f"URL du webhook: {args.url}")
    print("=====================================")
    
    success = send_test_webhook(args.group, args.message, args.url)
    
    if success:
        print("\nTest réussi! ✅")
        print("Pour vérifier le traitement du message, consultez les logs:")
        print("  tail -f /root/berinia/infra-ia/logs/berinia.log | grep WhatsApp")
    else:
        print("\nTest échoué! ❌")
        print("Assurez-vous que:")
        print("  1. Le serveur webhook BerinIA est en cours d'exécution")
        print("  2. L'URL du webhook est correcte")
        print("  3. Les agents requis sont initialisés")
        
        # Vérification du serveur webhook
        try:
            health_response = requests.get(args.url.rsplit("/", 1)[0])
            print(f"\nStatut du serveur webhook: {health_response.status_code}")
        except Exception:
            print("\nImpossible de se connecter au serveur webhook!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

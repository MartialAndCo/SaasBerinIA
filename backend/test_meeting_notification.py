#!/usr/bin/env python3
"""
Test de la notification Telegram pour un nouveau rendez-vous
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import requests
import json
from datetime import datetime, timedelta

def test_meeting_notification():
    """Teste la notification Telegram avec un RDV de test"""
    
    print("🔔 Test de Notification Telegram pour Nouveau RDV")
    print("=" * 60)
    
    # Données de test pour un RDV fictif
    test_meeting_data = {
        'meeting_id': 999,
        'client_name': 'Jean Dupont',
        'client_email': 'jean.dupont@test-entreprise.fr',
        'start_time': (datetime.now() + timedelta(days=1)).isoformat(),
        'end_time': (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
        'meeting_link': 'https://meet.jit.si/berinIA-rdv-test-123456',
        'calendar_event_id': 'test_event_12345',
        'lead_id': 42,
        'company_name': 'Test Entreprise SARL',
        'description': 'Rendez-vous de démonstration BerinIA - Test automatisé'
    }
    
    print("📋 Données du RDV de test :")
    print(f"   Client: {test_meeting_data['client_name']}")
    print(f"   Email: {test_meeting_data['client_email']}")
    print(f"   Entreprise: {test_meeting_data['company_name']}")
    print(f"   Date: {test_meeting_data['start_time'][:16]}")
    print(f"   Lien: {test_meeting_data['meeting_link']}")
    
    # URL du webhook
    webhook_url = "http://localhost:8000/api/webhooks/webhook/meeting-created"
    
    try:
        print(f"\n📡 Envoi du webhook vers: {webhook_url}")
        
        # Envoyer la requête
        response = requests.post(
            webhook_url,
            json=test_meeting_data,
            timeout=15,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Statut HTTP: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Succès: {result.get('message', 'OK')}")
            print(f"   Meeting ID: {result.get('meeting_id')}")
            print("\n🎉 Notification programmée avec succès !")
            print("   Vérifiez votre bot Telegram pour voir la notification.")
            
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Détail: {error_detail}")
            except:
                print(f"   Réponse: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter à l'API")
        print("   Vérifiez que berinia-api.service est démarré")
        
    except requests.exceptions.Timeout:
        print("❌ Erreur: Timeout de la requête")
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
    
    print(f"\n📱 Pour voir la notification :")
    print("   1. Ouvrez votre bot Telegram @BerinIABot")
    print("   2. La notification devrait apparaître automatiquement")
    print("   3. Cliquez sur les boutons pour tester les actions")

def test_conversation_summary():
    """Teste la récupération de résumé de conversation"""
    
    print("\n💬 Test de Résumé de Conversation")
    print("=" * 40)
    
    # Test avec un lead existant
    lead_id = 42  # ID de test
    
    summary_url = f"http://localhost:8000/api/conversations/leads/{lead_id}/conversation-summary"
    
    try:
        print(f"📡 Récupération du résumé pour lead {lead_id}")
        
        response = requests.get(summary_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            
            print(f"✅ Résumé récupéré:")
            print(f"   Lead: {data.get('lead_name', 'Inconnu')}")
            print(f"   Entreprise: {data.get('lead_company', 'Non renseignée')}")
            print(f"   Conversations: {data.get('conversations_count', 0)}")
            print(f"   Intérêt: {summary.get('interest_level', 'unknown')}")
            print(f"   Résumé: {summary.get('summary', 'Aucun')[:100]}...")
            
        elif response.status_code == 404:
            print(f"ℹ️  Lead {lead_id} non trouvé - test avec données fictives")
            
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur test résumé: {e}")

if __name__ == "__main__":
    print("🚀 Test complet du système de notifications RDV")
    print("=" * 70)
    
    # Test 1: Notification Telegram
    test_meeting_notification()
    
    # Test 2: Résumé de conversation
    test_conversation_summary()
    
    print(f"\n🏁 Tests terminés - {datetime.now().strftime('%H:%M:%S')}")
    print("\nConsultez vos notifications Telegram pour voir le résultat !")
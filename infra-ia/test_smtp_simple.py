#!/usr/bin/env python3
"""
Test simple du système SMTP avec mode test activé
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.messaging.messaging_agent import MessagingAgent

def test_smtp_simple():
    """Test simple avec mode test activé"""
    print("🧪 TEST SMTP SIMPLE (MODE TEST)")
    print("=" * 50)
    
    # Variables d'environnement de test
    os.environ.update({
        "MAILCHEAP_SMTP_HOST_1": "smtp1.test.com",
        "MAILCHEAP_SMTP_USER_1": "test1@domain.com",
        "MAILCHEAP_SMTP_PASSWORD_1": "password1",
        "MAILCHEAP_SMTP_HOST_2": "smtp2.test.com",
        "MAILCHEAP_SMTP_USER_2": "test2@domain.com",
        "MAILCHEAP_SMTP_PASSWORD_2": "password2",
        "MAILCHEAP_SMTP_HOST_3": "smtp3.test.com",
        "MAILCHEAP_SMTP_USER_3": "test3@domain.com",
        "MAILCHEAP_SMTP_PASSWORD_3": "password3"
    })
    
    try:
        # Créer un agent en mode test
        agent = MessagingAgent("/root/berinia/infra-ia/agents/messaging/config.json")
        
        # Forcer le mode test
        agent.config["test_mode"] = True
        
        # Test d'envoi
        lead_data = {
            "id": 1,
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": "jean.dupont@test.com",
            "company": "TestCorp",
            "position": "CEO",
            "campagne_id": 1,
            "industry": "Tech"
        }
        
        print(f"📧 Test envoi email à: {lead_data['email']}")
        
        task_data = {
            "leads": [lead_data],
            "campaign_id": lead_data["campagne_id"],
            "template_id": "default_email",
            "channel": "email",
            "batch_size": 1
        }
        
        result = agent.send_messages(task_data)
        print(f"📊 Résultat: {result.get('status')}")
        
        if result.get("status") == "success":
            stats = result.get("stats", {})
            print(f"  ✅ Envoyés: {stats.get('sent', 0)}")
            print(f"  ❌ Échecs: {stats.get('failed', 0)}")
            
            # Vérifier les messages envoyés
            sent_messages = result.get("sent_messages", [])
            if sent_messages:
                print(f"  📧 Message envoyé avec ID: {sent_messages[0].get('message_id')}")
            
        # Statistiques SMTP
        if hasattr(agent, 'smtp_rotation_manager'):
            print("\n📊 Statistiques SMTP:")
            smtp_stats = agent.smtp_rotation_manager.get_stats()
            print(f"  Comptes disponibles: {smtp_stats['available_accounts']}")
            print(f"  Conversations: {smtp_stats['total_conversations']}")
            print(f"  Comptes: {smtp_stats['accounts_list']}")
            print(f"  Distribution: {smtp_stats['usage_distribution']}")
            
        print("\n✅ Test terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_smtp_simple()
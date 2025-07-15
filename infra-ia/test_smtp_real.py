#!/usr/bin/env python3
"""
Test avec les vraies données Mailcheap
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.messaging.messaging_agent import MessagingAgent

def test_smtp_real():
    """Test avec les vraies données Mailcheap"""
    print("🚀 TEST SMTP MAILCHEAP RÉEL")
    print("=" * 50)
    
    # Configuration réelle
    os.environ.update({
        "MAILCHEAP_SMTP_HOST_1": "mail8.mymailcheap.com",
        "MAILCHEAP_SMTP_USER_1": "yann@beriniaservices.com",
        "MAILCHEAP_SMTP_PASSWORD_1": "Bhcmi6pm_Bhcmi6pm_",
        "MAILCHEAP_SMTP_HOST_2": "mail8.mymailcheap.com",
        "MAILCHEAP_SMTP_USER_2": "yann@beriniaconnect.com",
        "MAILCHEAP_SMTP_PASSWORD_2": "Bhcmi6pm_Bhcmi6pm_",
        "MAILCHEAP_SMTP_HOST_3": "mail8.mymailcheap.com",
        "MAILCHEAP_SMTP_USER_3": "yann@beriniacontact.com",
        "MAILCHEAP_SMTP_PASSWORD_3": "Bhcmi6pm_Bhcmi6pm_"
    })
    
    try:
        # Créer l'agent
        agent = MessagingAgent()
        
        # Forcer le mode test pour éviter l'envoi réel
        agent.config["test_mode"] = True
        
        # Test avec les 3 comptes
        leads = [
            {
                "id": 1,
                "first_name": "Jean",
                "last_name": "Dupont",
                "email": "jean.dupont@test.com",
                "company": "TestCorp1",
                "position": "CEO",
                "campagne_id": 1,
                "industry": "Tech"
            },
            {
                "id": 2,
                "first_name": "Marie",
                "last_name": "Martin",
                "email": "marie.martin@test.com",
                "company": "TestCorp2",
                "position": "CTO",
                "campagne_id": 1,
                "industry": "Finance"
            },
            {
                "id": 3,
                "first_name": "Paul",
                "last_name": "Durand",
                "email": "paul.durand@test.com",
                "company": "TestCorp3",
                "position": "COO",
                "campagne_id": 1,
                "industry": "Retail"
            }
        ]
        
        print(f"📧 Test avec {len(leads)} leads")
        
        for lead in leads:
            print(f"  → {lead['first_name']} {lead['last_name']} ({lead['email']})")
        
        task_data = {
            "leads": leads,
            "campaign_id": 1,
            "template_id": "default_email",
            "channel": "email",
            "batch_size": 1
        }
        
        result = agent.send_messages(task_data)
        print(f"\n📊 Résultat: {result.get('status')}")
        
        if result.get("status") == "success":
            stats = result.get("stats", {})
            print(f"  ✅ Envoyés: {stats.get('sent', 0)}")
            print(f"  ❌ Échecs: {stats.get('failed', 0)}")
            
            # Vérifier les messages envoyés
            sent_messages = result.get("sent_messages", [])
            print(f"  📧 Messages envoyés: {len(sent_messages)}")
            
        # Statistiques SMTP
        if hasattr(agent, 'smtp_rotation_manager'):
            print("\n📊 Statistiques SMTP:")
            smtp_stats = agent.smtp_rotation_manager.get_stats()
            print(f"  Comptes disponibles: {smtp_stats['available_accounts']}")
            print(f"  Conversations totales: {smtp_stats['total_conversations']}")
            print(f"  Distribution d'utilisation:")
            for email, count in smtp_stats['usage_distribution'].items():
                print(f"    - {email}: {count} messages")
            
        print("\n✅ Test terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_smtp_real()
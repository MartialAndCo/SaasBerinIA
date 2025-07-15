#!/usr/bin/env python3
"""
Test d'envoi d'email réel à discoursdiscours86@gmail.com
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.messaging.messaging_agent import MessagingAgent

def test_real_email_send():
    """Test d'envoi d'email réel"""
    print("📧 TEST ENVOI EMAIL RÉEL")
    print("=" * 50)
    
    # Configuration avec les vraies variables d'environnement
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
        
        # DÉSACTIVER le mode test pour envoyer réellement
        agent.config["test_mode"] = False
        
        # Données du lead de test
        lead_data = {
            "id": 999,
            "first_name": "Test",
            "last_name": "BerinIA",
            "email": "discoursdiscours86@gmail.com",
            "company": "Test Company",
            "position": "Testeur",
            "campagne_id": 1,
            "industry": "Test"
        }
        
        print(f"📧 Envoi d'email réel à: {lead_data['email']}")
        print(f"🏢 De: {lead_data['first_name']} {lead_data['last_name']} ({lead_data['company']})")
        
        task_data = {
            "leads": [lead_data],
            "campaign_id": lead_data["campagne_id"],
            "template_id": "default_email",
            "channel": "email",
            "batch_size": 1
        }
        
        print("\n🚀 Envoi en cours...")
        result = agent.send_messages(task_data)
        
        print(f"\n📊 Résultat: {result.get('status')}")
        
        if result.get("status") == "success":
            stats = result.get("stats", {})
            print(f"  ✅ Envoyés: {stats.get('sent', 0)}")
            print(f"  ❌ Échecs: {stats.get('failed', 0)}")
            
            # Vérifier les messages envoyés
            sent_messages = result.get("sent_messages", [])
            if sent_messages:
                message = sent_messages[0]
                print(f"  📧 Message ID: {message.get('message_id')}")
                print(f"  📤 Envoyé depuis: {message.get('smtp_email_used', 'N/A')}")
                print(f"  📝 Sujet: {message.get('subject', 'N/A')}")
                
        else:
            print(f"  ❌ Erreur: {result.get('error', 'Erreur inconnue')}")
            
        # Statistiques SMTP
        if hasattr(agent, 'smtp_rotation_manager'):
            print("\n📊 Statistiques SMTP:")
            smtp_stats = agent.smtp_rotation_manager.get_stats()
            print(f"  Comptes disponibles: {smtp_stats['available_accounts']}")
            print(f"  Conversations totales: {smtp_stats['total_conversations']}")
            print(f"  Distribution d'utilisation:")
            for email, count in smtp_stats['usage_distribution'].items():
                print(f"    - {email}: {count} messages")
            
        if result.get("status") == "success":
            print("\n✅ Email envoyé avec succès!")
            print("📬 Vérifiez la boîte de réception de discoursdiscours86@gmail.com")
        else:
            print(f"\n❌ Échec de l'envoi: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_email_send()
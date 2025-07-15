#!/usr/bin/env python3
"""
Test du système SMTP avec rotation des comptes Mailcheap
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.messaging.messaging_agent import MessagingAgent
from utils.smtp_rotation_manager import SMTPRotationManager

def test_smtp_rotation_manager():
    """Test du gestionnaire de rotation SMTP"""
    print("🔄 TEST SMTP ROTATION MANAGER")
    print("=" * 50)
    
    # Configuration test
    smtp_configs = [
        {
            "host": "serveur1.mymailcheap.com",
            "port": 587,
            "user": "email1@domain.com",
            "password": "password1",
            "from_email": "email1@domain.com",
            "status": "active"
        },
        {
            "host": "serveur2.mymailcheap.com",
            "port": 587,
            "user": "email2@domain.com",
            "password": "password2",
            "from_email": "email2@domain.com",
            "status": "active"
        }
    ]
    
    manager = SMTPRotationManager(smtp_configs, test_mode=True)
    
    # Test de sélection
    print("📧 Test de sélection de compte:")
    for i in range(1, 4):
        config = manager.select_smtp_config_for_campaign(f"lead_{i}")
        print(f"  Lead {i}: {config['from_email'] if config else 'None'}")
    
    # Test de réponse
    print("\n💬 Test de réponse:")
    reply_config = manager.get_smtp_config_for_reply("lead_1")
    print(f"  Réponse lead_1: {reply_config['from_email'] if reply_config else 'None'}")
    
    # Statistiques
    print("\n📊 Statistiques:")
    stats = manager.get_stats()
    print(f"  Comptes disponibles: {stats['available_accounts']}")
    print(f"  Conversations: {stats['total_conversations']}")
    print(f"  Distribution: {stats['usage_distribution']}")
    
def test_messaging_agent_smtp():
    """Test du MessagingAgent avec SMTP"""
    print("\n🚀 TEST MESSAGING AGENT SMTP")
    print("=" * 50)
    
    # Variables d'environnement pour le test
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
        agent = MessagingAgent()
        
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
        print(f"📊 Résultat: {result['status']}")
        
        if result.get("status") == "success":
            stats = result.get("stats", {})
            print(f"  ✅ Envoyés: {stats.get('sent', 0)}")
            print(f"  ❌ Échecs: {stats.get('failed', 0)}")
            
            # Test de réponse
            print("\n💬 Test de réponse:")
            response_data = {
                "lead_data": lead_data,
                "message": "Merci pour votre message",
                "campaign_id": lead_data["campagne_id"],
                "channel": "email"
            }
            
            reply_result = agent.send_response(response_data)
            print(f"  Réponse: {reply_result['status']}")
        
        # Statistiques SMTP
        if hasattr(agent, 'smtp_rotation_manager'):
            print("\n📊 Statistiques SMTP:")
            smtp_stats = agent.smtp_rotation_manager.get_stats()
            print(f"  Comptes disponibles: {smtp_stats['available_accounts']}")
            print(f"  Conversations: {smtp_stats['total_conversations']}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_environment_variables():
    """Test des variables d'environnement"""
    print("\n🔧 TEST VARIABLES D'ENVIRONNEMENT")
    print("=" * 50)
    
    required_vars = [
        "MAILCHEAP_SMTP_HOST_1", "MAILCHEAP_SMTP_USER_1", "MAILCHEAP_SMTP_PASSWORD_1",
        "MAILCHEAP_SMTP_HOST_2", "MAILCHEAP_SMTP_USER_2", "MAILCHEAP_SMTP_PASSWORD_2",
        "MAILCHEAP_SMTP_HOST_3", "MAILCHEAP_SMTP_USER_3", "MAILCHEAP_SMTP_PASSWORD_3"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Variables manquantes:")
        for var in missing_vars:
            print(f"  - {var}")
    else:
        print("✅ Toutes les variables sont définies")
    
    # Test des comptes configurés
    print("\n📧 Comptes configurés:")
    for i in range(1, 4):
        host = os.getenv(f"MAILCHEAP_SMTP_HOST_{i}")
        user = os.getenv(f"MAILCHEAP_SMTP_USER_{i}")
        if host and user:
            print(f"  Compte {i}: {user} @ {host}")
        else:
            print(f"  Compte {i}: ❌ Incomplet")

if __name__ == "__main__":
    print("🧪 TEST COMPLET SYSTÈME SMTP MAILCHEAP")
    print("=" * 60)
    
    # Test 1: Variables d'environnement
    test_environment_variables()
    
    # Test 2: Gestionnaire de rotation
    test_smtp_rotation_manager()
    
    # Test 3: MessagingAgent
    test_messaging_agent_smtp()
    
    print("\n🏁 TESTS TERMINÉS")
    print("=" * 60)
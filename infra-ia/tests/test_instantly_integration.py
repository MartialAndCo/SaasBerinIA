"""
Script de test pour l'intégration d'Instantly.ai avec BerinIA.
"""
import os
import sys
import json
import datetime
from unittest import mock

# Ajouter le répertoire parent au PYTHONPATH pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_clients.instantly_client import InstantlyClient
from agents.messaging.messaging_agent import MessagingAgent
from agents.response_listener.response_listener_agent import ResponseListenerAgent

# Configuration du test
TEST_API_KEY = "test_api_key"  # Clé factice pour les tests
TEST_FROM_EMAIL = "test@berinia.com"
TEST_TO_EMAIL = "lead@example.com"

def test_instantly_client():
    """Test du client InstantlyAPI"""
    print("\n=== Test du client InstantlyAPI ===")
    
    # Création du client avec la clé API factice
    client = InstantlyClient(api_key=TEST_API_KEY)
    
    # Vérification que le client a été initialisé correctement
    assert client.api_key == TEST_API_KEY
    assert client.base_url == "https://api.instantly.ai/api/v2/"
    assert client.headers["Authorization"] == f"Bearer {TEST_API_KEY}"
    
    print("✓ Initialisation du client OK")
    
    # Mock pour _validate_account pour éviter l'erreur
    with mock.patch.object(client, '_validate_account', return_value=TEST_FROM_EMAIL) as mock_validate, \
         mock.patch.object(client, '_make_request') as mock_request:
        # Configuration du mock pour retourner une réponse factice
        mock_request.return_value = {
            "status": "success", 
            "message_id": "test-message-id-123"
        }
        
        # Test de l'envoi d'email
        result = client.send_email(
            recipient=TEST_TO_EMAIL,
            subject="Test Email",
            html_content="<p>Test content</p>",
            from_email=TEST_FROM_EMAIL,
            campaign_id="test-campaign-123"
        )
        
        # Vérification que la méthode _make_request a été appelée correctement
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert args[1] == "emails/send"
        assert "eaccount" in args[2]
        assert args[2]["to"] == TEST_TO_EMAIL
        assert args[2]["subject"] == "Test Email"
        
        # Vérification du résultat
        assert result["status"] == "success"
        assert result["message_id"] == "test-message-id-123"
        
        print("✓ Envoi d'email simulé OK")
    
    # Test du parsing de webhook
    webhook_data = {
        "event_type": "reply_received",
        "timestamp": datetime.datetime.now().isoformat(),
        "campaign_id": "test-campaign-123",
        "campaign_name": "Test Campaign",
        "lead_email": TEST_TO_EMAIL,
        "email_account": TEST_FROM_EMAIL,
        "reply_content": "This is a test reply",
        "message_id": "reply-id-456"
    }
    
    parsed = client.parse_webhook(webhook_data)
    
    # Vérification du résultat
    assert parsed["event_type"] == "reply_received"
    assert parsed["lead_email"] == TEST_TO_EMAIL
    assert parsed["campaign_id"] == "test-campaign-123"
    assert "content" in parsed
    assert parsed["content"] == "This is a test reply"
    
    print("✓ Parsing de webhook OK")
    
    return True

def test_messaging_agent():
    """Test de l'intégration avec MessagingAgent"""
    print("\n=== Test du MessagingAgent ===")
    
    # Configuration d'un agent de test avec mode test activé
    with mock.patch('agents.messaging.messaging_agent.MessagingAgent._init_email_client'):
        agent = MessagingAgent()
        # Forcer le mode test pour éviter les vrais appels API
        agent.config["test_mode"] = True
        
        # Modifier la configuration de l'agent pour utiliser Instantly
        agent.email_service = "instantly"
        agent.from_email = TEST_FROM_EMAIL
        
        # Création d'un client factice et l'attribuer à l'agent
        mock_client = mock.MagicMock()
        mock_client.send_email.return_value = {"status": "success", "message_id": "test-123"}
        agent.instantly_client = mock_client
    
    # Création d'un lead de test
    test_lead = {
        "lead_id": "test-lead-123",
        "email": TEST_TO_EMAIL,
        "first_name": "Test",
        "last_name": "User",
        "company": "Test Company",
        "position": "CEO"
    }
    
    # Création d'un message de test
    message_data = {
        "subject": "Test Subject",
        "content": "<p>Test content</p>",
        "template_id": "test-template"
    }
    
    # En mode test, la méthode ne fait pas d'appel API réel
    # Nous désactivons temporairement le mode test pour forcer l'appel au client mock
    agent.config["test_mode"] = False
    
    # Appel de la méthode _send_email_instantly
    success, error = agent._send_email_instantly(
        recipient=test_lead["email"],
        subject=message_data["subject"],
        body=message_data["content"],
        campaign_id="test-campaign",
        lead=test_lead
    )
    
    # Vérification que la méthode send_email du client a été appelée correctement
    mock_client.send_email.assert_called_once()
    args, kwargs = mock_client.send_email.call_args
    assert kwargs["recipient"] == TEST_TO_EMAIL
    assert kwargs["subject"] == "Test Subject"
    assert kwargs["html_content"] == "<p>Test content</p>"
    assert kwargs["campaign_id"] == "test-campaign"
    
    # Vérification du résultat
    assert success is True
    assert error == ""
    
    print("✓ Envoi d'email via MessagingAgent OK")
    
    return True

def test_response_listener_agent():
    """Test de l'intégration avec ResponseListenerAgent"""
    print("\n=== Test du ResponseListenerAgent ===")
    
    # Configuration d'un agent de test
    agent = ResponseListenerAgent()
    
    # Création d'un mock pour le client Instantly et l'assigner à l'agent
    mock_client = mock.MagicMock()
    test_parsed_data = {
        "event_type": "reply_received",
        "timestamp": datetime.datetime.now().isoformat(),
        "campaign_id": "test-campaign-123",
        "lead_email": TEST_TO_EMAIL,
        "content": "This is a test reply",
        "message_id": "reply-id-456"
    }
    mock_client.parse_webhook.return_value = test_parsed_data
    agent.instantly_client = mock_client
    
    # Mock pour la méthode transmit_to_interpreter
    with mock.patch.object(agent, 'transmit_to_interpreter') as mock_transmit:
        # Webhook factice
        webhook_data = {
            "event_type": "reply_received",
            "timestamp": datetime.datetime.now().isoformat(),
            "campaign_id": "test-campaign-123",
            "lead_email": TEST_TO_EMAIL,
            "reply_content": "This is a test reply"
        }
        
        # Appel de la méthode _process_instantly_webhook
        result = agent._process_instantly_webhook(webhook_data)
        
        # Vérification que parse_webhook a été appelé
        mock_client.parse_webhook.assert_called_once_with(webhook_data)
        
        # Vérification que transmit_to_interpreter a été appelé
        mock_transmit.assert_called_once()
        
        # Vérification du résultat
        assert result["status"] == "success"
        assert "data" in result
        assert result["data"]["source"] == "email"
        assert result["data"]["sender"] == TEST_TO_EMAIL
        assert result["data"]["campaign_id"] == "test-campaign-123"
        
        print("✓ Traitement de webhook via ResponseListenerAgent OK")
    
    return True

def run_all_tests():
    """Exécute tous les tests d'intégration"""
    print("\n=== Début des tests d'intégration d'Instantly.ai ===\n")
    
    tests = [
        ("Client Instantly.ai", test_instantly_client),
        ("Agent de messagerie", test_messaging_agent),
        ("Agent d'écoute", test_response_listener_agent)
    ]
    
    success_count = 0
    for name, test_func in tests:
        print(f"\nTest: {name}")
        try:
            result = test_func()
            if result:
                success_count += 1
                print(f"✓ Test '{name}' réussi")
            else:
                print(f"✗ Test '{name}' échoué")
        except Exception as e:
            print(f"✗ Erreur lors du test '{name}': {str(e)}")
    
    print(f"\n=== Fin des tests: {success_count}/{len(tests)} tests réussis ===")

if __name__ == "__main__":
    # Exécution de tous les tests
    run_all_tests()

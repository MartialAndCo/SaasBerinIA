#!/usr/bin/env python3
"""
Test direct de la méthode _save_message_to_db pour vérifier si l'erreur template_id persiste
"""
import sys
import os

# Ajouter le chemin des modules
sys.path.append('/root/berinia/infra-ia')

def test_save_message_direct():
    """Test direct de _save_message_to_db"""
    try:
        # Import de l'agent
        from agents.messaging.messaging_agent import MessagingAgent
        
        print("🔄 Création de l'instance MessagingAgent...")
        agent = MessagingAgent()
        
        print("📝 Préparation des données de test...")
        test_lead = {
            "id": "test-lead-123",
            "lead_id": "test-lead-123", 
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        test_message = {
            "content": "Message de test",
            "subject": "Test Subject"
        }
        
        print("💾 Test de _save_message_to_db...")
        message_id = agent._save_message_to_db(
            lead=test_lead,
            message_data=test_message,
            campaign_id="1",
            channel="email"
        )
        
        print(f"✅ Message sauvegardé avec ID: {message_id}")
        print("✅ Test réussi - Aucune erreur template_id !")
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {str(e)}")
        if "template_id" in str(e):
            print("🚨 L'erreur template_id persiste !")
        else:
            print("ℹ️  Erreur différente de template_id")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save_message_direct()
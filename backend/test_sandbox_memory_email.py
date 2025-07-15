#!/usr/bin/env python3
"""
TEST MÉMOIRE CONVERSATIONNELLE - Système Sandbox EMAILS
Test si Louise se souvient de ce qui a été dit dans les conversations email
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api/sandbox"

def test_sandbox_memory_email():
    """
    Test SIMPLE : Est-ce que Louise se souvient de ce qui a été dit en EMAIL ?
    """
    print("📧 TEST MÉMOIRE CONVERSATIONNELLE EMAIL - Système Sandbox")
    print("=" * 60)
    
    # 1. Créer un lead sandbox EMAIL
    print("👤 1. Création du lead sandbox EMAIL...")
    lead_data = {
        "first_name": "Marie",
        "last_name": "Dubois",
        "email": "marie@restaurant-dubois.fr",
        "phone": "+33612345678",
        "company": "Restaurant Le Petit Dubois",
        "industry": "restauration",
        "test_platform": "email",  # 📧 IMPORTANT: EMAIL
        "score": 75
    }
    
    try:
        create_response = requests.post(f"{API_BASE}/leads", json=lead_data)
        if create_response.status_code != 200:
            print(f"❌ Erreur création lead: {create_response.text}")
            return
        
        lead = create_response.json()
        lead_id = lead["id"]
        print(f"   ✅ Lead EMAIL créé: ID {lead_id} - {lead['first_name']} {lead['last_name']}")
        
        # 2. Démarrer une conversation EMAIL
        print("\n📧 2. Démarrage de la conversation EMAIL...")
        start_data = {
            "sandbox_lead_id": lead_id,
            "platform": "email",  # 📧 EMAIL
            "action": "start_conversation"
        }
        
        start_response = requests.post(f"{API_BASE}/conversation", json=start_data)
        if start_response.status_code != 200:
            print(f"❌ Erreur démarrage: {start_response.text}")
            return
        
        start_result = start_response.json()
        session_id = start_result["conversation_session_id"]
        print(f"   ✅ Conversation EMAIL démarrée: {session_id}")
        print(f"   🤖 Louise: {start_result['ai_response'][:150]}...")
        
        # 3. Marie donne une info spécifique (25 couverts)
        print("\n💬 3. Marie donne une info spécifique par EMAIL...")
        msg1_data = {
            "sandbox_lead_id": lead_id,
            "platform": "email",
            "user_message": "Bonjour Louise, oui cela m'intéresse. Mon restaurant fait 25 couverts et nous avons du mal à gérer les réservations aux heures de pointe.",
            "action": "send_response",
            "conversation_session_id": session_id
        }
        
        msg1_response = requests.post(f"{API_BASE}/conversation", json=msg1_data)
        if msg1_response.status_code != 200:
            print(f"❌ Erreur message 1: {msg1_response.text}")
            return
        
        msg1_result = msg1_response.json()
        print(f"   👤 Marie: {msg1_data['user_message'][:80]}...")
        print(f"   🤖 Louise: {msg1_result['ai_response'][:150]}...")
        
        # 4. Question de mémoire de Marie par EMAIL
        print("\n🧠 4. TEST DE MÉMOIRE EMAIL - Marie demande...")
        msg2_data = {
            "sandbox_lead_id": lead_id,
            "platform": "email",
            "user_message": "Pouvez-vous me rappeler combien de couverts fait mon restaurant selon notre échange précédent ?",
            "action": "send_response",
            "conversation_session_id": session_id
        }
        
        msg2_response = requests.post(f"{API_BASE}/conversation", json=msg2_data)
        if msg2_response.status_code != 200:
            print(f"❌ Erreur message 2: {msg2_response.text}")
            return
        
        msg2_result = msg2_response.json()
        print(f"   👤 Marie: {msg2_data['user_message']}")
        print(f"   🤖 Louise: {msg2_result['ai_response']}")
        
        # 5. ANALYSE DE LA MÉMOIRE EMAIL
        print("\n🔍 ANALYSE DE LA MÉMOIRE EMAIL:")
        print("=" * 35)
        
        louise_response = msg2_result['ai_response']
        
        # Test si Louise se souvient du nombre de couverts
        if "25" in louise_response and ("couverts" in louise_response.lower() or "couvert" in louise_response.lower()):
            print("✅ EXCELLENTE MÉMOIRE: Louise se souvient des 25 couverts")
        else:
            print("❌ PROBLÈME MÉMOIRE: Louise ne se souvient pas des 25 couverts")
        
        # Test si elle fait référence à la conversation précédente
        memory_indicators = [
            "vous avez mentionné", "vous avez dit", "comme vous l'avez précisé",
            "25 couverts", "25", "vingt-cinq", "vous parliez", "selon votre message",
            "échange précédent", "comme indiqué"
        ]
        
        has_memory = any(indicator in louise_response.lower() for indicator in memory_indicators)
        
        if has_memory:
            print("✅ CONTEXTE: Louise fait référence à la conversation précédente")
        else:
            print("❌ CONTEXTE: Louise ne fait pas référence aux échanges précédents")
        
        # Test du format EMAIL (pas de "Bonjour" répétitif)
        if louise_response.startswith("Bonjour Marie"):
            print("⚠️ FORMAT EMAIL: Louise dit encore 'Bonjour Marie' (peut être acceptable en email)")
        else:
            print("✅ FORMAT EMAIL: Louise continue la conversation sans répéter les salutations")
        
        # 6. VÉRIFICATION HISTORIQUE EMAIL
        print("\n📜 VÉRIFICATION HISTORIQUE EMAIL:")
        history_response = requests.get(f"{API_BASE}/conversations/{lead_id}/{session_id}")
        
        if history_response.status_code == 200:
            history = history_response.json()
            messages = history.get("messages", [])
            print(f"   🔍 Messages EMAIL récupérés: {len(messages)}")
            
            for i, msg in enumerate(messages):
                if msg.get("messages", {}).get("user"):
                    print(f"   {i+1}. 👤 {msg['messages']['user'][:60]}...")
                if msg.get("messages", {}).get("ai"):
                    print(f"   {i+1}. 🤖 {msg['messages']['ai'][:60]}...")
        else:
            print(f"   ❌ Erreur récupération historique: {history_response.text}")
        
        # 7. DIAGNOSTIC FINAL EMAIL
        print("\n🎯 DIAGNOSTIC FINAL EMAIL:")
        print("=" * 25)
        
        if "25" in louise_response and has_memory:
            print("🎉 MÉMOIRE EMAIL PARFAITE: Louise se souvient parfaitement de la conversation")
        elif "25" in louise_response:
            print("⚠️ MÉMOIRE EMAIL PARTIELLE: Louise se souvient du chiffre mais pas du contexte")
        else:
            print("🚨 MÉMOIRE EMAIL DÉFAILLANTE: Louise ne se souvient de rien")
            
        print(f"\n📝 Réponse EMAIL complète de Louise:")
        print(f'"{louise_response}"')
        
    except Exception as e:
        print(f"❌ Erreur durant le test EMAIL: {e}")

if __name__ == "__main__":
    test_sandbox_memory_email()

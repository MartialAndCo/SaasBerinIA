#!/usr/bin/env python3
"""
TEST MÉMOIRE CONVERSATIONNELLE - Système Sandbox
Test si Louise se souvient de ce qui a été dit dans le système sandbox
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api/sandbox"

def test_sandbox_memory():
    """
    Test SIMPLE : Est-ce que Louise se souvient de ce qui a été dit dans le sandbox ?
    """
    print("🧠 TEST MÉMOIRE CONVERSATIONNELLE - Système Sandbox")
    print("=" * 60)
    
    # 1. Créer un lead sandbox
    print("👤 1. Création du lead sandbox...")
    lead_data = {
        "first_name": "Marc",
        "last_name": "Durand",
        "email": "marc@garage-durand.fr",
        "phone": "+33612345678",
        "company": "Garage Durand",
        "industry": "garage automobile",
        "test_platform": "sms",
        "score": 80
    }
    
    try:
        create_response = requests.post(f"{API_BASE}/leads", json=lead_data)
        if create_response.status_code != 200:
            print(f"❌ Erreur création lead: {create_response.text}")
            return
        
        lead = create_response.json()
        lead_id = lead["id"]
        print(f"   ✅ Lead créé: ID {lead_id} - {lead['first_name']} {lead['last_name']}")
        
        # 2. Démarrer une conversation
        print("\n🚀 2. Démarrage de la conversation...")
        start_data = {
            "sandbox_lead_id": lead_id,
            "platform": "sms",
            "action": "start_conversation"
        }
        
        start_response = requests.post(f"{API_BASE}/conversation", json=start_data)
        if start_response.status_code != 200:
            print(f"❌ Erreur démarrage: {start_response.text}")
            return
        
        start_result = start_response.json()
        session_id = start_result["conversation_session_id"]
        print(f"   ✅ Conversation démarrée: {session_id}")
        print(f"   🤖 Louise: {start_result['ai_response'][:100]}...")
        
        # 3. Marc donne une info spécifique (15 employés)
        print("\n💬 3. Marc donne une info spécifique...")
        msg1_data = {
            "sandbox_lead_id": lead_id,
            "platform": "sms",
            "user_message": "Oui ça m'intéresse, j'ai 15 employés et on galère avec les rendez-vous",
            "action": "send_response",
            "conversation_session_id": session_id
        }
        
        msg1_response = requests.post(f"{API_BASE}/conversation", json=msg1_data)
        if msg1_response.status_code != 200:
            print(f"❌ Erreur message 1: {msg1_response.text}")
            return
        
        msg1_result = msg1_response.json()
        print(f"   👤 Marc: {msg1_data['user_message']}")
        print(f"   🤖 Louise: {msg1_result['ai_response'][:100]}...")
        
        # 4. Question de mémoire de Marc
        print("\n🧠 4. TEST DE MÉMOIRE - Marc demande...")
        msg2_data = {
            "sandbox_lead_id": lead_id,
            "platform": "sms",
            "user_message": "Rappelez-moi, de combien d'employés j'ai parlé ?",
            "action": "send_response",
            "conversation_session_id": session_id
        }
        
        msg2_response = requests.post(f"{API_BASE}/conversation", json=msg2_data)
        if msg2_response.status_code != 200:
            print(f"❌ Erreur message 2: {msg2_response.text}")
            return
        
        msg2_result = msg2_response.json()
        print(f"   👤 Marc: {msg2_data['user_message']}")
        print(f"   🤖 Louise: {msg2_result['ai_response']}")
        
        # 5. ANALYSE DE LA MÉMOIRE
        print("\n🔍 ANALYSE DE LA MÉMOIRE:")
        print("=" * 30)
        
        louise_response = msg2_result['ai_response']
        
        # Test si Louise se souvient du nombre d'employés
        if "15" in louise_response:
            print("✅ EXCELLENTE MÉMOIRE: Louise se souvient des 15 employés")
        else:
            print("❌ PROBLÈME MÉMOIRE: Louise ne se souvient pas des 15 employés")
        
        # Test si elle fait référence à la conversation précédente
        memory_indicators = [
            "vous avez mentionné", "vous avez dit", "comme vous l'avez précisé",
            "15 employés", "15", "quinze", "vous parliez", "vous disiez"
        ]
        
        has_memory = any(indicator in louise_response.lower() for indicator in memory_indicators)
        
        if has_memory:
            print("✅ CONTEXTE: Louise fait référence à la conversation précédente")
        else:
            print("❌ CONTEXTE: Louise ne fait pas référence aux échanges précédents")
        
        # 6. VÉRIFICATION HISTORIQUE
        print("\n📜 VÉRIFICATION HISTORIQUE:")
        history_response = requests.get(f"{API_BASE}/conversations/{lead_id}/{session_id}")
        
        if history_response.status_code == 200:
            history = history_response.json()
            messages = history.get("messages", [])
            print(f"   🔍 Messages récupérés: {len(messages)}")
            
            for i, msg in enumerate(messages):
                if msg.get("messages", {}).get("user"):
                    print(f"   {i+1}. 👤 {msg['messages']['user'][:50]}...")
                if msg.get("messages", {}).get("ai"):
                    print(f"   {i+1}. 🤖 {msg['messages']['ai'][:50]}...")
        else:
            print(f"   ❌ Erreur récupération historique: {history_response.text}")
        
        # 7. DIAGNOSTIC FINAL
        print("\n🎯 DIAGNOSTIC FINAL:")
        print("=" * 20)
        
        if "15" in louise_response and has_memory:
            print("🎉 MÉMOIRE PARFAITE: Louise se souvient parfaitement de la conversation")
        elif "15" in louise_response:
            print("⚠️ MÉMOIRE PARTIELLE: Louise se souvient du chiffre mais pas du contexte")
        else:
            print("🚨 MÉMOIRE DÉFAILLANTE: Louise ne se souvient de rien")
            
        print(f"\n📝 Réponse complète de Louise:")
        print(f'"{louise_response}"')
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")

if __name__ == "__main__":
    test_sandbox_memory()

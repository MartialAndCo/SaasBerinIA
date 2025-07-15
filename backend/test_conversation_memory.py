#!/usr/bin/env python3
"""
Test spécifique pour reproduire le problème de boucle conversationnelle
où Louise répète "Comment puis-je vous aider ?" au lieu de répondre aux questions.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api"

def test_conversation_memory_problem():
    """Reproduit exactement le problème de conversation signalé"""
    
    print("🔍 REPRODUCTION DU PROBLÈME - Boucle conversationnelle Louise")
    print("=" * 70)
    
    # 1. Créer un lead de test (Plomberie Moreau comme dans l'exemple)
    print("\n📝 1. Création du lead Pierre Moreau...")
    lead_data = {
        "first_name": "Pierre",
        "last_name": "Moreau", 
        "email": "contact@plomberie-moreau.fr",
        "company": "Plomberie Moreau",
        "industry": "Artisanat",
        "test_platform": "sms",
        "score": 70
    }
    
    response = requests.post(f"{API_BASE}/sandbox/leads", json=lead_data)
    print(f"   ✅ Lead créé: {response.status_code}")
    lead_data_response = response.json()
    lead_id = lead_data_response["id"]
    print(f"   🆔 Lead ID: {lead_id}")
    
    # 2. Démarrer conversation (message d'approche)
    print("\n📝 2. Message d'approche initial...")
    conversation_data = {
        "sandbox_lead_id": lead_id,
        "platform": "sms",
        "action": "start_conversation"
    }
    
    response = requests.post(f"{API_BASE}/sandbox/conversation", json=conversation_data)
    print(f"   ✅ Conversation démarrée: {response.status_code}")
    result = response.json()
    session_id = result["conversation_session_id"]
    print(f"   🆔 Session: {session_id}")
    print(f"   🤖 Louise: {result['ai_response'][:100]}...")
    
    # 3. PROBLÈME : "vous faites quoi jai pas compris"
    print("\n📝 3. Test question prospect: 'vous faites quoi jai pas compris'")
    conversation_data = {
        "sandbox_lead_id": lead_id,
        "platform": "sms",
        "user_message": "vous faites quoi jai pas compris",
        "action": "send_response",
        "conversation_session_id": session_id
    }
    
    response = requests.post(f"{API_BASE}/sandbox/conversation", json=conversation_data)
    result = response.json()
    print(f"   ✅ Réponse: {response.status_code}")
    response1 = result['ai_response']
    print(f"   🤖 Louise: {response1}")
    
    # 4. Test "bah expliquez"
    print("\n📝 4. Test suite: 'bah expliquez'")
    conversation_data["user_message"] = "bah expliquez"
    
    response = requests.post(f"{API_BASE}/sandbox/conversation", json=conversation_data)
    result = response.json()
    print(f"   ✅ Réponse: {response.status_code}")
    response2 = result['ai_response']
    print(f"   🤖 Louise: {response2}")
    
    # 5. Test "jsp a vous de me dire?"
    print("\n📝 5. Test suite: 'jsp a vous de me dire?'")
    conversation_data["user_message"] = "jsp a vous de me dire?"
    
    response = requests.post(f"{API_BASE}/sandbox/conversation", json=conversation_data)
    result = response.json()
    print(f"   ✅ Réponse: {response.status_code}")
    response3 = result['ai_response']
    print(f"   🤖 Louise: {response3}")
    
    # 6. Analyse des problèmes
    print("\n" + "=" * 70)
    print("🔍 ANALYSE DES PROBLÈMES DÉTECTÉS:")
    print("=" * 70)
    
    # Vérifie si Louise répète la même chose
    similar_responses = []
    if "Comment puis-je vous aider" in response1:
        similar_responses.append("Réponse 1")
    if "Comment puis-je vous aider" in response2:
        similar_responses.append("Réponse 2") 
    if "Comment puis-je vous aider" in response3:
        similar_responses.append("Réponse 3")
        
    if len(similar_responses) >= 2:
        print(f"   ❌ BOUCLE DÉTECTÉE: {len(similar_responses)} réponses similaires")
        print(f"   📋 Réponses concernées: {', '.join(similar_responses)}")
    else:
        print("   ✅ Pas de boucle détectée")
    
    # Vérifie si Louise explique BerinIA
    explains_berinia = []
    berinia_keywords = ["BerinIA", "automatisation", "plombier", "artisan", "intervention"]
    
    for i, resp in enumerate([response1, response2, response3], 1):
        if any(keyword.lower() in resp.lower() for keyword in berinia_keywords):
            explains_berinia.append(f"Réponse {i}")
    
    if explains_berinia:
        print(f"   ✅ Explication BerinIA dans: {', '.join(explains_berinia)}")
    else:
        print("   ❌ AUCUNE EXPLICATION de BerinIA donnée")
    
    # Vérifie la contextualisation
    contextual_responses = []
    context_keywords = ["Plomberie Moreau", "Pierre", "artisanat", "plombier"]
    
    for i, resp in enumerate([response1, response2, response3], 1):
        if any(keyword.lower() in resp.lower() for keyword in context_keywords):
            contextual_responses.append(f"Réponse {i}")
    
    if contextual_responses:
        print(f"   ✅ Contexte maintenu dans: {', '.join(contextual_responses)}")
    else:
        print("   ❌ PERTE DE CONTEXTE - Aucune référence au lead")
    
    # 7. Récupération de l'historique pour vérifier la mémoire
    print("\n📝 6. Vérification mémoire conversationnelle...")
    response = requests.get(f"{API_BASE}/sandbox/conversations/{lead_id}/{session_id}")
    if response.status_code == 200:
        messages = response.json()["messages"]
        print(f"   ✅ Historique récupéré: {len(messages)} messages")
        
        # Vérifie si l'historique est transmis correctement
        for i, msg in enumerate(messages):
            print(f"   📜 Message {i+1}: {msg['messages'].get('user', 'N/A')[:50]}...")
    else:
        print(f"   ❌ Erreur récupération historique: {response.status_code}")
    
    print("\n" + "=" * 70)
    print("📊 DIAGNOSTIC TERMINÉ")
    print("=" * 70)

if __name__ == "__main__":
    test_conversation_memory_problem()

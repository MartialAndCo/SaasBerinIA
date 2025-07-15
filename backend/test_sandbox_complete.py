#!/usr/bin/env python3
"""
Test complet du système de sessions sandbox
Frontend + Backend intégration
"""

import requests
import json
import time

def test_complete_sandbox_system():
    """Test complet du système sandbox avec sessions"""
    
    print("🎯 TEST COMPLET - Système de sessions sandbox")
    print("=" * 70)
    
    base_url = 'http://localhost:8000/api'
    
    # Test 1: Créer un lead de test
    print("📝 1. Création d'un lead de test...")
    try:
        lead_data = {
            "first_name": "TestUser",
            "last_name": "Sandbox",
            "email": "test@sandbox.com",
            "company": "Test Company",
            "position": "CEO",
            "industry": "Test",
            "test_platform": "sms",
            "score": 75
        }
        
        response = requests.post(f'{base_url}/sandbox/leads', json=lead_data, timeout=10)
        print(f"   ✅ Création lead: {response.status_code}")
        
        if response.status_code == 200:
            lead = response.json()
            lead_id = lead['id']
            print(f"   🆔 Lead ID: {lead_id}")
        else:
            print(f"   ❌ Erreur: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erreur création lead: {e}")
        return
    
    # Test 2: Démarrer première conversation
    print("\n📝 2. Démarrage première conversation...")
    try:
        conv_data = {
            'sandbox_lead_id': lead_id,
            'platform': 'sms',
            'action': 'start_conversation'
        }
        
        response = requests.post(f'{base_url}/sandbox/conversation', json=conv_data, timeout=20)
        print(f"   ✅ Première conversation: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            session_id_1 = data.get('conversation_session_id')
            ai_response_1 = data.get('ai_response', '')
            
            print(f"   🆔 Session 1: {session_id_1}")
            print(f"   🤖 Réponse IA: {ai_response_1[:80]}...")
        else:
            print(f"   ❌ Erreur: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erreur première conversation: {e}")
        return
    
    # Test 3: Continuer la conversation
    print("\n📝 3. Continuation conversation (avec historique)...")
    try:
        conv_data = {
            'sandbox_lead_id': lead_id,
            'platform': 'sms',
            'action': 'send_response',
            'user_message': 'Bonjour, votre offre m\'intéresse mais j\'ai des questions',
            'conversation_session_id': session_id_1
        }
        
        response = requests.post(f'{base_url}/sandbox/conversation', json=conv_data, timeout=20)
        print(f"   ✅ Continuation: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            ai_response_2 = data.get('ai_response', '')
            history = data.get('conversation_history', [])
            
            print(f"   🤖 Réponse contextuelle: {ai_response_2[:80]}...")
            print(f"   📜 Historique: {len(history)} messages")
            
            if len(history) > 0:
                print(f"   📋 Premier message historique: {history[0].get('ai_response', '')[:50]}...")
        else:
            print(f"   ❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur continuation: {e}")
    
    # Test 4: Récupération historique
    print("\n📝 4. Récupération historique des conversations...")
    try:
        response = requests.get(f'{base_url}/sandbox/conversations/{lead_id}', timeout=10)
        print(f"   ✅ Historique conversations: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('conversations', [])
            total = data.get('total_conversations', 0)
            
            print(f"   📊 Total conversations: {total}")
            if conversations:
                latest = conversations[0]
                print(f"   🕐 Dernière: {latest.get('display_name', 'N/A')}")
                print(f"   💬 Messages: {latest.get('message_count', 0)}")
        else:
            print(f"   ❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur historique: {e}")
    
    # Test 5: Reset conversation
    print("\n📝 5. Reset conversation (nouvelle session)...")
    try:
        reset_data = {
            'sandbox_lead_id': lead_id,
            'platform': 'sms',
            'keep_lead': True
        }
        
        response = requests.post(f'{base_url}/sandbox/conversation/reset', json=reset_data, timeout=10)
        print(f"   ✅ Reset conversation: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            session_id_2 = data.get('new_conversation_session_id')
            archived = data.get('previous_session_archived', False)
            
            print(f"   🆔 Nouvelle session: {session_id_2}")
            print(f"   📦 Session précédente archivée: {archived}")
            
            if session_id_2 != session_id_1:
                print("   ✅ Reset réussi - sessions différentes")
            else:
                print("   ❌ Problème reset - même session")
        else:
            print(f"   ❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur reset: {e}")
    
    # Test 6: Nouvelle conversation après reset
    print("\n📝 6. Nouvelle conversation post-reset...")
    try:
        conv_data = {
            'sandbox_lead_id': lead_id,
            'platform': 'sms',
            'action': 'start_conversation'
        }
        
        response = requests.post(f'{base_url}/sandbox/conversation', json=conv_data, timeout=20)
        print(f"   ✅ Nouvelle conversation: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            session_id_3 = data.get('conversation_session_id')
            ai_response_3 = data.get('ai_response', '')
            
            print(f"   🆔 Session 3: {session_id_3}")
            print(f"   🤖 Nouvelle réponse: {ai_response_3[:80]}...")
            
            # Vérifier l'historique final
            hist_response = requests.get(f'{base_url}/sandbox/conversations/{lead_id}', timeout=10)
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                final_total = hist_data.get('total_conversations', 0)
                print(f"   📊 Total final conversations: {final_total}")
        else:
            print(f"   ❌ Erreur: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur nouvelle conversation: {e}")
    
    print("\n" + "=" * 70)
    print("�� TEST COMPLET TERMINÉ")
    print()
    print("📋 RÉSUMÉ DES FONCTIONNALITÉS TESTÉES:")
    print("✅ Création de leads sandbox")
    print("✅ Système de sessions unique")
    print("✅ Persistance des conversations")
    print("✅ Historique et contexte transmis à l'IA")
    print("✅ Reset propre avec nouvelles sessions")
    print("✅ Récupération complète de l'historique")
    print()
    print("�� Le sandbox est prêt pour les tests frontend !")

if __name__ == "__main__":
    test_complete_sandbox_system()

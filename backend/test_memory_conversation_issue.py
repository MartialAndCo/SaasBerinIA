#!/usr/bin/env python3
"""
Test spécifique pour reproduire le problème de mémoire conversationnelle de Louise
Elle dit "Bonjour Pierre" à chaque message au lieu de continuer la conversation
"""

import sys
import os
sys.path.append('/root/berinia/infra-ia')
sys.path.append('/root/berinia/backend')

from agents.messaging.messaging_agent import MessagingAgent
import json

def test_conversation_memory_issue():
    """
    Reproduit exactement le problème signalé par l'utilisateur
    """
    print("🐛 REPRODUCTION DU PROBLÈME - Mémoire conversationnelle Louise")
    print("=" * 70)
    
    # Initialiser l'agent
    agent = MessagingAgent()
    
    # Lead Pierre Moreau (plombier)
    pierre_lead = {
        "lead_id": 99,  # ID fixe pour ce test
        "first_name": "Pierre",
        "last_name": "Moreau", 
        "email": "pierre@plomberie-moreau.fr",
        "phone": "+33612345678",
        "company": "Plomberie Moreau",
        "position": "Gérant",
        "industry": "plombier",
        "score": 8
    }
    
    print(f"👤 Lead test: {pierre_lead['first_name']} {pierre_lead['last_name']} - {pierre_lead['company']}")
    print()
    
    # Simuler la conversation étape par étape
    messages = [
        {
            "step": 1,
            "description": "Message initial de Louise (premier contact)",
            "from_user": False,
            "message": "Bonjour Pierre,\n\nJe me permets de vous contacter car votre entreprise Plomberie Moreau, reconnue dans l'artisanat, pourrait bénéficier de nos solutions d'automatisation spécialement adaptées aux artisans plombiers souhaitant optimiser leur présence en ligne et leur gestion client. Seriez-vous disponible pour un bref échange ?\n\nCordialement,\nLouise de BerinIA"
        },
        {
            "step": 2,
            "description": "Réponse du prospect Pierre",
            "from_user": True,
            "message": "abon?"
        },
        {
            "step": 3,
            "description": "Réponse de Louise (PROBLÈME: elle dit encore 'Bonjour Pierre')",
            "from_user": False,
            "expected_problem": "Bonjour Pierre",
            "message": "Bonjour Pierre, chez BerinIA, on automatise la prospection, la gestion des rendez-vous et la communication pour les artisans comme vous, pour gagner du temps et attirer plus de clients. Souhaitez-vous en savoir plus ?"
        },
        {
            "step": 4,
            "description": "Deuxième question du prospect",
            "from_user": True, 
            "message": "ca peut m'aider en quoi?"
        }
    ]
    
    # Simuler l'insertion des premiers messages dans la base
    print("📝 Simulation de l'insertion des messages dans la base...")
    
    # Message 1: Louise -> Pierre (initial)
    agent._save_message_to_db(
        pierre_lead,
        {"content": messages[0]["message"], "subject": "Contact BerinIA"},
        "test_campaign",
        "email"
    )
    
    # Message 2: Pierre -> Louise (réponse)
    try:
        from core.db import DatabaseService
        db = DatabaseService()
        
        # Insérer directement le message entrant du prospect
        insert_query = """
            INSERT INTO messages (
                lead_id, lead_name, lead_email, content, type, status,
                direction, sender_type, sent_date, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
        """
        
        db.execute_query(insert_query, (
            pierre_lead["lead_id"],
            f"{pierre_lead['first_name']} {pierre_lead['last_name']}",
            pierre_lead["email"],
            messages[1]["message"],  # "abon?"
            "reply",
            "received",
            "inbound",
            "user"
        ))
        
        print(f"   ✅ Messages 1-2 insérés en base")
        
    except Exception as e:
        print(f"   ⚠️ Erreur insertion: {e}")
    
    print()
    
    # Maintenant, tester la génération de réponse contextuelle
    print("🧠 Test de génération de réponse contextuelle...")
    print("=" * 50)
    
    # Input pour la génération de réponse
    input_data = {
        "lead_data": pierre_lead,
        "message": messages[3]["message"],  # "ca peut m'aider en quoi?"
        "campaign_id": "test_campaign",
        "channel": "sms",
        "subject": "Contact BerinIA"
    }
    
    # Tester la récupération de l'historique d'abord
    print("📜 Test récupération historique...")
    history = agent.get_conversation_history(str(pierre_lead["lead_id"]), limit=10)
    print(f"   🔍 Historique récupéré: {len(history)} messages")
    
    for i, msg in enumerate(history):
        direction = "🤖 Louise" if msg.get("direction") == "outbound" else "👤 Pierre"
        content_preview = msg.get("content", "")[:50] + "..." if len(msg.get("content", "")) > 50 else msg.get("content", "")
        print(f"   {i+1}. {direction}: {content_preview}")
    
    print()
    
    # Générer la réponse contextuelle
    print("🎯 Génération de la réponse contextuelle...")
    response = agent.generate_contextual_response(input_data)
    
    print(f"📤 Réponse générée par Louise:")
    print(f"   \"{response}\"")
    print()
    
    # Analyser le problème
    print("🔍 ANALYSE DU PROBLÈME:")
    print("=" * 30)
    
    if "Bonjour Pierre" in response:
        print("❌ PROBLÈME CONFIRMÉ: Louise dit encore 'Bonjour Pierre'")
        print("   Elle ne comprend pas que la conversation a déjà commencé")
    else:
        print("✅ Pas de 'Bonjour Pierre' détecté")
    
    if "abon" in response.lower() or "abonnement" in response.lower():
        print("✅ Louise fait référence à la question précédente")
    else:
        print("❌ Louise ne fait pas référence à 'abon?'")
    
    # Analyser la mémoire conversationnelle
    conversation_context_indicators = [
        "vous avez demandé", "votre question", "comme vous le mentionniez",
        "suite à votre message", "pour répondre à", "concernant votre demande"
    ]
    
    has_context = any(indicator in response.lower() for indicator in conversation_context_indicators)
    
    if has_context:
        print("✅ Louise montre une conscience du contexte conversationnel")
    else:
        print("❌ Louise ne montre pas de conscience du contexte")
    
    print()
    print("🎯 DIAGNOSTIC:")
    print("=" * 15)
    
    if "Bonjour Pierre" in response:
        print("🚨 PROBLÈME PRINCIPAL: Louise traite chaque message comme un premier contact")
        print("📋 CAUSE PROBABLE:")
        print("   - Le prompt ne dit pas assez clairement de ne pas répéter les salutations")
        print("   - L'historique est récupéré mais mal utilisé dans le prompt")
        print("   - Le LLM ne comprend pas le contexte conversationnel")
        
        print("🔧 SOLUTIONS À IMPLÉMENTER:")
        print("   1. Modifier le prompt pour être explicite sur les salutations")
        print("   2. Ajouter des instructions claires sur la continuité conversationnelle")
        print("   3. Mieux structurer l'historique dans le prompt")
    else:
        print("✅ Louise gère correctement la continuité conversationnelle")

if __name__ == "__main__":
    test_conversation_memory_issue()

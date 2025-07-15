#!/usr/bin/env python3
"""
TEST SIMPLE ET EFFICACE - Mémoire conversationnelle de Louise
Test si Louise se souvient de ce qui a été dit dans la conversation
"""

import sys
import os
sys.path.append('/root/berinia/infra-ia')
sys.path.append('/root/berinia/backend')

from agents.messaging.messaging_agent import MessagingAgent
from core.db import DatabaseService
import datetime
import json

def test_real_memory():
    """
    Test SIMPLE : Est-ce que Louise se souvient de ce qui a été dit ?
    """
    print("🧠 TEST SIMPLE - Mémoire conversationnelle Louise")
    print("=" * 60)
    
    # Nettoyer les anciens tests
    db = DatabaseService()
    try:
        db.execute_query("DELETE FROM messages WHERE lead_id = 888")
    except Exception:
        pass  # Si pas de messages à supprimer, on continue
    
    agent = MessagingAgent()
    
    # Lead de test
    lead = {
        "lead_id": 888,
        "first_name": "Marc",
        "last_name": "Durand", 
        "email": "marc@garage-durand.fr",
        "phone": "+33612345678",
        "company": "Garage Durand",
        "industry": "garage automobile"
    }
    
    print(f"👤 Lead: {lead['first_name']} {lead['last_name']} - {lead['company']}")
    print()
    
    # 1. MESSAGE INITIAL de Louise
    msg1_louise = "Bonjour Marc, chez BerinIA nous aidons les garages comme Garage Durand à automatiser leur gestion client. Êtes-vous intéressé ?"
    
    # Sauver en base
    agent._save_message_to_db(
        lead,
        {"content": msg1_louise, "subject": "BerinIA - Automatisation garage"},
        "test_campaign",
        "sms"
    )
    print(f"1️⃣ Louise → Marc: {msg1_louise}")
    
    # 2. RÉPONSE de Marc avec info spécifique 
    msg2_marc = "Oui ça m'intéresse, j'ai 15 employés et on galère avec les rendez-vous"
    
    # Insérer message entrant
    try:
        from app.database.session import SessionLocal
        from sqlalchemy import text
        
        db_session = SessionLocal()
        insert_sql = text("""
            INSERT INTO messages (
                lead_id, lead_name, lead_email, content, type, status,
                direction, sender_type, sent_date, created_at, updated_at
            ) VALUES (:lead_id, :lead_name, :lead_email, :content, :type, :status, :direction, :sender_type, NOW(), NOW(), NOW())
        """)
        
        db_session.execute(insert_sql, {
            "lead_id": lead["lead_id"],
            "lead_name": f"{lead['first_name']} {lead['last_name']}",
            "lead_email": lead["email"],
            "content": msg2_marc,
            "type": "reply",
            "status": "received",
            "direction": "inbound", 
            "sender_type": "user"
        })
        db_session.commit()
        db_session.close()
    except Exception as e:
        print(f"   ⚠️ Erreur insertion message: {e}")
    print(f"2️⃣ Marc → Louise: {msg2_marc}")
    
    # 3. RÉPONSE de Louise
    input_data = {
        "lead_data": lead,
        "message": msg2_marc,
        "campaign_id": "test_campaign",
        "channel": "sms"
    }
    
    msg3_louise = agent.generate_contextual_response(input_data)
    print(f"3️⃣ Louise → Marc: {msg3_louise}")
    
    # Sauver en base
    agent._save_message_to_db(
        lead,
        {"content": msg3_louise},
        "test_campaign", 
        "sms"
    )
    
    # 4. Marc pose une QUESTION DE MÉMOIRE
    msg4_marc = "Rappelez-moi, de combien d'employés j'ai parlé ?"
    
    # Insérer en base
    try:
        db_session = SessionLocal()
        insert_sql = text("""
            INSERT INTO messages (
                lead_id, lead_name, lead_email, content, type, status,
                direction, sender_type, sent_date, created_at, updated_at
            ) VALUES (:lead_id, :lead_name, :lead_email, :content, :type, :status, :direction, :sender_type, NOW(), NOW(), NOW())
        """)
        
        db_session.execute(insert_sql, {
            "lead_id": lead["lead_id"],
            "lead_name": f"{lead['first_name']} {lead['last_name']}",
            "lead_email": lead["email"],
            "content": msg4_marc,
            "type": "reply",
            "status": "received",
            "direction": "inbound",
            "sender_type": "user"
        })
        db_session.commit()
        db_session.close()
    except Exception as e:
        print(f"   ⚠️ Erreur insertion message 4: {e}")
    print(f"4️⃣ Marc → Louise: {msg4_marc}")
    
    # 5. TEST DE MÉMOIRE : Louise se souvient-elle ?
    input_data_memory = {
        "lead_data": lead,
        "message": msg4_marc,
        "campaign_id": "test_campaign",
        "channel": "sms"
    }
    
    msg5_louise = agent.generate_contextual_response(input_data_memory)
    print(f"5️⃣ Louise → Marc: {msg5_louise}")
    
    print()
    print("🔍 ANALYSE DE LA MÉMOIRE:")
    print("=" * 30)
    
    # Test si Louise se souvient du nombre d'employés
    if "15" in msg5_louise:
        print("✅ EXCELLENTE MÉMOIRE: Louise se souvient des 15 employés")
    else:
        print("❌ PROBLÈME MÉMOIRE: Louise ne se souvient pas des 15 employés")
    
    # Test si elle fait référence à la conversation précédente
    memory_indicators = [
        "vous avez mentionné", "vous avez dit", "comme vous l'avez précisé",
        "15 employés", "15", "quinze", "vous parliez"
    ]
    
    has_memory = any(indicator in msg5_louise.lower() for indicator in memory_indicators)
    
    if has_memory:
        print("✅ CONTEXTE: Louise fait référence à la conversation précédente")
    else:
        print("❌ CONTEXTE: Louise ne fait pas référence aux échanges précédents")
    
    # Vérifier l'historique récupéré
    print()
    print("📜 VÉRIFICATION HISTORIQUE:")
    history = agent.get_conversation_history(str(lead["lead_id"]), limit=10)
    print(f"   🔍 Messages récupérés: {len(history)}")
    
    if len(history) >= 3:
        print("✅ HISTORIQUE: Récupération OK")
        for i, msg in enumerate(history):
            direction = "🤖" if msg.get("direction") == "outbound" else "👤"
            content = msg.get("content", "")[:40] + "..." if len(msg.get("content", "")) > 40 else msg.get("content", "")
            print(f"   {i+1}. {direction} {content}")
    else:
        print("❌ HISTORIQUE: Récupération incomplète")
    
    print()
    print("🎯 DIAGNOSTIC FINAL:")
    print("=" * 20)
    
    if "15" in msg5_louise and has_memory:
        print("🎉 MÉMOIRE PARFAITE: Louise se souvient parfaitement de la conversation")
    elif "15" in msg5_louise:
        print("⚠️ MÉMOIRE PARTIELLE: Louise se souvient du chiffre mais pas du contexte")
    else:
        print("🚨 MÉMOIRE DÉFAILLANTE: Louise ne se souvient de rien")
        print("🔧 PROBLÈME: L'historique n'est pas correctement utilisé dans le prompt")

if __name__ == "__main__":
    test_real_memory()

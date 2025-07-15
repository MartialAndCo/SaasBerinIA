#!/usr/bin/env python3
"""
Test pour vérifier si le MessagingAgent gère correctement les thread_id
"""

import sys
sys.path.append('/root/berinia/backend')
from app.database.session import SessionLocal
from sqlalchemy import text
import hashlib

def test_messaging_agent_thread_logic():
    """Teste la logique de thread_id du MessagingAgent"""
    db = SessionLocal()
    try:
        print("🔍 Test de la logique thread_id du MessagingAgent")
        print("=" * 50)
        
        # 1. Vérifier les colonnes de la table messages
        print("📋 Structure de la table messages:")
        columns = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'messages' AND column_name = 'thread_id'
        """)).fetchall()
        
        has_thread_id = len(columns) > 0
        print(f"   - Colonne thread_id présente: {'✅' if has_thread_id else '❌'}")
        
        if not has_thread_id:
            print("   ❌ La table messages n'a pas de colonne thread_id !")
            return
        
        # 2. Vérifier les messages existants
        print("\n📨 Analyse des messages existants:")
        
        # Messages avec thread_id
        with_thread = db.execute(text("""
            SELECT COUNT(*) as count FROM messages WHERE thread_id IS NOT NULL
        """)).scalar()
        
        # Messages sans thread_id
        without_thread = db.execute(text("""
            SELECT COUNT(*) as count FROM messages WHERE thread_id IS NULL
        """)).scalar()
        
        total_messages = with_thread + without_thread
        
        print(f"   - Messages avec thread_id: {with_thread}")
        print(f"   - Messages sans thread_id: {without_thread}")
        print(f"   - Total messages: {total_messages}")
        
        # 3. Analyser les conversations par thread
        print("\n💬 Analyse des conversations:")
        
        conversations = db.execute(text("""
            SELECT thread_id, COUNT(*) as message_count
            FROM messages 
            WHERE thread_id IS NOT NULL
            GROUP BY thread_id
            ORDER BY COUNT(*) DESC
        """)).fetchall()
        
        print(f"   - Nombre de conversations (threads): {len(conversations)}")
        
        if conversations:
            for conv in conversations[:5]:  # Top 5 conversations
                print(f"   - Thread {conv.thread_id}: {conv.message_count} messages")
        
        # 4. Vérifier les leads sans conversation
        print("\n👥 Leads et conversations:")
        
        leads_with_messages = db.execute(text("""
            SELECT l.id, l.first_name, l.last_name, l.email,
                   COUNT(m.id) as message_count,
                   STRING_AGG(DISTINCT m.thread_id, ', ') as thread_ids
            FROM leads l
            LEFT JOIN messages m ON l.id = m.lead_id
            GROUP BY l.id, l.first_name, l.last_name, l.email
            ORDER BY COUNT(m.id) DESC
        """)).fetchall()
        
        for lead in leads_with_messages:
            if lead.message_count > 0:
                thread_status = "✅" if lead.thread_ids and lead.thread_ids != "None" else "❌"
                print(f"   {thread_status} {lead.first_name} {lead.last_name}: {lead.message_count} messages, threads: {lead.thread_ids or 'AUCUN'}")
        
        # 5. Test de la génération de thread_id
        print("\n🧪 Test de génération de thread_id:")
        
        def generate_thread_id(lead_email, lead_name):
            """Génère un thread_id unique basé sur le lead"""
            base = (lead_email or lead_name or "unknown").lower()
            return "thread_" + hashlib.md5(base.encode()).hexdigest()[:8]
        
        test_leads = [
            {"email": "test@example.com", "name": "Test User"},
            {"email": "john@company.com", "name": "John Doe"},
            {"email": "test@example.com", "name": "Test User"},  # Même lead
        ]
        
        for lead in test_leads:
            thread_id = generate_thread_id(lead["email"], lead["name"])
            print(f"   - {lead['name']} ({lead['email']}) → {thread_id}")
        
        print("\n✅ Test terminé !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_messaging_agent_thread_logic()

#!/usr/bin/env python3
"""
Script pour ajouter des thread_id aux messages existants
Chaque lead (personne) aura son propre thread_id unique
"""

import sys
sys.path.append('/root/berinia/backend')
from app.database.session import SessionLocal
from sqlalchemy import text
import hashlib

def generate_thread_id(lead_email, lead_name):
    """Génère un thread_id unique basé sur le lead"""
    # Utilise l'email ou le nom pour créer un ID unique
    base = (lead_email or lead_name or "unknown").lower()
    return "thread_" + hashlib.md5(base.encode()).hexdigest()[:8]

def fix_thread_ids():
    """Ajoute des thread_id aux messages existants"""
    db = SessionLocal()
    try:
        # Récupère tous les messages sans thread_id
        messages = db.execute(text("""
            SELECT id, lead_id, lead_name, lead_email 
            FROM messages 
            WHERE thread_id IS NULL
            ORDER BY lead_email, lead_name
        """)).fetchall()
        
        print(f"Trouvé {len(messages)} messages sans thread_id")
        
        # Groupe par lead et assigne des thread_id
        updated_count = 0
        thread_assignments = {}
        
        for msg in messages:
            # Crée une clé unique pour chaque lead
            lead_key = f"{msg.lead_email or 'no-email'}_{msg.lead_name or 'no-name'}"
            
            # Si c'est la première fois qu'on voit ce lead, créer un thread_id
            if lead_key not in thread_assignments:
                thread_id = generate_thread_id(msg.lead_email, msg.lead_name)
                thread_assignments[lead_key] = thread_id
                print(f"Nouveau thread_id '{thread_id}' pour {msg.lead_name} ({msg.lead_email})")
            
            # Met à jour le message avec le thread_id
            thread_id = thread_assignments[lead_key]
            db.execute(text("""
                UPDATE messages 
                SET thread_id = :thread_id 
                WHERE id = :message_id
            """), {"thread_id": thread_id, "message_id": msg.id})
            
            updated_count += 1
        
        db.commit()
        print(f"\n✅ Mis à jour {updated_count} messages avec des thread_id")
        print(f"✅ Créé {len(thread_assignments)} conversations distinctes")
        
        # Vérification
        verification = db.execute(text("""
            SELECT COUNT(DISTINCT thread_id) as conversations,
                   COUNT(*) as total_messages
            FROM messages 
            WHERE thread_id IS NOT NULL
        """)).fetchone()
        
        print(f"\n📊 Vérification:")
        print(f"   - {verification.conversations} conversations")
        print(f"   - {verification.total_messages} messages avec thread_id")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Correction des thread_id pour les conversations")
    print("=" * 50)
    fix_thread_ids()

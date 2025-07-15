#!/usr/bin/env python3
"""
Script de vérification des mises à jour dans la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.database.session import SessionLocal

def verify_updates():
    """Vérifie les mises à jour dans la base de données"""
    
    new_email = "yannrosemark@gmail.com"
    new_phone = "+33695472237"
    
    db = SessionLocal()
    
    try:
        print("🔍 VÉRIFICATION DES MISES À JOUR")
        print("=" * 50)
        
        # Vérifications avec SQL brut pour éviter les problèmes de modèles
        verifications = [
            ("SELECT COUNT(*) FROM leads WHERE email = :email", "📊 Leads avec le nouvel email"),
            ("SELECT COUNT(*) FROM leads WHERE phone = :phone", "📱 Leads avec le nouveau téléphone"),
            ("SELECT COUNT(*) FROM users WHERE email = :email", "👥 Users avec le nouvel email"),
            ("SELECT COUNT(*) FROM messages WHERE lead_email = :email", "💬 Messages avec le nouvel email"),
        ]
        
        for sql, description in verifications:
            try:
                result = db.execute(text(sql), {"email": new_email, "phone": new_phone})
                count = result.scalar()
                print(f"{description}: {count}")
            except Exception as e:
                print(f"{description}: ❌ Erreur - {e}")
        
        print("\n" + "=" * 50)
        print("✅ Vérification terminée")
        
    except Exception as e:
        print(f"❌ ERREUR : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_updates()

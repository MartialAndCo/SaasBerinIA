#!/usr/bin/env python3
"""
Script simple pour mettre à jour tous les emails et numéros de téléphone dans la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.database.session import SessionLocal

def update_contact_info():
    """Met à jour tous les emails et numéros de téléphone dans la base de données"""
    
    new_email = "yannrosemark@gmail.com"
    new_phone = "+33695472237"
    
    db = SessionLocal()
    
    try:
        print("🔄 Début de la mise à jour des informations de contact...")
        
        # Utilisation de requêtes SQL directes
        sql_updates = [
            ("UPDATE leads SET email = :email WHERE email IS NOT NULL", "📊 leads (email)"),
            ("UPDATE leads SET phone = :phone WHERE phone IS NOT NULL", "📱 leads (phone)"),
            ("UPDATE users SET email = :email WHERE email IS NOT NULL", "👥 users (email)"),
            ("UPDATE messages SET lead_email = :email WHERE lead_email IS NOT NULL", "💬 messages (lead_email)"),
        ]
        
        total_updated = 0
        for sql, description in sql_updates:
            print(f"\n🔧 Mise à jour de {description}...")
            result = db.execute(text(sql), {"email": new_email, "phone": new_phone})
            count = result.rowcount
            total_updated += count
            print(f"   ✅ {count} lignes mises à jour")
        
        # Commit des changements IMMÉDIATEMENT
        db.commit()
        print(f"\n✅ SUCCÈS : Transaction committée")
        print(f"✅ SUCCÈS : Total de {total_updated} lignes mises à jour")
        print(f"✅ SUCCÈS : Tous les emails ont été changés pour '{new_email}'")
        print(f"✅ SUCCÈS : Tous les téléphones ont été changés pour '{new_phone}'")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 MISE À JOUR DES INFORMATIONS DE CONTACT")
    print("=" * 60)
    print(f"📧 Nouveau email : yannrosemark@gmail.com")
    print(f"📱 Nouveau téléphone : +33695472237")
    print("=" * 60)
    
    confirm = input("\n⚠️  Confirmer la mise à jour ? (oui/non) : ").lower().strip()
    
    if confirm in ['oui', 'o', 'yes', 'y']:
        success = update_contact_info()
        if success:
            print("\n🎉 Mise à jour terminée avec succès !")
        else:
            print("\n💥 Échec de la mise à jour")
            sys.exit(1)
    else:
        print("\n❌ Mise à jour annulée")
        sys.exit(0)

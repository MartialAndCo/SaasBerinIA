#!/usr/bin/env python3
"""
Script pour mettre à jour tous les emails et numéros de téléphone dans la base de données
avec les nouvelles valeurs : yannrosemark@gmail.com et +33695472237
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database.session import SessionLocal
from app.models.lead import Lead
from app.models.user import User
from app.models.message import Message
from app.models.system_settings import SystemIntegrations

def update_contact_info():
    """Met à jour tous les emails et numéros de téléphone dans la base de données"""
    
    new_email = "yannrosemark@gmail.com"
    new_phone = "+33695472237"
    
    db = SessionLocal()
    
    try:
        print("🔄 Début de la mise à jour des informations de contact...")
        
        # Utilisation de requêtes SQL directes pour éviter les problèmes d'auto-update
        sql_updates = [
            # 1. Mise à jour de la table leads
            ("UPDATE leads SET email = :email WHERE email IS NOT NULL", "📊 leads (email)"),
            ("UPDATE leads SET phone = :phone WHERE phone IS NOT NULL", "📱 leads (phone)"),
            
            # 2. Mise à jour de la table users
            ("UPDATE users SET email = :email WHERE email IS NOT NULL", "👥 users (email)"),
            
            # 3. Mise à jour de la table messages
            ("UPDATE messages SET lead_email = :email WHERE lead_email IS NOT NULL", "💬 messages (lead_email)"),
            
            # 4. Mise à jour de la table system_integrations
            ("UPDATE system_integrations SET from_email = :email WHERE from_email IS NOT NULL", "⚙️ system_integrations (from_email)"),
        ]
        
        total_updated = 0
        for sql, description in sql_updates:
            try:
                print(f"\n🔧 Mise à jour de {description}...")
                result = db.execute(text(sql), {"email": new_email, "phone": new_phone})
                count = result.rowcount
                total_updated += count
                print(f"   ✅ {count} lignes mises à jour")
            except Exception as e:
                print(f"   ⚠️ Erreur (table peut-être vide) : {e}")
        
        # Commit des changements
        db.commit()
        print(f"\n✅ SUCCÈS : Tous les emails ont été changés pour '{new_email}'")
        print(f"✅ SUCCÈS : Tous les téléphones ont été changés pour '{new_phone}'")
        
        # Vérification
        print("\n🔍 Vérification des changements...")
        lead_count = db.query(Lead).filter(Lead.email == new_email).count()
        user_count = db.query(User).filter(User.email == new_email).count()
        message_count = db.query(Message).filter(Message.lead_email == new_email).count()
        
        print(f"   📊 Leads avec le nouvel email : {lead_count}")
        print(f"   👥 Users avec le nouvel email : {user_count}")
        print(f"   💬 Messages avec le nouvel email : {message_count}")
        
        phone_count = db.query(Lead).filter(Lead.phone == new_phone).count()
        print(f"   📱 Leads avec le nouveau téléphone : {phone_count}")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

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

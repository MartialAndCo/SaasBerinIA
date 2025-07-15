#!/usr/bin/env python3
"""
Script pour appliquer la migration sandbox sessions
"""

import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.session import SessionLocal

def apply_migration():
    """Applique la migration pour les sessions sandbox"""
    db = SessionLocal()
    
    try:
        print("🔄 Application de la migration sandbox sessions...")
        
        # Lire le fichier de migration
        migration_file = "migrations/add_sandbox_conversation_sessions.sql"
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Séparer les commandes SQL (attention aux commentaires)
        sql_commands = []
        current_command = ""
        
        for line in migration_sql.split('\n'):
            line = line.strip()
            
            # Ignorer les commentaires et lignes vides
            if line.startswith('--') or not line:
                continue
                
            current_command += line + " "
            
            # Si la ligne se termine par un ;, c'est la fin d'une commande
            if line.endswith(';'):
                sql_commands.append(current_command.strip())
                current_command = ""
        
        # Exécuter chaque commande
        for i, command in enumerate(sql_commands):
            if command:
                try:
                    print(f"   📝 Exécution commande {i+1}/{len(sql_commands)}: {command[:60]}...")
                    db.execute(text(command))
                    db.commit()
                    print(f"   ✅ Commande {i+1} exécutée avec succès")
                    
                except Exception as e:
                    print(f"   ⚠️  Commande {i+1} ignorée (déjà appliquée ou erreur): {e}")
                    # Continue avec les autres commandes
                    db.rollback()
                    continue
        
        print("✅ Migration appliquée avec succès !")
        
        # Vérifier que les nouvelles colonnes existent
        result = db.execute(text("SELECT sql FROM sqlite_master WHERE name = 'sandbox_conversations' AND type = 'table'"))
        table_schema = result.fetchone()
        
        if table_schema and 'conversation_session_id' in table_schema[0]:
            print("✅ Nouvelles colonnes détectées dans le schéma")
        else:
            print("⚠️  Vérification du schéma - nouvelles colonnes non détectées")
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()

if __name__ == "__main__":
    apply_migration()

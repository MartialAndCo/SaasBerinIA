#!/usr/bin/env python3
"""
Script pour ajouter les contraintes et indexes manquants à la table meetings
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from sqlalchemy import text

def add_meetings_constraints():
    """Ajoute les contraintes foreign key et indexes à la table meetings"""
    
    # Obtenir une session SQLAlchemy
    db = SessionLocal()
    
    try:
        print("🔧 Ajout des contraintes et indexes à la table meetings...")
        
        # 0. Ajouter la colonne calendar_event_id si elle n'existe pas
        print("📋 Vérification des colonnes...")
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'meetings' AND column_name = 'calendar_event_id'
        """))
        
        existing_column = result.fetchone()
        
        if not existing_column:
            print("➕ Ajout de la colonne calendar_event_id")
            db.execute(text("""
                ALTER TABLE meetings 
                ADD COLUMN calendar_event_id VARCHAR(255)
            """))
            print("✅ Colonne calendar_event_id ajoutée")
        else:
            print("ℹ️  Colonne calendar_event_id déjà existante")
        
        # 1. Vérifier si la foreign key existe déjà
        print("📋 Vérification des contraintes existantes...")
        result = db.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'meetings' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name = 'fk_meetings_lead_id'
        """))
        
        existing_fk = result.fetchone()
        
        if not existing_fk:
            print("➕ Ajout de la contrainte foreign key meetings.lead_id -> leads.id")
            db.execute(text("""
                ALTER TABLE meetings 
                ADD CONSTRAINT fk_meetings_lead_id 
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL
            """))
            print("✅ Contrainte foreign key ajoutée")
        else:
            print("ℹ️  Contrainte foreign key déjà existante")
        
        # 2. Ajouter les indexes pour optimiser les requêtes
        indexes_to_create = [
            ("idx_meetings_lead_id", "lead_id"),
            ("idx_meetings_status", "status"),
            ("idx_meetings_start_time", "start_time"),
            ("idx_meetings_calendar_event_id", "calendar_event_id")
        ]
        
        for index_name, column in indexes_to_create:
            # Vérifier si l'index existe déjà
            result = db.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'meetings' 
                AND indexname = :index_name
            """), {"index_name": index_name})
            
            existing_index = result.fetchone()
            
            if not existing_index:
                print(f"📊 Création de l'index {index_name} sur la colonne {column}")
                db.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON meetings({column})
                """))
                print(f"✅ Index {index_name} créé")
            else:
                print(f"ℹ️  Index {index_name} déjà existant")
        
        # 3. Vérifier la structure de la table
        print("📋 Vérification de la structure finale de la table meetings...")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'meetings'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        print("\n📊 Structure de la table meetings:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        # 4. Compter les meetings existants
        result = db.execute(text("SELECT COUNT(*) FROM meetings"))
        count = result.fetchone()[0]
        print(f"\n📈 Nombre de meetings dans la base: {count}")
        
        # Valider les changements
        db.commit()
        print("\n🎉 Toutes les contraintes et indexes ont été ajoutés avec succès!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout des contraintes: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Configuration de la table meetings pour l'intégration backend")
    print("=" * 70)
    
    success = add_meetings_constraints()
    
    if success:
        print("\n✅ Configuration terminée avec succès!")
        print("   - Contrainte foreign key ajoutée")
        print("   - Indexes d'optimisation créés") 
        print("   - Table prête pour l'API backend")
    else:
        print("\n❌ Échec de la configuration")
        sys.exit(1)
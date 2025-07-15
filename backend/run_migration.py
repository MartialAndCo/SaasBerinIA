#!/usr/bin/env python3

import os
import sys
sys.path.append('/root/berinia/backend')

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le bon .env
load_dotenv('/root/berinia/infra-ia/.env')

# Configuration de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://berinia_user:berinia_pass@localhost/berinia")

print(f"🔗 Connexion à la base: {DATABASE_URL.replace('://', '://[USER]:[PASS]@').split('@')[1]}")

# Créer l'engine
engine = create_engine(DATABASE_URL)

# SQL à exécuter
migration_sql = """
-- 1. Ajouter les colonnes ville
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS ville VARCHAR;
ALTER TABLE niches ADD COLUMN IF NOT EXISTS ville VARCHAR;

-- 2. Migration des données existantes - CAMPAGNES
UPDATE campaigns SET 
    ville = CASE 
        WHEN name LIKE '%Paris%' THEN 'Paris'
        WHEN name LIKE '%Lyon%' THEN 'Lyon'
        WHEN name LIKE '%Marseille%' THEN 'Marseille'
        WHEN name LIKE '%Toulouse%' THEN 'Toulouse'
        WHEN name LIKE '%Nice%' THEN 'Nice'
        WHEN name LIKE '%Bordeaux%' THEN 'Bordeaux'
        WHEN name LIKE '%Lille%' THEN 'Lille'
        WHEN name LIKE '%Nantes%' THEN 'Nantes'
        WHEN name LIKE '%Strasbourg%' THEN 'Strasbourg'
        WHEN name LIKE '%Montpellier%' THEN 'Montpellier'
        ELSE NULL
    END
WHERE ville IS NULL;

-- 3. Nettoyage du champ name pour les campagnes
UPDATE campaigns SET 
    name = CASE 
        WHEN ville IS NOT NULL THEN 
            TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                name, 
                ' Paris', ''), 
                ' Lyon', ''), 
                ' Marseille', ''), 
                ' Toulouse', ''), 
                ' Nice', ''), 
                ' Bordeaux', ''), 
                ' Lille', ''), 
                ' Nantes', ''), 
                ' Strasbourg', ''), 
                ' Montpellier', ''))
        ELSE name
    END
WHERE ville IS NOT NULL;

-- 4. Migration des données existantes - NICHES  
UPDATE niches SET 
    ville = CASE 
        WHEN name LIKE '%Paris%' THEN 'Paris'
        WHEN name LIKE '%Lyon%' THEN 'Lyon'
        WHEN name LIKE '%Marseille%' THEN 'Marseille'
        WHEN name LIKE '%Toulouse%' THEN 'Toulouse'
        WHEN name LIKE '%Nice%' THEN 'Nice'
        WHEN name LIKE '%Bordeaux%' THEN 'Bordeaux'
        WHEN name LIKE '%Lille%' THEN 'Lille'
        WHEN name LIKE '%Nantes%' THEN 'Nantes'
        WHEN name LIKE '%Strasbourg%' THEN 'Strasbourg'
        WHEN name LIKE '%Montpellier%' THEN 'Montpellier'
        ELSE NULL
    END
WHERE ville IS NULL;

-- 5. Nettoyage du champ name pour les niches
UPDATE niches SET 
    name = CASE 
        WHEN ville IS NOT NULL THEN 
            TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                name, 
                ' Paris', ''), 
                ' Lyon', ''), 
                ' Marseille', ''), 
                ' Toulouse', ''), 
                ' Nice', ''), 
                ' Bordeaux', ''), 
                ' Lille', ''), 
                ' Nantes', ''), 
                ' Strasbourg', ''), 
                ' Montpellier', ''))
        ELSE name
    END
WHERE ville IS NOT NULL;
"""

try:
    with engine.connect() as connection:
        print("✅ Connexion réussie à la base de données")
        
        # Exécuter la migration en plusieurs parties pour une meilleure gestion d'erreurs
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"📝 Exécution de l'étape {i}/{len(statements)}")
                result = connection.execute(text(statement))
                if result.rowcount and result.rowcount > 0:
                    print(f"   ✅ {result.rowcount} lignes affectées")
                else:
                    print(f"   ✅ Commande exécutée")
        
        connection.commit()
        print("\n🎉 Migration terminée avec succès !")
        
        # Vérification des résultats
        print("\n📊 VÉRIFICATION DES RÉSULTATS :")
        
        # Campagnes migrées
        result = connection.execute(text("SELECT name, ville FROM campaigns WHERE ville IS NOT NULL LIMIT 5"))
        campaigns = result.fetchall()
        if campaigns:
            print("\n🎯 CAMPAGNES MIGRÉES :")
            for name, ville in campaigns:
                print(f"   - {name} | {ville}")
        
        # Niches migrées
        result = connection.execute(text("SELECT name, ville FROM niches WHERE ville IS NOT NULL LIMIT 5"))
        niches = result.fetchall()
        if niches:
            print("\n📂 NICHES MIGRÉES :")
            for name, ville in niches:
                print(f"   - {name} | {ville}")

except Exception as e:
    print(f"❌ Erreur lors de la migration : {e}")
    sys.exit(1)

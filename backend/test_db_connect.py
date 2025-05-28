#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion à la base de données.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Configuration de la connexion
db_user = "berinia_user"
db_password = "berinia_pass"
db_host = "localhost"
db_port = "5432"
db_name = "berinia"

# Construire l'URL de connexion
db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

print(f"Tentative de connexion à la base de données avec l'URL: {db_url.replace(db_password, '******')}")

try:
    # Créer le moteur SQLAlchemy
    engine = create_engine(db_url)
    
    # Tester la connexion avec une requête simple
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1 AS test"))
        row = result.fetchone()
        print(f"Connexion réussie! Résultat du test: {row[0]}")
        
        # Vérifier la présence de la table system_settings
        result = connection.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'system_settings')"))
        has_system_settings = result.scalar()
        if has_system_settings:
            print("La table system_settings existe.")
            
            # Vérifier les entrées pour Instantly.ai
            result = connection.execute(text("SELECT name, value FROM system_settings WHERE name LIKE 'instantly%'"))
            rows = result.fetchall()
            if rows:
                print("Paramètres Instantly.ai trouvés:")
                for row in rows:
                    print(f"  - {row[0]}: {row[1]}")
            else:
                print("Aucun paramètre Instantly.ai trouvé.")
        else:
            print("La table system_settings n'existe PAS.")
    
    print("Test de connexion terminé avec succès.")
except Exception as e:
    print(f"Erreur lors de la connexion à la base de données: {str(e)}")
    sys.exit(1)

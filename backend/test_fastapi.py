#!/usr/bin/env python3
"""
Application FastAPI minimale pour tester la connexion à la base de données.
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
db_user = os.getenv("DB_USER", "berinia_user")
db_password = os.getenv("DB_PASSWORD", "berinia_pass")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "berinia")

# URL de connexion SQLAlchemy
SQLALCHEMY_DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
print(f"URL de connexion: {SQLALCHEMY_DATABASE_URL.replace(db_password, '*****')}")

# Créer le moteur SQLAlchemy et la session
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Fonction de dépendance pour obtenir une session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Application FastAPI
app = FastAPI(title="DB Test API")

@app.get("/")
def read_root():
    return {"message": "API de test de connexion à la base de données"}

@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    """Test simple de la connexion à la base de données."""
    try:
        # Exécuter une requête simple
        result = db.execute(text("SELECT 1 AS test"))
        value = result.scalar()
        
        # Vérifier si la table system_settings existe
        result = db.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'system_settings')"
        ))
        has_system_settings = result.scalar()
        
        if has_system_settings:
            # Compter les entrées dans system_settings
            result = db.execute(text("SELECT COUNT(*) FROM system_settings"))
            count = result.scalar()
        else:
            count = None
        
        # Renvoyer les résultats
        return {
            "connection": "success",
            "test_query_result": value,
            "has_system_settings_table": has_system_settings,
            "system_settings_count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de base de données: {str(e)}")

@app.get("/pg-info")
def pg_info(db: Session = Depends(get_db)):
    """Obtenir des informations sur la configuration PostgreSQL."""
    try:
        # Version PostgreSQL
        result = db.execute(text("SELECT version()"))
        pg_version = result.scalar()
        
        # Configuration de l'authentification
        result = db.execute(text("SHOW hba_file"))
        hba_file = result.scalar()
        
        return {
            "postgresql_version": pg_version,
            "hba_file": hba_file,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des infos PG: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("Démarrage du serveur de test FastAPI...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

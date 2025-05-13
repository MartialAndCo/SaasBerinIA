"""
Module de connexion à la base de données pour le système BerinIA
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de la base de données
DB_USER = os.getenv("DB_USER", "berinia_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "berinia_pass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "berinia")

# Construction de l'URL de connexion
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL)

# Création d'une SessionLocal qui sera utilisée pour les requêtes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import de Base depuis models.py au lieu de le déclarer ici
from ..models.models import Base

# Fonction pour obtenir une session de base de données
def get_db():
    """
    Fonction de gestion de contexte pour obtenir une session de base de données.
    Utilisez cette fonction avec un gestionnaire de contexte 'with' pour les opérations de base de données.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Gestionnaire de contexte pour la session de base de données
@contextmanager
def db_session():
    """
    Gestionnaire de contexte pour une session de base de données.
    Gère automatiquement la création et la fermeture de la session ainsi que les transactions.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

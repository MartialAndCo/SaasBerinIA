"""
Connexion à la base de données et dépendances FastAPI
"""

from sqlalchemy.orm import Session
from app.database.session import SessionLocal

def get_db():
    """
    Dépendance FastAPI pour obtenir une session de base de données
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

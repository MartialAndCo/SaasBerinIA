"""
Module pour la gestion de la connexion à la base de données PostgreSQL
"""
import os
from typing import Any, Dict, List, Optional, Union
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis le fichier .env spécifique
load_dotenv("/root/berinia/infra-ia/.env")

# Configuration de la connexion à la base de données
DB_USER = os.getenv("DB_USER", "berinia_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "berinia_pass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "berinia")

# Création de l'URL de connexion
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Création de la base pour les modèles SQLAlchemy
Base = declarative_base()

# Création de l'engine SQLAlchemy
engine = sa.create_engine(DATABASE_URL)

# Création du sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    Fonction utilitaire pour obtenir une session de base de données
    
    Returns:
        Une session SQLAlchemy
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

class DatabaseService:
    """Service pour les interactions avec la base de données PostgreSQL"""
    
    @staticmethod
    def execute_query(query: str, params: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None) -> List[Dict[str, Any]]:
        """
        Exécute une requête SQL et retourne les résultats
        
        Args:
            query: La requête SQL à exécuter
            params: Les paramètres de la requête (dict ou liste de dicts)
            
        Returns:
            Liste des résultats (liste de dictionnaires)
        """
        with engine.connect() as connection:
            # Convertir la requête en TextClause
            sql = sa.text(query)
            
            # Exécuter la requête avec les paramètres
            if params is None:
                result = connection.execute(sql)
            else:
                result = connection.execute(sql, params)
                
            # Convertir les résultats en liste de dictionnaires
            return [dict(row._mapping) for row in result]
    
    @staticmethod
    def fetch_one(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Exécute une requête SQL et retourne le premier résultat

        Args:
            query: La requête SQL à exécuter
            params: Les paramètres de la requête

        Returns:
            Le premier résultat ou None
        """
        results = DatabaseService.execute_query(query, params)
        return results[0] if results else None
        
    @staticmethod
    def fetch_all(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Exécute une requête SQL et retourne tous les résultats
        
        Args:
            query: La requête SQL à exécuter
            params: Les paramètres de la requête
            
        Returns:
            Liste des résultats (liste de dictionnaires)
        """
        return DatabaseService.execute_query(query, params)
    
    @staticmethod
    def insert(table: str, data: Dict[str, Any]) -> int:
        """
        Insère des données dans une table
        
        Args:
            table: Le nom de la table
            data: Les données à insérer
            
        Returns:
            L'ID de la ligne insérée
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{key}" for key in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        
        with engine.connect() as connection:
            sql = sa.text(query)
            result = connection.execute(sql, data)
            connection.commit()
            return result.scalar_one()
    
    @staticmethod
    def update(table: str, id_: int, data: Dict[str, Any]) -> bool:
        """
        Met à jour des données dans une table
        
        Args:
            table: Le nom de la table
            id_: L'ID de la ligne à mettre à jour
            data: Les données à mettre à jour
            
        Returns:
            True si la mise à jour a réussi, False sinon
        """
        set_clause = ", ".join([f"{key} = :{key}" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = :id"
        
        with engine.connect() as connection:
            params = {**data, "id": id_}
            sql = sa.text(query)
            result = connection.execute(sql, params)
            connection.commit()
            return result.rowcount > 0
    
    @staticmethod
    def delete(table: str, id_: int) -> bool:
        """
        Supprime une ligne d'une table
        
        Args:
            table: Le nom de la table
            id_: L'ID de la ligne à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        query = f"DELETE FROM {table} WHERE id = :id"
        
        with engine.connect() as connection:
            sql = sa.text(query)
            result = connection.execute(sql, {"id": id_})
            connection.commit()
            return result.rowcount > 0

# Fonctions utilitaires pour l'accès à la base de données
def query_db(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Fonction utilitaire pour exécuter une requête SQL
    
    Args:
        query: La requête SQL
        params: Les paramètres
        
    Returns:
        Liste des résultats
    """
    return DatabaseService.execute_query(query, params)

def get_one(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Fonction utilitaire pour récupérer un seul résultat
    
    Args:
        query: La requête SQL
        params: Les paramètres
        
    Returns:
        Le résultat ou None
    """
    return DatabaseService.fetch_one(query, params)

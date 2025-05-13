#!/usr/bin/env python3
"""
Script d'initialisation de Qdrant pour le système BerinIA.

Ce script configure les collections Qdrant nécessaires pour stocker les connaissances
et les embeddings vectoriels utilisés dans le système.
"""
import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import time

try:
    import qdrant_client
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import VectorParams, Distance, OptimizersConfigDiff
    from qdrant_client.models import PointStruct, FieldCondition, Filter, MatchValue
except ImportError:
    print("La bibliothèque 'qdrant_client' n'est pas installée.")
    print("Installez-la avec 'pip install qdrant-client'")
    sys.exit(1)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/qdrant_init.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("BerinIA-QdrantInit")

# Charger la configuration
def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Charge la configuration depuis un fichier JSON
    
    Args:
        config_path: Chemin vers le fichier de configuration
        
    Returns:
        Configuration chargée
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        return config
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        return {}

# Création de la connexion au client Qdrant
def create_qdrant_client(config: Dict[str, Any]) -> QdrantClient:
    """
    Crée et configure le client Qdrant
    
    Args:
        config: Configuration pour la connexion
        
    Returns:
        Client Qdrant configuré
    """
    qdrant_config = config.get("qdrant", {})
    host = qdrant_config.get("host", "localhost")
    port = qdrant_config.get("port", 6333)
    
    # Tentative de connexion avec retry
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = QdrantClient(host=host, port=port)
            
            # Test de la connexion
            client.get_collections()
            
            logger.info(f"Connexion à Qdrant établie ({host}:{port})")
            return client
            
        except Exception as e:
            logger.warning(f"Tentative {attempt+1}/{max_retries} échouée: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Backoff exponentiel
            else:
                logger.error("Impossible de se connecter à Qdrant")
                raise
    
    raise ConnectionError("Impossible de se connecter à Qdrant après plusieurs tentatives")

# Création des collections nécessaires
def create_collections(client: QdrantClient, config: Dict[str, Any]) -> None:
    """
    Crée les collections nécessaires dans Qdrant
    
    Args:
        client: Client Qdrant
        config: Configuration du système
    """
    collections_config = config.get("qdrant", {}).get("collections", {})
    
    # Collection principale de connaissances
    knowledge_config = collections_config.get("knowledge", {})
    create_knowledge_collection(
        client, 
        "knowledge",
        vector_size=knowledge_config.get("vector_size", 1536),
        distance=knowledge_config.get("distance", "Cosine")
    )
    
    # Collection pour les documents et contextes
    docs_config = collections_config.get("documents", {})
    create_knowledge_collection(
        client, 
        "documents",
        vector_size=docs_config.get("vector_size", 1536),
        distance=docs_config.get("distance", "Cosine")
    )
    
    # Collection pour les embeddings de leads
    leads_config = collections_config.get("leads", {})
    create_knowledge_collection(
        client, 
        "leads",
        vector_size=leads_config.get("vector_size", 1536),
        distance=leads_config.get("distance", "Cosine")
    )
    
    # Collection pour les templates de messages
    templates_config = collections_config.get("templates", {})
    create_knowledge_collection(
        client, 
        "templates",
        vector_size=templates_config.get("vector_size", 1536),
        distance=templates_config.get("distance", "Cosine")
    )
    
    logger.info("Toutes les collections ont été créées/initialisées")

def create_knowledge_collection(
    client: QdrantClient, 
    collection_name: str, 
    vector_size: int = 1536, 
    distance: str = "Cosine"
) -> None:
    """
    Crée une collection pour stocker des connaissances
    
    Args:
        client: Client Qdrant
        collection_name: Nom de la collection
        vector_size: Taille des vecteurs d'embedding
        distance: Type de mesure de distance (Cosine, Euclid, Dot)
    """
    # Vérifier si la collection existe déjà
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if collection_name in collection_names:
        logger.info(f"Collection '{collection_name}' existe déjà")
        return
    
    # Conversion du type de distance
    distance_type = {
        "Cosine": Distance.COSINE,
        "Euclid": Distance.EUCLID, 
        "Dot": Distance.DOT
    }.get(distance, Distance.COSINE)
    
    # Création de la collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=distance_type
        ),
        optimizers_config=OptimizersConfigDiff(
            indexing_threshold=5000  # Seuil pour l'indexation automatique
        )
    )
    
    logger.info(f"Collection '{collection_name}' créée avec succès")
    
    # Création des index de payloads pour accélérer les recherches
    client.create_payload_index(
        collection_name=collection_name,
        field_name="category",
        field_schema="keyword"
    )
    
    client.create_payload_index(
        collection_name=collection_name,
        field_name="timestamp",
        field_schema="float"
    )
    
    client.create_payload_index(
        collection_name=collection_name,
        field_name="type",
        field_schema="keyword"
    )
    
    logger.info(f"Index de payloads créés pour '{collection_name}'")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Initialisation de Qdrant pour BerinIA")
    parser.add_argument("--config", type=str, default="config.json", help="Chemin vers le fichier de configuration")
    parser.add_argument("--reset", action="store_true", help="Réinitialiser toutes les collections existantes")
    args = parser.parse_args()
    
    try:
        logger.info("===== INITIALISATION DE QDRANT POUR BERINIA =====")
        
        # Chargement de la configuration
        config = load_config(args.config)
        
        if not config:
            logger.error("Configuration non valide ou manquante")
            return 1
        
        # Création du client Qdrant
        client = create_qdrant_client(config)
        
        # Réinitialisation des collections si demandé
        if args.reset:
            logger.warning("Réinitialisation des collections demandée")
            
            collections = client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            for name in ["knowledge", "documents", "leads", "templates"]:
                if name in collection_names:
                    logger.info(f"Suppression de la collection '{name}'")
                    client.delete_collection(name)
        
        # Création des collections
        create_collections(client, config)
        
        logger.info("===== INITIALISATION DE QDRANT TERMINÉE =====")
        return 0
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de Qdrant: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())

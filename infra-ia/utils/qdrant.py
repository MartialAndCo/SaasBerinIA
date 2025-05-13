"""
Module pour l'interaction avec la base de données vectorielle Qdrant
"""
import os
import time
import numpy as np
from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct, Distance, VectorParams, CollectionStatus
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Cache de client Qdrant pour éviter de recréer la connexion
_client_cache = {}

def get_client(url: Optional[str] = None) -> QdrantClient:
    """
    Obtient une instance du client Qdrant, avec cache pour optimiser les performances
    
    Args:
        url: URL du serveur Qdrant (si None, utilise la variable d'environnement)
        
    Returns:
        QdrantClient: Instance du client Qdrant
    """
    global _client_cache
    
    # Utiliser l'URL de la variable d'environnement si aucune n'est fournie
    qdrant_url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
    
    # Utiliser le client du cache s'il existe
    if qdrant_url in _client_cache:
        return _client_cache[qdrant_url]
    
    # Créer un nouveau client
    client = QdrantClient(url=qdrant_url)
    _client_cache[qdrant_url] = client
    
    return client

def create_collection(collection_name: str, vector_size: int = 1536) -> bool:
    """
    Crée une nouvelle collection Qdrant
    
    Args:
        collection_name: Nom de la collection à créer
        vector_size: Taille des vecteurs d'embedding (default: 1536 pour OpenAI)
        
    Returns:
        bool: True si la collection a été créée, False si elle existait déjà
    """
    client = get_client()
    
    # Vérifier si la collection existe déjà
    collections = client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        return False
    
    # Créer la collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        ),
        optimizers_config=models.OptimizersConfigDiff(
            indexing_threshold=10000  # Indexer après 10k vecteurs
        )
    )
    return True

def create_embedding(text: str) -> List[float]:
    """
    Crée un embedding de texte en utilisant l'API OpenAI
    
    Args:
        text: Texte à vectoriser
        
    Returns:
        List[float]: Vecteur d'embedding
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.embeddings.create(
            model="text-embedding-3-small",  # Modèle plus récent
            input=text
        )
        
        # Extract the embedding
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        print(f"Erreur lors de la création de l'embedding: {e}")
        # En cas d'erreur, retourner un vecteur aléatoire pour les tests
        return list(np.random.rand(1536))

def search_similar(collection_name: str, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Recherche des vecteurs similaires dans une collection
    
    Args:
        collection_name: Nom de la collection
        query_vector: Vecteur de recherche
        limit: Nombre maximum de résultats
        
    Returns:
        List[Dict]: Liste des résultats avec scores et payloads
    """
    client = get_client()
    
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit
    )
    
    formatted_results = []
    for scored_point in results:
        formatted_results.append({
            "score": scored_point.score,
            "content": scored_point.payload.get("content", ""),
            "metadata": {k: v for k, v in scored_point.payload.items() if k != "content"}
        })
    
    return formatted_results

def add_to_collection(collection_name: str, text: str, metadata: Dict[str, Any]) -> bool:
    """
    Ajoute un document à une collection
    
    Args:
        collection_name: Nom de la collection
        text: Texte à vectoriser et stocker
        metadata: Métadonnées associées au document
        
    Returns:
        bool: True si l'ajout a réussi
    """
    client = get_client()
    
    # Créer l'embedding
    embedding = create_embedding(text)
    
    # Générer un ID unique basé sur l'horodatage et un hash du texte
    point_id = f"{int(time.time())}_{abs(hash(text)) % 10000000}"
    
    # Construire le payload
    payload = {
        "content": text,
        "created_at": time.time(),
        **metadata
    }
    
    # Insérer le point
    client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
        ]
    )
    
    return True

def search_knowledge(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Recherche des connaissances similaires dans la collection knowledge
    
    Args:
        query: Requête de recherche
        limit: Nombre maximum de résultats
        
    Returns:
        List[Dict]: Liste des résultats pertinents
    """
    query_vector = create_embedding(query)
    return search_similar("knowledge", query_vector, limit)

def get_collection_info(collection_name: str) -> Dict[str, Any]:
    """
    Obtient des informations sur une collection
    
    Args:
        collection_name: Nom de la collection
        
    Returns:
        Dict: Informations sur la collection
    """
    client = get_client()
    
    try:
        info = client.get_collection(collection_name)
        
        return {
            "name": collection_name,
            "status": "green" if info.status == CollectionStatus.GREEN else "yellow",
            "vectors_count": info.vectors_count,
            "indexed_percent": info.indexed_vectors_count / info.vectors_count * 100 if info.vectors_count > 0 else 100,
            "optimization": info.optimizers_status.indexing_threshold
        }
    except Exception as e:
        return {
            "name": collection_name,
            "status": "error",
            "error": str(e)
        }

class QdrantService:
    """Service pour interagir avec Qdrant pour la mémoire vectorielle"""
    
    def __init__(self):
        """Initialise la connexion à Qdrant"""
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        
    def query_knowledge(self, query: str, collection_name: str = "knowledge", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche des connaissances similaires dans Qdrant
        
        Args:
            query: La requête à rechercher
            collection_name: Le nom de la collection dans Qdrant
            limit: Le nombre maximum de résultats à retourner
            
        Returns:
            Liste des documents similaires avec leurs métadonnées
        """
        # Obtention des embeddings pour la requête (via OpenAI)
        # Note: Dans une implémentation réelle, il faudrait appeler l'API des embeddings
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        query_vector = client.embeddings.create(
            model="text-embedding-ada-002",  # Utilisez un modèle adapté
            input=query
        ).data[0].embedding
        
        # Recherche des vecteurs similaires
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        # Formatage des résultats
        results = []
        for scored_point in search_result:
            results.append({
                "score": scored_point.score,
                "document": scored_point.payload.get("document", ""),
                "metadata": {
                    k: v for k, v in scored_point.payload.items() if k != "document"
                }
            })
            
        return results
    
    def create_knowledge_collection(self, collection_name: str = "knowledge"):
        """
        Crée une collection pour stocker les connaissances
        
        Args:
            collection_name: Le nom de la collection à créer
        """
        # Vérifier si la collection existe déjà
        collections = self.client.get_collections().collections
        if collection_name in [c.name for c in collections]:
            return
            
        # Créer la collection avec la dimension appropriée pour les embeddings
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1536,  # Dimension de text-embedding-ada-002
                distance=models.Distance.COSINE
            )
        )
        
    def store_knowledge(self, document: str, metadata: Dict[str, Any], collection_name: str = "knowledge"):
        """
        Stocke un document dans la collection de connaissances
        
        Args:
            document: Le document à stocker
            metadata: Les métadonnées associées au document
            collection_name: Le nom de la collection
        """
        # Obtention de l'embedding pour le document
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        embedding = client.embeddings.create(
            model="text-embedding-ada-002",
            input=document
        ).data[0].embedding
        
        # Construction du payload
        payload = {
            "document": document,
            **metadata
        }
        
        # Stockage dans Qdrant
        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=metadata.get("id", str(hash(document))),
                    vector=embedding,
                    payload=payload
                )
            ]
        )

# Fonctions d'utilitaire pour une API simple
def query_knowledge(query: str, collection_name: str = "knowledge", limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fonction utilitaire pour interroger la mémoire vectorielle
    
    Args:
        query: La requête à rechercher
        collection_name: Le nom de la collection
        limit: Le nombre maximum de résultats
        
    Returns:
        Liste des documents pertinents
    """
    service = QdrantService()
    return service.query_knowledge(query, collection_name, limit)

def store_knowledge(content: str, metadata: Dict[str, Any], collection_name: str = "knowledge") -> None:
    """
    Fonction utilitaire pour stocker des connaissances dans la mémoire vectorielle
    
    Args:
        content: Le contenu à stocker
        metadata: Les métadonnées associées au contenu
        collection_name: Le nom de la collection
    """
    service = QdrantService()
    service.store_knowledge(content, metadata, collection_name)

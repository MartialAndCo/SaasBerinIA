#!/usr/bin/env python3
"""
Tests d'intégration de Qdrant pour BerinIA.

Ce module contient des tests pour vérifier l'interaction avec la base de données vectorielle Qdrant,
la création d'embeddings, et la recherche de similarité.
"""
import os
import sys
import unittest
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib.util

# Ajout du répertoire parent au chemin de recherche des modules
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

# Import des modules à tester (avec gestion des erreurs)
try:
    from utils import qdrant
    import openai
except ImportError:
    qdrant = None
    openai = None

class TestQdrantVectorization(unittest.TestCase):
    """
    Tests pour la vectorisation et la recherche de similarité avec Qdrant.
    """
    
    @classmethod
    def setUpClass(cls):
        """Préparation des tests de classe."""
        # Configuration des variables d'environnement pour les tests
        os.environ["TESTING"] = "1"
        
        # Chemin vers le fichier de configuration global
        cls.config_path = ROOT_DIR / "config.json"
        if cls.config_path.exists():
            with open(cls.config_path, 'r') as f:
                cls.global_config = json.load(f)
        else:
            cls.global_config = {}
    
    @unittest.skipIf(qdrant is None, "Module Qdrant non disponible")
    def test_qdrant_client_creation(self):
        """Vérifie que le client Qdrant peut être créé."""
        # On utilise un mock pour éviter la connexion réelle
        with patch('utils.qdrant.QdrantClient', return_value=MagicMock()) as mock_client:
            url = "http://localhost:6333"
            client = qdrant.get_client(url)
            
            # Vérifier que le client a été créé
            mock_client.assert_called_once_with(url=url)
            self.assertIsNotNone(client, "Le client Qdrant n'a pas pu être créé")
    
    @unittest.skipIf(qdrant is None or openai is None, "Module Qdrant ou OpenAI non disponible")
    def test_embedding_creation(self):
        """Vérifie que les embeddings peuvent être créés correctement."""
        # Créer un mock direct pour la fonction OpenAI.Embedding.create
        sample_embedding = np.random.rand(1536).tolist()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=sample_embedding)]
        
        with patch('utils.qdrant.create_embedding', wraps=qdrant.create_embedding) as create_mock:
            with patch('openai.OpenAI') as mock_openai:
                # Configuration du mock
                mock_client = MagicMock()
                mock_client.embeddings.create.return_value = mock_response
                mock_openai.return_value = mock_client
                
                # Test direct
                text = "Ceci est un test d'embedding"
                embedding = qdrant.create_embedding(text)
                
                # Vérifications
                create_mock.assert_called_once()
                self.assertEqual(len(embedding), 1536, "L'embedding n'a pas la bonne dimension")
    
    @unittest.skipIf(qdrant is None, "Module Qdrant non disponible")
    def test_collection_management(self):
        """Vérifie les opérations de gestion des collections Qdrant."""
        # Création d'un mock pour le client Qdrant
        mock_client = MagicMock()
        mock_collections_info = MagicMock()
        mock_collections_info.collections = []
        mock_client.get_collections.return_value = mock_collections_info
        
        with patch('utils.qdrant.get_client', return_value=mock_client):
            # Si le module a une fonction pour créer une collection
            if hasattr(qdrant, 'create_collection'):
                qdrant.create_collection("test_collection", 1536)
                
                # Vérifier que la méthode create_collection du client a été appelée
                mock_client.create_collection.assert_called_once()
                
                # Vérifier les arguments
                args, kwargs = mock_client.create_collection.call_args
                self.assertEqual(kwargs.get('collection_name'), "test_collection", 
                                "Mauvais nom de collection")
    
    @unittest.skipIf(qdrant is None, "Module Qdrant non disponible")
    def test_vector_search(self):
        """Vérifie la recherche de vecteurs similaires."""
        # Création d'un mock pour le client Qdrant
        mock_client = MagicMock()
        mock_search_result = [
            MagicMock(payload={"content": "Test document 1"}, score=0.95),
            MagicMock(payload={"content": "Test document 2"}, score=0.85)
        ]
        mock_client.search.return_value = mock_search_result
        
        with patch('utils.qdrant.get_client', return_value=mock_client):
            # Si le module a une fonction de recherche
            if hasattr(qdrant, 'search_similar'):
                # Test avec un vecteur factice
                query_vector = np.random.rand(1536).tolist()
                results = qdrant.search_similar("test_collection", query_vector, limit=2)
                
                # Vérifier que la méthode search du client a été appelée
                mock_client.search.assert_called_once()
                
                # Vérifier le format des résultats
                self.assertEqual(len(results), 2, "Le nombre de résultats ne correspond pas")
                
                # Vérifier le traitement des résultats si approprié
                if isinstance(results[0], dict) and "content" in results[0]:
                    self.assertEqual(results[0]["content"], "Test document 1",
                                   "Le contenu du premier résultat ne correspond pas")

class TestQdrantIntegration(unittest.TestCase):
    """
    Tests plus complets pour l'intégration Qdrant.
    """
    
    def setUp(self):
        """Préparation des tests."""
        # Création d'un vecteur de test
        self.test_vector = np.random.rand(1536).astype(np.float32)
        
        # Mock du client Qdrant
        self.mock_client = MagicMock()
        
        # Mock de la réponse OpenAI pour les embeddings
        self.mock_embedding_response = {
            'data': [{'embedding': self.test_vector.tolist()}]
        }
    
    @unittest.skipIf(qdrant is None or openai is None, "Module Qdrant ou OpenAI non disponible")
    def test_complete_knowledge_flow(self):
        """Test du flux complet d'ajout et recherche de connaissances."""
        # Créer un mock pour OpenAI
        sample_embedding = np.random.rand(1536).tolist()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=sample_embedding)]
        
        with patch('utils.qdrant.get_client', return_value=self.mock_client):
            with patch('openai.OpenAI') as mock_openai:
                # Configuration du mock
                mock_client = MagicMock()
                mock_client.embeddings.create.return_value = mock_response
                mock_openai.return_value = mock_client
                
                # Vectorisation du texte
                text = "Ceci est un document de test pour la base de connaissances"
                
                # Ajout à Qdrant
                result = qdrant.add_to_collection(
                    collection_name="knowledge",
                    text=text,
                    metadata={"source": "test", "type": "document"}
                )
                
                # Vérifications
                self.assertTrue(result, "L'ajout à la collection a échoué")
                self.mock_client.upsert.assert_called_once()
                
                # Recherche de documents similaires
                query = "Test de recherche"
                
                # Réinitialiser le mock pour une nouvelle requête
                self.mock_client.reset_mock()
                mock_client.embeddings.create.return_value = mock_response
                
                results = qdrant.search_knowledge(query, limit=5)
                
                # Vérifier que la recherche a été effectuée
                self.mock_client.search.assert_called_once()
    
    @unittest.skipIf(qdrant is None, "Module Qdrant non disponible")
    def test_collection_status(self):
        """Vérifie que le statut des collections peut être récupéré."""
        # Mock de la réponse pour get_collection
        mock_collection_info = MagicMock()
        mock_collection_info.vectors_count = 100
        mock_collection_info.indexed_vectors_count = 100
        self.mock_client.get_collection.return_value = mock_collection_info
        
        with patch('utils.qdrant.get_client', return_value=self.mock_client):
            # Si la fonction existe
            if hasattr(qdrant, 'get_collection_info'):
                info = qdrant.get_collection_info("knowledge")
                
                # Vérifier que la méthode get_collection a été appelée
                self.mock_client.get_collection.assert_called_once_with("knowledge")
                
                # Vérifier que l'information est bien retournée
                self.assertIsNotNone(info, "Aucune information de collection retournée")

if __name__ == "__main__":
    unittest.main()

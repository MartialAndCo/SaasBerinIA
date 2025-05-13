#!/usr/bin/env python3
"""
Tests pour la fonctionnalité de délégation de l'OverseerAgent.

Ce module vérifie que l'OverseerAgent peut correctement déléguer des tâches
aux différents superviseurs et recevoir leurs résultats.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ajout du répertoire parent au chemin de recherche des modules
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

# Import des modules à tester
try:
    from agents.overseer.overseer_agent import OverseerAgent
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    OverseerAgent = None

class TestOverseerDelegation(unittest.TestCase):
    """Tests de la fonctionnalité de délégation de l'OverseerAgent."""
    
    def setUp(self):
        """Préparation des tests."""
        # Vérifier si l'OverseerAgent est disponible
        if OverseerAgent is None:
            self.skipTest("OverseerAgent non disponible")
        
        # Mock du LoggerAgent pour éviter les effets secondaires
        self.logger_patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.logger_patcher.start()
        
        # Instanciation de l'OverseerAgent
        self.overseer = OverseerAgent()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        # Arrêt des patchers
        self.logger_patcher.stop()
    
    @patch('importlib.import_module')
    def test_delegate_to_scraping_supervisor(self, mock_import_module):
        """Teste la délégation vers le ScrapingSupervisor."""
        # Configuration du mock pour simuler l'importation du module
        mock_module = MagicMock()
        mock_supervisor_class = MagicMock()
        mock_supervisor = MagicMock()
        mock_supervisor.run.return_value = {
            "status": "success",
            "leads": [{"name": "Test Lead", "email": "test@example.com"}]
        }
        mock_supervisor_class.return_value = mock_supervisor
        mock_module.ScrapingSupervisor = mock_supervisor_class
        mock_import_module.return_value = mock_module
        
        # Données de test
        test_data = {
            "action": "scrape_leads",
            "parameters": {
                "niche": "test_niche",
                "count": 10
            }
        }
        
        # Appel de la méthode à tester
        result = self.overseer.delegate_to_supervisor("ScrapingSupervisor", test_data)
        
        # Vérifications
        mock_import_module.assert_called_once()
        mock_module.ScrapingSupervisor.assert_called_once()
        mock_supervisor.run.assert_called_once_with(test_data)
        self.assertEqual(result["status"], "success", "La délégation a échoué")
        self.assertIn("leads", result, "Les leads sont manquants dans le résultat")
    
    @patch('importlib.import_module')
    def test_delegate_to_qualification_supervisor(self, mock_import_module):
        """Teste la délégation vers le QualificationSupervisor."""
        # Configuration du mock pour simuler l'importation du module
        mock_module = MagicMock()
        mock_supervisor_class = MagicMock()
        mock_supervisor = MagicMock()
        mock_supervisor.run.return_value = {
            "status": "success",
            "qualified_leads": [{"name": "Test Lead", "score": 85}]
        }
        mock_supervisor_class.return_value = mock_supervisor
        mock_module.QualificationSupervisor = mock_supervisor_class
        mock_import_module.return_value = mock_module
        
        # Données de test
        test_data = {
            "action": "qualify_leads",
            "parameters": {
                "leads": [{"name": "Test Lead", "email": "test@example.com"}],
                "min_score": 70
            }
        }
        
        # Appel de la méthode à tester
        result = self.overseer.delegate_to_supervisor("QualificationSupervisor", test_data)
        
        # Vérifications
        mock_import_module.assert_called_once()
        mock_module.QualificationSupervisor.assert_called_once()
        mock_supervisor.run.assert_called_once_with(test_data)
        self.assertEqual(result["status"], "success", "La délégation a échoué")
        self.assertIn("qualified_leads", result, "Les leads qualifiés sont manquants dans le résultat")
    
    @patch('importlib.import_module')
    def test_delegate_to_prospection_supervisor(self, mock_import_module):
        """Teste la délégation vers le ProspectionSupervisor."""
        # Configuration du mock pour simuler l'importation du module
        mock_module = MagicMock()
        mock_supervisor_class = MagicMock()
        mock_supervisor = MagicMock()
        mock_supervisor.run.return_value = {
            "status": "success", 
            "messages_sent": 5,
            "campaign_id": "test_campaign"
        }
        mock_supervisor_class.return_value = mock_supervisor
        mock_module.ProspectionSupervisor = mock_supervisor_class
        mock_import_module.return_value = mock_module
        
        # Données de test
        test_data = {
            "action": "send_campaign",
            "parameters": {
                "leads": [{"name": "Test Lead", "email": "test@example.com"}],
                "template": "default"
            }
        }
        
        # Appel de la méthode à tester
        result = self.overseer.delegate_to_supervisor("ProspectionSupervisor", test_data)
        
        # Vérifications
        mock_import_module.assert_called_once()
        mock_module.ProspectionSupervisor.assert_called_once()
        mock_supervisor.run.assert_called_once_with(test_data)
        self.assertEqual(result["status"], "success", "La délégation a échoué")
        self.assertIn("messages_sent", result, "Le nombre de messages envoyés est manquant dans le résultat")
    
    def test_delegate_to_unknown_supervisor(self):
        """Teste la délégation vers un superviseur inconnu."""
        # Données de test
        test_data = {"action": "test_action"}
        
        # Appel de la méthode à tester
        result = self.overseer.delegate_to_supervisor("UnknownSupervisor", test_data)
        
        # Vérifications
        self.assertEqual(result["status"], "error", "La délégation aurait dû échouer")
        self.assertIn("message", result, "Le message d'erreur est manquant")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Tests d'intégration pour les interactions entre agents BerinIA.

Ce module teste les interactions entre différents agents pour s'assurer
que la communication et la délégation fonctionnent correctement.
"""
import os
import sys
import unittest
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ajout du répertoire parent au chemin de recherche
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

# Import conditionnel des modules à tester
try:
    from agents.overseer.overseer_agent import OverseerAgent
    from agents.admin_interpreter.admin_interpreter_agent import AdminInterpreterAgent
    from agents.pivot_strategy.pivot_strategy_agent import PivotStrategyAgent
    from agents.response_listener.response_listener_agent import ResponseListenerAgent
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    OverseerAgent = None
    AdminInterpreterAgent = None
    PivotStrategyAgent = None
    ResponseListenerAgent = None

class TestAgentIntegration(unittest.TestCase):
    """Tests d'intégration entre les agents du système."""
    
    def setUp(self):
        """Configuration initiale des tests."""
        # Vérifier si les agents sont disponibles
        if OverseerAgent is None or AdminInterpreterAgent is None:
            self.skipTest("Agents non disponibles")
        
        # Mock du LoggerAgent pour éviter les effets secondaires
        self.logger_patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.logger_patcher.start()
        
        # Instanciation des agents principaux
        # Pour les tests, on utilise les vraies instances mais on évite les effets secondaires
        with patch('agents.logger.logger_agent.LoggerAgent'):
            self.overseer = OverseerAgent()
            self.admin_interpreter = AdminInterpreterAgent()
            if PivotStrategyAgent is not None:
                self.pivot_strategy = PivotStrategyAgent()
            if ResponseListenerAgent is not None:
                self.response_listener = ResponseListenerAgent()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.logger_patcher.stop()
    
    def test_admin_to_overseer_integration(self):
        """
        Teste l'intégration entre AdminInterpreterAgent et OverseerAgent.
        
        Ce test vérifie que l'AdminInterpreterAgent peut interpréter des commandes
        en langage naturel et les transmettre correctement à l'OverseerAgent.
        """
        # Patch de la méthode run de l'OverseerAgent pour éviter les effets secondaires
        with patch.object(self.overseer, 'run') as mock_overseer_run:
            # Configuration du mock pour retourner une réponse attendue
            mock_overseer_run.return_value = {
                "status": "success",
                "message": "Tâche déléguée avec succès"
            }
            
            # Test avec une commande simple
            admin_input = {
                "action": "interpret",
                "command": "Récupère les statistiques des campagnes actives"
            }
            
            # Exécution de l'interprétation de commande
            result = self.admin_interpreter.run(admin_input)
            
            # Vérifications
            self.assertEqual(result["status"], "success", "L'interprétation a échoué")
            
            # Vérifier que l'OverseerAgent a été appelé avec les bons paramètres
            mock_overseer_run.assert_called_once()
            args = mock_overseer_run.call_args[0][0]
            
            # La commande doit être transformée en une action structurée
            self.assertIn("action", args, "L'action n'est pas définie")
    
    def test_overseer_delegation(self):
        """
        Teste la capacité de l'OverseerAgent à déléguer des tâches.
        """
        # Mock des agents superviseurs
        mock_scraping_supervisor = MagicMock()
        mock_scraping_supervisor.run.return_value = {"status": "success"}
        
        mock_qualification_supervisor = MagicMock()
        mock_qualification_supervisor.run.return_value = {"status": "success"}
        
        # Patch de la méthode get_agent pour retourner nos mocks
        def mock_get_agent(agent_name):
            if agent_name == "ScrapingSupervisor":
                return mock_scraping_supervisor
            elif agent_name == "QualificationSupervisor":
                return mock_qualification_supervisor
            else:
                return None
        
        with patch.object(self.overseer, '_get_agent', side_effect=mock_get_agent):
            # Test de délégation au ScrapingSupervisor
            scraping_request = {
                "action": "delegate",
                "target": "ScrapingSupervisor",
                "task": {
                    "action": "scrape_niche",
                    "niche": "développement web freelance"
                }
            }
            
            result = self.overseer.run(scraping_request)
            
            # Vérifications
            self.assertEqual(result["status"], "success", "La délégation au ScrapingSupervisor a échoué")
            mock_scraping_supervisor.run.assert_called_once()
            
            # Test de délégation au QualificationSupervisor
            qualification_request = {
                "action": "delegate",
                "target": "QualificationSupervisor",
                "task": {
                    "action": "qualify_leads",
                    "leads": [{"id": 1}, {"id": 2}]
                }
            }
            
            result = self.overseer.run(qualification_request)
            
            # Vérifications
            self.assertEqual(result["status"], "success", "La délégation au QualificationSupervisor a échoué")
            mock_qualification_supervisor.run.assert_called_once()
    
    @unittest.skipIf(PivotStrategyAgent is None, "PivotStrategyAgent non disponible")
    def test_pivot_strategy_integration(self):
        """
        Teste l'intégration du PivotStrategyAgent avec le système.
        """
        # Données de test
        test_metrics = {
            "campaign_id": "test_campaign",
            "open_rate": 0.15,
            "response_rate": 0.03,
            "positive_rate": 0.10,
            "conversion_rate": 0.01
        }
        
        # Mock du service d'embedding pour éviter les appels à l'API OpenAI
        with patch('utils.qdrant.create_embedding', return_value=[0.1] * 1536):
            # Test de l'analyse des métriques
            analysis_request = {
                "action": "analyze_performance",
                "metrics": test_metrics
            }
            
            result = self.pivot_strategy.run(analysis_request)
            
            # Vérifications
            self.assertEqual(result["status"], "success", "L'analyse de performance a échoué")
            self.assertIn("recommendations", result, "Aucune recommandation n'a été générée")
    
    @unittest.skipIf(ResponseListenerAgent is None, "ResponseListenerAgent non disponible")
    def test_response_listener_integration(self):
        """
        Teste l'intégration du ResponseListenerAgent avec le système.
        """
        # Simulation d'une notification de réponse email
        email_notification = {
            "action": "process_email_response",
            "email_data": {
                "from": "prospect@example.com",
                "subject": "Re: Votre proposition",
                "body": "Bonjour, je suis intéressé par votre offre. Pouvons-nous discuter?",
                "campaign_id": "test_campaign",
                "lead_id": "test_lead_123"
            }
        }
        
        # Mock de la méthode speak pour éviter les effets secondaires
        # et capturer les messages envoyés à l'OverseerAgent
        with patch.object(self.response_listener, 'speak') as mock_speak:
            result = self.response_listener.run(email_notification)
            
            # Vérifications
            self.assertEqual(result["status"], "success", "Le traitement de la réponse a échoué")
            
            # Vérifier que le ResponseListenerAgent a informé l'OverseerAgent
            mock_speak.assert_called()
            
            # Vérifier que le message parle bien d'une réponse positive
            args = mock_speak.call_args[0]
            self.assertIn("intéressé", args[0], "Le sentiment n'a pas été correctement détecté")
            self.assertEqual(args[1], "OverseerAgent", "Le message n'est pas adressé à l'OverseerAgent")

if __name__ == "__main__":
    unittest.main()

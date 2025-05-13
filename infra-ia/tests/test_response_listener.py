#!/usr/bin/env python3
"""
Tests pour le ResponseListenerAgent.

Ce module vérifie que le ResponseListenerAgent peut correctement recevoir
et traiter les réponses entrantes (emails et SMS) et les transmettre au
ResponseInterpreterAgent.
"""
import os
import sys
import unittest
import json
import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ajout du répertoire parent au chemin de recherche des modules
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

# Import des modules à tester
try:
    from agents.response_listener.response_listener_agent import ResponseListenerAgent
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    ResponseListenerAgent = None

class TestResponseListener(unittest.TestCase):
    """Tests de la fonctionnalité du ResponseListenerAgent."""
    
    def setUp(self):
        """Préparation des tests."""
        # Vérifier si le ResponseListenerAgent est disponible
        if ResponseListenerAgent is None:
            self.skipTest("ResponseListenerAgent non disponible")
        
        # Mock du LoggerAgent pour éviter les effets secondaires
        self.logger_patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.logger_patcher.start()
        
        # Instanciation du ResponseListenerAgent
        self.listener = ResponseListenerAgent()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        # Arrêt des patchers
        self.logger_patcher.stop()
    
    @patch('agents.response_listener.response_listener_agent.ResponseListenerAgent.transmit_to_interpreter')
    def test_process_email_response(self, mock_transmit):
        """Teste le traitement d'une réponse email."""
        # Données de test
        test_data = {
            "sender": "lead@example.com",
            "recipient": "campaign+test123@berinia.com",
            "subject": "Re: Votre offre",
            "body": "Bonjour, je suis intéressé par votre offre. Pouvons-nous discuter mardi prochain ? Merci.",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Appel de la méthode à tester
        result = self.listener.process_email_response(test_data)
        
        # Vérifications
        self.assertEqual(result["status"], "success", "Le traitement de l'email a échoué")
        mock_transmit.assert_called_once()
        
        # Vérification des données transmises
        call_args = mock_transmit.call_args[0][0]
        self.assertEqual(call_args["source"], "email")
        self.assertEqual(call_args["sender"], "lead@example.com")
        self.assertEqual(call_args["campaign_id"], "test123")
    
    @patch('agents.response_listener.response_listener_agent.ResponseListenerAgent.transmit_to_interpreter')
    def test_process_sms_response(self, mock_transmit):
        """Teste le traitement d'une réponse SMS."""
        # Données de test
        test_data = {
            "sender": "+33612345678",
            "recipient": "+33987654321",
            "body": "#sms123 Oui, je suis disponible demain à 15h",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Appel de la méthode à tester
        result = self.listener.process_sms_response(test_data)
        
        # Vérifications
        self.assertEqual(result["status"], "success", "Le traitement du SMS a échoué")
        mock_transmit.assert_called_once()
        
        # Vérification des données transmises
        call_args = mock_transmit.call_args[0][0]
        self.assertEqual(call_args["source"], "sms")
        self.assertEqual(call_args["sender"], "+33612345678")
        self.assertEqual(call_args["campaign_id"], "sms123")
    
    @patch('agents.response_interpreter.response_interpreter_agent.ResponseInterpreterAgent')
    def test_transmit_to_interpreter(self, mock_interpreter_class):
        """Teste la transmission au ResponseInterpreterAgent."""
        # Configuration du mock
        mock_interpreter = MagicMock()
        mock_interpreter.run.return_value = {
            "status": "success",
            "intent": "interest",
            "sentiment": "positive"
        }
        mock_interpreter_class.return_value = mock_interpreter
        
        # Données de test
        test_data = {
            "source": "email",
            "sender": "lead@example.com",
            "content": "Je suis intéressé",
            "campaign_id": "test123"
        }
        
        # Appel de la méthode à tester
        self.listener.transmit_to_interpreter(test_data)
        
        # Vérifications
        mock_interpreter_class.assert_called_once()
        mock_interpreter.run.assert_called_once()
        
        # Vérification des données transmises
        call_args = mock_interpreter.run.call_args[0][0]
        self.assertEqual(call_args["action"], "interpret_response")
        self.assertEqual(call_args["data"], test_data)
    
    def test_get_stats(self):
        """Teste la récupération des statistiques."""
        # Configuration initiale
        self.listener.stats = {
            "emails_received": 10,
            "sms_received": 5,
            "processed_successfully": 13,
            "processing_errors": 2,
            "last_activity": datetime.datetime.now().isoformat()
        }
        
        # Appel de la méthode à tester
        result = self.listener.run({"action": "get_stats"})
        
        # Vérifications
        self.assertEqual(result["status"], "success", "La récupération des stats a échoué")
        self.assertEqual(result["stats"]["emails_received"], 10)
        self.assertEqual(result["stats"]["sms_received"], 5)
        self.assertEqual(result["stats"]["processed_successfully"], 13)
        self.assertEqual(result["stats"]["processing_errors"], 2)
    
    def test_invalid_action(self):
        """Teste la gestion d'une action invalide."""
        # Appel de la méthode à tester
        result = self.listener.run({"action": "invalid_action"})
        
        # Vérifications
        self.assertEqual(result["status"], "error", "Une action invalide devrait échouer")
        self.assertIn("message", result, "Un message d'erreur devrait être présent")

if __name__ == "__main__":
    unittest.main()

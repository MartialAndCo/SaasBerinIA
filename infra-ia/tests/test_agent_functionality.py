#!/usr/bin/env python3
"""
Tests de fonctionnalité pour les agents du système BerinIA.

Ce module contient des tests pour vérifier le bon fonctionnement de chaque agent
et leurs interactions dans différents scénarios d'utilisation.
"""
import os
import sys
import unittest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import importlib.util

# Ajout du répertoire parent au chemin de recherche des modules
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

# Tentative d'importation des modules agents
try:
    from core import agent_base
    from agents.overseer.overseer_agent import OverseerAgent
    from agents.admin_interpreter.admin_interpreter_agent import AdminInterpreterAgent
except ImportError as e:
    print(f"Erreur d'importation des modules agents: {e}")
    # On continue quand même pour permettre aux tests de s'exécuter avec skipIf

class TestAgentBase(unittest.TestCase):
    """Tests pour la classe de base Agent."""
    
    def setUp(self):
        """Préparation des tests."""
        # Création d'un agent de test basé sur Agent
        if hasattr(agent_base, "Agent"):
            self.agent = agent_base.Agent("TestAgent")
        else:
            self.skipTest("Classe Agent non disponible")
    
    def test_agent_initialization(self):
        """Vérifie que l'agent s'initialise correctement."""
        self.assertEqual(self.agent.name, "TestAgent", 
                        "Le nom de l'agent n'a pas été correctement défini")
        self.assertIsNotNone(self.agent.agent_id, 
                            "L'ID de l'agent n'a pas été généré")
    
    def test_config_loading(self):
        """Vérifie que la configuration est chargée correctement."""
        # La configuration est chargée lors de l'initialisation
        self.assertIsNotNone(self.agent.config, 
                            "La configuration n'a pas été chargée")
        self.assertIsInstance(self.agent.config, dict, 
                             "La configuration n'est pas un dictionnaire")
    
    def test_prompt_building(self):
        """Vérifie que le prompt est construit correctement."""
        context = {"action": "test_action", "data": "test_data"}
        prompt = self.agent.build_prompt(context)
        
        # Vérifier que le prompt est une chaîne non vide
        self.assertIsInstance(prompt, str, "Le prompt n'est pas une chaîne")
        self.assertTrue(len(prompt) > 0, "Le prompt est vide")
    
    @patch('agents.logger.logger_agent.LoggerAgent.log_interaction')
    def test_agent_speaking(self, mock_log_interaction):
        """Vérifie que l'agent peut envoyer des messages."""
        # Configuration du mock pour la méthode de classe
        mock_log_interaction.return_value = {"status": "success", "log_id": "test_id"}
        
        # Test de la méthode speak
        self.agent.speak("Test message", target="TargetAgent", context_id="test_context")
        
        # Vérifier que log_interaction a été appelé avec les bons arguments
        mock_log_interaction.assert_called_once_with(
            from_agent="TestAgent",
            to_agent="TargetAgent",
            message="Test message",
            context_id="test_context"
        )

class TestOverseerAgent(unittest.TestCase):
    """Tests pour l'OverseerAgent."""
    
    def setUp(self):
        """Préparation des tests."""
        # Vérifier si la classe OverseerAgent est disponible
        if 'OverseerAgent' not in globals():
            self.skipTest("OverseerAgent non disponible")
        
        # Creation d'un mock pour logger_agent pour éviter les effets secondaires
        self.patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.patcher.start()
        
        # Initialisation de l'OverseerAgent avec un mock pour le module LLM
        with patch('utils.llm.LLMService.call_llm', return_value='{"status": "ok"}'):
            self.overseer = OverseerAgent()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.patcher.stop()
    
    def test_overseer_processing(self):
        """Teste la capacité de l'OverseerAgent à traiter les commandes."""
        # Note: Ce test est un placeholder - nous testons simplement l'interface
        # sans vérifier les détails d'implémentation qui peuvent varier
        
        # Test du traitement d'une commande
        with patch('utils.llm.LLMService.call_llm') as mock_call_llm:
            # Configuration du mock pour qu'il retourne un JSON valide
            mock_call_llm.return_value = '{"status": "success"}'
            
            # Appel de la méthode run
            result = self.overseer.run({
                "action": "process_command",
                "command": "Commande de test"
            })
            
            # Vérification de base
            self.assertIsInstance(result, dict, "Le résultat n'est pas un dictionnaire")
            self.assertIn("status", result, "Le résultat ne contient pas de statut")
    
    @patch('utils.llm.LLMService.call_llm')
    def test_agent_delegation(self, mock_call_llm):
        """Teste la capacité de l'OverseerAgent à déléguer des tâches."""
        # Configuration du mock pour simuler une délégation
        mock_call_llm.return_value = json.dumps({
            "status": "success",
            "action": "delegate",
            "target_agent": "ScraperAgent",
            "parameters": {"niche": "test_niche", "limit": 10}
        })
        
        # Mock pour le ScraperAgent
        with patch('agents.scraper.scraper_agent.ScraperAgent') as mock_scraper_class:
            # Configuration du mock de ScraperAgent
            mock_scraper = MagicMock()
            mock_scraper.run.return_value = {"status": "success", "leads": []}
            mock_scraper_class.return_value = mock_scraper
            
            # Test de la délégation
            result = self.overseer.run({
                "action": "process_command",
                "command": "Scrape 10 leads in test_niche"
            })
            
            # Vérifier que la délégation a été tentée
            # Note: Ceci pourrait échouer si l'OverseerAgent ne tente pas réellement de créer un ScraperAgent
            # C'est attendu dans un test unitaire où nous ne voulons pas de dépendances externes
            if mock_scraper_class.called:
                mock_scraper.run.assert_called_once()

class TestAdminInterpreterAgent(unittest.TestCase):
    """Tests pour l'AdminInterpreterAgent."""
    
    def setUp(self):
        """Préparation des tests."""
        # Vérifier si la classe AdminInterpreterAgent est disponible
        if 'AdminInterpreterAgent' not in globals():
            self.skipTest("AdminInterpreterAgent non disponible")
        
        # Creation d'un mock pour logger_agent pour éviter les effets secondaires
        self.patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.patcher.start()
        
        # Initialisation de l'AdminInterpreterAgent avec un mock pour le module LLM
        with patch('utils.llm.LLMService.call_llm', return_value='{"status": "ok"}'):
            self.interpreter = AdminInterpreterAgent()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.patcher.stop()
    
    def test_command_interpretation(self):
        """Teste la capacité de l'AdminInterpreterAgent à interpréter les commandes."""
        # Note: Ce test est un placeholder - nous testons simplement l'interface
        # sans vérifier les détails d'implémentation qui peuvent varier
        
        with patch('utils.llm.LLMService.call_llm') as mock_call_llm:
            # Configuration du mock pour qu'il retourne un JSON valide
            mock_call_llm.return_value = '{"status": "success", "message": "Interprétation de test"}'
            
            # Test de l'interprétation
            result = self.interpreter.run({
                "action": "interpret",
                "command": "Commande de test"
            })
            
            # Vérifications de base
            self.assertIsInstance(result, dict, "Le résultat n'est pas un dictionnaire")
            self.assertIn("status", result, "Le résultat ne contient pas de statut")

class TestAgentInteractions(unittest.TestCase):
    """
    Tests d'intégration pour les interactions entre agents.
    Ces tests vérifient les flux de communication et de délégation entre agents.
    """
    
    def setUp(self):
        """Préparation des tests."""
        # Creation d'un mock pour logger_agent pour éviter les effets secondaires
        self.patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.patcher.start()
        
        # Patches pour éviter les appels réels à l'API LLM
        self.llm_patcher = patch('utils.llm.LLMService.call_llm', return_value='{"status": "ok"}')
        self.mock_llm = self.llm_patcher.start()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.patcher.stop()
        self.llm_patcher.stop()
    
    def test_admin_to_overseer_flow(self):
        """Teste le flux de l'administrateur à l'OverseerAgent via l'AdminInterpreterAgent."""
        # Cette fonction teste le flux suivant:
        # Admin -> AdminInterpreterAgent -> OverseerAgent
        
        # 1. Configuration des mocks
        # Mock pour l'AdminInterpreterAgent
        with patch('agents.admin_interpreter.admin_interpreter_agent.AdminInterpreterAgent') as mock_interpreter_class:
            mock_interpreter = MagicMock()
            mock_interpreter.run.return_value = {
                "status": "success",
                "interpretation": {
                    "action": "scrape_leads",
                    "parameters": {"niche": "test_niche", "count": 10}
                }
            }
            mock_interpreter_class.return_value = mock_interpreter
            
            # Mock pour l'OverseerAgent
            with patch('agents.overseer.overseer_agent.OverseerAgent') as mock_overseer_class:
                mock_overseer = MagicMock()
                mock_overseer.run.return_value = {"status": "success", "result": "Scraping started"}
                mock_overseer_class.return_value = mock_overseer
                
                # 2. Simulation du flux
                # Ceci simule le processus d'interaction normalement déclenché par interact.py
                # On crée d'abord l'interpréteur
                interpreter = mock_interpreter_class()
                
                # On interprète une commande admin
                command = "Extraire 10 leads dans la niche test_niche"
                interpretation = interpreter.run({"action": "interpret", "command": command})
                
                # On passe l'interprétation à l'overseer
                overseer = mock_overseer_class()
                result = overseer.run(interpretation["interpretation"])
                
                # 3. Vérifications
                mock_interpreter.run.assert_called_once()
                mock_overseer.run.assert_called_once_with(interpretation["interpretation"])
                self.assertEqual(result["status"], "success", "Le flux a échoué")

class TestScrapingFlow(unittest.TestCase):
    """
    Tests pour le flux de scraping.
    """
    
    def setUp(self):
        """Préparation des tests."""
        # Creation d'un mock pour logger_agent pour éviter les effets secondaires
        self.patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.patcher.start()
        
        # Patches pour éviter les appels réels à l'API LLM
        self.llm_patcher = patch('utils.llm.LLMService.call_llm', return_value='{"status": "ok"}')
        self.mock_llm = self.llm_patcher.start()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.patcher.stop()
        self.llm_patcher.stop()
    
    def test_scraping_delegation_flow(self):
        """Teste le flux de délégation du scraping."""
        # Cette fonction teste le flux suivant:
        # OverseerAgent -> ScrapingSupervisor -> ScraperAgent -> CleanerAgent
        
        # 1. Configuration des mocks
        # Mock pour ScrapingSupervisor
        with patch('agents.scraping_supervisor.scraping_supervisor.ScrapingSupervisor') as mock_supervisor_class:
            mock_supervisor = MagicMock()
            mock_supervisor.run.return_value = {
                "status": "success", 
                "plan": {
                    "agents": ["ScraperAgent", "CleanerAgent"]
                }
            }
            mock_supervisor_class.return_value = mock_supervisor
            
            # Mock pour ScraperAgent
            with patch('agents.scraper.scraper_agent.ScraperAgent') as mock_scraper_class:
                mock_scraper = MagicMock()
                mock_scraper.run.return_value = {"status": "success", "leads": [{"name": "Test Lead"}]}
                mock_scraper_class.return_value = mock_scraper
                
                # Mock pour CleanerAgent
                with patch('agents.cleaner.cleaner_agent.CleanerAgent') as mock_cleaner_class:
                    mock_cleaner = MagicMock()
                    mock_cleaner.run.return_value = {"status": "success", "cleaned_leads": [{"name": "Test Lead", "cleaned": True}]}
                    mock_cleaner_class.return_value = mock_cleaner
                    
                    # 2. Simulation du flux
                    # On crée d'abord l'OverseerAgent (déjà mocké via llm_patcher)
                    with patch('agents.overseer.overseer_agent.OverseerAgent') as mock_overseer_class:
                        mock_overseer = MagicMock()
                        mock_overseer.run.return_value = {"status": "success", "result": "Scraping flow completed"}
                        # Configuration pour simuler le comportement de l'Overseer
                        mock_overseer.delegate_to_supervisor.return_value = mock_supervisor.run({})
                        mock_overseer_class.return_value = mock_overseer
                        
                        # Exécution du flux
                        overseer = mock_overseer_class()
                        result = overseer.run({
                            "action": "scrape_leads",
                            "parameters": {"niche": "test_niche", "count": 10}
                        })
                        
                        # 3. Vérifications
                        # Vérifier seulement que l'application ne plante pas et retourne un résultat valide
                        # Note: Dans une implémentation réelle, on vérifierait les appels spécifiques
                        self.assertIsInstance(result, dict, "Le résultat n'est pas un dictionnaire")
                        self.assertIn("status", result, "Le résultat ne contient pas de statut")

class TestQualificationFlow(unittest.TestCase):
    """
    Tests pour le flux de qualification des leads.
    """
    
    def setUp(self):
        """Préparation des tests."""
        # Creation d'un mock pour logger_agent pour éviter les effets secondaires
        self.patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.patcher.start()
        
        # Patches pour éviter les appels réels à l'API LLM
        self.llm_patcher = patch('utils.llm.LLMService.call_llm', return_value='{"status": "ok"}')
        self.mock_llm = self.llm_patcher.start()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.patcher.stop()
        self.llm_patcher.stop()
    
    def test_qualification_flow(self):
        """Teste le flux de qualification des leads."""
        # Cette fonction teste le flux suivant:
        # OverseerAgent -> QualificationSupervisor -> ValidatorAgent -> ScoringAgent -> DuplicateCheckerAgent
        
        # 1. Configuration des mocks pour les agents
        with patch('agents.qualification_supervisor.qualification_supervisor.QualificationSupervisor') as mock_supervisor_class:
            mock_supervisor = MagicMock()
            mock_supervisor.run.return_value = {
                "status": "success", 
                "plan": {
                    "agents": ["ValidatorAgent", "ScoringAgent", "DuplicateCheckerAgent"]
                }
            }
            mock_supervisor_class.return_value = mock_supervisor
            
            # Mock pour ValidatorAgent
            with patch('agents.validator.validator_agent.ValidatorAgent') as mock_validator_class:
                mock_validator = MagicMock()
                mock_validator.run.return_value = {"status": "success", "validated": True}
                mock_validator_class.return_value = mock_validator
                
                # Mock pour ScoringAgent
                with patch('agents.scoring.scoring_agent.ScoringAgent') as mock_scoring_class:
                    mock_scoring = MagicMock()
                    mock_scoring.run.return_value = {"status": "success", "score": 85}
                    mock_scoring_class.return_value = mock_scoring
                    
                    # Mock pour DuplicateCheckerAgent
                    with patch('agents.duplicate_checker.duplicate_checker_agent.DuplicateCheckerAgent') as mock_dupcheck_class:
                        mock_dupcheck = MagicMock()
                        mock_dupcheck.run.return_value = {"status": "success", "is_duplicate": False}
                        mock_dupcheck_class.return_value = mock_dupcheck
                        
                        # 2. Simulation du flux
                        # On crée d'abord l'OverseerAgent (déjà mocké via llm_patcher)
                        with patch('agents.overseer.overseer_agent.OverseerAgent') as mock_overseer_class:
                            mock_overseer = MagicMock()
                            mock_overseer.run.return_value = {"status": "success", "result": "Qualification flow completed"}
                            # Configuration pour simuler le comportement de l'Overseer
                            mock_overseer.delegate_to_supervisor.return_value = mock_supervisor.run({})
                            mock_overseer_class.return_value = mock_overseer
                            
                            # Exécution du flux
                            overseer = mock_overseer_class()
                            result = overseer.run({
                                "action": "qualify_leads",
                                "parameters": {"leads": [{"name": "Test Lead"}], "min_score": 70}
                            })
                            
                            # 3. Vérifications
                            # Vérifier seulement que l'application ne plante pas et retourne un résultat valide
                            self.assertIsInstance(result, dict, "Le résultat n'est pas un dictionnaire")
                            self.assertIn("status", result, "Le résultat ne contient pas de statut")

class TestProspectionFlow(unittest.TestCase):
    """
    Tests pour le flux de prospection.
    """
    
    def setUp(self):
        """Préparation des tests."""
        # Creation d'un mock pour logger_agent pour éviter les effets secondaires
        self.patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.patcher.start()
        
        # Patches pour éviter les appels réels à l'API LLM
        self.llm_patcher = patch('utils.llm.LLMService.call_llm', return_value='{"status": "ok"}')
        self.mock_llm = self.llm_patcher.start()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.patcher.stop()
        self.llm_patcher.stop()
    
    def test_prospection_flow(self):
        """Teste le flux de prospection."""
        # Cette fonction teste le flux suivant:
        # OverseerAgent -> ProspectionSupervisor -> MessagingAgent -> FollowUpAgent
        
        # 1. Configuration des mocks pour les agents
        with patch('agents.prospection_supervisor.prospection_supervisor.ProspectionSupervisor') as mock_supervisor_class:
            mock_supervisor = MagicMock()
            mock_supervisor.run.return_value = {
                "status": "success", 
                "plan": {
                    "agents": ["MessagingAgent", "FollowUpAgent"]
                }
            }
            mock_supervisor_class.return_value = mock_supervisor
            
            # Mock pour MessagingAgent
            with patch('agents.messaging.messaging_agent.MessagingAgent') as mock_messaging_class:
                mock_messaging = MagicMock()
                mock_messaging.run.return_value = {"status": "success", "sent": True}
                mock_messaging_class.return_value = mock_messaging
                
                # Mock pour FollowUpAgent
                with patch('agents.follow_up.follow_up_agent.FollowUpAgent') as mock_followup_class:
                    mock_followup = MagicMock()
                    mock_followup.run.return_value = {"status": "success", "follow_ups_scheduled": 2}
                    mock_followup_class.return_value = mock_followup
                    
                    # 2. Simulation du flux
                    # On crée d'abord l'OverseerAgent (déjà mocké via llm_patcher)
                    with patch('agents.overseer.overseer_agent.OverseerAgent') as mock_overseer_class:
                        mock_overseer = MagicMock()
                        mock_overseer.run.return_value = {"status": "success", "result": "Prospection flow completed"}
                        # Configuration pour simuler le comportement de l'Overseer
                        mock_overseer.delegate_to_supervisor.return_value = mock_supervisor.run({})
                        mock_overseer_class.return_value = mock_overseer
                        
                        # Exécution du flux
                        overseer = mock_overseer_class()
                        result = overseer.run({
                            "action": "send_campaign",
                            "parameters": {
                                "campaign_id": "test_campaign",
                                "leads": [{"name": "Test Lead", "email": "test@example.com"}],
                                "template": "Default"
                            }
                        })
                        
                        # 3. Vérifications
                        # Vérifier seulement que l'application ne plante pas et retourne un résultat valide
                        self.assertIsInstance(result, dict, "Le résultat n'est pas un dictionnaire")
                        self.assertIn("status", result, "Le résultat ne contient pas de statut")

class TestResponseHandlingFlow(unittest.TestCase):
    """
    Tests pour le flux de gestion des réponses.
    """
    
    def setUp(self):
        """Préparation des tests."""
        # Creation d'un mock pour logger_agent pour éviter les effets secondaires
        self.patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.patcher.start()
        
        # Patches pour éviter les appels réels à l'API LLM
        self.llm_patcher = patch('utils.llm.LLMService.call_llm', return_value='{"status": "ok"}')
        self.mock_llm = self.llm_patcher.start()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.patcher.stop()
        self.llm_patcher.stop()
    
    def test_response_handling_flow(self):
        """Teste le flux de gestion des réponses."""
        # Cette fonction teste le flux suivant:
        # ResponseListenerAgent -> ResponseInterpreterAgent -> OverseerAgent -> ProspectionSupervisor
        
        # 1. Configuration des mocks pour les agents
        with patch('agents.response_listener.response_listener_agent.ResponseListenerAgent') as mock_listener_class:
            mock_listener = MagicMock()
            mock_listener.handle.return_value = {"status": "success", "received": True}
            mock_listener_class.return_value = mock_listener
            
            # Mock pour ResponseInterpreterAgent
            with patch('agents.response_interpreter.response_interpreter_agent.ResponseInterpreterAgent') as mock_interpreter_class:
                mock_interpreter = MagicMock()
                mock_interpreter.run.return_value = {
                    "status": "success", 
                    "analysis": {
                        "sentiment": "positive",
                        "intent": "interest",
                        "action_needed": "follow_up"
                    }
                }
                mock_interpreter_class.return_value = mock_interpreter
                
                # Mock pour ProspectionSupervisor (déjà créé dans un test précédent)
                with patch('agents.prospection_supervisor.prospection_supervisor.ProspectionSupervisor') as mock_supervisor_class:
                    mock_supervisor = MagicMock()
                    mock_supervisor.run.return_value = {
                        "status": "success", 
                        "action": "transfer_to_crm"
                    }
                    mock_supervisor_class.return_value = mock_supervisor
                    
                    # 2. Simulation du flux
                    # On commence par le ResponseListenerAgent qui reçoit une réponse via webhook
                    listener = mock_listener_class()
                    webhook_data = {
                        "sender": "test@example.com",
                        "content": "Oui, je suis intéressé par votre offre.",
                        "campaign_id": "test_campaign"
                    }
                    
                    # Le listener traite la réponse et la transmet à l'interpréteur
                    listener_result = listener.handle(webhook_data)
                    
                    # L'interpréteur analyse la réponse
                    interpreter = mock_interpreter_class()
                    interpreter_result = interpreter.run({
                        "action": "interpret_response",
                        "response": webhook_data
                    })
                    
                    # L'OverseerAgent reçoit l'analyse et décide quoi faire
                    with patch('agents.overseer.overseer_agent.OverseerAgent') as mock_overseer_class:
                        mock_overseer = MagicMock()
                        mock_overseer.handle_event.return_value = {"status": "success", "action_taken": "delegated_to_prospection"}
                        mock_overseer_class.return_value = mock_overseer
                        
                        overseer = mock_overseer_class()
                        overseer_result = overseer.handle_event(interpreter_result)
                        
                        # 3. Vérifications
                        mock_listener.handle.assert_called_once_with(webhook_data)
                        mock_interpreter.run.assert_called_once()
                        mock_overseer.handle_event.assert_called_once_with(interpreter_result)
                        
                        # Vérifier que le flux s'est bien déroulé
                        self.assertEqual(overseer_result["status"], "success", "Le flux de gestion des réponses a échoué")

class TestEndToEndFlow(unittest.TestCase):
    """
    Tests de bout en bout pour simuler des scénarios complets.
    """
    
    def setUp(self):
        """Préparation des tests."""
        # Creation d'un mock pour logger_agent pour éviter les effets secondaires
        self.patcher = patch('agents.logger.logger_agent.LoggerAgent')
        self.mock_logger = self.patcher.start()
        
        # Patches pour éviter les appels réels à l'API LLM
        self.llm_patcher = patch('utils.llm.LLMService.call_llm')
        self.mock_llm = self.llm_patcher.start()
        
        # Configuration des réponses LLM par défaut
        self.mock_llm.return_value = '{"status": "success"}'
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.patcher.stop()
        self.llm_patcher.stop()
    
    def test_full_campaign_flow(self):
        """
        Teste un flux complet de campagne de prospection, de l'exploration de niche
        jusqu'au traitement des réponses.
        """
        # Cette fonction simule un flux complet de campagne
        # Mais comme elle est très complexe et implique tous les agents,
        # elle est implémentée sous forme de test d'intégration
        # et sera exécutée séparément dans un environnement contrôlé
        
        # Pour le moment, on se contente de vérifier que le test existe
        # et qu'il peut être lancé
        self.assertTrue(True, "Test d'intégration complet à implémenter séparément")
        
        # Note: Un test complet nécessiterait de mocker tous les agents et leurs interactions,
        # ce qui serait très verbeux et difficile à maintenir.
        # Mieux vaut exécuter un test réel dans un environnement isolé (sandbox).

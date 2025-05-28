"""
Tests pour le ConversationAgent 2.0
"""

import sys
import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock

# Ajout du chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.conversation.conversation_agent import ConversationAgent

class TestConversationAgent:
    """Tests pour le ConversationAgent"""
    
    def setup_method(self):
        """Setup pour chaque test"""
        self.agent = ConversationAgent()
        
    def test_initialization(self):
        """Test d'initialisation de l'agent"""
        assert self.agent.name == "ConversationAgent"
        assert hasattr(self.agent, "conversation_history")
        assert hasattr(self.agent, "available_agents")
        assert hasattr(self.agent, "quick_patterns")
        
    def test_quick_responses_greeting(self):
        """Test des réponses rapides - salutations"""
        response = self.agent.check_quick_responses("Bonjour")
        
        assert response is not None
        assert response["status"] == "success"
        assert "Bonjour" in response["message"]
        assert "BerinIA" in response["message"]
        
    def test_quick_responses_help(self):
        """Test des réponses rapides - aide"""
        response = self.agent.check_quick_responses("aide")
        
        assert response is not None
        assert response["status"] == "success"
        assert "BerinIA" in response["message"]
        assert "Assistant Conversationnel" in response["message"]
        
    def test_quick_responses_thanks(self):
        """Test des réponses rapides - remerciements"""
        response = self.agent.check_quick_responses("merci")
        
        assert response is not None
        assert response["status"] == "success"
        assert "De rien" in response["message"]
        
    def test_conversation_history(self):
        """Test de l'historique conversationnel"""
        # Ajout d'un message
        self.agent.add_to_history("Test message", "user", "test_user")
        
        assert len(self.agent.conversation_history) == 1
        assert self.agent.conversation_history[0]["content"] == "Test message"
        assert self.agent.conversation_history[0]["role"] == "user"
        assert self.agent.conversation_history[0]["author"] == "test_user"
        
    def test_success_response_format(self):
        """Test du format des réponses de succès"""
        response = self.agent.success_response("Test message")
        
        assert response["status"] == "success"
        assert response["message"] == "Test message"
        assert response["agent"] == "ConversationAgent"
        assert "timestamp" in response
        
    def test_error_response_format(self):
        """Test du format des réponses d'erreur"""
        response = self.agent.error_response("Test error")
        
        assert response["status"] == "error"
        assert response["message"] == "Test error"
        assert response["agent"] == "ConversationAgent"
        assert "timestamp" in response
        
    def test_run_with_empty_message(self):
        """Test avec un message vide"""
        response = self.agent.run({})
        
        assert response["status"] == "error"
        assert "Aucun message fourni" in response["message"]
        
    def test_run_with_greeting(self):
        """Test avec une salutation"""
        response = self.agent.run({"message": "Salut !"})
        
        assert response["status"] == "success"
        assert "Bonjour" in response["message"]
        
    @patch('agents.conversation.conversation_agent.LLMService.call_llm')
    def test_llm_analysis_database_strategy(self, mock_llm):
        """Test de l'analyse LLM - stratégie base de données"""
        # Mock de la réponse LLM
        mock_llm.return_value = "Je vais utiliser l'accès direct base de données pour cette requête."
        
        with patch.object(self.agent, 'handle_database_direct') as mock_db:
            mock_db.return_value = self.agent.success_response("Résultat BDD")
            
            response = self.agent.analyze_with_llm("Combien de leads avons-nous ?")
            
            mock_db.assert_called_once()
            assert response["status"] == "success"
            
    @patch('agents.conversation.conversation_agent.LLMService.call_llm')
    def test_llm_analysis_agent_delegation(self, mock_llm):
        """Test de l'analyse LLM - délégation d'agent"""
        # Mock de la réponse LLM
        mock_llm.return_value = "Je vais déléguer cette tâche au DatabaseQueryAgent."
        
        with patch.object(self.agent, 'delegate_to_agent') as mock_delegate:
            mock_delegate.return_value = self.agent.success_response("Résultat agent")
            
            response = self.agent.analyze_with_llm("Statistiques des leads")
            
            mock_delegate.assert_called_once_with("DatabaseQueryAgent", "Statistiques des leads")
            assert response["status"] == "success"
            
    @patch('agents.conversation.conversation_agent.LLMService.call_llm')
    def test_llm_analysis_overseer_call(self, mock_llm):
        """Test de l'analyse LLM - appel OverseerAgent"""
        # Mock de la réponse LLM
        mock_llm.return_value = "Cette tâche est complexe, je vais appeler l'OverseerAgent."
        
        with patch.object(self.agent, 'call_overseer') as mock_overseer:
            mock_overseer.return_value = self.agent.success_response("Résultat overseer")
            
            response = self.agent.analyze_with_llm("Lance une campagne complexe")
            
            mock_overseer.assert_called_once()
            assert response["status"] == "success"
            
    def test_generate_simple_sql(self):
        """Test de génération SQL simple"""
        # Test comptage leads
        sql = self.agent.generate_sql_from_message("Combien de leads avons-nous ?")
        assert "SELECT COUNT(*) FROM leads" in sql
        
        # Test leads contactés
        sql = self.agent.generate_sql_from_message("Combien de leads contactés ?")
        assert "contacted = true" in sql
        
        # Test statistiques
        sql = self.agent.generate_sql_from_message("Statistiques globales")
        assert "total_leads" in sql
        assert "contacted_leads" in sql
        
    def test_format_database_result_simple_count(self):
        """Test formatage résultat BDD - comptage simple"""
        result = [(42,)]
        formatted = self.agent.format_database_result(result, "Combien de leads")
        
        assert "42 leads" in formatted
        assert "base de données" in formatted
        
    def test_format_database_result_multiple_rows(self):
        """Test formatage résultat BDD - résultats multiples"""
        result = [("lead1", "email1"), ("lead2", "email2")]
        formatted = self.agent.format_database_result(result, "Liste des leads")
        
        assert "résultats" in formatted
        assert "lead1" in formatted
        assert "lead2" in formatted
        
    def test_extract_agent_name_patterns(self):
        """Test extraction de nom d'agent"""
        # Test patterns spécifiques
        assert self.agent.extract_agent_name("utilise la base de données") == "DatabaseQueryAgent"
        assert self.agent.extract_agent_name("fait du scraping") == "ScraperAgent"
        assert self.agent.extract_agent_name("envoie un message") == "MessagingAgent"
        assert self.agent.extract_agent_name("analyse la niche") == "NicheClassifierAgent"
        
    def test_fallback_analysis_keywords(self):
        """Test de l'analyse de fallback par mots-clés"""
        with patch.object(self.agent, 'delegate_to_agent') as mock_delegate:
            mock_delegate.return_value = self.agent.success_response("Test")
            
            # Test délégation DatabaseQueryAgent
            self.agent.fallback_analysis("Combien de statistiques ?")
            mock_delegate.assert_called_with("DatabaseQueryAgent", "Combien de statistiques ?")
            
            # Test délégation ScraperAgent  
            self.agent.fallback_analysis("Scrape des leads")
            mock_delegate.assert_called_with("ScraperAgent", "Scrape des leads")
            
            # Test délégation MessagingAgent
            self.agent.fallback_analysis("Envoie un email")
            mock_delegate.assert_called_with("MessagingAgent", "Envoie un email")
            
    @patch('agents.conversation.conversation_agent.registry')
    def test_delegate_to_agent_success(self, mock_registry):
        """Test délégation d'agent - succès"""
        # Mock de l'agent
        mock_agent = Mock()
        mock_agent.run.return_value = {"status": "success", "message": "Tâche réussie"}
        mock_registry.get_or_create.return_value = mock_agent
        
        response = self.agent.delegate_to_agent("TestAgent", "Test message")
        
        assert response["status"] == "success"
        assert "Tâche réussie" in response["message"]
        mock_agent.run.assert_called_once()
        
    @patch('agents.conversation.conversation_agent.registry')
    def test_delegate_to_agent_not_found(self, mock_registry):
        """Test délégation d'agent - agent non trouvé"""
        mock_registry.get_or_create.return_value = None
        
        response = self.agent.delegate_to_agent("NonExistentAgent", "Test message")
        
        assert response["status"] == "error"
        assert "non disponible" in response["message"]
        
    @patch('agents.conversation.conversation_agent.registry')
    def test_call_overseer_success(self, mock_registry):
        """Test appel OverseerAgent - succès"""
        # Mock de l'OverseerAgent
        mock_overseer = Mock()
        mock_overseer.run.return_value = {"status": "success", "message": "Tâche complexe réussie"}
        mock_registry.get_or_create.return_value = mock_overseer
        
        response = self.agent.call_overseer("Tâche complexe")
        
        assert response["status"] == "success"
        assert "Tâche complexe réussie" in response["message"]
        mock_overseer.run.assert_called_once()
        
    def test_build_system_context(self):
        """Test construction du contexte système"""
        self.agent.available_agents = {"TestAgent": {}, "OtherAgent": {}}
        context = self.agent.build_system_context()
        
        assert "Agents disponibles" in context
        assert "TestAgent" in context
        assert "OtherAgent" in context
        assert "Timestamp" in context
        
    def test_get_conversation_context_empty(self):
        """Test contexte conversationnel vide"""
        context = self.agent.get_conversation_context()
        assert context == "Nouvelle conversation"
        
    def test_get_conversation_context_with_history(self):
        """Test contexte conversationnel avec historique"""
        self.agent.add_to_history("Premier message", "user", "test")
        self.agent.add_to_history("Réponse", "assistant", "ConversationAgent")
        
        context = self.agent.get_conversation_context()
        
        assert "user: Premier message" in context
        assert "assistant: Réponse" in context
        
    def test_store_learning_interaction(self):
        """Test stockage d'interaction pour apprentissage"""
        response = {"status": "success", "message": "Test"}
        
        # Le stockage ne devrait pas lever d'exception
        self.agent.store_learning_interaction("Test message", response)
        
        # Pour l'instant, c'est juste un log, donc pas d'assertion spécifique
        # TODO: Ajouter des assertions quand le vrai système de stockage sera implémenté


if __name__ == "__main__":
    # Exécution des tests si le script est lancé directement
    pytest.main([__file__, "-v"])

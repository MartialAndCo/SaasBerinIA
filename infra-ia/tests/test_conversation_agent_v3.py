"""
Tests pour ConversationAgent V3 - Agent révolutionnaire 100% IA
Tests complets pour vérifier la nouvelle architecture intelligente
"""

import pytest
import json
import logging
from typing import Dict, Any
from unittest.mock import Mock, patch

# Configuration du logging pour les tests
logging.basicConfig(level=logging.INFO)

# Import des modules à tester
from agents.conversation.conversation_agent_v3 import ConversationAgentV3

class TestConversationAgentV3:
    """Suite de tests pour ConversationAgent V3"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.agent = ConversationAgentV3()
        
        # Mock du registre d'agents pour les tests
        self.mock_agents = {
            "ScraperAgent": Mock(),
            "DatabaseQueryAgent": Mock(), 
            "MessagingAgent": Mock(),
            "OverseerAgent": Mock(),
            "AnalyzerAgent": Mock()
        }
        
        # Configuration des mocks
        for agent_name, mock_agent in self.mock_agents.items():
            mock_agent.run.return_value = {
                "status": "success",
                "message": f"Mock réponse de {agent_name}"
            }
        
        # Injection des mocks
        self.agent.available_agents = self.mock_agents
    
    def test_revolutionary_scraping_case(self):
        """Test du cas critique qui échouait: 'scrappe 2 restaurants a toulouse'"""
        
        print("\n🎯 TEST CRITIQUE: scrappe 2 restaurants a toulouse")
        
        # Le cas qui échouait avec l'ancien système
        test_input = {
            "message": "scrappe 2 restaurants a toulouse",
            "source": "whatsapp",
            "author": "user_test"
        }
        
        # Mock du ScraperAgent pour ce test
        self.mock_agents["ScraperAgent"].run.return_value = {
            "status": "success", 
            "message": "2 restaurants récupérés à Toulouse",
            "leads": [
                {"name": "Restaurant A", "location": "Toulouse"},
                {"name": "Restaurant B", "location": "Toulouse"}
            ]
        }
        
        # Exécution
        result = self.agent.run(test_input)
        
        # Vérifications
        assert result["status"] == "success", f"Échec: {result}"
        assert "restaurants" in result["message"].lower(), f"Pas de mention de restaurants: {result['message']}"
        assert "toulouse" in result["message"].lower(), f"Pas de mention de Toulouse: {result['message']}"
        
        # Vérifier que le ScraperAgent a été appelé
        self.mock_agents["ScraperAgent"].run.assert_called_once()
        
        # Vérifier les paramètres passés au ScraperAgent
        call_args = self.mock_agents["ScraperAgent"].run.call_args[0][0]
        assert "niche" in call_args, "Paramètre niche manquant"
        assert "restaurants" in call_args["niche"].lower(), f"Niche incorrecte: {call_args['niche']}"
        assert call_args.get("limit") == 2, f"Limite incorrecte: {call_args.get('limit')}"
        assert "toulouse" in call_args.get("city", "").lower(), f"Ville incorrecte: {call_args.get('city')}"
        
        print(f"✅ SUCCÈS: {result['message']}")
        print(f"📋 Paramètres extraits: niche={call_args.get('niche')}, limit={call_args.get('limit')}, city={call_args.get('city')}")
    
    def test_various_scraping_requests(self):
        """Test de diverses demandes de scraping avec variantes naturelles"""
        
        test_cases = [
            {
                "message": "trouve 5 dentistes sur paris",
                "expected_niche": "dentistes",
                "expected_quantity": 5,
                "expected_location": "paris"
            },
            {
                "message": "récupère 10 leads dans l'immobilier",
                "expected_niche": "immobilier",
                "expected_quantity": 10
            },
            {
                "message": "scrape des avocats à lyon",
                "expected_niche": "avocats",
                "expected_location": "lyon"
            },
            {
                "message": "extraction de 20 prospects coaching",
                "expected_niche": "coaching",
                "expected_quantity": 20
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n🧪 Test scraping {i+1}: {test_case['message']}")
            
            # Reset du mock
            self.mock_agents["ScraperAgent"].reset_mock()
            
            # Exécution
            result = self.agent.run({"message": test_case["message"]})
            
            # Vérifications
            assert result["status"] == "success", f"Échec pour: {test_case['message']}"
            
            # Vérifier l'appel au ScraperAgent
            self.mock_agents["ScraperAgent"].run.assert_called_once()
            call_args = self.mock_agents["ScraperAgent"].run.call_args[0][0]
            
            # Vérifier les paramètres extraits
            if "expected_niche" in test_case:
                assert test_case["expected_niche"] in call_args.get("niche", "").lower()
            
            if "expected_quantity" in test_case:
                assert call_args.get("limit") == test_case["expected_quantity"]
            
            if "expected_location" in test_case:
                assert test_case["expected_location"] in call_args.get("city", "").lower()
            
            print(f"✅ Succès: niche={call_args.get('niche')}, limit={call_args.get('limit')}")
    
    def test_data_query_requests(self):
        """Test des requêtes de données"""
        
        test_cases = [
            "combien de leads avons-nous ?",
            "statistiques de la dernière campagne",
            "nombre de prospects dans l'immobilier",
            "stats performance par niche"
        ]
        
        for message in test_cases:
            print(f"\n🧪 Test données: {message}")
            
            # Reset du mock
            self.mock_agents["DatabaseQueryAgent"].reset_mock()
            
            # Exécution
            result = self.agent.run({"message": message})
            
            # Vérifications
            assert result["status"] == "success"
            
            # Le DatabaseQueryAgent devrait être appelé
            self.mock_agents["DatabaseQueryAgent"].run.assert_called_once()
            
            print(f"✅ Succès: délégation à DatabaseQueryAgent")
    
    def test_messaging_requests(self):
        """Test des demandes d'envoi de messages"""
        
        test_cases = [
            "envoie un email aux nouveaux leads",
            "prépare une campagne SMS", 
            "contact les prospects immobilier"
        ]
        
        for message in test_cases:
            print(f"\n🧪 Test messaging: {message}")
            
            # Reset du mock
            self.mock_agents["MessagingAgent"].reset_mock()
            
            # Exécution
            result = self.agent.run({"message": message})
            
            # Vérifications
            assert result["status"] == "success"
            
            # Le MessagingAgent devrait être appelé
            self.mock_agents["MessagingAgent"].run.assert_called_once()
            
            print(f"✅ Succès: délégation à MessagingAgent")
    
    def test_general_chat_responses(self):
        """Test des réponses de conversation générale"""
        
        test_cases = [
            ("salut", "bonjour"),
            ("bonjour", "bonjour"),
            ("merci", "rien"),
            ("que peux-tu faire ?", "berinia"),
            ("aide", "scraping")
        ]
        
        for message, expected_keyword in test_cases:
            print(f"\n🧪 Test chat: {message}")
            
            result = self.agent.run({"message": message})
            
            # Vérifications
            assert result["status"] == "success"
            assert expected_keyword.lower() in result["message"].lower()
            
            print(f"✅ Succès: réponse appropriée")
    
    def test_ai_analysis_integration(self):
        """Test de l'intégration avec AIRequestParser"""
        
        message = "scrappe 3 restaurants bio à marseille"
        
        print(f"\n🧪 Test intégration IA: {message}")
        
        # Patch pour capturer l'analyse IA
        with patch('utils.ai_request_parser.analyze_user_request') as mock_analyze:
            mock_analyze.return_value = {
                "intention": "scrape_leads",
                "parameters": {
                    "niche": "restaurants",
                    "quantity": 3,
                    "location": "Marseille",
                    "filters": ["bio"]
                },
                "agent_target": "ScraperAgent",
                "confidence": 0.95
            }
            
            # Exécution
            result = self.agent.run({"message": message})
            
            # Vérifications
            assert result["status"] == "success"
            
            # Vérifier que l'analyse IA a été appelée
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args
            assert call_args[1]["message"] == message
            
            print(f"✅ Succès: intégration IA fonctionnelle")
    
    def test_error_handling(self):
        """Test de la gestion d'erreurs"""
        
        print(f"\n🧪 Test gestion erreurs")
        
        # Simuler une erreur dans le ScraperAgent
        self.mock_agents["ScraperAgent"].run.side_effect = Exception("Erreur test")
        
        result = self.agent.run({"message": "scrappe des restaurants"})
        
        # L'agent doit gérer l'erreur gracieusement
        assert result["status"] == "error"
        assert "erreur" in result["message"].lower()
        
        print(f"✅ Succès: erreur gérée correctement")
    
    def test_conversation_history(self):
        """Test de la gestion de l'historique conversationnel"""
        
        print(f"\n🧪 Test historique conversation")
        
        # Séquence de messages
        messages = [
            "salut",
            "scrappe 2 restaurants",
            "merci"
        ]
        
        for message in messages:
            result = self.agent.run({"message": message})
            assert result["status"] == "success"
        
        # Vérifier que l'historique est maintenu
        assert len(self.agent.conversation_history) == 6  # 3 messages × 2 (user + assistant)
        
        # Vérifier le contenu de l'historique
        user_messages = [entry for entry in self.agent.conversation_history if entry["role"] == "user"]
        assert len(user_messages) == 3
        assert user_messages[0]["content"] == "salut"
        assert user_messages[1]["content"] == "scrappe 2 restaurants"
        assert user_messages[2]["content"] == "merci"
        
        print(f"✅ Succès: historique maintenu correctement")
    
    def test_usage_statistics(self):
        """Test des statistiques d'utilisation"""
        
        print(f"\n🧪 Test statistiques utilisation")
        
        initial_stats = self.agent.usage_stats.copy()
        
        # Plusieurs types de requêtes
        self.agent.run({"message": "scrappe des restaurants"})  # Délégation
        self.agent.run({"message": "salut"})  # Réponse directe
        
        # Vérifier les statistiques
        stats = self.agent.usage_stats
        assert stats["total_requests"] == initial_stats["total_requests"] + 2
        assert stats["agent_delegations"] == initial_stats["agent_delegations"] + 1
        assert stats["direct_responses"] == initial_stats["direct_responses"] + 1
        
        # Test de la méthode get_usage_stats
        full_stats = self.agent.get_usage_stats()
        assert "agent_version" in full_stats
        assert full_stats["agent_version"] == "3.0"
        
        print(f"✅ Succès: statistiques correctes")
    
    def test_parameter_extraction_accuracy(self):
        """Test de précision d'extraction des paramètres"""
        
        test_cases = [
            {
                "message": "scrappe 15 restaurants bio à marseille via apollo",
                "expected_params": {
                    "niche": "restaurants",
                    "limit": 15,
                    "city": "marseille",
                    "source": "apollo"
                }
            },
            {
                "message": "trouve 50 dentistes spécialisés sur nice",
                "expected_params": {
                    "niche": "dentistes", 
                    "limit": 50,
                    "city": "nice"
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Test extraction: {test_case['message']}")
            
            # Reset du mock
            self.mock_agents["ScraperAgent"].reset_mock()
            
            # Exécution
            result = self.agent.run({"message": test_case["message"]})
            
            # Vérifications
            assert result["status"] == "success"
            
            # Vérifier les paramètres passés
            call_args = self.mock_agents["ScraperAgent"].run.call_args[0][0]
            expected = test_case["expected_params"]
            
            for key, expected_value in expected.items():
                actual_value = call_args.get(key, "")
                
                if isinstance(expected_value, str):
                    assert expected_value.lower() in str(actual_value).lower(), f"{key}: attendu '{expected_value}', reçu '{actual_value}'"
                else:
                    assert actual_value == expected_value, f"{key}: attendu {expected_value}, reçu {actual_value}"
            
            print(f"✅ Paramètres corrects: {expected}")

def test_integration_with_real_ai_parser():
    """Test d'intégration avec le vrai AIRequestParser (sans mock)"""
    
    print(f"\n🧪 Test intégration réelle")
    
    agent = ConversationAgentV3()
    
    # Mock simple des agents pour ce test
    agent.available_agents = {"ScraperAgent": Mock()}
    agent.available_agents["ScraperAgent"].run.return_value = {
        "status": "success",
        "message": "Mock scraping réussi"
    }
    
    # Test avec le vrai parser IA
    result = agent.run({"message": "scrappe 2 restaurants a toulouse"})
    
    # Vérifications
    assert result["status"] == "success"
    
    print(f"✅ Intégration réelle fonctionne")

if __name__ == "__main__":
    """Exécution directe des tests"""
    
    print("🚀 Tests ConversationAgent V3 - Agent Révolutionnaire 100% IA")
    print("=" * 70)
    
    # Création de l'instance de test
    test_suite = TestConversationAgentV3()
    test_suite.setup_method()
    
    # Exécution des tests
    test_methods = [
        ("Test CRITIQUE - Scraping Original", test_suite.test_revolutionary_scraping_case),
        ("Test Variantes Scraping", test_suite.test_various_scraping_requests),
        ("Test Requêtes Données", test_suite.test_data_query_requests),
        ("Test Messaging", test_suite.test_messaging_requests),
        ("Test Chat Général", test_suite.test_general_chat_responses),
        ("Test Intégration IA", test_suite.test_ai_analysis_integration),
        ("Test Gestion Erreurs", test_suite.test_error_handling),
        ("Test Historique", test_suite.test_conversation_history),
        ("Test Statistiques", test_suite.test_usage_statistics),
        ("Test Extraction Paramètres", test_suite.test_parameter_extraction_accuracy)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_method in test_methods:
        try:
            print(f"\n🧪 {test_name}")
            print("-" * 50)
            test_method()
            print(f"✅ {test_name} RÉUSSI")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} ÉCHOUÉ: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Test d'intégration réelle
    try:
        print(f"\n🧪 Test Intégration Réelle")
        print("-" * 50)
        test_integration_with_real_ai_parser()
        print(f"✅ Test Intégration Réelle RÉUSSI")
        passed += 1
    except Exception as e:
        print(f"❌ Test Intégration Réelle ÉCHOUÉ: {e}")
        failed += 1
    
    # Résumé
    print("\n" + "=" * 70)
    print(f"🏁 RÉSUMÉ DES TESTS CONVERSATIONAGENT V3")
    print(f"✅ Tests réussis: {passed}")
    print(f"❌ Tests échoués: {failed}")
    print(f"📊 Taux de réussite: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("🚀 ConversationAgent V3 est prêt pour la révolution !")
        print("💯 Le cas 'scrappe 2 restaurants a toulouse' fonctionne maintenant !")
    else:
        print("⚠️ Des améliorations sont nécessaires.")

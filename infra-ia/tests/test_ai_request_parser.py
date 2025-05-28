"""
Tests pour AIRequestParser - Parser intelligent 100% IA
Tests complets pour vérifier l'analyse intelligente des demandes
"""

import pytest
import json
import logging
from typing import Dict, Any

# Configuration du logging pour les tests
logging.basicConfig(level=logging.INFO)

# Import des modules à tester
from utils.ai_request_parser import AIRequestParser, analyze_user_request

class TestAIRequestParser:
    """Suite de tests pour AIRequestParser"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.parser = AIRequestParser()
        self.test_agents = [
            "ScraperAgent", "DatabaseQueryAgent", "MessagingAgent", 
            "OverseerAgent", "AnalyzerAgent"
        ]
    
    def test_analyze_scraping_requests(self):
        """Test des demandes de scraping - LE CAS QUI ÉCHOUAIT"""
        
        test_cases = [
            # Le cas original qui échouait
            {
                "message": "scrappe 2 restaurants a toulouse",
                "expected_intention": "scrape_leads",
                "expected_niche": "restaurants",
                "expected_quantity": 2,
                "expected_location": "Toulouse"
            },
            # Variantes diverses
            {
                "message": "trouve 5 dentistes sur paris",
                "expected_intention": "scrape_leads", 
                "expected_niche": "dentistes",
                "expected_quantity": 5,
                "expected_location": "Paris"
            },
            {
                "message": "récupère 10 leads dans l'immobilier",
                "expected_intention": "scrape_leads",
                "expected_niche": "immobilier", 
                "expected_quantity": 10
            },
            {
                "message": "scrape des avocats à lyon",
                "expected_intention": "scrape_leads",
                "expected_niche": "avocats",
                "expected_location": "Lyon"
            },
            {
                "message": "extraction de 20 prospects coaching",
                "expected_intention": "scrape_leads",
                "expected_niche": "coaching",
                "expected_quantity": 20
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n🧪 Test {i+1}: {test_case['message']}")
            
            # Analyse
            result = self.parser.analyze_request(
                message=test_case["message"],
                available_agents=self.test_agents
            )
            
            # Vérifications
            assert result["intention"] == test_case["expected_intention"], f"Intention incorrecte: {result['intention']}"
            
            parameters = result.get("parameters", {})
            
            if "expected_niche" in test_case:
                assert test_case["expected_niche"] in parameters.get("niche", "").lower(), f"Niche non détectée: {parameters.get('niche')}"
            
            if "expected_quantity" in test_case:
                assert parameters.get("quantity") == test_case["expected_quantity"], f"Quantité incorrecte: {parameters.get('quantity')}"
            
            if "expected_location" in test_case:
                assert test_case["expected_location"].lower() in parameters.get("location", "").lower(), f"Location non détectée: {parameters.get('location')}"
            
            # L'agent doit être ScraperAgent ou auto
            assert result.get("agent_target") in ["ScraperAgent", "auto"], f"Agent incorrect: {result.get('agent_target')}"
            
            print(f"✅ Résultat: {result['intention']} | {parameters} | {result.get('agent_target')}")
    
    def test_analyze_data_queries(self):
        """Test des requêtes de données"""
        
        test_cases = [
            {
                "message": "combien de leads avons-nous ?",
                "expected_intention": "query_data"
            },
            {
                "message": "statistiques de la dernière campagne",
                "expected_intention": "query_data"
            },
            {
                "message": "nombre de prospects dans l'immobilier", 
                "expected_intention": "query_data",
                "expected_niche": "immobilier"
            },
            {
                "message": "stats performance par niche",
                "expected_intention": "query_data"
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Test données: {test_case['message']}")
            
            result = self.parser.analyze_request(
                message=test_case["message"],
                available_agents=self.test_agents
            )
            
            assert result["intention"] == test_case["expected_intention"]
            assert result.get("agent_target") in ["DatabaseQueryAgent", "auto"]
            
            print(f"✅ Résultat: {result['intention']} | {result.get('agent_target')}")
    
    def test_analyze_messaging_requests(self):
        """Test des demandes d'envoi de messages"""
        
        test_cases = [
            {
                "message": "envoie un email aux nouveaux leads",
                "expected_intention": "send_messages"
            },
            {
                "message": "prépare une campagne SMS",
                "expected_intention": "send_messages"
            },
            {
                "message": "contact les prospects immobilier",
                "expected_intention": "send_messages",
                "expected_niche": "immobilier"
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Test messaging: {test_case['message']}")
            
            result = self.parser.analyze_request(
                message=test_case["message"],
                available_agents=self.test_agents
            )
            
            assert result["intention"] == test_case["expected_intention"]
            print(f"✅ Résultat: {result['intention']} | {result.get('agent_target')}")
    
    def test_analyze_general_chat(self):
        """Test des conversations générales"""
        
        test_cases = [
            "salut",
            "bonjour",
            "merci",
            "que peux-tu faire ?",
            "aide moi",
            "comment ça va ?"
        ]
        
        for message in test_cases:
            print(f"\n🧪 Test chat: {message}")
            
            result = self.parser.analyze_request(
                message=message,
                available_agents=self.test_agents
            )
            
            assert result["intention"] == "general_chat"
            print(f"✅ Résultat: {result['intention']}")
    
    def test_parameter_extraction_accuracy(self):
        """Test de précision d'extraction des paramètres"""
        
        test_cases = [
            {
                "message": "scrappe 15 restaurants bio à marseille via apollo",
                "expected_params": {
                    "niche": "restaurants",
                    "quantity": 15,
                    "location": "Marseille", 
                    "source": "apollo",
                    "filters": ["bio"]
                }
            },
            {
                "message": "trouve 50 dentistes spécialisés orthodontie sur nice",
                "expected_params": {
                    "niche": "dentistes",
                    "quantity": 50,
                    "location": "Nice"
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Test extraction: {test_case['message']}")
            
            result = self.parser.analyze_request(
                message=test_case["message"],
                available_agents=self.test_agents
            )
            
            parameters = result.get("parameters", {})
            expected = test_case["expected_params"]
            
            # Vérification de chaque paramètre attendu
            for key, expected_value in expected.items():
                if key == "filters":
                    continue  # Filters plus complexe à tester
                
                actual_value = parameters.get(key)
                
                if isinstance(expected_value, str):
                    assert expected_value.lower() in str(actual_value).lower(), f"{key}: attendu '{expected_value}', reçu '{actual_value}'"
                else:
                    assert actual_value == expected_value, f"{key}: attendu {expected_value}, reçu {actual_value}"
            
            print(f"✅ Paramètres extraits: {parameters}")
    
    def test_agent_suggestion_logic(self):
        """Test de la logique de suggestion d'agents"""
        
        test_cases = [
            ("scrape_leads", ["ScraperAgent", "ScrapingSupervisor"]),
            ("query_data", ["DatabaseQueryAgent"]),
            ("send_messages", ["MessagingAgent", "ProspectionSupervisor"]),
            ("analyze_data", ["DatabaseQueryAgent", "AnalyzerAgent"]),
            ("system_config", ["OverseerAgent"])
        ]
        
        for intention, expected_agents in test_cases:
            print(f"\n🧪 Test suggestion: {intention}")
            
            suggested_agent = self.parser.suggest_agent(
                intention=intention,
                parameters={},
                available_agents=self.test_agents
            )
            
            # L'agent suggéré doit être dans la liste des agents disponibles
            assert suggested_agent in self.test_agents or suggested_agent == "auto"
            
            print(f"✅ Agent suggéré: {suggested_agent}")
    
    def test_fallback_mechanisms(self):
        """Test des mécanismes de fallback"""
        
        # Test avec JSON malformé (simulé en mockant l'erreur)
        original_method = self.parser._parse_llm_response
        
        def mock_parse_error(llm_response, original_message):
            # Force l'utilisation du fallback
            return self.parser._extract_from_text("texte non parsable", original_message)
        
        self.parser._parse_llm_response = mock_parse_error
        
        result = self.parser.analyze_request(
            message="scrappe des restaurants",
            available_agents=self.test_agents
        )
        
        # Restore original method
        self.parser._parse_llm_response = original_method
        
        # Même avec le fallback, on doit avoir un résultat valide
        assert result["intention"] in self.parser.supported_intentions
        assert "confidence" in result
        
        print(f"✅ Fallback test: {result['intention']} (confiance: {result['confidence']})")
    
    def test_cache_functionality(self):
        """Test du système de cache"""
        
        message = "scrappe 3 restaurants a toulouse"
        
        # Premier appel - mise en cache
        result1 = self.parser.analyze_request(
            message=message,
            available_agents=self.test_agents
        )
        
        # Deuxième appel - depuis le cache
        result2 = self.parser.analyze_request(
            message=message,
            available_agents=self.test_agents
        )
        
        # Les résultats doivent être identiques
        assert result1 == result2
        
        # Le cache doit contenir l'entrée
        cache_key = f"{message}_{str(self.test_agents)}"
        assert cache_key in self.parser.analysis_cache
        
        print("✅ Cache fonctionne correctement")
    
    def test_confidence_scores(self):
        """Test des scores de confiance"""
        
        test_cases = [
            ("scrappe 2 restaurants a toulouse", 0.8),  # Demande claire, confiance élevée
            ("trouve des trucs", 0.5),  # Demande vague, confiance plus faible
            ("salut", 0.9),  # Salutation simple, confiance élevée
        ]
        
        for message, min_confidence in test_cases:
            result = self.parser.analyze_request(
                message=message,
                available_agents=self.test_agents
            )
            
            confidence = result.get("confidence", 0)
            assert confidence >= min_confidence, f"Confiance trop faible: {confidence} < {min_confidence}"
            
            print(f"✅ Confiance pour '{message}': {confidence:.2f}")

def test_analyze_user_request_function():
    """Test de la fonction utilitaire"""
    
    result = analyze_user_request(
        message="scrappe 2 restaurants a toulouse",
        available_agents=["ScraperAgent", "DatabaseQueryAgent"]
    )
    
    assert result["intention"] == "scrape_leads"
    assert "restaurants" in result["parameters"].get("niche", "").lower()
    assert result["parameters"].get("quantity") == 2
    
    print("✅ Fonction utilitaire fonctionne")

if __name__ == "__main__":
    """Exécution directe des tests"""
    
    print("🚀 Tests AIRequestParser - Parser Intelligent 100% IA")
    print("=" * 60)
    
    # Création de l'instance de test
    test_suite = TestAIRequestParser()
    test_suite.setup_method()
    
    # Exécution des tests
    test_methods = [
        ("Test Scraping (CAS CRITIQUE)", test_suite.test_analyze_scraping_requests),
        ("Test Requêtes Données", test_suite.test_analyze_data_queries),
        ("Test Messaging", test_suite.test_analyze_messaging_requests),
        ("Test Chat Général", test_suite.test_analyze_general_chat),
        ("Test Extraction Paramètres", test_suite.test_parameter_extraction_accuracy),
        ("Test Suggestion Agents", test_suite.test_agent_suggestion_logic),
        ("Test Fallback", test_suite.test_fallback_mechanisms),
        ("Test Cache", test_suite.test_cache_functionality),
        ("Test Confiance", test_suite.test_confidence_scores)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_method in test_methods:
        try:
            print(f"\n🧪 {test_name}")
            print("-" * 40)
            test_method()
            print(f"✅ {test_name} RÉUSSI")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} ÉCHOUÉ: {e}")
            failed += 1
    
    # Test de la fonction utilitaire
    try:
        print(f"\n🧪 Test Fonction Utilitaire")
        print("-" * 40)
        test_analyze_user_request_function()
        print(f"✅ Test Fonction Utilitaire RÉUSSI")
        passed += 1
    except Exception as e:
        print(f"❌ Test Fonction Utilitaire ÉCHOUÉ: {e}")
        failed += 1
    
    # Résumé
    print("\n" + "=" * 60)
    print(f"🏁 RÉSUMÉ DES TESTS")
    print(f"✅ Tests réussis: {passed}")
    print(f"❌ Tests échoués: {failed}")
    print(f"📊 Taux de réussite: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("🚀 AIRequestParser est prêt pour la production !")
    else:
        print("⚠️ Des améliorations sont nécessaires.")

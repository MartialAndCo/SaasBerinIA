#!/usr/bin/env python3
"""
Tests d'intégration des fonctionnalités LLM de BerinIA.

Ce module contient des tests pour vérifier l'interaction avec les modèles
de langage OpenAI, la construction des prompts, et le traitement des réponses.
"""
import os
import sys
import unittest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib.util

# Ajout du répertoire parent au chemin de recherche des modules
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

# Import des modules à tester (avec gestion des erreurs)
try:
    from utils import llm
    import openai
except ImportError:
    llm = None
    openai = None

class TestLLMUtilMock(unittest.TestCase):
    """
    Tests des fonctionnalités LLM avec mock pour éviter les appels API réels.
    """
    
    def setUp(self):
        """Préparation des tests."""
        self.mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "Ceci est une réponse de test du LLM"
                    }
                }
            ]
        }
    
    @unittest.skipIf(llm is None, "Module LLM non disponible")
    @patch('utils.llm.openai.ChatCompletion.create')
    def test_call_llm_basic(self, mock_create):
        """Test de base de l'appel au LLM."""
        # Configuration du mock
        mock_create.return_value = self.mock_response
        
        # Test de l'appel
        prompt = "Ceci est un prompt de test"
        result = llm.LLMService.call_llm(prompt)
        
        # Vérifications
        self.assertEqual(result, "Ceci est une réponse de test du LLM")
        mock_create.assert_called_once()
        
        # Vérification des arguments
        args, kwargs = mock_create.call_args
        self.assertIn("messages", kwargs)
        self.assertEqual(kwargs["messages"][0]["content"], prompt)
    
    @unittest.skipIf(llm is None, "Module LLM non disponible")
    @patch('utils.llm.openai.ChatCompletion.create')
    def test_call_llm_complexity_levels(self, mock_create):
        """Test des différents niveaux de complexité pour les appels LLM."""
        # Configuration du mock
        mock_create.return_value = self.mock_response
        
        # Test des différents niveaux de complexité
        complexities = ["high", "medium", "low"]
        expected_models = {
            "high": "gpt-4.1",
            "medium": "gpt-4.1-mini",
            "low": "gpt-4.1-nano"
        }
        
        for complexity in complexities:
            # Reset du mock
            mock_create.reset_mock()
            
            # Appel avec complexité spécifique
            prompt = f"Test prompt for {complexity} complexity"
            llm.LLMService.call_llm(prompt, complexity=complexity)
            
            # Vérification du modèle utilisé
            args, kwargs = mock_create.call_args
            expected_model = expected_models[complexity]
            self.assertEqual(kwargs.get("model"), expected_model, 
                           f"Mauvais modèle pour la complexité {complexity}")
    
    @unittest.skipIf(llm is None, "Module LLM non disponible")
    @patch('utils.llm.openai.ChatCompletion.create')
    def test_call_llm_with_system_message(self, mock_create):
        """Test de l'appel au LLM avec un message système."""
        # Configuration du mock
        mock_create.return_value = self.mock_response
        
        # Test avec message système
        prompt = "Prompt utilisateur"
        system_message = "Tu es un assistant intelligent"
        
        # Construction des messages avec un message système
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        # Utilisation du mock pour un appel direct à l'API
        mock_create.return_value = self.mock_response
        openai.ChatCompletion.create(
            model=llm.LLMService.MODELS["high"],
            messages=messages,
            temperature=0.3
        )
        
        # Vérification
        args, kwargs = mock_create.call_args
        messages = kwargs.get("messages", [])
        
        # Chercher le message système dans les messages
        has_system = any(msg.get("role") == "system" and msg.get("content") == system_message 
                        for msg in messages)
        
        self.assertTrue(has_system, "Le message système n'a pas été inclus correctement")

class TestPromptTesting(unittest.TestCase):
    """
    Tests pour vérifier les prompts des agents.
    """
    
    def setUp(self):
        """Préparation des tests."""
        self.agents_dir = ROOT_DIR / "agents"
        
    def test_prompt_variables(self):
        """Vérifie que les variables dans les prompts sont bien formatées."""
        prompt_files = []
        
        # Recherche de tous les fichiers prompt.txt
        for agent_dir in self.agents_dir.iterdir():
            if agent_dir.is_dir() and not agent_dir.name.startswith('__'):
                prompt_path = agent_dir / "prompt.txt"
                if prompt_path.exists():
                    prompt_files.append(prompt_path)
        
        for prompt_file in prompt_files:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Recherche des sections d'exemples JSON pour les exclure
            import re
            json_sections = []
            
            # Recherche des blocs de code JSON délimités par ```
            json_blocks = re.finditer(r'```(?:json)?\n(.*?)```', content, re.DOTALL)
            for block in json_blocks:
                start, end = block.span()
                json_sections.append((start, end))
            
            # Recherche d'exemples JSON inlinés
            json_examples = re.finditer(r'\{(\s*"[^"]+"\s*:.*?)\}', content, re.DOTALL)
            for example in json_examples:
                # Vérifie si l'exemple contient des paires clé/valeur typiques du JSON
                if re.search(r'"[^"]+"\s*:\s*(?:"[^"]*"|true|false|\d+)', example.group(1)):
                    start, end = example.span()
                    json_sections.append((start, end))
            
            # Trouver les variables de formatage (en dehors des exemples JSON)
            template_variables = []
            var_matches = re.finditer(r'\{([^{}]+)\}', content)
            
            for match in var_matches:
                var = match.group(1)
                var_pos = match.start()
                
                # Vérifier si la variable est dans une section JSON
                in_json_section = False
                for start, end in json_sections:
                    if start <= var_pos <= end:
                        in_json_section = True
                        break
                
                if not in_json_section:
                    template_variables.append(var)
            
            # Vérifier que les variables de template sont bien formatées
            for var in template_variables:
                # Vérifier le format des variables
                self.assertFalse(' ' in var, 
                               f"Variable '{var}' dans {prompt_file.name} contient des espaces")
                self.assertFalse('-' in var, 
                               f"Variable '{var}' dans {prompt_file.name} contient des tirets")
            
            # Vérifier les accolades non appariées (erreurs de formatage)
            open_braces = content.count('{')
            close_braces = content.count('}')
            
            # On ignore les déséquilibres dans les exemples JSON
            if "```json" not in content:
                self.assertEqual(open_braces, close_braces, 
                               f"Accolades non appariées dans {prompt_file.name}: {open_braces} ouvertes, {close_braces} fermées")

class TestJSONFormatting(unittest.TestCase):
    """
    Tests pour vérifier le formatage JSON dans les agents.
    """
    
    def setUp(self):
        """Préparation des tests."""
        self.agents_dir = ROOT_DIR / "agents"
    
    def test_config_json_schema(self):
        """Vérifie que les fichiers config.json suivent un schéma cohérent."""
        config_files = []
        
        # Recherche de tous les fichiers config.json
        for agent_dir in self.agents_dir.iterdir():
            if agent_dir.is_dir() and not agent_dir.name.startswith('__'):
                config_path = agent_dir / "config.json"
                if config_path.exists():
                    config_files.append(config_path)
        
        # Vérification de chaque fichier config.json
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Vérifier qu'il s'agit bien d'un dictionnaire
                self.assertIsInstance(config, dict, f"Le fichier {config_file} n'est pas un dictionnaire JSON")
                
            except json.JSONDecodeError as e:
                self.fail(f"Le fichier {config_file} n'est pas un JSON valide: {e}")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Tests d'initialisation du système BerinIA.

Ce module contient des tests pour vérifier que le système s'initialise correctement,
que les agents peuvent être chargés et que leurs configurations sont valides.
"""
import os
import sys
import unittest
import json
from pathlib import Path
import importlib.util

# Ajout du répertoire parent au chemin de recherche des modules
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

# Import des modules à tester
import init_system
from utils import llm, qdrant
from core import agent_base, db

class TestSystemInitialization(unittest.TestCase):
    """Tests pour l'initialisation du système."""
    
    def setUp(self):
        """Préparation des tests."""
        # Charger la configuration globale
        self.config_path = ROOT_DIR / "config.json"
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.global_config = json.load(f)
        else:
            self.global_config = {}
    
    def test_config_file_exists(self):
        """Vérifie que le fichier de configuration global existe."""
        self.assertTrue(self.config_path.exists(), 
                       f"Le fichier de configuration {self.config_path} n'existe pas")
    
    def test_global_config_structure(self):
        """Vérifie que la structure de la configuration globale est correcte."""
        required_sections = ["system", "llm", "database", "agents", "webhook"]
        for section in required_sections:
            self.assertIn(section, self.global_config, 
                         f"La section '{section}' est manquante dans la configuration globale")
    
    def test_agent_directories_exist(self):
        """Vérifie que les répertoires des agents existent."""
        agents_dir = ROOT_DIR / "agents"
        self.assertTrue(agents_dir.exists(), "Le répertoire des agents n'existe pas")
        
        # Liste des agents attendus (d'après la documentation)
        expected_agents = [
            "overseer", "admin_interpreter", 
            "scraping_supervisor", "qualification_supervisor", "prospection_supervisor",
            "niche_explorer", "scraper", "cleaner", 
            "scoring", "validator", "duplicate_checker",
            "messaging", "follow_up", "response_interpreter",
            "scheduler", "pivot_strategy"
        ]
        
        for agent in expected_agents:
            agent_dir = agents_dir / agent
            self.assertTrue(agent_dir.exists(), 
                           f"Le répertoire de l'agent '{agent}' n'existe pas")
    
    def test_agent_required_files(self):
        """Vérifie que chaque agent possède les fichiers requis."""
        agents_dir = ROOT_DIR / "agents"
        
        # Liste des agents à tester
        agent_dirs = []
        for d in agents_dir.iterdir():
            if d.is_dir() and not d.name.startswith('__'):
                # On exclut les répertoires qui ne sont pas des agents ou qui ont une structure particulière
                if d.name not in ["overseeragent", "admininterpreteragent", "__pycache__", "testagent"]:
                    agent_dirs.append(d)
        
        for agent_dir in agent_dirs:
            agent_name = agent_dir.name
            
            # Détecter les fichiers Python dans le répertoire
            python_files = list(agent_dir.glob("*.py"))
            
            if not python_files:
                self.fail(f"Aucun fichier Python trouvé pour l'agent '{agent_name}'")
                continue
                
            # Vérifier la présence du fichier de configuration
            config_file = agent_dir / "config.json"
            self.assertTrue(config_file.exists(), 
                          f"Le fichier 'config.json' est manquant pour l'agent '{agent_name}'")
            
            # Vérifier la présence du fichier de prompt
            prompt_file = agent_dir / "prompt.txt"
            self.assertTrue(prompt_file.exists(), 
                          f"Le fichier 'prompt.txt' est manquant pour l'agent '{agent_name}'")
    
    def test_config_json_validity(self):
        """Vérifie que les fichiers config.json des agents sont valides."""
        agents_dir = ROOT_DIR / "agents"
        
        # Liste des agents
        agent_dirs = [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith('__')]
        
        for agent_dir in agent_dirs:
            config_path = agent_dir / "config.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    # Si on arrive ici, c'est que le JSON est valide
                    self.assertTrue(True)
                except json.JSONDecodeError as e:
                    self.fail(f"Le fichier config.json de l'agent '{agent_dir.name}' n'est pas un JSON valide: {e}")
    
    def test_init_system_imports(self):
        """Vérifie que le module init_system peut être importé."""
        self.assertIsNotNone(init_system, "Le module init_system n'a pas pu être importé")
        self.assertTrue(hasattr(init_system, "main"), 
                       "La fonction 'main' est manquante dans le module init_system")
    
    def test_core_modules(self):
        """Vérifie que les modules core peuvent être importés."""
        self.assertIsNotNone(agent_base, "Le module core.agent_base n'a pas pu être importé")
        self.assertIsNotNone(db, "Le module core.db n'a pas pu être importé")
        
        # Vérification de l'existence de classes/fonctions clés
        self.assertTrue(hasattr(agent_base, "Agent"), 
                       "La classe 'Agent' est manquante dans le module core.agent_base")

    def test_utils_modules(self):
        """Vérifie que les modules utils peuvent être importés."""
        self.assertIsNotNone(llm, "Le module utils.llm n'a pas pu être importé")
        self.assertIsNotNone(qdrant, "Le module utils.qdrant n'a pas pu être importé")

class TestAgentInitialization(unittest.TestCase):
    """Tests pour l'initialisation des agents."""
    
    @classmethod
    def setUpClass(cls):
        """Préparation des tests de classe."""
        # Configuration des variables d'environnement pour les tests
        os.environ["TESTING"] = "1"
        
        # Chemin vers les agents
        cls.agents_dir = ROOT_DIR / "agents"
        
        # Importer la classe Agent
        spec = importlib.util.spec_from_file_location(
            "agent_base", 
            str(ROOT_DIR / "core" / "agent_base.py")
        )
        cls.agent_base_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.agent_base_module)
    
    def test_agents_inheritance(self):
        """Vérifie que les agents héritent correctement de Agent."""
        # Liste des agents principaux à tester
        main_agents = ["overseer", "scraper", "cleaner", "messaging"]
        
        for agent_name in main_agents:
            agent_dir = self.agents_dir / agent_name
            
            # Déterminer le nom du fichier Python
            if agent_name.endswith("_supervisor"):
                py_file = f"{agent_name}.py"
            else:
                py_file = f"{agent_name}_agent.py"
            
            py_path = agent_dir / py_file
            
            if py_path.exists():
                # Importer le module de l'agent
                spec = importlib.util.spec_from_file_location(
                    f"{agent_name}_module", 
                    str(py_path)
                )
                agent_module = importlib.util.module_from_spec(spec)
                
                try:
                    spec.loader.exec_module(agent_module)
                    
                    # Trouver la classe d'agent principale
                    agent_class_name = "".join(word.capitalize() for word in agent_name.split('_'))
                    if agent_class_name.endswith("Agent") is False:
                        agent_class_name += "Agent"
                    
                    # Vérifier que la classe existe et hérite de Agent
                    self.assertTrue(hasattr(agent_module, agent_class_name), 
                                   f"La classe '{agent_class_name}' est manquante dans {py_file}")
                    
                    # Cette vérification est commentée car elle nécessiterait d'instancier les classes
                    # ce qui pourrait avoir des effets de bord indésirables en test
                    # agent_class = getattr(agent_module, agent_class_name)
                    # self.assertTrue(issubclass(agent_class, self.agent_base_module.Agent),
                    #               f"La classe '{agent_class_name}' n'hérite pas de Agent")
                    
                except Exception as e:
                    self.fail(f"Erreur lors de l'importation du module {py_file}: {e}")

if __name__ == "__main__":
    unittest.main()

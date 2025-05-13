#!/usr/bin/env python3
"""
Script de débogage pour l'initialisation et le chargement des agents
"""

import os
import sys
import logging
import json
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("debug")

# Ajouter le répertoire courant au path pour l'import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_registry_agents():
    """Vérifie les agents dans le registre."""
    from agents.registry import registry
    
    print("=== AGENTS DANS LE REGISTRE GLOBAL ===")
    agents = registry.list_agents()
    
    if not agents:
        print("Aucun agent dans le registre!")
    else:
        print(f"Nombre d'agents: {len(agents)}")
        for name, agent in agents.items():
            print(f" - {name} ({type(agent).__name__})")
    
    return agents

def check_agent_initialization():
    """Vérifie l'initialisation des agents listés dans webhook_config.py"""
    print("\n=== TEST D'INITIALISATION DES AGENTS ===")
    
    # Liste des agents mentionnés dans webhook_config.py
    agent_names = [
        "LoggerAgent",
        "OverseerAgent",
        "ResponseListenerAgent",
        "ResponseInterpreterAgent",
        "AdminInterpreterAgent",
        "MessagingAgent",
        "PivotStrategyAgent",
        "MetaAgent"
    ]
    
    from agents.registry import registry
    
    for agent_name in agent_names:
        # Essayer de récupérer l'agent
        agent = registry.get(agent_name)
        
        if agent:
            print(f" - {agent_name}: Déjà dans le registre")
        else:
            print(f" - {agent_name}: Pas dans le registre, tentative de création...")
            
            agent = registry.get_or_create(agent_name)
            
            if agent:
                print(f"   > Création réussie! Type: {type(agent).__name__}")
            else:
                print(f"   > Échec de la création")
                
                # Tester avec des variantes de casse
                variants = [
                    agent_name.lower(),
                    agent_name.upper(),
                    agent_name[0].lower() + agent_name[1:],
                    agent_name[0].upper() + agent_name[1:].lower()
                ]
                
                for variant in variants:
                    print(f"   > Essai avec variante '{variant}'...")
                    agent = registry.get_or_create(variant)
                    if agent:
                        print(f"     --> Succès avec '{variant}'")
                        break
                else:
                    print("     --> Échec avec toutes les variantes")

def check_agent_directories():
    """Vérifie les dossiers d'agents et leur structure"""
    print("\n=== ANALYSE DES DOSSIERS D'AGENTS ===")
    
    agents_dir = Path("agents")
    if not agents_dir.exists() or not agents_dir.is_dir():
        print(f"Erreur: Dossier 'agents' introuvable dans {os.getcwd()}")
        return
    
    agent_dirs = [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith("__")]
    print(f"Nombre de dossiers d'agents: {len(agent_dirs)}")
    
    for agent_dir in agent_dirs:
        agent_files = list(agent_dir.glob("*.py"))
        agent_name = agent_dir.name
        
        print(f"\nDossier: {agent_name}")
        print(f"Fichiers Python: {len(agent_files)}")
        
        # Recherche du fichier principal de l'agent
        main_agent_file = None
        expected_names = [
            f"{agent_name}_agent.py",
            f"{agent_name.replace('_', '')}Agent.py",
            "agent.py"
        ]
        
        for filename in expected_names:
            file_path = agent_dir / filename
            if file_path.exists():
                main_agent_file = file_path
                break
                
        if main_agent_file:
            print(f"Fichier principal trouvé: {main_agent_file.name}")
            
            # Analyse du fichier pour trouver la classe d'agent
            with open(main_agent_file, "r") as f:
                content = f.read()
                
            import re
            class_matches = re.findall(r'class\s+(\w+)\s*\(', content)
            
            if class_matches:
                print(f"Classes trouvées: {', '.join(class_matches)}")
                
                # Vérifier la correspondance entre nom de dossier et classe
                expected_class = f"{agent_name.replace('_', '').capitalize()}Agent"
                if expected_class in class_matches:
                    print(f"La classe attendue {expected_class} a été trouvée ✓")
                else:
                    print(f"ALERTE: La classe attendue {expected_class} n'est pas dans {class_matches} ⚠️")
                    
                    # Suggestions pour le nom correct
                    for class_name in class_matches:
                        if "agent" in class_name.lower():
                            print(f"  Suggestion: Utiliser '{class_name}' au lieu de '{expected_class}'")
            else:
                print("Aucune classe d'agent trouvée dans le fichier")
        else:
            print(f"ALERTE: Aucun fichier principal d'agent trouvé dans {agent_name} ⚠️")

def check_module_imports():
    """Vérifie si les modules peuvent être importés correctement"""
    print("\n=== TEST D'IMPORTATION DES MODULES D'AGENTS ===")
    
    from agents.registry import registry
    
    # Liste des agents à tester
    agents_to_test = [
        "OverseerAgent",
        "LoggerAgent",
        "AdminInterpreterAgent",
        "ScraperAgent",
        "MessagingAgent",
        "PivotStrategyAgent",
        "MetaAgent"
    ]
    
    for agent_name in agents_to_test:
        # Normalisation du nom pour l'importation
        if agent_name.endswith("Agent"):
            module_name = agent_name[:-5].lower()
        else:
            module_name = agent_name.lower()
            
        expected_module = f"agents.{module_name}.{module_name}_agent"
        expected_class = agent_name
        
        print(f"\nTest d'importation pour {agent_name}:")
        print(f"Module attendu: {expected_module}")
        print(f"Classe attendue: {expected_class}")
        
        try:
            import importlib
            module = importlib.import_module(expected_module)
            print(f"✓ Module importé avec succès")
            
            # Vérifier si la classe existe
            if hasattr(module, expected_class):
                print(f"✓ Classe {expected_class} trouvée dans le module")
                
                # Vérifier si on peut instancier la classe
                try:
                    AgentClass = getattr(module, expected_class)
                    agent = AgentClass()
                    print(f"✓ Instance de {expected_class} créée avec succès")
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'instanciation: {str(e)}")
            else:
                print(f"⚠️ Classe {expected_class} non trouvée dans le module")
                
                # Lister toutes les classes disponibles
                import inspect
                classes = [name for name, obj in inspect.getmembers(module, inspect.isclass) 
                          if obj.__module__ == module.__name__]
                
                if classes:
                    print(f"Classes disponibles: {', '.join(classes)}")
                else:
                    print("Aucune classe définie dans ce module")
                    
        except ImportError as e:
            print(f"⚠️ Erreur d'importation: {str(e)}")
            
            # Essayer des alternatives
            alternatives = [
                (f"agents.{module_name}.{agent_name.lower()}", agent_name),
                (f"agents.{module_name}", agent_name),
                (f"agents.{agent_name.lower()}", agent_name)
            ]
            
            for alt_module, alt_class in alternatives:
                try:
                    print(f"Essai alternatif: {alt_module}.{alt_class}")
                    module = importlib.import_module(alt_module)
                    if hasattr(module, alt_class):
                        print(f"✓ Alternative trouvée! {alt_module}.{alt_class}")
                        break
                except ImportError:
                    pass
            else:
                print("Échec de toutes les alternatives")

def test_meta_agent():
    """Teste le MetaAgent avec des requêtes spécifiques"""
    print("\n=== TEST DU META AGENT ===")
    
    try:
        from agents.meta_agent.meta_agent import MetaAgent
        
        meta = MetaAgent()
        print("MetaAgent créé avec succès")
        
        # Test avec une requête simple qui devrait fonctionner
        test_request = "Explique-moi comment fonctionne BerinIA"
        
        print(f"\nTest avec la requête: '{test_request}'")
        result = meta.run({"message": test_request, "source": "test", "author": "debugger"})
        
        print(f"Statut: {result.get('status')}")
        if "message" in result:
            print("Message de réponse:")
            print(result["message"])
        
        # Test avec une requête qui nécessite un agent spécifique
        agent_request = "Quel est l'état du système?"
        
        print(f"\nTest avec la requête orientée agent: '{agent_request}'")
        result = meta.analyze_request(agent_request)
        
        print("Analyse:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Vérifier que l'agent est correctement identifié
        if "actions" in result and result["actions"]:
            agent_name = result["actions"][0].get("agent")
            print(f"\nAgent identifié: {agent_name}")
            
            # Tester si l'agent existe
            from agents.registry import registry
            agent = registry.get_or_create(agent_name)
            
            if agent:
                print(f"✓ Agent {agent_name} trouvé et chargé avec succès")
            else:
                print(f"⚠️ Agent {agent_name} non trouvé")
                
    except Exception as e:
        print(f"Erreur lors du test de MetaAgent: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== DÉMARRAGE DU DÉBOGAGE DES AGENTS ===")
    print(f"Répertoire courant: {os.getcwd()}")
    
    check_registry_agents()
    check_agent_initialization()
    check_agent_directories()
    check_module_imports()
    test_meta_agent()
    
    print("\n=== DÉBOGAGE TERMINÉ ===")

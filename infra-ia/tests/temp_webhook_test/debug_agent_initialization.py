#!/usr/bin/env python3
"""
Script de diagnostic pour comprendre pourquoi l'agent ResponseListenerAgent
n'est pas correctement accessible au webhook.
"""
import os
import sys
import json
import logging
import importlib.util
from pathlib import Path

# Ajout du répertoire parent au path pour les imports
sys.path.append("/root/berinia/infra-ia")

# Configuration du logging
log_dir = "/root/berinia/infra-ia/tests/temp_webhook_test"
os.makedirs(log_dir, exist_ok=True)
log_file = f"{log_dir}/agent_init_debug.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("AgentInitDebug")

def check_agent_file_exists(agent_name, format_type):
    """Vérifie si le fichier agent existe dans une structure spécifique"""
    if format_type == "snake_case":
        # Format snake_case: response_listener/response_listener_agent.py
        name_parts = ''.join(['_' + c.lower() if c.isupper() else c.lower() for c in agent_name]).lstrip('_')
        if name_parts.endswith("_agent"):
            name_parts = name_parts[:-6]  # Retirer "_agent" à la fin
        
        agent_dir = f"/root/berinia/infra-ia/agents/{name_parts}"
        agent_file = f"{agent_dir}/{name_parts}_agent.py"
    else:
        # Format camelCase: responselisteneragent/responselisteneragent.py
        name_parts = agent_name.lower()
        if name_parts.endswith("agent"):
            name_parts = name_parts[:-5]  # Retirer "agent" à la fin
        
        agent_dir = f"/root/berinia/infra-ia/agents/{name_parts}agent"
        agent_file = f"{agent_dir}/{name_parts}agent.py"
    
    dir_exists = os.path.isdir(agent_dir)
    file_exists = os.path.isfile(agent_file)
    
    return {
        "format": format_type,
        "dir_path": agent_dir,
        "file_path": agent_file,
        "dir_exists": dir_exists,
        "file_exists": file_exists
    }

def attempt_agent_import(agent_name, module_path):
    """Tente d'importer l'agent depuis le chemin spécifié"""
    try:
        logger.info(f"Tentative d'import depuis {module_path}")
        
        # Vérifier si le fichier existe
        if not os.path.exists(module_path):
            logger.error(f"Le fichier {module_path} n'existe pas")
            return {
                "success": False,
                "error": f"Le fichier n'existe pas: {module_path}"
            }
        
        # Déterminer le nom du module à partir du chemin
        module_name = os.path.splitext(os.path.basename(module_path))[0]
        package_path = os.path.dirname(module_path)
        
        # Tenter l'import
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Vérifier si la classe existe dans le module
        if hasattr(module, agent_name):
            agent_class = getattr(module, agent_name)
            logger.info(f"Classe {agent_name} trouvée dans le module")
            
            # Tenter d'instancier l'agent
            try:
                agent_instance = agent_class()
                logger.info(f"Agent {agent_name} instancié avec succès")
                
                # Vérifier si l'agent a une méthode run
                if hasattr(agent_instance, "run") and callable(getattr(agent_instance, "run")):
                    logger.info(f"L'agent {agent_name} a une méthode run() valide")
                    
                    return {
                        "success": True,
                        "agent": agent_instance,
                        "module": module
                    }
                else:
                    logger.error(f"L'agent {agent_name} n'a pas de méthode run() valide")
                    return {
                        "success": False,
                        "error": f"Pas de méthode run() trouvée pour {agent_name}"
                    }
            
            except Exception as e:
                logger.error(f"Erreur lors de l'instanciation de {agent_name}: {str(e)}")
                return {
                    "success": False,
                    "error": f"Erreur d'instanciation: {str(e)}"
                }
        else:
            logger.error(f"Classe {agent_name} non trouvée dans le module {module_name}")
            
            # Lister toutes les classes dans le module
            all_items = dir(module)
            potential_classes = [item for item in all_items if item[0].isupper()]
            logger.info(f"Classes trouvées dans le module: {potential_classes}")
            
            return {
                "success": False,
                "error": f"Classe {agent_name} non trouvée. Classes disponibles: {potential_classes}"
            }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'import du module: {str(e)}")
        return {
            "success": False,
            "error": f"Erreur d'import: {str(e)}"
        }

def test_agent_initialization():
    """Teste l'initialisation de ResponseListenerAgent"""
    agents_to_test = ["ResponseListenerAgent", "ResponseInterpreterAgent"]
    
    for agent_name in agents_to_test:
        logger.info(f"=== TEST DE L'AGENT {agent_name} ===")
        
        # Vérifier les différentes structures possibles
        snake_check = check_agent_file_exists(agent_name, "snake_case")
        camel_check = check_agent_file_exists(agent_name, "camelCase")
        
        logger.info(f"Structure snake_case: {json.dumps(snake_check, indent=2)}")
        logger.info(f"Structure camelCase: {json.dumps(camel_check, indent=2)}")
        
        # Récupérer le chemin de fichier qui existe
        if snake_check["file_exists"]:
            module_path = snake_check["file_path"]
            format_type = "snake_case"
        elif camel_check["file_exists"]:
            module_path = camel_check["file_path"]
            format_type = "camelCase"
        else:
            logger.error(f"Aucun fichier d'agent trouvé pour {agent_name}")
            continue
        
        logger.info(f"Utilisation du format {format_type}: {module_path}")
        
        # Tenter d'importer et d'instancier l'agent
        result = attempt_agent_import(agent_name, module_path)
        
        if result["success"]:
            logger.info(f"Agent {agent_name} importé et instancié avec succès")
            
            # Tester une action simple
            try:
                agent = result["agent"]
                test_result = agent.run({"action": "test"})
                logger.info(f"Résultat du test: {json.dumps(test_result, default=str, indent=2)}")
            except Exception as e:
                logger.error(f"Erreur lors du test de l'agent: {str(e)}")
        else:
            logger.error(f"Échec de l'import/instanciation de l'agent: {result['error']}")
            
        logger.info("=" * 50)

def analyze_init_system():
    """Analyse comment init_system.py initialise les agents"""
    logger.info("=== ANALYSE DE INIT_SYSTEM.PY ===")
    
    init_system_path = "/root/berinia/infra-ia/init_system.py"
    
    try:
        with open(init_system_path, 'r') as f:
            content = f.read()
            
        # Rechercher les configurations pour ResponseListener et ResponseInterpreter
        import re
        
        # Rechercher la définition des agents
        agent_def_pattern = r'agent_definitions\s*=\s*\[(.*?)\]'
        agent_defs = re.search(agent_def_pattern, content, re.DOTALL)
        
        if agent_defs:
            agent_defs_content = agent_defs.group(1)
            logger.info("Définitions d'agents trouvées dans init_system.py")
            
            # Rechercher spécifiquement ResponseListener et ResponseInterpreter
            response_patterns = [
                r'\{\s*"name":\s*"ResponseListenerAgent".*?class_path.*?\}',
                r'\{\s*"name":\s*"ResponseInterpreterAgent".*?class_path.*?\}'
            ]
            
            for pattern in response_patterns:
                matches = re.findall(pattern, agent_defs_content, re.DOTALL)
                for match in matches:
                    logger.info(f"Configuration d'agent trouvée:\n{match}")
                    
                    # Extraire le class_path
                    class_path_match = re.search(r'"class_path":\s*"([^"]+)"', match)
                    if class_path_match:
                        class_path = class_path_match.group(1)
                        logger.info(f"Chemin de classe: {class_path}")
                        
                        # Vérifier si ce chemin existe
                        parts = class_path.split('.')
                        if len(parts) >= 3:
                            agent_dir = parts[1]  # Ex: "response_listener"
                            agent_file = f"{agent_dir}{'_agent' if '_' in agent_dir else 'agent'}" # Ex: "response_listener_agent"
                            full_path = f"/root/berinia/infra-ia/agents/{agent_dir}/{agent_file}.py"
                            
                            exists = os.path.exists(full_path)
                            logger.info(f"Chemin calculé: {full_path}, Existe: {exists}")
                        
        else:
            logger.error("Aucune définition d'agents trouvée dans init_system.py")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de init_system.py: {str(e)}")
    
    logger.info("=" * 50)

def check_webhook_agent_access():
    """Analyse comment le webhook accède aux agents"""
    logger.info("=== ANALYSE DE RUN_WEBHOOK.PY ===")
    
    webhook_path = "/root/berinia/infra-ia/webhook/run_webhook.py"
    
    try:
        with open(webhook_path, 'r') as f:
            content = f.read()
            
        # Analyser comment les agents sont initialisés
        import re
        
        # Rechercher les lignes qui importent ou initialisent des agents
        agent_init_lines = re.findall(r'agents\s*=.*', content)
        for line in agent_init_lines:
            logger.info(f"Initialisation des agents: {line}")
        
        # Rechercher les accès à l'agent ResponseListenerAgent
        response_listener_lines = re.findall(r'.*ResponseListenerAgent.*', content)
        for i, line in enumerate(response_listener_lines):
            logger.info(f"Accès à ResponseListenerAgent [{i+1}]: {line}")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de run_webhook.py: {str(e)}")
    
    logger.info("=" * 50)

def main():
    """Fonction principale"""
    logger.info("DÉMARRAGE DU DIAGNOSTIC D'INITIALISATION DES AGENTS")
    
    # Analyser comment init_system.py initialise les agents
    analyze_init_system()
    
    # Analyser comment le webhook accède aux agents
    check_webhook_agent_access()
    
    # Tester l'initialisation des agents directement
    test_agent_initialization()
    
    logger.info("DIAGNOSTIC TERMINÉ")
    print(f"\nDiagnostic terminé. Log: {log_file}")

if __name__ == "__main__":
    main()

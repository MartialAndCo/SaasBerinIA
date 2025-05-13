#!/usr/bin/env python3
"""
Module de correction pour le webhook SMS
Ce fichier contient une solution pour réparer le webhook sans modifier les fichiers existants.
"""
import os
import sys
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ajout du répertoire parent au path pour les imports
sys.path.append("/root/berinia/infra-ia")

# Configuration du logging
log_dir = "/root/berinia/infra-ia/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = f"{log_dir}/webhook_fix.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("WebhookFix")

def import_agent_class(agent_name: str, module_path: str):
    """
    Importe dynamiquement une classe d'agent à partir de son module
    
    Args:
        agent_name: Nom de la classe de l'agent
        module_path: Chemin vers le module de l'agent
        
    Returns:
        La classe de l'agent ou None si l'import échoue
    """
    try:
        logger.info(f"Import de {agent_name} depuis {module_path}")
        
        # Construire le chemin complet du module
        full_path = f"/root/berinia/infra-ia/{module_path.replace('.', '/')}.py"
        
        if not os.path.exists(full_path):
            logger.error(f"Module non trouvé: {full_path}")
            return None
            
        # Créer un nom unique pour le module
        module_name = module_path.replace(".", "_")
        
        # Charger le module
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Obtenir la classe de l'agent
        if hasattr(module, agent_name):
            agent_class = getattr(module, agent_name)
            logger.info(f"Classe {agent_name} trouvée dans {module_path}")
            return agent_class
        else:
            logger.error(f"Classe {agent_name} non trouvée dans {module_path}")
            return None
            
    except Exception as e:
        logger.error(f"Erreur lors de l'import de {agent_name}: {str(e)}")
        return None

def create_webhook_agents():
    """
    Crée un dictionnaire d'agents pour le webhook
    
    Returns:
        Un dictionnaire d'instances d'agents
    """
    webhook_agents = {}
    
    # Définir les agents requis pour le webhook
    required_agents = [
        {
            "name": "ResponseListenerAgent",
            "module_path": "agents.response_listener.response_listener_agent"
        },
        {
            "name": "ResponseInterpreterAgent",
            "module_path": "agents.response_interpreter.response_interpreter_agent"
        }
    ]
    
    # Importer et instancier chaque agent
    for agent_def in required_agents:
        agent_name = agent_def["name"]
        module_path = agent_def["module_path"]
        
        # Importer la classe de l'agent
        agent_class = import_agent_class(agent_name, module_path)
        
        if agent_class:
            try:
                # Instancier l'agent
                agent_instance = agent_class()
                webhook_agents[agent_name] = agent_instance
                logger.info(f"Agent {agent_name} créé et ajouté au dictionnaire")
            except Exception as e:
                logger.error(f"Erreur lors de l'instanciation de {agent_name}: {str(e)}")
        else:
            logger.error(f"Impossible de créer l'agent {agent_name}, classe non trouvée")
    
    return webhook_agents

def main():
    """
    Fonction principale
    """
    logger.info("=== DÉMARRAGE DE LA CORRECTION DU WEBHOOK ===")
    
    # Créer les agents pour le webhook
    webhook_agents = create_webhook_agents()
    
    # Vérifier les agents créés
    logger.info(f"Agents créés: {list(webhook_agents.keys())}")
    
    # Création du fichier de configuration pour le webhook
    config_path = "/root/berinia/infra-ia/webhook/webhook_config.py"
    
    with open(config_path, 'w') as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
Configuration des agents pour le webhook
Ce fichier est automatiquement généré par webhook_fix.py
\"\"\"
from agents.response_listener.response_listener_agent import ResponseListenerAgent
from agents.response_interpreter.response_interpreter_agent import ResponseInterpreterAgent

# Création des instances d'agents pour le webhook
webhook_agents = {
    "ResponseListenerAgent": ResponseListenerAgent(),
    "ResponseInterpreterAgent": ResponseInterpreterAgent()
}
""")
    
    logger.info(f"Fichier de configuration généré: {config_path}")
    
    # Instructions de modification du webhook
    patch_instructions = """
Pour utiliser cette correction, modifiez le fichier run_webhook.py:

1. Remplacez:
   ```python
   agents = {}
   for agent_name in agents_list:
       if agent_name in init_agents:
           agents[agent_name] = init_agents[agent_name]
   ```

   Par:
   ```python
   from webhook.webhook_config import webhook_agents as agents
   ```

2. Redémarrez le service webhook:
   ```bash
   sudo systemctl restart berinia-webhook.service
   ```
"""
    
    print("\n=== CORRECTION DU WEBHOOK TERMINÉE ===")
    print(f"Configuration générée dans: {config_path}")
    print(patch_instructions)
    print(f"Log complet: {log_file}")
    
    return True

if __name__ == "__main__":
    main()

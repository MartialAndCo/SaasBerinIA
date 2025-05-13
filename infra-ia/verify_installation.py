#!/usr/bin/env python3
"""
Script de vérification de l'installation du système BerinIA.

Ce script vérifie que tous les prérequis sont installés et que
la configuration est correcte pour exécuter le système BerinIA.
"""
import os
import sys
import json
import logging
import importlib
import argparse
from pathlib import Path
import traceback
import subprocess
import pkg_resources

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("BerinIA-Verify")

# Couleurs pour le terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
ENDC = "\033[0m"
BOLD = "\033[1m"

def print_header(message):
    """Affiche un header dans le terminal."""
    print("\n" + "=" * 80)
    print(f"{BOLD}{BLUE}{message}{ENDC}")
    print("=" * 80 + "\n")

def print_success(message):
    """Affiche un message de succès."""
    print(f"{GREEN}✅ {message}{ENDC}")

def print_warning(message):
    """Affiche un avertissement."""
    print(f"{YELLOW}⚠️  {message}{ENDC}")

def print_error(message):
    """Affiche une erreur."""
    print(f"{RED}❌ {message}{ENDC}")

def print_info(message):
    """Affiche une information."""
    print(f"{BLUE}ℹ️  {message}{ENDC}")

def check_python_version():
    """Vérifie que la version de Python est correcte."""
    print_info("Vérification de la version de Python...")
    
    major, minor, *_ = sys.version_info
    
    if major < 3 or (major == 3 and minor < 8):
        print_error(f"Python 3.8+ est requis, mais vous utilisez Python {major}.{minor}")
        return False
    
    print_success(f"Python {major}.{minor} détecté")
    return True

def check_venv():
    """Vérifie que le script s'exécute dans un environnement virtuel."""
    print_info("Vérification de l'environnement virtuel Python...")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Environnement virtuel Python détecté")
        return True
    
    print_warning("Script exécuté en dehors d'un environnement virtuel Python")
    print_info("Utilisez 'python -m venv .venv && source .venv/bin/activate' avant d'exécuter ce script")
    return False

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées."""
    print_info("Vérification des dépendances...")
    
    required_packages = [
        "openai", 
        "qdrant-client", 
        "python-dotenv", 
        "httpx", 
        "pydantic", 
        "tqdm", 
        "orjson",
        "fastapi",
        "uvicorn",
        "colorama"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            pkg_resources.get_distribution(package)
            print_success(f"Package {package} installé")
        except pkg_resources.DistributionNotFound:
            print_error(f"Package {package} manquant")
            missing_packages.append(package)
    
    if missing_packages:
        print_warning(f"Packages manquants: {', '.join(missing_packages)}")
        print_info(f"Exécutez 'pip install {' '.join(missing_packages)}' pour les installer")
        return False
    
    return True

def check_env_file():
    """Vérifie que le fichier .env existe et contient les variables nécessaires."""
    print_info("Vérification du fichier .env...")
    
    env_path = Path(".env")
    
    if not env_path.exists():
        print_error("Fichier .env non trouvé")
        print_info("Créez un fichier .env avec les variables requises")
        return False
    
    required_vars = [
        "OPENAI_API_KEY"
    ]
    
    optional_vars = [
        "QDRANT_URL",
        "MAILGUN_API_KEY",
        "MAILGUN_DOMAIN",
        "TWILIO_SID",
        "TWILIO_TOKEN",
        "TWILIO_PHONE"
    ]
    
    env_vars = {}
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                try:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                except ValueError:
                    print_warning(f"Ligne invalide dans .env: {line}")
    except Exception as e:
        print_error(f"Erreur lors de la lecture du fichier .env: {e}")
        return False
    
    missing_vars = [var for var in required_vars if var not in env_vars]
    
    if missing_vars:
        print_error(f"Variables d'environnement requises manquantes: {', '.join(missing_vars)}")
        return False
    
    missing_optional = [var for var in optional_vars if var not in env_vars]
    
    if missing_optional:
        print_warning(f"Variables d'environnement optionnelles non définies: {', '.join(missing_optional)}")
    
    print_success("Fichier .env vérifié")
    return True

def check_openai_api_key():
    """Vérifie que la clé API OpenAI est valide."""
    print_info("Vérification de la clé API OpenAI...")
    
    try:
        # Import ici pour éviter les erreurs si le package n'est pas installé
        import openai
        from dotenv import load_dotenv
        
        # Chargement du fichier .env
        load_dotenv()
        
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai.api_key:
            print_error("Clé API OpenAI non trouvée dans les variables d'environnement")
            return False
        
        # Test d'appel à l'API
        try:
            models = openai.models.list()
            print_success("Connexion à l'API OpenAI réussie")
            return True
        except Exception as e:
            print_error(f"Erreur lors de la connexion à l'API OpenAI: {e}")
            return False
        
    except ImportError:
        print_error("Module OpenAI non trouvé. Installez-le avec 'pip install openai'")
        return False

def check_project_structure():
    """Vérifie que la structure du projet est correcte."""
    print_info("Vérification de la structure du projet...")
    
    required_dirs = [
        "agents",
        "core",
        "utils",
        "webhook"
    ]
    
    required_files = [
        "init_system.py",
        "interact.py",
        "webhook/run_webhook.py",
        "core/agent_base.py",
        "utils/llm.py"
    ]
    
    missing_dirs = [dir_name for dir_name in required_dirs if not os.path.isdir(dir_name)]
    missing_files = [file_name for file_name in required_files if not os.path.isfile(file_name)]
    
    if missing_dirs:
        print_error(f"Répertoires manquants: {', '.join(missing_dirs)}")
    
    if missing_files:
        print_error(f"Fichiers manquants: {', '.join(missing_files)}")
    
    if missing_dirs or missing_files:
        return False
    
    # Vérification des agents
    agent_dirs = [
        d for d in os.listdir("agents") 
        if os.path.isdir(os.path.join("agents", d)) and d != "__pycache__"
    ]
    
    if not agent_dirs:
        print_error("Aucun agent trouvé dans le répertoire 'agents'")
        return False
    
    agents_found = 0
    agents_configured = 0
    
    for agent_dir in agent_dirs:
        agent_path = os.path.join("agents", agent_dir)
        
        # Vérification des fichiers clés pour chaque agent
        py_files = [f for f in os.listdir(agent_path) if f.endswith(".py")]
        has_config = os.path.isfile(os.path.join(agent_path, "config.json"))
        has_prompt = os.path.isfile(os.path.join(agent_path, "prompt.txt"))
        
        if py_files:
            agents_found += 1
            
            if has_config and has_prompt:
                agents_configured += 1
            elif not has_config:
                print_warning(f"Agent {agent_dir} sans fichier config.json")
            elif not has_prompt:
                print_warning(f"Agent {agent_dir} sans fichier prompt.txt")
    
    print_info(f"Agents trouvés: {agents_found}")
    print_info(f"Agents complètement configurés (config.json + prompt.txt): {agents_configured}")
    
    if agents_found < 5:
        print_warning("Moins de 5 agents trouvés. Le système pourrait ne pas être complet.")
    
    print_success("Structure du projet vérifiée")
    return True

def check_directory_permissions():
    """Vérifie les permissions des répertoires."""
    print_info("Vérification des permissions des répertoires...")
    
    dirs_to_check = [
        ".",
        "logs",
        "data",
        "db"
    ]
    
    all_ok = True
    
    for dir_name in dirs_to_check:
        # Créer le répertoire s'il n'existe pas
        os.makedirs(dir_name, exist_ok=True)
        
        # Vérifier les permissions d'écriture
        try:
            test_file = os.path.join(dir_name, ".test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.unlink(test_file)
            print_success(f"Permissions d'écriture dans {dir_name} OK")
        except Exception as e:
            print_error(f"Erreur lors de l'écriture dans {dir_name}: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Fonction principale du script de vérification."""
    parser = argparse.ArgumentParser(description="Vérification de l'installation du système BerinIA")
    parser.add_argument("--full", action="store_true", help="Exécuter une vérification complète, y compris l'API OpenAI")
    args = parser.parse_args()
    
    print_header("VÉRIFICATION DE L'INSTALLATION BERINIA")
    
    checks = {
        "Python version": check_python_version(),
        "Virtual environment": check_venv(),
        "Dependencies": check_dependencies(),
        "Environment file": check_env_file(),
        "Project structure": check_project_structure(),
        "Directory permissions": check_directory_permissions()
    }
    
    # Vérification de l'API OpenAI si demandé
    if args.full:
        checks["OpenAI API key"] = check_openai_api_key()
    
    # Affichage du résumé
    print_header("RÉSUMÉ DES VÉRIFICATIONS")
    
    all_ok = True
    
    for check_name, result in checks.items():
        if result:
            print_success(f"{check_name}: OK")
        else:
            print_error(f"{check_name}: ÉCHEC")
            all_ok = False
    
    if all_ok:
        print_header("INSTALLATION VÉRIFIÉE AVEC SUCCÈS")
        print_info("Le système BerinIA est correctement installé et configuré.")
        print_info("Vous pouvez démarrer le système avec les commandes suivantes :")
        print_info("  - Interface de ligne de commande : python interact.py")
        print_info("  - Serveur de webhooks : python webhook/run_webhook.py")
        return 0
    else:
        print_header("PROBLÈMES DÉTECTÉS DANS L'INSTALLATION")
        print_warning("Corrigez les problèmes ci-dessus avant de démarrer le système.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Script de test pour vérifier que tous les agents définis dans agent_definitions.py 
peuvent être correctement chargés avec la convention snake_case.
"""
import os
import sys
import logging
import importlib
import argparse
from typing import Dict, List, Any, Tuple, Set

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/agent_loading_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("AgentLoadingTest")

# Import du registre d'agents et des définitions
from agents.registry import registry
from utils.agent_definitions import AGENT_DEFINITIONS, ALL_AGENT_NAMES
from utils.safe_imports import (
    check_optional_dependencies, 
    get_missing_dependencies,
    print_dependencies_status
)

def test_agent_loading(
    agent_definitions: List[Dict[str, Any]], 
    ignore_optional_deps: bool = False
) -> Tuple[Dict[str, bool], Set[str]]:
    """
    Teste le chargement de chaque agent défini dans agent_definitions.
    
    Args:
        agent_definitions: Liste des définitions d'agents à tester
        ignore_optional_deps: Si True, les erreurs liées à des dépendances optionnelles
                             sont considérées comme des succès avec limitation
                             
    Returns:
        Tuple contenant:
        - Dict[str, bool]: Un dictionnaire indiquant pour chaque agent s'il a pu être chargé
        - Set[str]: Ensemble des agents avec dépendances optionnelles manquantes
    """
    results = {}
    optional_deps_missing = set()
    
    # Liste des messages d'erreur liés aux dépendances optionnelles
    optional_deps_errors = [
        "No module named 'tldextract'",
        "No module named 'twilio'",
        "No module named 'playwright'"
    ]
    
    for agent_def in agent_definitions:
        agent_name = agent_def["name"]
        module_path = agent_def["module_path"]
        class_name = agent_def["class_name"]
        
        logger.info(f"Test de chargement de l'agent: {agent_name}")
        logger.info(f"  - Module: {module_path}")
        logger.info(f"  - Classe: {class_name}")
        
        # Tenter de charger le module
        try:
            # Vérifier si le dossier existe
            module_parts = module_path.split('.')
            base_dir = os.path.join(*module_parts[:-1])
            if not os.path.exists(base_dir):
                logger.error(f"  ❌ Dossier non trouvé: {base_dir}")
                results[agent_name] = False
                continue
                
            # Tenter d'importer le module
            module = importlib.import_module(module_path)
            
            # Vérifier si la classe existe
            if not hasattr(module, class_name):
                logger.error(f"  ❌ Classe non trouvée: {class_name}")
                results[agent_name] = False
                continue
            
            # Tout est OK
            logger.info(f"  ✓ Module et classe trouvés")
            results[agent_name] = True
            
        except Exception as e:
            error_message = str(e)
            
            # Si l'erreur concerne une dépendance optionnelle et qu'on les ignore
            if ignore_optional_deps and any(dep_err in error_message for dep_err in optional_deps_errors):
                logger.warning(f"  ⚠️ Dépendance optionnelle manquante: {error_message}")
                results[agent_name] = True  # Considéré comme un succès limité
                optional_deps_missing.add(agent_name)
            else:
                logger.error(f"  ❌ Erreur lors du chargement: {error_message}")
                results[agent_name] = False
    
    return results, optional_deps_missing

def test_registry_loading(ignore_optional_deps: bool = False) -> Dict[str, Any]:
    """
    Teste le chargement de chaque agent via le registre.
    
    Args:
        ignore_optional_deps: Si True, les erreurs liées à des dépendances optionnelles
                             sont considérées comme des succès avec limitation
    
    Returns:
        Dict[str, Any]: Résultats du test, avec stats et liste des échecs
    """
    logger.info("Test de chargement via le registre...")
    
    # Réinitialiser le registre pour un test propre
    registry.clear()
    registry.initialized = False
    
    # Liste des messages d'erreur liés aux dépendances optionnelles
    optional_deps_errors = [
        "No module named 'tldextract'",
        "No module named 'twilio'", 
        "No module named 'playwright'"
    ]
    
    # Tenter de créer chaque agent
    success_count = 0
    limited_success_count = 0
    failure_count = 0
    failures = []
    limited_successes = []
    
    for agent_name in ALL_AGENT_NAMES:
        try:
            logger.info(f"Création de l'agent: {agent_name}")
            agent = registry.get_or_create(agent_name)
            
            if agent:
                success_count += 1
                logger.info(f"  ✓ Agent créé avec succès")
            else:
                failure_count += 1
                failures.append(agent_name)
                logger.error(f"  ❌ Échec de création de l'agent")
                
        except Exception as e:
            error_message = str(e)
            
            # Si l'erreur concerne une dépendance optionnelle et qu'on les ignore
            if ignore_optional_deps and any(dep_err in error_message for dep_err in optional_deps_errors):
                limited_success_count += 1
                limited_successes.append(agent_name)
                logger.warning(f"  ⚠️ Agent créé avec limitations (dépendance manquante)")
            else:
                failure_count += 1
                failures.append(f"{agent_name}: {error_message}")
                logger.error(f"  ❌ Exception lors de la création: {error_message}")
    
    return {
        "success_count": success_count,
        "limited_success_count": limited_success_count,
        "failure_count": failure_count,
        "failures": failures,
        "limited_successes": limited_successes,
        "total": success_count + limited_success_count + failure_count
    }

def main():
    """
    Fonction principale exécutant les tests de chargement.
    """
    # Parser les arguments
    parser = argparse.ArgumentParser(description="Test de chargement des agents BerinIA")
    parser.add_argument(
        "--ignore-optional-deps", 
        action="store_true", 
        help="Ignorer les erreurs liées aux dépendances optionnelles"
    )
    args = parser.parse_args()
    
    logger.info("=== DÉBUT DES TESTS DE CHARGEMENT ===")
    
    # Vérifier les dépendances optionnelles
    logger.info("Vérification des dépendances optionnelles:")
    print_dependencies_status()
    
    # Test 1: Chargement direct des modules
    logger.info("Test 1: Chargement direct des modules")
    module_results, optional_missing_modules = test_agent_loading(
        AGENT_DEFINITIONS, 
        ignore_optional_deps=args.ignore_optional_deps
    )
    
    # Compter les succès/échecs
    successes = sum(1 for result in module_results.values() if result)
    failures = sum(1 for result in module_results.values() if not result)
    
    logger.info(f"Résultats du test de modules: {successes} succès, {failures} échecs")
    
    # Afficher les agents avec dépendances optionnelles manquantes
    if optional_missing_modules:
        logger.warning(f"Agents avec dépendances optionnelles manquantes: {len(optional_missing_modules)}")
        for agent_name in optional_missing_modules:
            logger.warning(f"  - {agent_name}")
    
    # Afficher les échecs
    if failures > 0:
        logger.error("Modules en échec:")
        for agent_name, result in module_results.items():
            if not result:
                logger.error(f"  - {agent_name}")
    
    # Test 2: Chargement via le registre
    logger.info("Test 2: Chargement via le registre")
    registry_results = test_registry_loading(ignore_optional_deps=args.ignore_optional_deps)
    
    # Afficher les résultats incluant les succès limités
    if args.ignore_optional_deps and registry_results["limited_success_count"] > 0:
        logger.info(
            f"Résultats du test de registre: "
            f"{registry_results['success_count']} succès, "
            f"{registry_results['limited_success_count']} succès avec limitations, "
            f"{registry_results['failure_count']} échecs"
        )
    else:
        logger.info(
            f"Résultats du test de registre: "
            f"{registry_results['success_count']} succès, "
            f"{registry_results['failure_count']} échecs"
        )
    
    # Afficher les échecs
    if registry_results["failure_count"] > 0:
        logger.error("Échecs du registre:")
        for failure in registry_results["failures"]:
            logger.error(f"  - {failure}")
    
    # Résultat global
    total_tests = len(module_results) + registry_results["total"]
    if args.ignore_optional_deps:
        # Inclure les succès limités comme des succès
        total_successes = (
            successes + 
            registry_results["success_count"] + 
            registry_results["limited_success_count"]
        )
    else:
        total_successes = successes + registry_results["success_count"]
        
    success_percentage = (total_successes / total_tests) * 100 if total_tests > 0 else 0
    
    logger.info("=== RÉSULTAT GLOBAL ===")
    logger.info(f"Tests réussis: {total_successes} / {total_tests} ({success_percentage:.1f}%)")
    
    if success_percentage == 100:
        logger.info("✅ Tous les tests ont réussi! Le système est correctement unifié en snake_case.")
    else:
        logger.error("❌ Certains tests ont échoué. Des corrections sont nécessaires.")
    
    return module_results, registry_results

if __name__ == "__main__":
    main()

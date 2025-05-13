#!/usr/bin/env python3
"""
Test d'intégration du NicheClassifierAgent avec l'OverseerAgent
et les autres agents du système BerinIA
"""

import os
import sys
import json
from pathlib import Path
import argparse

# Ajouter le répertoire parent au PATH pour pouvoir importer les modules
parent_dir = str(Path(__file__).parent.parent)
sys.path.append(parent_dir)

# Imports des agents
from agents.overseer.overseer_agent import OverseerAgent
from agents.niche_classifier.niche_classifier_agent import NicheClassifierAgent

def test_classify_niche():
    """
    Teste la classification d'une niche directement via le NicheClassifierAgent
    """
    print("\n=== Test direct de classification de niche ===\n")
    
    agent = NicheClassifierAgent()
    
    # Teste plusieurs niches
    niches_to_test = [
        "Ostéopathe",
        "Plombier",
        "Expert-comptable",
        "Coach sportif",
        "Développeur freelance"
    ]
    
    for niche in niches_to_test:
        print(f"\nClassification de la niche: {niche}")
        
        result = agent.run({
            "action": "classify",
            "niche": niche
        })
        
        print(f"Famille détectée: {result.get('family_name', 'Non classifiée')}")
        print(f"ID de famille: {result.get('family_id', 'inconnu')}")
        print(f"Type de correspondance: {result.get('match_type', 'inconnu')}")
        print(f"Confiance: {result.get('confidence', 0)}")
    
def test_personalized_approach():
    """
    Teste la génération d'approches personnalisées avec analyse visuelle
    """
    print("\n=== Test de génération d'approches personnalisées ===\n")
    
    agent = NicheClassifierAgent()
    
    # Cas de test avec une analyse visuelle fictive
    test_case = {
        "niche": "Ostéopathe",
        "visual_analysis": {
            "visual_score": 75,
            "visual_quality": 8,
            "website_maturity": "advanced",
            "has_popup": True,
            "popup_removed": True,
            "screenshot_path": "/path/to/screenshot.png",
            "visual_analysis_data": {"detected_elements": ["doctolib", "formulaire", "tarifs"]}
        }
    }
    
    print(f"Niche: {test_case['niche']}")
    print("Avec analyse visuelle")
    
    result = agent.run({
        "action": "generate_approach",
        "niche": test_case["niche"],
        "visual_analysis": test_case["visual_analysis"]
    })
    
    print(f"Famille: {result.get('family', 'Non classifiée')}")
    print(f"Conditions détectées: {', '.join(result.get('conditions_detected', ['aucune']))}")
    print(f"Besoins recommandés: {', '.join(result.get('recommended_needs', []))}")
    print(f"Proposition: {result.get('proposal', 'Aucune')}")

def test_overseer_niche_workflow():
    """
    Teste l'intégration avec l'OverseerAgent via des workflows
    """
    print("\n=== Test d'intégration avec l'OverseerAgent ===\n")
    
    # Création de l'OverseerAgent
    overseer = OverseerAgent()
    
    # Vérification que l'agent NicheClassifier est bien enregistré
    system_state = overseer.get_system_state()
    if "NicheClassifierAgent" in system_state["agents_status"]:
        print("NicheClassifierAgent correctement enregistré dans l'OverseerAgent.")
    else:
        print("ERREUR: NicheClassifierAgent non trouvé dans l'OverseerAgent!")
        return
    
    # Test d'exécution directe via l'OverseerAgent
    print("\nExécution directe via l'OverseerAgent:")
    
    result = overseer.execute_agent("NicheClassifierAgent", {
        "action": "classify",
        "niche": "Dentiste"
    })
    
    if result.get("status") == "error":
        print(f"ERREUR: {result.get('message', 'Erreur inconnue')}")
    else:
        print(f"Famille: {result.get('family_name', 'Non classifiée')}")
        print(f"ID: {result.get('family_id', 'inconnu')}")
    
    # Test de workflow
    print("\nSimulation du workflow visual_analysis_with_classification:")
    
    # Dans un vrai test, nous utiliserions VisualAnalyzerAgent,
    # mais pour ce test nous allons simuler sa sortie
    mock_visual_analysis = {
        "visual_score": 65,
        "visual_quality": 6,
        "website_maturity": "intermediate",
        "has_popup": True,
        "popup_removed": True,
        "screenshot_path": "/path/to/screenshot.png",
        "visual_analysis_data": {"detected_elements": ["contact_form", "gallery", "about_us"]}
    }
    
    print("\nPremière étape - Normallement VisualAnalyzerAgent (simulé ici):")
    print(f"Analyse visuelle générée avec un score de {mock_visual_analysis['visual_score']}")
    
    print("\nDeuxième étape - Appel au NicheClassifierAgent:")
    result = overseer.execute_agent("NicheClassifierAgent", {
        "action": "generate_approach",
        "niche": "Photographe freelance",
        "visual_analysis": mock_visual_analysis
    })
    
    if result.get("status") == "error":
        print(f"ERREUR: {result.get('message', 'Erreur inconnue')}")
    else:
        print(f"Famille: {result.get('family', 'Non classifiée')}")
        print(f"Besoins recommandés: {', '.join(result.get('recommended_needs', []))}")
        print(f"Proposition: {result.get('proposal', 'Aucune')}")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Test d'intégration du NicheClassifierAgent")
    parser.add_argument('--all', action='store_true', help="Exécuter tous les tests")
    parser.add_argument('--classify', action='store_true', help="Tester la classification")
    parser.add_argument('--approach', action='store_true', help="Tester la génération d'approches")
    parser.add_argument('--overseer', action='store_true', help="Tester l'intégration OverseerAgent")
    
    args = parser.parse_args()
    
    # Si aucun argument n'est fourni, exécuter tous les tests
    if not (args.all or args.classify or args.approach or args.overseer):
        args.all = True
    
    if args.all or args.classify:
        test_classify_niche()
    
    if args.all or args.approach:
        test_personalized_approach()
    
    if args.all or args.overseer:
        test_overseer_niche_workflow()
    
    print("\nTests terminés.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script de test pour le NicheClassifierAgent
Ce script permet de tester les fonctionnalités de classification et de génération d'approches
"""

import os
import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au PATH pour pouvoir importer les modules
parent_dir = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_dir)

# Importer l'agent
from agents.niche_classifier.niche_classifier_agent import NicheClassifierAgent

def test_classify():
    """Teste la classification des niches"""
    agent = NicheClassifierAgent()
    
    # Liste de niches à tester
    test_niches = [
        # Niches dans le dictionnaire
        "Ostéopathe",
        "Plombier",
        "Expert-comptable",
        "Agent immobilier",
        "Coiffeur",
        
        # Niches proches mais pas exactes
        "Dentiste",
        "Menuisier",
        "Consultant financier",
        "Courtier immobilier",
        "Salon de beauté",
        
        # Niches complètement différentes
        "Développeur web",
        "Fleuriste",
        "École de musique",
        "Garage automobile",
        "Restaurant"
    ]
    
    print("\n=== Test de classification des niches ===\n")
    
    for niche in test_niches:
        result = agent.run({"action": "classify", "niche": niche})
        
        # Afficher le résultat formaté
        print(f"Niche: {niche}")
        print(f"  -> Famille: {result.get('family_name', 'Non classifiée')}")
        print(f"  -> ID: {result.get('family_id', 'inconnu')}")
        print(f"  -> Type de correspondance: {result.get('match_type', 'inconnu')}")
        print(f"  -> Confiance: {result.get('confidence', 0)}")
        
        if "reasoning" in result:
            print(f"  -> Justification: {result['reasoning']}")
        
        print("")

def test_personalized_approach():
    """Teste la génération d'approches personnalisées"""
    agent = NicheClassifierAgent()
    
    # Scénarios de test avec différentes analyses visuelles
    test_scenarios = [
        {
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
        },
        {
            "niche": "Plombier",
            "visual_analysis": {
                "visual_score": 30,
                "visual_quality": 3,
                "website_maturity": "basic",
                "has_popup": False,
                "screenshot_path": "/path/to/screenshot.png",
                "visual_analysis_data": {"detected_elements": ["telephone", "adresse"]}
            }
        },
        {
            "niche": "Expert-comptable",
            "visual_analysis": None  # Pas d'analyse visuelle
        }
    ]
    
    print("\n=== Test de génération d'approches personnalisées ===\n")
    
    for scenario in test_scenarios:
        niche = scenario["niche"]
        visual_analysis = scenario["visual_analysis"]
        
        result = agent.run({
            "action": "generate_approach",
            "niche": niche,
            "visual_analysis": visual_analysis
        })
        
        # Afficher le résultat formaté
        print(f"Niche: {niche}")
        print(f"Analyse visuelle: {'Disponible' if visual_analysis else 'Non disponible'}")
        print(f"  -> Famille: {result.get('family', 'Non classifiée')}")
        print(f"  -> Conditions détectées: {', '.join(result.get('conditions_detected', ['aucune']))}")
        print(f"  -> Besoins recommandés: {', '.join(result.get('recommended_needs', []))}")
        print(f"  -> Proposition: {result.get('proposal', 'Aucune')}")
        
        if "visual_score" in result:
            print(f"  -> Score visuel: {result['visual_score']}")
        
        print("")

if __name__ == "__main__":
    # Exécuter les tests
    test_classify()
    test_personalized_approach()
    
    print("Tests terminés.")

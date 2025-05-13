#!/usr/bin/env python3
"""
Test simplifié d'intégration entre l'OverseerAgent et le NicheClassifierAgent
sans appel à l'API OpenAI
"""

import os
import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au PATH pour pouvoir importer les modules
parent_dir = str(Path(__file__).parent.parent)
sys.path.append(parent_dir)

# Import des agents
from agents.overseer.overseer_agent import OverseerAgent
from tests.test_niche_classifier_basic import MockNicheClassifierAgent

# Créer une fonction pour remplacer _get_agent_instance dans l'OverseerAgent
def mock_get_agent_instance(self, agent_name):
    """
    Version modifiée de _get_agent_instance qui retourne notre MockNicheClassifierAgent
    pour les tests sans API OpenAI
    """
    if agent_name == "NicheClassifierAgent":
        return MockNicheClassifierAgent()
    
    # Version simplifiée qui retourne un agent de base pour les autres types (juste pour les tests)
    from core.agent_base import Agent
    return Agent(agent_name)

def test_overseer_integration():
    """
    Teste l'intégration basique entre l'OverseerAgent et le NicheClassifierAgent
    """
    print("\n=== Test d'intégration OverseerAgent avec NicheClassifierAgent ===\n")
    
    # Créer l'instance de l'OverseerAgent
    overseer = OverseerAgent()
    
    # Remplacer temporairement la méthode _get_agent_instance pour utiliser notre version mock
    original_method = overseer._get_agent_instance
    overseer._get_agent_instance = lambda agent_name: mock_get_agent_instance(overseer, agent_name)
    
    # Vérifier que l'agent NicheClassifierAgent est correctement enregistré
    system_state = overseer.get_system_state()
    if "NicheClassifierAgent" in system_state["agents_status"]:
        print("NicheClassifierAgent est correctement enregistré dans l'OverseerAgent.")
    else:
        print("ERREUR: NicheClassifierAgent n'est pas enregistré dans l'OverseerAgent!")
        return
    
    # Tester l'exécution du NicheClassifierAgent via l'OverseerAgent
    print("\nClassification de niche via l'OverseerAgent:")
    
    # Test avec une niche connue
    try:
        result = overseer.execute_agent("NicheClassifierAgent", {
            "action": "classify",
            "niche": "Ostéopathe"
        })
        
        if isinstance(result, dict) and "family_name" in result:
            print(f"Niche: Ostéopathe")
            print(f"Famille: {result.get('family_name', 'Non classifiée')}")
            print(f"ID: {result.get('family_id', 'inconnu')}")
            print(f"Confiance: {result.get('confidence', 0)}")
            print("Exécution réussie via l'OverseerAgent!")
        else:
            print(f"ERREUR: Résultat inattendu - {result}")
    except Exception as e:
        print(f"ERREUR lors de l'exécution: {e}")
    
    # Restaurer la méthode originale
    overseer._get_agent_instance = original_method
    
    print("\nTest d'intégration terminé.")

def main():
    """Fonction principale"""
    test_overseer_integration()

if __name__ == "__main__":
    main()

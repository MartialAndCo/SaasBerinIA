#!/usr/bin/env python3
"""
Test simplifié du NicheClassifierAgent sans appel à l'API OpenAI
"""

import os
import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au PATH pour pouvoir importer les modules
parent_dir = str(Path(__file__).parent.parent)
sys.path.append(parent_dir)

# Import de la classe NicheClassifierAgent
from agents.niche_classifier.niche_classifier_agent import NicheClassifierAgent

class MockNicheClassifierAgent(NicheClassifierAgent):
    """Version modifiée du NicheClassifierAgent pour tester sans API OpenAI"""
    
    def _classify_with_llm(self, niche: str) -> dict:
        """Version mock qui ne fait pas d'appel API mais retourne un résultat prédéfini"""
        # Mappings personnalisés pour quelques niches spécifiques
        custom_mappings = {
            "coach sportif": {
                "family_id": "retail",
                "family_name": "Commerces physiques",
                "match_type": "semantic",
                "confidence": 0.85,
                "reasoning": "Les coachs sportifs fournissent un service en personne similaire aux métiers du bien-être physique"
            },
            "développeur freelance": {
                "family_id": "b2b_services",
                "family_name": "B2B Services",
                "match_type": "semantic",
                "confidence": 0.9,
                "reasoning": "Les développeurs freelance fournissent des services professionnels aux entreprises"
            },
            "photographe": {
                "family_id": "b2b_services",
                "family_name": "B2B Services",
                "match_type": "semantic",
                "confidence": 0.75,
                "reasoning": "Les photographes freelance peuvent servir à la fois le B2C et le B2B"
            },
            "dentiste": {
                "family_id": "health",
                "family_name": "Métiers de la santé",
                "match_type": "semantic",
                "confidence": 0.95,
                "reasoning": "Les dentistes sont clairement dans le domaine de la santé"
            }
        }
        
        # Recherche dans nos mappings personnalisés
        niche_lower = niche.lower()
        if niche_lower in custom_mappings:
            result = custom_mappings[niche_lower]
        else:
            # Utilise la méthode de secours pour trouver la famille la plus proche
            family_id = self._find_closest_family(niche)
            family_info = next((f for f in self.niche_families["families"] if f["id"] == family_id), None)
            
            result = {
                "family_id": family_id,
                "family_name": family_info["name"],
                "match_type": "fallback",
                "confidence": 0.7,
                "reasoning": "Classification par similarité textuelle"
            }
        
        # Ajoute l'info de la famille
        family_id = result["family_id"]
        family_info = next((f for f in self.niche_families["families"] if f["id"] == family_id), None)
        result["family_info"] = family_info
        
        return result

def test_classify_niche():
    """
    Teste la classification d'une niche
    """
    print("\n=== Test de classification de niche ===\n")
    
    agent = MockNicheClassifierAgent()
    
    # Liste de niches à tester
    niches_to_test = [
        "Ostéopathe",        # Dans notre dictionnaire
        "Plombier",          # Dans notre dictionnaire
        "Expert-comptable",  # Dans notre dictionnaire
        "Coach sportif",     # Pas dans notre dictionnaire, mapping personnalisé
        "Développeur freelance" # Pas dans notre dictionnaire, mapping personnalisé 
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
    Teste la génération d'approche personnalisée
    """
    print("\n=== Test de génération d'approche personnalisée ===\n")
    
    agent = MockNicheClassifierAgent()
    
    # Cas de test
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
    
    if "visual_score" in result:
        print(f"Score visuel: {result['visual_score']}")

def main():
    """Fonction principale"""
    test_classify_niche()
    test_personalized_approach()
    
    print("\nTests terminés.")

if __name__ == "__main__":
    main()

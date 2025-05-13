#!/usr/bin/env python3
"""
Script de test du MetaAgent
"""

import logging
import json
import sys
from pathlib import Path

# Configure le chemin pour l'import
sys.path.append(str(Path(__file__).parent))

# Configure le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import des modules nécessaires
from agents.meta_agent.meta_agent import MetaAgent

def test_meta_agent():
    """
    Teste le MetaAgent avec plusieurs requêtes
    """
    print("=== TEST DU META AGENT ===")
    
    # Création d'une instance du MetaAgent
    meta = MetaAgent()
    
    # Liste des requêtes à tester
    test_queries = [
        "Quel est l'état du système?",
        "Combien de leads avons-nous dans la base de données?",
        "Montre-moi les dernières statistiques",
        "Aide-moi à comprendre comment fonctionne BerinIA"
    ]
    
    # Test de chaque requête
    for query in test_queries:
        print(f"\n\n=== REQUÊTE: {query} ===")
        
        # Création des données d'entrée
        input_data = {
            "message": query,
            "source": "test_script",
            "author": "tester",
            "content": query
        }
        
        # Exécution du MetaAgent
        result = meta.run(input_data)
        
        # Affichage du résultat
        print("STATUT:", result.get("status"))
        
        if "message" in result:
            print("MESSAGE:")
            print(result["message"])
        
        print("\nRÉSULTAT COMPLET:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_meta_agent()

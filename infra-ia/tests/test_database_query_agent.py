#!/usr/bin/env python3
"""
Test du DatabaseQueryAgent.
Ce script permet de tester les fonctionnalités du DatabaseQueryAgent
en lui posant différentes questions et en affichant les réponses obtenues.
"""
import os
import sys
import json
import logging
from datetime import datetime

# Configuration du chemin d'accès aux modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'logs', 'test_database_query.log'))
    ]
)

logger = logging.getLogger("TestDatabaseQueryAgent")

def print_separator():
    """Affiche une ligne de séparation."""
    print("\n" + "=" * 80 + "\n")

def run_query_test(agent, question):
    """
    Exécute un test de requête et affiche les résultats.
    
    Args:
        agent: Instance du DatabaseQueryAgent
        question: Question à poser
    """
    print(f"QUESTION: {question}")
    print("-" * 40)
    
    try:
        # Mesurer le temps d'exécution
        start_time = datetime.now()
        result = agent.run({"question": question})
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Afficher la réponse
        print(f"RÉPONSE: \n{result['message']}")
        
        # Afficher des détails techniques
        print(f"\nDurée d'exécution: {execution_time:.2f} secondes")
        if "sql" in result:
            print(f"Requête SQL: {result['sql']}")
        
        print(f"Type de requête: {result.get('query_type', 'inconnue')}")
        print(f"Statut: {result['status']}")
        
        # Afficher les données brutes pour les requêtes réussies avec peu de résultats
        if result['status'] == "success" and "data" in result:
            if isinstance(result["data"], list) and len(result["data"]) <= 3:
                print("\nDonnées brutes:")
                for item in result["data"]:
                    print(json.dumps(item, indent=2, ensure_ascii=False))
            elif isinstance(result["data"], dict) and len(result["data"]) <= 5:
                print("\nDonnées brutes:")
                print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"ERREUR: {str(e)}")
        logger.error(f"Erreur lors du test pour la question '{question}': {str(e)}", exc_info=True)
    
    print_separator()

def main():
    """Fonction principale."""
    try:
        # Importer l'agent (ici pour éviter d'importer si le script échoue plus tôt)
        from agents.database_query.database_query_agent import DatabaseQueryAgent
        
        # Initialiser l'agent
        logger.info("Initialisation du DatabaseQueryAgent...")
        db_agent = DatabaseQueryAgent()
        
        # Liste de questions à tester
        questions = [
            "Combien de leads avons-nous dans la base?",
            "Montre-moi les 3 leads les plus récents",
            "Combien de prospects ont été contactés?",
            "Avec qui sommes-nous en train de discuter activement?",
            "Quel est notre taux de conversion sur les dernières campagnes?",
            "Quelle est la dernière campagne?",
            "Montre-moi le lead avec ID 1",
            "Cherche des leads dans le secteur immobilier"
        ]
        
        print_separator()
        print(f"DÉBUT DES TESTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Nombre de questions à tester: {len(questions)}")
        print_separator()
        
        # Exécuter les tests pour chaque question
        for question in questions:
            run_query_test(db_agent, question)
        
        # Test d'une requête SQL directe (mode expert)
        print("TEST DE REQUÊTE SQL DIRECTE")
        print("-" * 40)
        
        result = db_agent.run({
            "direct_sql": True,
            "sql": "SELECT COUNT(*) as total_count FROM leads"
        })
        
        print(f"RÉPONSE: \n{result['message']}")
        if "data" in result and result["data"]:
            print(f"Résultat: {result['data']}")
        
        print_separator()
        print("TESTS TERMINÉS")
        
    except Exception as e:
        logger.error(f"Erreur générale: {str(e)}", exc_info=True)
        print(f"Une erreur s'est produite: {str(e)}")

if __name__ == "__main__":
    main()

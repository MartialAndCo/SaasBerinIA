#!/usr/bin/env python3
"""
Script de test pour le ScraperAgent avec l'SDK Apify
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv
from apify_client import ApifyClient

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("BerinIA-Test")

def test_apify_sdk():
    """Teste l'intégration directe avec le SDK Apify"""
    print("\n" + "="*80)
    print("TEST DE L'SDK APIFY")
    print("="*80)
    
    # Charger les variables d'environnement
    load_dotenv()
    apify_api_key = os.getenv("APIFY_API_KEY")
    
    if not apify_api_key:
        print("❌ Erreur: Clé API Apify manquante. Vérifiez votre fichier .env")
        return
    
    print(f"✅ Clé API Apify trouvée: {apify_api_key[:5]}...")
    
    try:
        # Initialiser le client Apify
        print("\n[1] Initialisation du client Apify...")
        client = ApifyClient(apify_api_key)
        
        # Paramètres de recherche
        print("\n[2] Configuration des paramètres de recherche...")
        search_params = {
            "searchStringsArray": ["restaurants"],
            "locationQuery": "Paris, France",
            "maxCrawledPlacesPerSearch": 5,
            "language": "fr",
            "placeMinimumStars": "",
            "website": "allPlaces",
            "searchMatching": "all",
            "skipClosedPlaces": False,
        }
        
        print(f"Paramètres: {json.dumps(search_params, indent=2)}")
        
        # Exécuter l'acteur Google Places Scraper
        print("\n[3] Exécution de l'acteur Google Places Scraper...")
        
        try:
            # Actor ID pour Google Places Scraper
            actor_id = "2Mdma1N6Fd0y3QEjR"
            print(f"Actor ID: {actor_id}")
            
            # Exécuter l'acteur et attendre la fin
            print("Lancement de l'acteur...")
            run = client.actor(actor_id).call(run_input=search_params)
            
            # Vérifier les résultats
            print(f"\n[4] Run ID: {run.get('id')}")
            print(f"Dataset ID: {run.get('defaultDatasetId')}")
            
            # Récupérer les données du dataset
            print("\n[5] Récupération des résultats du dataset...")
            
            items = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(item)
                if len(items) >= 5:  # Limiter à 5 items pour le test
                    break
            
            print(f"Nombre d'items récupérés: {len(items)}")
            
            if items:
                print("\n[6] Premier résultat:")
                print(json.dumps(items[0], indent=2))
            else:
                print("\n❌ Aucun résultat trouvé.")
                
            print("\n✅ Test SDK Apify complété avec succès!")
            
        except Exception as actor_error:
            print(f"\n❌ Erreur lors de l'exécution de l'acteur: {str(actor_error)}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"\n❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()

def test_scraper_agent():
    """Teste le ScraperAgent avec l'SDK Apify intégré"""
    print("\n" + "="*80)
    print("TEST DU SCRAPER AGENT AVEC SDK APIFY")
    print("="*80)
    
    # Importer le ScraperAgent
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from agents.scraper.scraper_agent import ScraperAgent
    
    # Initialisation du ScraperAgent
    print("\n[1] Initialisation du ScraperAgent...")
    scraper = ScraperAgent()
    
    # Vérifier la configuration
    print("\n[2] Configuration du ScraperAgent:")
    print(f"API Keys: {json.dumps({k: '***' if v else 'Non définie' for k, v in scraper.api_keys.items()}, indent=2)}")
    
    # Préparer les données de test
    test_data = {
        "action": "scrape",
        "niche": "restaurants",
        "location": "Paris",
        "limit": 5
    }
    
    # Exécuter le ScraperAgent
    print("\n[3] Exécution du ScraperAgent avec les paramètres:")
    print(json.dumps(test_data, indent=2))
    
    try:
        # Exécuter le test
        result = scraper.run(test_data)
        
        # Afficher le résultat
        print("\n[4] Résultat de l'exécution:")
        
        # Afficher le statut
        print(f"Statut: {result.get('status')}")
        print(f"Nombre de leads: {result.get('count')}")
        print(f"Source: {result.get('source')}")
        
        # Afficher quelques leads d'exemple
        if result.get("status") == "success" and result.get("leads"):
            print("\n[5] Exemple de leads (2 premiers):")
            leads = result.get("leads", [])
            print(json.dumps(leads[:2], indent=2))
        
        print("\n✅ Test ScraperAgent complété!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test du ScraperAgent: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_apify_sdk()
    print("\n\n" + "="*80)
    print("\nPassage au test du ScraperAgent...\n")
    test_scraper_agent()

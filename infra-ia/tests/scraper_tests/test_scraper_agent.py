#!/usr/bin/env python3
"""
Script de test pour le ScraperAgent - Diagnostique les problèmes d'API
"""
import os
import sys
import json
import logging
import httpx
from dotenv import load_dotenv

# Configuration du logging pour voir tous les détails
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Activer le logging HTTPX pour voir tous les détails des requêtes
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)

# Charger les variables d'environnement
load_dotenv()

# Importer le ScraperAgent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.scraper.scraper_agent import ScraperAgent

def test_scraper_agent():
    """Teste le ScraperAgent avec des paramètres simples"""
    print("\n" + "="*80)
    print("TEST DU SCRAPER AGENT")
    print("="*80)
    
    # Afficher la version d'HTTPX
    print(f"Version HTTPX: {httpx.__version__}")
    
    # Initialiser le ScraperAgent
    print("\n[1] Initialisation du ScraperAgent...")
    scraper = ScraperAgent()
    
    # Vérifier la configuration
    print("\n[2] Configuration du ScraperAgent:")
    print(f"API Keys: {json.dumps({k: '***' if v else 'Non définie' for k, v in scraper.api_keys.items()}, indent=2)}")
    print(f"Use Mock Data: {scraper.config.get('use_mock_data', False)}")
    
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
    
    # Mode détaillé: inspections des appels API
    print("\n[4] Détails de l'appel API (APIFY):")
    try:
        # Extraire et afficher les détails de l'appel Apify avant de l'exécuter
        api_key = scraper.api_keys["apify"]
        api_url = f"https://api.apify.com/v2/acts/apify/google-places-scraper/runs"
        
        payload = {
            "query": test_data["niche"],
            "maxItems": test_data["limit"],
            "country": "FR",
            "location": test_data.get("location", "")
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key[:5]}..." if api_key else "Non défini"
        }
        
        print(f"URL: {api_url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Détails du code de la méthode scrape_from_apify
        print("\n[5] Détail de l'exécution pour scrape_from_apify:")
        
        # Exécuter le test
        result = scraper.run(test_data)
        
        # Afficher le résultat
        print("\n[6] Résultat de l'exécution:")
        print(json.dumps(result, indent=2))
        
        # Afficher quelques leads d'exemple
        if result.get("status") == "success" and result.get("leads"):
            print("\n[7] Exemple de leads (2 premiers):")
            leads = result.get("leads", [])
            print(json.dumps(leads[:2], indent=2))
        
    except Exception as e:
        print(f"\nERREUR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper_agent()

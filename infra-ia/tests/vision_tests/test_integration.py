#!/usr/bin/env python3
"""
Test d'intégration pour l'agent d'analyse visuelle

Ce test démontre comment l'agent d'analyse visuelle peut être intégré 
au système de gestion des leads BerinIA.
"""
import sys
import os
import asyncio
import json
from pathlib import Path
import logging

# Ajout du chemin parent pour les imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import de la classe d'intégration et de l'analyse visuelle
from agents.visual_analyzer.integration import VisualIntegration
from agents.visual_analyzer import VisualAnalyzer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BerinIA-Integration-Test")

async def test_lead_enrichment():
    """
    Test l'enrichissement des données d'un lead avec l'analyse visuelle de son site web
    """
    print("\n===== TEST D'ENRICHISSEMENT DE LEAD =====")
    
    # Créer des données de test pour un lead
    test_lead = {
        "lead_id": "vision_test_001",
        "company": "Journal Le Monde",
        "company_website": "https://www.lemonde.fr",
        "email": "contact@lemonde.fr",
        "first_name": "Test",
        "last_name": "User",
        "status": "new"
    }
    
    # Créer une instance de l'intégration
    integration = VisualIntegration()
    
    print(f"Analyse du site web pour: {test_lead['company']}")
    print(f"URL: {test_lead['company_website']}")
    
    # Enrichir les données du lead
    start_time = asyncio.get_event_loop().time()
    enriched_lead = await integration.analyze_lead_website(test_lead)
    elapsed = asyncio.get_event_loop().time() - start_time
    
    print(f"\nAnalyse terminée en {elapsed:.2f} secondes")
    
    # Afficher les résultats d'enrichissement
    if "web_metadata" in enriched_lead:
        metadata = enriched_lead["web_metadata"]
        
        print("\n----- MÉTA-DONNÉES WEB -----")
        print(f"Site accessible: {metadata.get('reachable', False)}")
        print(f"Type de site: {metadata.get('site_type', 'Inconnu')}")
        print(f"Score de maturité: {metadata.get('maturity_score', 0)}/100")
        print(f"Tag de maturité: {metadata.get('maturity_tag', 'Inconnu')}")
        print(f"Qualité visuelle: {metadata.get('visual_quality', 0)}/10")
        print(f"Professionnalisme: {metadata.get('professionalism', 0)}/10")
        
        print("\n----- FORCES ET FAIBLESSES -----")
        strengths = metadata.get("strengths", [])
        weaknesses = metadata.get("weaknesses", [])
        
        if strengths:
            print("Forces:")
            for s in strengths[:3]:  # Afficher seulement les 3 premières
                print(f"- {s}")
        
        if weaknesses:
            print("\nFaiblesses:")
            for w in weaknesses[:3]:  # Afficher seulement les 3 premières
                print(f"- {w}")
            
        print("\n----- TECHNOLOGIE -----")
        technologies = metadata.get("technologies", [])
        if technologies:
            print("Technologies détectées:")
            for tech in technologies:
                print(f"- {tech}")
                
        # Afficher le statut de popup
        print("\n----- POPUPS -----")
        print(f"Popup détecté: {metadata.get('has_popup', False)}")
        print(f"Popup supprimé: {metadata.get('popup_removed', False)}")
        
        # Afficher les captures d'écran
        print("\n----- CAPTURES D'ÉCRAN -----")
        screenshots = metadata.get("screenshots", {})
        for name, path in screenshots.items():
            print(f"{name}: {path}")
    else:
        print("\nAucune métadonnée web disponible")
    
    # Sauvegarder les résultats complets dans un fichier JSON
    output_file = Path(__file__).parent / "integration_results.json"
    with open(output_file, "w") as f:
        json.dump(enriched_lead, f, indent=2)
    
    print(f"\nRésultats complets sauvegardés dans: {output_file}")
    print("=========================================\n")
    
    return enriched_lead

async def test_batch_processing():
    """
    Test le traitement par lot de plusieurs leads
    """
    print("\n===== TEST DE TRAITEMENT PAR LOT =====")
    
    # Créer plusieurs leads de test
    test_leads = [
        {
            "lead_id": "vision_test_002",
            "company": "New York Times",
            "company_website": "https://www.nytimes.com",
            "status": "new"
        },
        {
            "lead_id": "vision_test_003",
            "company": "BBC",
            "company_website": "https://www.bbc.com",
            "status": "new"
        }
    ]
    
    print(f"Traitement par lot de {len(test_leads)} leads")
    
    # Créer une instance de l'intégration
    integration = VisualIntegration()
    
    # Traitement par lot
    start_time = asyncio.get_event_loop().time()
    enriched_leads = await integration.batch_analyze_leads(test_leads)
    elapsed = asyncio.get_event_loop().time() - start_time
    
    print(f"\nTraitement terminé en {elapsed:.2f} secondes")
    
    # Afficher les résultats pour chaque lead
    for lead in enriched_leads:
        print(f"\n----- {lead['company']} -----")
        
        if "web_metadata" in lead:
            metadata = lead["web_metadata"]
            print(f"Site accessible: {metadata.get('reachable', False)}")
            print(f"Type de site: {metadata.get('site_type', 'Inconnu')}")
            print(f"Score de maturité: {metadata.get('maturity_score', 0)}/100")
            print(f"Popup géré: {metadata.get('popup_removed', False)}")
        else:
            print("Aucune métadonnée web disponible")
    
    # Sauvegarder les résultats complets dans un fichier JSON
    output_file = Path(__file__).parent / "batch_results.json"
    with open(output_file, "w") as f:
        json.dump(enriched_leads, f, indent=2)
    
    print(f"\nRésultats complets sauvegardés dans: {output_file}")
    print("==========================================\n")
    
    return enriched_leads

async def main():
    """Fonction principale pour exécuter les tests d'intégration"""
    try:
        # Test d'enrichissement d'un lead
        await test_lead_enrichment()
        
        # Test de traitement par lot
        # Commenter cette ligne pour un test plus court
        # await test_batch_processing()
        
        print("\nTous les tests d'intégration sont terminés avec succès!")
    except Exception as e:
        logger.error(f"Erreur lors des tests d'intégration: {str(e)}")
        print(f"\nErreur: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

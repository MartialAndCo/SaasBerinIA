#!/usr/bin/env python3
"""
Test du ScreenshotAnalyzer sur des sites spécifiques
"""
import sys
import json
import logging
import asyncio
import os
from pathlib import Path

# Ajout du répertoire parent au chemin de recherche
sys.path.append(str(Path(__file__).parent))

# Import de l'agent à tester
from agents.web_checker.screenshot_analyzer import ScreenshotAnalyzer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_site(url, site_name):
    """Test l'analyse de screenshot sur un site donné"""
    print(f"\n{'='*80}")
    print(f"ANALYSE VISUELLE DE: {url} ({site_name})")
    print(f"{'='*80}")
    
    # Créer le répertoire de screenshots s'il n'existe pas
    screenshots_dir = Path(__file__).parent / "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Créer l'analyseur
    analyzer = ScreenshotAnalyzer(str(screenshots_dir))
    
    # Générer un ID de lead pour le test
    lead_id = f"test-{site_name.lower().replace(' ', '-')}"
    
    # Capturer et analyser le site
    try:
        print(f"Capture du screenshot de {url}...")
        results = await analyzer.capture_and_analyze(url, lead_id)
        
        if results.get("error"):
            print(f"ERREUR: {results['error']}")
            return
        
        # Afficher les résultats
        print(f"\nScreenshot sauvegardé: {results['screenshot_path']}")
        
        # Afficher l'analyse UI
        ui_components = results.get("ui_components", {})
        print("\nCOMPOSANTS UI DÉTECTÉS:")
        for component, present in ui_components.items():
            if present:
                print(f"- {component}")
        
        # Afficher les couleurs dominantes
        dominant_colors = results.get("dominant_colors", [])
        print("\nCOULEURS DOMINANTES:")
        for color in dominant_colors:
            print(f"- {color['color']} ({color['proportion']*100:.1f}%)")
        
        # Afficher l'harmonie des couleurs
        color_harmony = results.get("color_harmony", "unknown")
        print(f"\nHARMONIE DES COULEURS: {color_harmony}")
        
        # Afficher l'espace blanc
        whitespace = results.get("white_space_ratio", 0)
        print(f"\nRATIO D'ESPACE BLANC: {whitespace*100:.1f}%")
        
        # Afficher la complexité visuelle
        complexity = results.get("visual_complexity", 0)
        print(f"\nCOMPLEXITÉ VISUELLE: {complexity:.1f}/100")
        
        # Afficher le score visuel
        visual_score = results.get("visual_score", 0)
        print(f"\nSCORE VISUEL GLOBAL: {visual_score}/100")
        
        # Afficher le chemin vers l'image
        print(f"\nVous pouvez voir le screenshot dans: {results['screenshot_path']}")
        
    except Exception as e:
        print(f"Erreur lors de l'analyse: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Fonction principale"""
    # Sites à tester
    sites = [
        ("https://app.berinia.com", "Berinia App"),
        ("https://sejouris.com", "Sejouris"),
        ("https://www.visuara.fr", "Visuara")
    ]
    
    # Tester chaque site
    for url, name in sites:
        await test_site(url, name)

if __name__ == "__main__":
    # Exécuter le test asynchrone
    asyncio.run(main())

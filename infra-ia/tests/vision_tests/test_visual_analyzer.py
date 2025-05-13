#!/usr/bin/env python3
"""
Test principal pour le Visual Analyzer Agent

Ce script démontre l'utilisation complète de l'agent d'analyse visuelle
qui combine:
1. Détection et gestion de popups
2. Analyse visuelle des sites web
3. Reconstruction des éléments visuels

Usage:
    python3 test_visual_analyzer.py [url1] [url2] ...
"""
import sys
import os
import asyncio
from pathlib import Path

# Ajout du chemin parent pour les imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import de l'agent d'analyse visuelle
from agents.visual_analyzer import VisualAnalyzer

async def test_sites(urls=None):
    """
    Test l'analyseur visuel sur une liste d'URLs
    
    Args:
        urls: Liste d'URLs à analyser. Si None, utilise des URLs par défaut.
    """
    if not urls:
        # URLs de test par défaut
        urls = [
            "https://www.lemonde.fr",
            "https://www.nytimes.com", 
            "https://www.bbc.com",
            "https://www.amazon.fr"
        ]
    
    analyzer = VisualAnalyzer()
    
    for i, url in enumerate(urls):
        print(f"\n[Test {i+1}/{len(urls)}] Analyse de: {url}")
        await analyzer.analyze_website(url)
        
        if i < len(urls) - 1:
            print("\nAppuyez sur Entrée pour continuer vers le site suivant...")
            input()

def main():
    """Fonction principale pour exécuter les tests"""
    # Utiliser les arguments de ligne de commande comme URLs, ou utiliser les par défaut
    test_urls = sys.argv[1:] if len(sys.argv) > 1 else None
    
    print("\n===== TEST DE L'ANALYSEUR VISUEL =====")
    print("Cet outil analyse visuellement les sites web en")
    print("détectant et fermant les popups, puis en analysant")
    print("la structure visuelle et le contenu du site.")
    print("========================================\n")
    
    try:
        asyncio.run(test_sites(test_urls))
        print("\nTests terminés avec succès!")
    except KeyboardInterrupt:
        print("\nTests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\nErreur lors des tests: {e}")

if __name__ == "__main__":
    main()

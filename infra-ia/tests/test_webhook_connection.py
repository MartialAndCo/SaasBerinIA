#!/usr/bin/env python3
"""
Script simple pour tester la connexion au serveur webhook
"""
import sys
import requests
import time

print("=== TEST DE CONNEXION AU WEBHOOK BERINIA ===")

# URL du webhook
base_url = "http://127.0.0.1:8001"
urls_to_test = [
    "",  # Route racine
    "/health"  # Route de santé
]

for url_path in urls_to_test:
    full_url = base_url + url_path
    print(f"\nTest de l'URL: {full_url}")
    
    try:
        # Envoi d'une requête GET
        start_time = time.time()
        response = requests.get(full_url, timeout=5)
        elapsed = time.time() - start_time
        
        # Affichage des informations de réponse
        print(f"  Statut: {response.status_code}")
        print(f"  Temps de réponse: {elapsed:.2f}s")
        print(f"  Contenu: {response.text[:200]}" + ("..." if len(response.text) > 200 else ""))
    
    except Exception as e:
        print(f"  ERREUR: {str(e)}")

print("\n=== FIN DU TEST DE CONNEXION ===")

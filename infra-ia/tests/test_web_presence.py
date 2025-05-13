#!/usr/bin/env python3
"""
Test de l'agent WebPresenceCheckerAgent
"""
import os
import sys
import json
import logging
from pathlib import Path

# Ajout du répertoire parent au chemin de recherche
sys.path.append(str(Path(__file__).parent.parent))

# Import de l'agent à tester
from agents.web_checker.web_presence_checker_agent import WebPresenceCheckerAgent

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_web_presence_checker():
    """Teste les fonctionnalités de base de l'agent WebPresenceCheckerAgent"""
    print("\n" + "="*80)
    print("TEST DE L'AGENT WebPresenceCheckerAgent")
    print("="*80)
    
    # Création de l'agent
    agent = WebPresenceCheckerAgent()
    
    # Définition des leads de test avec différentes configurations
    test_leads = [
        {
            "lead_id": "test-lead-1",
            "company": "Apple",
            "company_website": "apple.com",
            "email": "contact@apple.com"
        },
        {
            "lead_id": "test-lead-2",
            "company": "Google",
            "company_website": "google.fr",
            "email": "contact@google.com"
        },
        {
            "lead_id": "test-lead-3",
            "company": "Restaurant Le Bistrot",
            "company_website": "",
            "email": "contact@bistrot-paris.fr"
        },
        {
            "lead_id": "test-lead-4",
            "company": "Cabinet Dupont Avocats",
            "company_website": "",
            "email": "contact@gmail.com"  # Email personnel, pas de domaine d'entreprise
        },
    ]
    
    # Tester l'agent avec plusieurs leads
    print("\n1. Test de traitement de plusieurs leads")
    result = agent.run({
        "action": "check_web_presence",
        "leads": test_leads
    })
    
    # Afficher les statistiques
    print(f"\nLeads traités: {result.get('leads_processed', 0)}")
    print(f"Statistiques: {json.dumps(result.get('stats', {}), indent=2)}")
    
    # Afficher les résultats détaillés pour un lead
    if result.get("leads") and len(result.get("leads", [])) > 0:
        first_lead_result = result.get("leads")[0]
        print(f"\n2. Détail du premier lead analysé ({first_lead_result.get('company', 'inconnu')})")
        
        web_metadata = first_lead_result.get("web_metadata", {})
        print(f"URL: {web_metadata.get('url', 'Non trouvée')}")
        print(f"Accessible: {web_metadata.get('reachable', False)}")
        print(f"Score de maturité: {web_metadata.get('maturity_score', 0)}")
        print(f"Catégorie: {web_metadata.get('maturity_tag', 'inconnu')}")
        print(f"Tag commercial: {web_metadata.get('web_status_tag', 'inconnu')}")
        
        # Afficher la stack technologique si disponible
        if web_metadata.get("tech_stack"):
            print(f"Technologies détectées: {', '.join(web_metadata.get('tech_stack', []))}")
        
        # Vérifier si le site a un formulaire
        print(f"Présence de formulaire: {web_metadata.get('has_form', False)}")
        
        # Vérifier le CMS
        print(f"CMS détecté: {web_metadata.get('cms', 'inconnu')}")
    
    # Tester l'agent avec un seul lead
    print("\n3. Test de traitement d'un seul lead")
    single_lead = {
        "lead_id": "test-lead-single",
        "company": "Microsoft",
        "company_website": "microsoft.com",
        "email": "info@microsoft.com"
    }
    
    result_single = agent.run({
        "action": "check_web_presence",
        "lead": single_lead
    })
    
    print(f"Lead traité: {result_single.get('leads_processed', 0)}")
    
    # Tester la récupération des statistiques
    print("\n4. Test de récupération des statistiques")
    stats_result = agent.run({
        "action": "get_stats"
    })
    
    print(f"Statistiques: {json.dumps(stats_result.get('stats', {}), indent=2)}")
    
    print("\nTest terminé!")

if __name__ == "__main__":
    test_web_presence_checker()

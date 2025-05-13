#!/usr/bin/env python3
"""
Test du WebPresenceCheckerAgent sur des sites spécifiques
"""
import sys
import json
import logging
from pathlib import Path

# Ajout du répertoire parent au chemin de recherche
sys.path.append(str(Path(__file__).parent))

# Import de l'agent à tester
from agents.web_checker.web_presence_checker_agent import WebPresenceCheckerAgent

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def analyze_site(url, company_name):
    """Analyse un site web spécifique et affiche les résultats"""
    print("\n" + "="*80)
    print(f"ANALYSE DU SITE: {url} ({company_name})")
    print("="*80)
    
    # Création de l'agent
    agent = WebPresenceCheckerAgent()
    
    # Création d'un lead factice avec l'URL à tester
    test_lead = {
        "lead_id": f"test-{url.replace('.', '-')}",
        "company": company_name,
        "company_website": url,
        "email": f"contact@{url}"
    }
    
    # Exécution de l'analyse
    result = agent.run({
        "action": "check_web_presence",
        "lead": test_lead
    })
    
    # Récupération des données d'analyse
    if result.get("leads") and len(result.get("leads", [])) > 0:
        lead_result = result.get("leads")[0]
        web_metadata = lead_result.get("web_metadata", {})
        
        # Affichage des informations principales
        print(f"\nURL: {web_metadata.get('url', 'Non trouvée')}")
        print(f"Accessible: {web_metadata.get('reachable', False)}")
        print(f"Score de maturité: {web_metadata.get('maturity_score', 0)}/100")
        print(f"Catégorie: {web_metadata.get('maturity_tag', 'inconnu')}")
        print(f"Tag commercial: {web_metadata.get('web_status_tag', 'inconnu')}")
        
        # Affichage des détails techniques
        print("\nDÉTAILS TECHNIQUES:")
        print(f"- HTTPS: {'Oui' if web_metadata.get('has_https', False) else 'Non'}")
        print(f"- Mobile-friendly: {'Oui' if web_metadata.get('mobile_friendly', False) else 'Non'}")
        print(f"- Formulaires: {'Oui' if web_metadata.get('has_form', False) else 'Non'}")
        print(f"- Liens sociaux: {'Oui' if web_metadata.get('has_social_links', False) else 'Non'}")
        print(f"- Notice cookies: {'Oui' if web_metadata.get('has_cookie_notice', False) else 'Non'}")
        
        # Affichage des technologies
        print(f"\nCMS détecté: {web_metadata.get('cms', 'inconnu')}")
        
        if web_metadata.get("tech_stack"):
            print(f"Technologies: {', '.join(web_metadata.get('tech_stack', []))}")
        else:
            print("Technologies: Aucune détectée")
        
        # Affichage des métriques de performance
        print(f"\nPERFORMANCE:")
        print(f"- Temps de réponse: {web_metadata.get('response_time_ms', 0)} ms")
        print(f"- Taille de page: {web_metadata.get('page_size_kb', 0)} Ko")
        print(f"- Nombre d'images: {web_metadata.get('num_images', 0)}")
        print(f"- Nombre de liens: {web_metadata.get('num_links', 0)}")
        
        # Affichage de l'analyse visuelle et esthétique
        print(f"\nQUALITÉ VISUELLE ET ESTHÉTIQUE:")
        if web_metadata.get("visual_score"):
            print(f"- Score visuel: {web_metadata.get('visual_score', 0)}/100")
        if web_metadata.get("design_quality"):
            print(f"- Qualité du design: {web_metadata.get('design_quality', 'inconnue')}")
        if web_metadata.get("design_modernity"):
            print(f"- Modernité du design: {web_metadata.get('design_modernity', 'inconnue')}")
        if web_metadata.get("visual_coherence"):
            print(f"- Cohérence visuelle: {web_metadata.get('visual_coherence', 'inconnue')}")
        
        # Affichage des forces et faiblesses du design
        if web_metadata.get("design_strengths"):
            print("\nPOINTS FORTS DU DESIGN:")
            for strength in web_metadata.get("design_strengths", []):
                print(f"- {strength}")
        
        if web_metadata.get("design_issues"):
            print("\nPOINTS FAIBLES DU DESIGN:")
            for issue in web_metadata.get("design_issues", []):
                print(f"- {issue}")
    else:
        print("\nAucun résultat d'analyse disponible")

if __name__ == "__main__":
    # Test des sites spécifiés
    analyze_site("app.berinia.com", "Berinia App")
    analyze_site("sejouris.com", "Sejouris")
    analyze_site("vipcrossing.com", "Vip Crossing")
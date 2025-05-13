#!/usr/bin/env python3
"""
Test du WebPresenceCheckerAgent sur des sites spécifiques
avec affichage formaté des résultats
"""
import sys
import json
import logging
import os
import time
from pathlib import Path
from colorama import init, Fore, Back, Style

# Initialiser colorama pour les couleurs dans le terminal
init(autoreset=True)

# Ajout du répertoire parent au chemin de recherche
sys.path.append(str(Path(__file__).parent))

# Import de l'agent à tester
from agents.web_checker.web_presence_checker_agent import WebPresenceCheckerAgent
from agents.web_checker.screenshot_analyzer import ScreenshotAnalyzer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def print_header(title):
    """Affiche un en-tête bien formaté"""
    print("\n" + "="*80)
    print(Fore.CYAN + Style.BRIGHT + f" {title}")
    print("="*80)

def print_section(title):
    """Affiche un titre de section"""
    print("\n" + Fore.YELLOW + Style.BRIGHT + f"➤ {title}")
    print(Fore.YELLOW + "─" * 60)

def print_info(label, value, color=Fore.WHITE):
    """Affiche une information avec formatage"""
    print(Fore.BLUE + f"{label}: " + color + f"{value}")

def print_check(label, value):
    """Affiche un élément de vérification avec une coche ou une croix"""
    icon = Fore.GREEN + "✓" if value else Fore.RED + "✗"
    print(f"{icon} {Fore.BLUE}{label}")

def format_score(score):
    """Formate un score avec couleur selon sa valeur"""
    if score >= 80:
        return Fore.GREEN + f"{score}/100"
    elif score >= 50:
        return Fore.YELLOW + f"{score}/100"
    else:
        return Fore.RED + f"{score}/100"

def analyze_site(url, company_name):
    """Analyse un site web spécifique et affiche les résultats formatés"""
    print_header(f"ANALYSE DU SITE: {url} ({company_name})")
    
    # Création de l'agent
    agent = WebPresenceCheckerAgent()
    
    # Créer le répertoire de screenshots s'il n'existe pas
    screenshots_dir = Path(__file__).parent / "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Création d'un lead factice avec l'URL à tester
    test_lead = {
        "lead_id": f"test-{url.replace('.', '-')}",
        "company": company_name,
        "company_website": url,
        "email": f"contact@{url}"
    }
    
    # Horodatage de début
    start_time = time.time()
    
    # Exécution de l'analyse
    print(Fore.CYAN + "Analyse en cours...")
    result = agent.run({
        "action": "check_web_presence",
        "lead": test_lead
    })
    
    # Calculer le temps d'exécution
    exec_time = time.time() - start_time
    
    # Récupération des données d'analyse
    if result.get("leads") and len(result.get("leads", [])) > 0:
        lead_result = result.get("leads")[0]
        web_metadata = lead_result.get("web_metadata", {})
        
        # 1. Section URL et statut
        print_section("INFORMATIONS GÉNÉRALES")
        print_info("URL", web_metadata.get('url', 'Non trouvée'))
        accessible = web_metadata.get('reachable', False)
        print_info("Accessible", "Oui" if accessible else "Non", 
                   Fore.GREEN if accessible else Fore.RED)
        print_info("Temps d'analyse", f"{exec_time:.2f} secondes")
        
        # 2. Section Maturité
        print_section("MATURITÉ DIGITALE")
        maturity_score = web_metadata.get('maturity_score', 0)
        print_info("Score de maturité", format_score(maturity_score))
        
        maturity_tag = web_metadata.get('maturity_tag', 'inconnu')
        maturity_color = Fore.GREEN if maturity_tag == 'pro_site' else (
            Fore.YELLOW if maturity_tag == 'standard_site' else Fore.RED)
        print_info("Catégorie", maturity_tag, maturity_color)
        
        tag = web_metadata.get('web_status_tag', 'inconnu')
        print_info("Tag commercial", tag, 
                  Fore.GREEN if tag == 'déjà bien équipé' else Fore.YELLOW)
        
        # 3. Section technique
        print_section("DÉTAILS TECHNIQUES")
        print_check("HTTPS", web_metadata.get('has_https', False))
        print_check("Mobile-friendly", web_metadata.get('mobile_friendly', False))
        print_check("Formulaires", web_metadata.get('has_form', False))
        print_check("Liens sociaux", web_metadata.get('has_social_links', False))
        print_check("Notice cookies", web_metadata.get('has_cookie_notice', False))
        
        # 4. Section Technologies
        print_section("TECHNOLOGIES")
        cms = web_metadata.get('cms', 'inconnu')
        print_info("CMS détecté", cms if cms != "unknown" else "Non détecté")
        
        tech_stack = web_metadata.get('tech_stack', [])
        if tech_stack:
            print_info("Technologies", ', '.join(tech_stack), Fore.GREEN)
        else:
            print_info("Technologies", "Aucune détectée", Fore.YELLOW)
        
        # 5. Section Performance
        print_section("PERFORMANCE")
        response_time = web_metadata.get('response_time_ms', 0)
        time_color = Fore.GREEN if response_time < 300 else (
            Fore.YELLOW if response_time < 1000 else Fore.RED)
        print_info("Temps de réponse", f"{response_time} ms", time_color)
        print_info("Taille de page", f"{web_metadata.get('page_size_kb', 0)} Ko")
        print_info("Nombre d'images", web_metadata.get('num_images', 0))
        print_info("Nombre de liens", web_metadata.get('num_links', 0))
        
        # 6. Section Analyse visuelle
        print_section("ANALYSE VISUELLE")
        visual_score = web_metadata.get('visual_score', 0)
        print_info("Score visuel", format_score(visual_score))
        
        if 'design_quality' in web_metadata and web_metadata['design_quality'] != "unknown":
            print_info("Qualité du design", web_metadata.get('design_quality', 'inconnue'))
        
        if 'design_modernity' in web_metadata and web_metadata['design_modernity'] != "unknown":
            modernity = web_metadata.get('design_modernity', 'inconnue')
            modernity_color = Fore.GREEN if modernity == 'moderne' else (
                Fore.YELLOW if modernity == 'standard' else Fore.RED)
            print_info("Modernité du design", modernity, modernity_color)
        
        if 'visual_coherence' in web_metadata and web_metadata['visual_coherence'] != "unknown":
            coherence = web_metadata.get('visual_coherence', 'inconnue')
            coherence_color = Fore.GREEN if coherence == 'très cohérent' else (
                Fore.YELLOW if coherence == 'cohérent' else Fore.RED)
            print_info("Cohérence visuelle", coherence, coherence_color)
        
        # 7. Section Analyse du screenshot
        if 'screenshot_path' in web_metadata:
            print_section("ANALYSE DU SCREENSHOT")
            screenshot_path = web_metadata.get('screenshot_path', '')
            print_info("Screenshot généré", screenshot_path, Fore.GREEN)
            
            if 'ui_components' in web_metadata:
                print("\nComposants UI détectés:")
                ui_components = web_metadata.get('ui_components', {})
                for component, present in ui_components.items():
                    if present:
                        print(Fore.GREEN + f"  ✓ {component}")
            
            if 'dominant_colors' in web_metadata:
                print("\nCouleurs dominantes:")
                colors = web_metadata.get('dominant_colors', [])
                for color in colors:
                    print(f"  • {color['color']} ({color['proportion']*100:.1f}%)")
            
            color_harmony = web_metadata.get('color_harmony', 'inconnu')
            harmony_color = Fore.GREEN if color_harmony == 'harmonieux' else (
                Fore.YELLOW if color_harmony == 'acceptable' else Fore.RED)
            print_info("\nHarmonie des couleurs", color_harmony, harmony_color)
            
            white_space = web_metadata.get('white_space_ratio', 0)
            print_info("Ratio d'espace blanc", f"{white_space*100:.1f}%")
            
            complexity = web_metadata.get('visual_complexity', 0)
            complexity_color = Fore.GREEN if 40 <= complexity <= 70 else (
                Fore.YELLOW if 30 <= complexity <= 80 else Fore.RED)
            print_info("Complexité visuelle", f"{complexity}/100", complexity_color)
        
        # 8. Points forts et faibles
        if web_metadata.get("design_strengths") or web_metadata.get("design_issues"):
            print_section("FORCES ET FAIBLESSES")
            
            if web_metadata.get("design_strengths"):
                print(Fore.GREEN + "\nPoints forts du design:")
                for strength in web_metadata.get("design_strengths", []):
                    print(Fore.GREEN + f"  ✓ {strength}")
            
            if web_metadata.get("design_issues"):
                print(Fore.RED + "\nPoints faibles du design:")
                for issue in web_metadata.get("design_issues", []):
                    print(Fore.RED + f"  ✗ {issue}")
    else:
        print(Fore.RED + "\nAucun résultat d'analyse disponible")

if __name__ == "__main__":
    # Test des sites spécifiés
    analyze_site("app.berinia.com", "Berinia App")
    analyze_site("sejouris.com", "Sejouris")
    analyze_site("vipcrossing.com", "Vip Crossing")

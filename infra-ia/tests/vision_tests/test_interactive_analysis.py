#!/usr/bin/env python3
"""
Test d'analyse interactive de sites web avec gestion améliorée des contenus dynamiques.
Cet outil permet d'analyser les sites qui utilisent des effets d'affichage au scroll.
"""
import sys
import os
import json
import logging
import time
import asyncio
from pathlib import Path
from colorama import init, Fore, Back, Style

# Initialiser colorama pour les couleurs dans le terminal
init(autoreset=True)

# Ajout du répertoire parent au chemin de recherche
sys.path.append(str(Path(__file__).parent))

# Import des composants nécessaires
from playwright.async_api import async_playwright
from agents.web_checker.web_presence_checker_agent import WebPresenceCheckerAgent

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("BerinIA-InteractiveAnalyzer")

# Fonctions d'affichage
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

async def interactive_screenshot(url, lead_id, screenshots_dir):
    """
    Capture des screenshots interactifs d'un site web en faisant défiler la page
    pour capturer également les éléments qui apparaissent au scroll
    
    Args:
        url: URL du site à capturer
        lead_id: Identifiant pour nommer les fichiers
        screenshots_dir: Répertoire de destination
        
    Returns:
        dict: Informations sur les captures réalisées
    """
    print_info("Analyse interactive", f"Préparation de la capture pour {url}", Fore.CYAN)
    screenshots = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Créer un contexte de navigation avec une taille définie
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1
        )
        
        # Créer une nouvelle page
        page = await context.new_page()
        
        # Navigation avec timeout étendu
        try:
            print_info("Chargement", "Accès à la page...", Fore.CYAN)
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Attendre un peu plus pour les animations de chargement
            print_info("Attente", "Délai pour animations initiales...", Fore.CYAN)
            await asyncio.sleep(3)
            
            # 1. Screenshot initial (au-dessus de la ligne de pli)
            initial_path = str(Path(screenshots_dir) / f"{lead_id}_initial.png")
            await page.screenshot(path=initial_path, full_page=False)
            print_info("Capture", f"Screenshot initial: {initial_path}", Fore.GREEN)
            screenshots.append({"type": "initial", "path": initial_path})
            
            # 2. Obtenir la hauteur de la page
            page_height = await page.evaluate("""
                () => document.documentElement.scrollHeight
            """)
            viewport_height = await page.evaluate("""
                () => window.innerHeight
            """)
            
            print_info("Page", f"Hauteur totale: {page_height}px, Viewport: {viewport_height}px", Fore.CYAN)
            
            # 3. Screenshots à différentes positions de scroll
            scroll_positions = []
            current_position = 0
            while current_position < page_height:
                scroll_positions.append(current_position)
                current_position += int(viewport_height * 0.8)  # Chevauchement de 20%
            
            # Ajouter la position finale
            if page_height - max(scroll_positions, default=0) > viewport_height * 0.2:
                scroll_positions.append(page_height - viewport_height)
            
            # Limiter à 5 positions maximum pour éviter trop de captures
            if len(scroll_positions) > 5:
                step = len(scroll_positions) // 5
                scroll_positions = scroll_positions[::step]
                if scroll_positions[-1] < page_height - viewport_height:
                    scroll_positions.append(page_height - viewport_height)
            
            # Effectuer les captures à chaque position
            for idx, position in enumerate(scroll_positions):
                # Scroll à la position
                await page.evaluate(f"window.scrollTo(0, {position})")
                
                # Attendre que les animations de scroll se terminent
                print_info("Scroll", f"Position {position}px...", Fore.CYAN)
                await asyncio.sleep(1.5)
                
                # Capture
                scroll_path = str(Path(screenshots_dir) / f"{lead_id}_scroll_{idx}.png")
                await page.screenshot(path=scroll_path, full_page=False)
                print_info("Capture", f"Screenshot position {position}px: {scroll_path}", Fore.GREEN)
                screenshots.append({"type": f"scroll_{idx}", "position": position, "path": scroll_path})
            
            # 4. Screenshot complet de la page
            full_path = str(Path(screenshots_dir) / f"{lead_id}_full.png")
            await page.screenshot(path=full_path, full_page=True)
            print_info("Capture", f"Screenshot complet: {full_path}", Fore.GREEN)
            screenshots.append({"type": "full", "path": full_path})
            
            # 5. Interactions avec les éléments interactifs (onglets, accordion, etc.)
            # Détecter les éléments interactifs
            interactive_elements = await page.evaluate("""
                () => {
                    // Sélecteurs pour les éléments interactifs courants
                    const selectors = [
                        '.tab, [role="tab"]',                          // Onglets
                        '.accordion-button, .accordion-header, details' // Accordéons
                    ];
                    
                    // Trouver tous les éléments correspondants
                    let elements = [];
                    for (const selector of selectors) {
                        elements = [...elements, ...Array.from(document.querySelectorAll(selector))];
                    }
                    
                    // Récupérer leurs coordonnées
                    return elements.map(el => {
                        const rect = el.getBoundingClientRect();
                        return {
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            type: el.tagName.toLowerCase(),
                            classes: el.className
                        };
                    }).filter(el => el.y >= 0 && el.y < window.innerHeight);  // Visibles actuellement
                }
            """)
            
            # Interagir avec les éléments et prendre des screenshots
            for idx, element in enumerate(interactive_elements):
                # Scroll vers l'élément si nécessaire
                await page.mouse.move(element["x"], element["y"])
                await asyncio.sleep(0.5)
                
                # Clic
                await page.mouse.click(element["x"], element["y"])
                print_info("Interaction", f"Clic sur élément {element['type']} ({element['classes']})", Fore.CYAN)
                
                # Attendre les animations
                await asyncio.sleep(1.5)
                
                # Capture après interaction
                interaction_path = str(Path(screenshots_dir) / f"{lead_id}_interaction_{idx}.png")
                await page.screenshot(path=interaction_path, full_page=False)
                print_info("Capture", f"Screenshot après interaction {idx}: {interaction_path}", Fore.GREEN)
                screenshots.append({"type": f"interaction_{idx}", "element": element, "path": interaction_path})
                
            # Fermer le navigateur
            await browser.close()
            
            print_info("Analyse", "Captures terminées", Fore.GREEN)
            
        except Exception as e:
            print_info("Erreur", str(e), Fore.RED)
            if browser:
                await browser.close()
            return {"success": False, "error": str(e)}
    
    return {
        "success": True,
        "screenshots": screenshots,
        "count": len(screenshots)
    }

async def analyze_site_interactive(url, company_name):
    """
    Analyse un site web avec des captures interactives pour gérer les éléments dynamiques
    qui apparaissent au défilement.
    
    Args:
        url: URL du site à analyser
        company_name: Nom de l'entreprise
    """
    print_header(f"ANALYSE INTERACTIVE DE: {url} ({company_name})")
    
    # Créer le répertoire de screenshots s'il n'existe pas
    screenshots_dir = Path(__file__).parent / "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Identifiant de lead formaté
    lead_id = f"test-{url.replace('.', '-').replace('/', '-')}"
    
    # 1. Capture des screenshots interactifs
    print_section("CAPTURE INTERACTIVE")
    capture_results = await interactive_screenshot(url, lead_id, screenshots_dir)
    
    if not capture_results.get("success", False):
        print_info("Erreur", capture_results.get("error", "Échec de la capture"), Fore.RED)
        return
    
    print_info("Captures réalisées", str(capture_results.get("count", 0)), Fore.GREEN)
    
    # 2. Création d'un lead factice avec l'URL à tester
    test_lead = {
        "lead_id": lead_id,
        "company": company_name,
        "company_website": url,
        "email": f"contact@{url.split('/')[0]}"
    }
    
    # 3. Analyse via l'agent
    print_section("ANALYSE STANDARD VIA AGENT")
    print_info("Analyse en cours", "Utilisation du WebPresenceCheckerAgent", Fore.CYAN)
    
    start_time = time.time()
    agent = WebPresenceCheckerAgent()
    result = agent.run({
        "action": "check_web_presence",
        "lead": test_lead
    })
    exec_time = time.time() - start_time
    
    # 4. Présentation des résultats
    if result.get("leads") and len(result.get("leads", [])) > 0:
        lead_result = result.get("leads")[0]
        web_metadata = lead_result.get("web_metadata", {})
        
        # Sections d'informations
        print_section("INFORMATIONS GÉNÉRALES")
        print_info("URL", web_metadata.get('url', 'Non trouvée'))
        accessible = web_metadata.get('reachable', False)
        print_info("Accessible", "Oui" if accessible else "Non", 
                  Fore.GREEN if accessible else Fore.RED)
        print_info("Temps d'analyse", f"{exec_time:.2f} secondes")
        
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
        
        print_section("DÉTAILS TECHNIQUES")
        print_check("HTTPS", web_metadata.get('has_https', False))
        print_check("Mobile-friendly", web_metadata.get('mobile_friendly', False))
        print_check("Formulaires", web_metadata.get('has_form', False))
        print_check("Liens sociaux", web_metadata.get('has_social_links', False))
        print_check("Notice cookies", web_metadata.get('has_cookie_notice', False))
        
        # Compare les résultats des captures standards et interactives
        print_section("CAPTURES RÉALISÉES")
        print_info("Total de captures", str(capture_results.get("count", 0)), Fore.GREEN)
        
        # Liste tous les screenshots capturés
        screenshots = capture_results.get("screenshots", [])
        for idx, screenshot in enumerate(screenshots):
            screenshot_type = screenshot.get("type", "unknown")
            screenshot_path = screenshot.get("path", "")
            
            type_color = Fore.CYAN
            if screenshot_type == "initial":
                type_label = "Capture initiale (sans scroll)"
            elif screenshot_type == "full":
                type_label = "Capture complète de la page"
                type_color = Fore.GREEN
            elif screenshot_type.startswith("scroll_"):
                position = screenshot.get("position", 0)
                type_label = f"Capture position scroll {position}px"
            elif screenshot_type.startswith("interaction_"):
                element = screenshot.get("element", {})
                type_label = f"Capture après interaction ({element.get('type', '')})"
                type_color = Fore.YELLOW
            else:
                type_label = f"Capture {screenshot_type}"
            
            print_info(f"Screenshot {idx+1}", type_label, type_color)
            print(f"  {Fore.BLUE}Path: {screenshot_path}")
            
        # Afficher d'autres informations pertinentes
        print_section("RECOMMANDATIONS")
        print(f"{Fore.WHITE}Pour une analyse plus précise:")
        print(f"{Fore.WHITE}1. Vérifiez les captures à différentes positions de scroll pour voir tous les éléments")
        print(f"{Fore.WHITE}2. Comparez les interactions avec les éléments dynamiques pour évaluer le design")
        print(f"{Fore.WHITE}3. Utilisez le score de maturité comme indicateur global, mais examinez les captures pour confirmation")
        
        if web_metadata.get('has_form', False):
            print(f"\n{Fore.GREEN}Ce site contient des formulaires - potentiel d'interaction client élevé")
        
        if web_metadata.get('tech_stack', []):
            tech_stack = web_metadata.get('tech_stack', [])
            print(f"\n{Fore.CYAN}Technologies détectées: {', '.join(tech_stack)}")
    else:
        print(Fore.RED + "\nAucun résultat d'analyse disponible")

async def main():
    """Fonction principale asynchrone"""
    sites = [
        ("https://app.berinia.com", "Berinia App"),
        ("https://sejouris.com", "Sejouris"),
        ("https://vipcrossing.com", "Vip Crossing")
    ]
    
    for url, name in sites:
        await analyze_site_interactive(url, name)

if __name__ == "__main__":
    # Exécution du programme principal
    asyncio.run(main())

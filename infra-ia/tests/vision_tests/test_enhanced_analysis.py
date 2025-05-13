#!/usr/bin/env python3
"""
Test d'analyse avancée de sites web avec :
1. Détection et gestion des popups de confidentialité
2. Captures progressives avec reconstruction d'une image complète
3. Analyse des éléments dynamiques apparaissant au scroll
"""
import sys
import os
import logging
import time
import asyncio
from pathlib import Path
from PIL import Image
from colorama import init, Fore, Back, Style

# Initialiser colorama pour les couleurs dans le terminal
init(autoreset=True)

# Ajout du répertoire parent au chemin de recherche
sys.path.append(str(Path(__file__).parent))

# Import des composants nécessaires
from playwright.async_api import async_playwright, TimeoutError
from agents.web_checker.web_presence_checker_agent import WebPresenceCheckerAgent

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("BerinIA-EnhancedAnalyzer")

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

async def handle_cookie_consent(page):
    """
    Détecte et accepte les popups de cookies/confidentialité
    
    Args:
        page: Page Playwright
        
    Returns:
        bool: True si une popup a été détectée et traitée
    """
    # Liste des sélecteurs communs pour les boutons d'acceptation de cookies
    consent_button_selectors = [
        # Boutons génériques
        "button[id*='accept']", "button[id*='cookie']", "button[id*='consent']",
        "button[class*='accept']", "button[class*='cookie']", "button[class*='consent']",
        "a[id*='accept']", "a[class*='accept']", "a[class*='cookie']",
        "[aria-label*='accept cookies']", "[aria-label*='accept all']",
        
        # Textes de boutons communs (avec sélecteurs de texte plus robustes)
        "button:has-text(\"Accept\")", "button:has-text(\"Accept All\")", 
        "button:has-text(\"Accepter\")", "button:has-text(\"OK\")",
        "button:has-text(\"Agree\")", "button:has-text(\"I Agree\")",
        "button:has-text(\"Got it\")", "button:has-text(\"Allow\")",
        
        # Solutions populaires de gestion des cookies
        "#didomi-notice-agree-button", ".didomi-continue-button",
        "#onetrust-accept-btn-handler", "#accept-cookies",
        ".cc-button", ".cc-accept", ".cc-dismiss",
        "#CybotCookiebotDialogBodyButtonAccept",
        ".cookieconsent-button", ".gdpr-consent-button",
        
        # Autres sélecteurs courants
        ".cookie-banner button", ".cookie-notice button", 
        ".privacy-notice button", ".consent-banner button",
        ".gdpr-banner button", ".cookie-popup button"
    ]
    
    # Vérifier chaque sélecteur et interagir avec le premier trouvé
    for selector in consent_button_selectors:
        try:
            # Attendre un court instant pour que le bouton soit visible
            cookie_button = await page.wait_for_selector(selector, timeout=1000)
            
            if cookie_button:
                print_info("Popup", f"Popup de confidentialité détectée! Tentative d'acceptation...", Fore.YELLOW)
                
                # Cliquer sur le bouton
                await cookie_button.click()
                print_info("Interaction", "Popup de confidentialité acceptée", Fore.GREEN)
                
                # Attendre que les animations se terminent
                await asyncio.sleep(1)
                return True
                
        except TimeoutError:
            # Continuer avec le prochain sélecteur si celui-ci n'est pas trouvé
            continue
        except Exception as e:
            print_info("Erreur", f"Erreur lors de la gestion de la popup: {str(e)}", Fore.RED)
    
    return False

async def stitch_screenshots(screenshots, output_path, lead_id):
    """
    Reconstitue une image complète à partir des captures partielles
    
    Args:
        screenshots: Liste des chemins de captures partielles
        output_path: Chemin de sortie pour l'image reconstituée
        lead_id: Identifiant du lead
        
    Returns:
        str: Chemin de l'image reconstituée
    """
    try:
        # Filtrer les screenshots pour ne garder que ceux de type scroll
        scroll_screenshots = [s for s in screenshots if 
                             "scroll_" in s.get("type", "") and 
                             "path" in s and 
                             os.path.exists(s["path"])]
        
        # S'il n'y a pas au moins 2 screenshots, pas besoin de les combiner
        if len(scroll_screenshots) < 2:
            print_info("Reconstruction", "Pas assez de captures pour reconstruire une image complète", Fore.YELLOW)
            return None
        
        # Trier les screenshots par position
        scroll_screenshots.sort(key=lambda x: x.get("position", 0))
        
        # Ouvrir le premier screenshot pour déterminer la largeur
        first_img = Image.open(scroll_screenshots[0]["path"])
        width, _ = first_img.size
        
        # Calculer la hauteur totale en tenant compte du chevauchement
        total_height = 0
        for idx, screenshot in enumerate(scroll_screenshots):
            img = Image.open(screenshot["path"])
            if idx == 0:
                total_height += img.height
            else:
                # Soustraire environ 20% pour le chevauchement
                overlap = int(img.height * 0.2)
                total_height += img.height - overlap
        
        # Créer une nouvelle image avec la hauteur totale
        combined_img = Image.new('RGB', (width, total_height))
        
        # Combiner les screenshots
        y_offset = 0
        for idx, screenshot in enumerate(scroll_screenshots):
            img = Image.open(screenshot["path"])
            
            # Pour toutes les images sauf la première, décaler pour tenir compte du chevauchement
            if idx > 0:
                overlap = int(img.height * 0.2)
                y_offset -= overlap
            
            combined_img.paste(img, (0, y_offset))
            y_offset += img.height
        
        # Sauvegarder l'image combinée
        stitched_path = os.path.join(output_path, f"{lead_id}_reconstructed.png")
        combined_img.save(stitched_path)
        
        print_info("Reconstruction", f"Image complète reconstruite: {stitched_path}", Fore.GREEN)
        return stitched_path
    
    except Exception as e:
        print_info("Erreur", f"Erreur lors de la reconstruction de l'image: {str(e)}", Fore.RED)
        return None

async def enhanced_screenshot_analysis(url, lead_id, screenshots_dir):
    """
    Analyse avancée avec gestion des popups et reconstitution d'image
    
    Args:
        url: URL du site à capturer
        lead_id: Identifiant pour nommer les fichiers
        screenshots_dir: Répertoire de destination
        
    Returns:
        dict: Informations sur les captures réalisées
    """
    print_info("Analyse améliorée", f"Préparation de la capture pour {url}", Fore.CYAN)
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
            
            # 1. Gérer les popups de confidentialité avant de commencer l'analyse
            popup_handled = await handle_cookie_consent(page)
            if popup_handled:
                # Si popup traitée, attendre que la page se stabilise
                await asyncio.sleep(2)
            
            # Attendre un peu plus pour les animations de chargement
            print_info("Attente", "Délai pour animations initiales...", Fore.CYAN)
            await asyncio.sleep(3)
            
            # 2. Screenshot initial (au-dessus de la ligne de pli)
            initial_path = str(Path(screenshots_dir) / f"{lead_id}_initial.png")
            await page.screenshot(path=initial_path, full_page=False)
            print_info("Capture", f"Screenshot initial: {initial_path}", Fore.GREEN)
            screenshots.append({"type": "initial", "path": initial_path})
            
            # 3. Obtenir la hauteur initiale de la page
            initial_height = await page.evaluate("""
                () => document.documentElement.scrollHeight
            """)
            viewport_height = await page.evaluate("""
                () => window.innerHeight
            """)
            
            print_info("Page", f"Hauteur initiale: {initial_height}px, Viewport: {viewport_height}px", Fore.CYAN)
            
            # 4. Screenshots à différentes positions de scroll avec surveillance de changements de hauteur
            scroll_positions = []
            current_position = 0
            while current_position < initial_height:
                scroll_positions.append(current_position)
                current_position += int(viewport_height * 0.8)  # Chevauchement de 20%
            
            # S'assurer que la position finale est incluse
            if initial_height - max(scroll_positions, default=0) > viewport_height * 0.2:
                scroll_positions.append(initial_height - viewport_height)
            
            # Limiter à un nombre raisonnable de positions pour les très longues pages
            if len(scroll_positions) > 10:
                step = len(scroll_positions) // 10
                scroll_positions = scroll_positions[::step]
                # S'assurer que la position finale est incluse
                if scroll_positions[-1] < initial_height - viewport_height:
                    scroll_positions.append(initial_height - viewport_height)
            
            # Effectuer les captures à chaque position avec vérification de hauteur dynamique
            for idx, position in enumerate(scroll_positions):
                # Scroll à la position
                await page.evaluate(f"window.scrollTo(0, {position})")
                
                # Attendre que les animations de scroll se terminent
                print_info("Scroll", f"Position {position}px...", Fore.CYAN)
                await asyncio.sleep(2)  # Délai plus long pour laisser le temps aux éléments de charger
                
                # Vérifier si la page a changé de hauteur (chargement dynamique de contenu)
                new_height = await page.evaluate("""
                    () => document.documentElement.scrollHeight
                """)
                
                if new_height > initial_height:
                    print_info("Page", f"Hauteur augmentée: {new_height}px (était {initial_height}px)", Fore.YELLOW)
                    # Ajuster les positions de scroll restantes si la page a grandi
                    remaining_positions = [pos for pos in scroll_positions if pos > position]
                    if remaining_positions:
                        # Ajouter des positions intermédiaires
                        new_positions = []
                        last_pos = position
                        while last_pos < new_height:
                            next_pos = last_pos + int(viewport_height * 0.8)
                            if next_pos >= new_height:
                                next_pos = new_height - viewport_height
                            if next_pos > last_pos:  # Éviter les positions dupliquées
                                new_positions.append(next_pos)
                            last_pos = next_pos
                            if last_pos >= new_height - viewport_height:
                                break
                        
                        # Remplacer les positions restantes
                        scroll_positions = [p for p in scroll_positions if p <= position] + new_positions
                    initial_height = new_height
                
                # Capture
                scroll_path = str(Path(screenshots_dir) / f"{lead_id}_scroll_{idx}.png")
                await page.screenshot(path=scroll_path, full_page=False)
                print_info("Capture", f"Screenshot position {position}px: {scroll_path}", Fore.GREEN)
                screenshots.append({"type": f"scroll_{idx}", "position": position, "path": scroll_path})
                
                # Vérifier s'il y a une popup qui est apparue
                # (certains sites affichent des popups après un certain temps ou scroll)
                popup_handled = await handle_cookie_consent(page)
                if popup_handled:
                    await asyncio.sleep(1)
            
            # 5. Screenshot complet de la page
            full_path = str(Path(screenshots_dir) / f"{lead_id}_full.png")
            try:
                await page.screenshot(path=full_path, full_page=True)
                print_info("Capture", f"Screenshot complet: {full_path}", Fore.GREEN)
                screenshots.append({"type": "full", "path": full_path})
            except Exception as e:
                print_info("Erreur", f"Impossible de capturer la page complète: {str(e)}", Fore.RED)
                print_info("Solution", "Utilisation de la reconstruction d'image à la place", Fore.YELLOW)
            
            # 6. Interactions avec les éléments interactifs (onglets, accordion, etc.)
            interactive_elements = await page.evaluate("""
                () => {
                    // Sélecteurs pour les éléments interactifs courants
                    const selectors = [
                        '.tab, [role="tab"]',                          // Onglets
                        '.accordion-button, .accordion-header, details', // Accordéons
                        '.dropdown-toggle, .dropdown-button',           // Menus déroulants
                        '.carousel-control, .slider-control'            // Carrousels
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
                try:
                    # Scroll vers l'élément si nécessaire
                    await page.mouse.move(element["x"], element["y"])
                    await asyncio.sleep(0.5)
                    
                    # Clic
                    await page.mouse.click(element["x"], element["y"])
                    print_info("Interaction", f"Clic sur élément {element['type']} ({element['classes']})", Fore.CYAN)
                    
                    # Attendre les animations
                    await asyncio.sleep(2)
                    
                    # Capture après interaction
                    interaction_path = str(Path(screenshots_dir) / f"{lead_id}_interaction_{idx}.png")
                    await page.screenshot(path=interaction_path, full_page=False)
                    print_info("Capture", f"Screenshot après interaction {idx}: {interaction_path}", Fore.GREEN)
                    screenshots.append({"type": f"interaction_{idx}", "element": element, "path": interaction_path})
                except Exception as e:
                    print_info("Erreur", f"Erreur lors de l'interaction {idx}: {str(e)}", Fore.RED)
            
            # Fermer le navigateur
            await browser.close()
            
            # 7. Reconstruction d'une image complète à partir des captures partielles
            if "full" not in [s.get("type") for s in screenshots]:
                stitched_path = await stitch_screenshots(screenshots, screenshots_dir, lead_id)
                if stitched_path:
                    screenshots.append({"type": "reconstructed", "path": stitched_path})
            
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

async def analyze_site_enhanced(url, company_name):
    """
    Analyse améliorée d'un site web avec gestion des popups et reconstitution d'image
    
    Args:
        url: URL du site à analyser
        company_name: Nom de l'entreprise
    """
    print_header(f"ANALYSE AMÉLIORÉE DE: {url} ({company_name})")
    
    # Créer le répertoire de screenshots s'il n'existe pas
    screenshots_dir = Path(__file__).parent / "enhanced_screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Identifiant de lead formaté
    lead_id = f"test-{url.replace('https://', '').replace('http://', '').replace('.', '-').replace('/', '-')}"
    
    # 1. Capture des screenshots avec gestion avancée
    print_section("CAPTURE AVANCÉE")
    capture_results = await enhanced_screenshot_analysis(url, lead_id, screenshots_dir)
    
    if not capture_results.get("success", False):
        print_info("Erreur", capture_results.get("error", "Échec de la capture"), Fore.RED)
        return
    
    print_info("Captures réalisées", str(capture_results.get("count", 0)), Fore.GREEN)
    
    # 2. Création d'un lead factice avec l'URL à tester
    test_lead = {
        "lead_id": lead_id,
        "company": company_name,
        "company_website": url,
        "email": f"contact@{url.split('//')[1].split('/')[0]}"
    }
    
    # 3. Analyse via l'agent
    print_section("ANALYSE VIA AGENT")
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
        
        # Technologies détectées
        if web_metadata.get('tech_stack', []):
            tech_stack = web_metadata.get('tech_stack', [])
            print_section("TECHNOLOGIES")
            print_info("Technologies détectées", ', '.join(tech_stack), Fore.CYAN)
        
        # Liste des captures réalisées
        print_section("CAPTURES RÉALISÉES")
        print_info("Total de captures", str(capture_results.get("count", 0)), Fore.GREEN)
        
        # Organiser les captures par type
        screenshots = capture_results.get("screenshots", [])
        
        # Capture initiale
        initial_shots = [s for s in screenshots if s.get("type") == "initial"]
        if initial_shots:
            print_info("Capture initiale", initial_shots[0].get("path", ""), Fore.CYAN)
        
        # Captures par scroll
        scroll_shots = [s for s in screenshots if s.get("type", "").startswith("scroll_")]
        if scroll_shots:
            print_info("Captures de scroll", f"{len(scroll_shots)} positions", Fore.CYAN)
            for shot in scroll_shots:
                position = shot.get("position", 0)
                print(f"  {Fore.BLUE}Position {position}px: {shot.get('path', '')}")
        
        # Captures d'interactions
        interaction_shots = [s for s in screenshots if s.get("type", "").startswith("interaction_")]
        if interaction_shots:
            print_info("Captures d'interactions", f"{len(interaction_shots)} éléments", Fore.YELLOW)
            for idx, shot in enumerate(interaction_shots):
                element = shot.get("element", {})
                element_type = element.get("type", "inconnu")
                element_class = element.get("classes", "")
                print(f"  {Fore.BLUE}Élément {element_type} {element_class}: {shot.get('path', '')}")
        
        # Capture complète ou reconstruite
        full_shots = [s for s in screenshots if s.get("type") in ["full", "reconstructed"]]
        if full_shots:
            for shot in full_shots:
                shot_type = "complète (native)" if shot.get("type") == "full" else "complète (reconstruite)"
                print_info(f"Capture {shot_type}", shot.get("path", ""), Fore.GREEN)
        
        # Afficher recommandations
        print_section("RECOMMANDATIONS")
        print(f"{Fore.WHITE}Pour une analyse optimale:")
        print(f"{Fore.WHITE}1. Utilisez la capture complète/reconstruite pour analyse globale")
        print(f"{Fore.WHITE}2. Vérifiez les interactions pour évaluer le comportement des éléments dynamiques")
        
        # Spécificités du site détectées
        print_section("SPÉCIFICITÉS DÉTECTÉES")
        
        if "popup_handled" in capture_results:
            print_info("Popup de confidentialité", "Détectée et acceptée automatiquement", Fore.GREEN)
        
        if web_metadata.get('has_form', False):
            print_info("Formulaires", "Le site contient des formulaires - potentiel d'interaction client", Fore.GREEN)
        
        if "reconstructed" in [s.get("type") for s in screenshots]:
            print_info("Image reconstruite", "Une image a été reconstruite à partir des captures partielles", Fore.YELLOW)
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
        await analyze_site_enhanced(url, name)

if __name__ == "__main__":
    # S'assurer que PIL est installé
    try:
        import PIL
    except ImportError:
        print(f"{Fore.RED}Erreur: La bibliothèque PIL (Pillow) est requise.")
        print(f"{Fore.YELLOW}Installez-la avec: pip install pillow")
        sys.exit(1)
        
    # Exécution du programme principal
    asyncio.run(main())

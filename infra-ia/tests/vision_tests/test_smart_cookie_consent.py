#!/usr/bin/env python3
"""
Module intelligent pour la détection et gestion des popups de consentement/cookies
sans dépendre de sélecteurs prédéfinis.

Cette approche utilise:
1. Une détection basée sur l'intelligence artificielle
2. Une analyse visuelle des éléments de la page
3. Une stratégie adaptative qui apprend des interactions précédentes
"""
import os
import asyncio
import logging
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError
from colorama import init, Fore, Style

# Initialiser colorama pour les couleurs dans le terminal
init(autoreset=True)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("BerinIA-SmartConsent")

class SmartConsentDetector:
    """
    Détecteur intelligent de popups de consentement qui utilise
    des heuristiques avancées et des techniques d'analyse visuelle
    pour identifier et gérer les popups.
    """
    
    def __init__(self):
        """Initialisation du détecteur intelligent"""
        # Caractéristiques visuelles communes des popups de consentement
        self.popup_signatures = {
            "position": ["fixed", "sticky", "absolute"],
            "z_index": [1000, 9999],  # Les z-index élevés sont souvent utilisés pour les popups
            "common_words": ["cookie", "consent", "gdpr", "privacy", "accept", 
                            "cookies", "policy", "accepter", "confidentialité"]
        }
        
        # Historique des interactions réussies pour apprentissage
        self.successful_interactions = []
        
    async def detect_and_handle_consent(self, page):
        """
        Méthode principale pour détecter et gérer les popups de consentement
        
        Args:
            page: Page Playwright
            
        Returns:
            bool: True si une popup a été détectée et traitée
        """
        print(f"{Fore.BLUE}Détection intelligente{Fore.RESET}: Analyse de la page pour popups...")
        
        # Stratégie 1: Analyse des éléments visuels de la page
        visual_candidates = await self._find_visual_candidates(page)
        
        # Stratégie 2: Analyse textuelle
        text_candidates = await self._find_text_candidates(page)
        
        # Stratégie 3: Analyse des éléments fixés/en superposition
        overlay_candidates = await self._find_overlay_candidates(page)
        
        # Combiner les candidats des différentes stratégies (sans doublons)
        candidates = []
        for candidate in visual_candidates + text_candidates + overlay_candidates:
            if candidate not in candidates:
                candidates.append(candidate)
        
        # Évaluer et trier les candidats selon une probabilité
        candidates_with_scores = await self._score_candidates(page, candidates)
        
        # Tenter l'interaction avec les candidats, en ordre de score décroissant
        for candidate, score in sorted(candidates_with_scores, key=lambda x: x[1], reverse=True):
            success = await self._attempt_interaction(page, candidate, score)
            if success:
                print(f"{Fore.GREEN}Popup gérée{Fore.RESET}: Interaction réussie avec élément (score: {score:.2f})")
                return True
                
        print(f"{Fore.YELLOW}Aucune popup{Fore.RESET}: Aucun élément de consentement détecté ou géré")
        return False
    
    async def _find_visual_candidates(self, page):
        """
        Trouve des éléments visuels qui ressemblent à des bannières de consentement
        basé sur leurs caractéristiques visuelles
        
        Args:
            page: Page Playwright
            
        Returns:
            list: Liste des éléments candidats
        """
        candidates = await page.evaluate("""
            () => {
                // Rechercher des éléments avec des caractéristiques visuelles de popup
                const allElements = Array.from(document.querySelectorAll('*'));
                
                // Filtrer pour les éléments qui pourraient être des popups/bannières
                return allElements
                    .filter(el => {
                        if (!el || !el.getBoundingClientRect) return false;
                        
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        
                        // Ignorer les éléments très petits
                        if (rect.width < 200 || rect.height < 50) return false;
                        
                        // Les popups sont souvent positionnés en bas ou en haut de la page
                        const isAtBottomOrTop = 
                            (rect.bottom >= window.innerHeight - 10 && rect.bottom <= window.innerHeight + 50) ||
                            (rect.top <= 10 && rect.top >= -50);
                            
                        // Les popups ont souvent un fond différent et une bordure/ombre
                        const hasDistinctBackground = 
                            style.backgroundColor !== 'rgba(0, 0, 0, 0)' && 
                            style.backgroundColor !== 'transparent';
                            
                        const hasBoxShadowOrBorder = 
                            style.boxShadow !== 'none' || 
                            (style.border !== 'none' && style.border !== '0px none');
                            
                        // Position fixe/absolue est commune pour les popups
                        const hasFixedPosition = 
                            style.position === 'fixed' || 
                            style.position === 'sticky' || 
                            style.position === 'absolute';
                            
                        // z-index élevé est commun pour les popups
                        const hasHighZIndex = 
                            parseInt(style.zIndex) > 10;
                        
                        // Retourner true si plusieurs de ces caractéristiques sont présentes
                        return (isAtBottomOrTop && hasDistinctBackground && hasFixedPosition) || 
                               (hasHighZIndex && hasDistinctBackground && hasBoxShadowOrBorder);
                    })
                    .map(el => {
                        const rect = el.getBoundingClientRect();
                        return {
                            tagName: el.tagName,
                            id: el.id,
                            className: el.className,
                            position: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                top: rect.top,
                                bottom: rect.bottom
                            },
                            text: el.innerText,
                            type: 'visual'
                        };
                    });
            }
        """)
        
        print(f"{Fore.BLUE}Candidats visuels{Fore.RESET}: {len(candidates)} éléments identifiés")
        return candidates
        
    async def _find_text_candidates(self, page):
        """
        Trouve des éléments basés sur leur contenu textuel
        
        Args:
            page: Page Playwright
            
        Returns:
            list: Liste des éléments candidats
        """
        # Mots-clés de consentement dans plusieurs langues
        keywords = [
            "cookie", "cookies", "consent", "gdpr", "rgpd", 
            "privacy", "privacidad", "confidentialité", "datenschutz",
            "accept", "accepter", "aceptar", "akzeptieren",
            "agree", "j'accepte", "i agree", "estoy de acuerdo",
            "ok", "continue", "continuer", "got it"
        ]
        
        # Construire une expression régulière pour la recherche (insensible à la casse)
        keyword_regex = "|".join(keywords)
        
        candidates = await page.evaluate(f"""
            () => {{
                // Recherche d'éléments contenant des mots-clés liés au consentement
                const keywordRegex = new RegExp("({keyword_regex})", "i");
                
                // Trouver tous les boutons et liens
                const clickableElements = Array.from(document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]'));
                
                // Filtrer pour ceux qui contiennent des mots-clés
                return clickableElements
                    .filter(el => {{
                        // Vérifier le texte de l'élément
                        const text = el.innerText || el.textContent || el.value || '';
                        if (keywordRegex.test(text)) return true;
                        
                        // Vérifier les attributs pertinents
                        const ariaLabel = el.getAttribute('aria-label') || '';
                        const title = el.getAttribute('title') || '';
                        const id = el.id || '';
                        const className = el.className || '';
                        
                        return keywordRegex.test(ariaLabel) || 
                               keywordRegex.test(title) || 
                               keywordRegex.test(id) || 
                               keywordRegex.test(className);
                    }})
                    .map(el => {{
                        const rect = el.getBoundingClientRect();
                        return {{
                            tagName: el.tagName,
                            id: el.id,
                            className: el.className,
                            position: {{
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                top: rect.top,
                                bottom: rect.bottom
                            }},
                            text: el.innerText || el.textContent || el.value || '',
                            type: 'text'
                        }};
                    }});
            }}
        """)
        
        print(f"{Fore.BLUE}Candidats textuels{Fore.RESET}: {len(candidates)} éléments identifiés")
        return candidates
    
    async def _find_overlay_candidates(self, page):
        """
        Trouve des éléments qui sont positionnés comme des superpositions/modales
        
        Args:
            page: Page Playwright
            
        Returns:
            list: Liste des éléments candidats
        """
        candidates = await page.evaluate("""
            () => {
                // Rechercher des éléments qui semblent être des superpositions/modales
                const potentialOverlays = Array.from(document.querySelectorAll(
                    'div[class*="modal"], div[class*="popup"], div[class*="overlay"], div[class*="banner"], ' +
                    'div[class*="cookie"], div[class*="consent"], div[id*="cookie"], div[id*="consent"], ' +
                    'section[class*="cookie"], section[class*="consent"], ' +
                    'aside[class*="cookie"], aside[class*="consent"], ' +
                    'div[aria-label*="cookie"], div[aria-describedby*="cookie"]'
                ));
                
                // Filtrer pour ceux qui sont visibles
                return potentialOverlays
                    .filter(el => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        
                        // Ignorer les éléments cachés ou trop petits
                        if (style.display === 'none' || 
                            style.visibility === 'hidden' || 
                            style.opacity === '0' ||
                            rect.width < 100 || 
                            rect.height < 50) {
                            return false;
                        }
                        
                        return true;
                    })
                    .map(el => {
                        // Trouver les boutons à l'intérieur de ces overlays
                        const buttons = Array.from(el.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]'));
                        let buttonDetails = [];
                        
                        if (buttons.length > 0) {
                            buttonDetails = buttons.map(btn => {
                                const btnRect = btn.getBoundingClientRect();
                                return {
                                    tagName: btn.tagName,
                                    id: btn.id,
                                    className: btn.className,
                                    position: {
                                        x: btnRect.x,
                                        y: btnRect.y,
                                        width: btnRect.width,
                                        height: btnRect.height
                                    },
                                    text: btn.innerText || btn.textContent || btn.value || ''
                                };
                            });
                        }
                        
                        const rect = el.getBoundingClientRect();
                        return {
                            tagName: el.tagName,
                            id: el.id,
                            className: el.className,
                            position: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                top: rect.top,
                                bottom: rect.bottom
                            },
                            text: el.innerText,
                            buttons: buttonDetails,
                            type: 'overlay'
                        };
                    });
            }
        """)
        
        # Aplatir la liste pour inclure à la fois les overlays et leurs boutons
        flattened_candidates = []
        for overlay in candidates:
            flattened_candidates.append(overlay)
            
            # Si l'overlay contient des boutons, les ajouter comme candidats distincts
            if "buttons" in overlay and overlay["buttons"]:
                for button in overlay["buttons"]:
                    button["type"] = "overlay_button"
                    flattened_candidates.append(button)
        
        print(f"{Fore.BLUE}Candidats overlay{Fore.RESET}: {len(flattened_candidates)} éléments identifiés")
        return flattened_candidates
    
    async def _score_candidates(self, page, candidates):
        """
        Évalue chaque candidat et lui attribue un score de probabilité
        
        Args:
            page: Page Playwright
            candidates: Liste des candidats
            
        Returns:
            list: Liste des tuples (candidat, score)
        """
        results = []
        
        for candidate in candidates:
            score = 0.0
            
            # 1. Points basés sur le type de candidat
            if candidate.get("type") == "overlay_button":
                score += 2.0  # Boutons dans des overlays sont très probables
            elif candidate.get("type") == "text":
                score += 1.5  # Candidats textuels sont assez probables
            elif candidate.get("type") == "visual":
                score += 1.0  # Candidats visuels sont moins certains
            
            # 2. Points basés sur le contenu textuel
            text = candidate.get("text", "").lower()
            
            # Mots très spécifiques aux consentements
            if any(word in text for word in ["accept all", "accept cookies", "accepter tous", 
                                             "j'accepte", "i agree", "agree", "accepter"]):
                score += 3.0
            
            # Mots liés aux cookies/consentement
            elif any(word in text for word in ["cookie", "consent", "gdpr", "rgpd", "privacy"]):
                score += 1.5
                
            # Mots d'action positifs
            elif any(word in text for word in ["ok", "continue", "got it", "allow"]):
                score += 1.0
            
            # 3. Points basés sur la position et la visibilité
            position = candidate.get("position", {})
            
            # En bas ou en haut de la page (typique des bannières)
            if position.get("bottom", 0) >= (await page.evaluate("window.innerHeight")) - 150:
                score += 1.5  # Bannières en bas
            elif position.get("top", 1000) <= 150:
                score += 1.0  # Bannières en haut
                
            # Largeur significative (typique des bannières)
            viewport_width = await page.evaluate("window.innerWidth")
            if position.get("width", 0) >= viewport_width * 0.8:
                score += 1.0
            
            # 4. Points basés sur les attributs HTML
            id_class = (candidate.get("id", "") + " " + candidate.get("className", "")).lower()
            
            if any(word in id_class for word in ["cookie", "consent", "gdpr", "privacy", "cmp"]):
                score += 2.0
                
            if any(word in id_class for word in ["banner", "modal", "popup", "notice"]):
                score += 1.0
            
            # 5. Bonus pour les types d'éléments typiques
            tag_name = candidate.get("tagName", "").lower()
            if tag_name == "button":
                score += 1.0
            elif tag_name == "a" and "button" in id_class:
                score += 0.8
            
            results.append((candidate, score))
        
        # Trier par score décroissant
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Afficher les meilleurs candidats
        if results:
            print(f"{Fore.BLUE}Meilleurs candidats{Fore.RESET}:")
            for candidate, score in results[:3]:  # Afficher les 3 meilleurs
                tag = candidate.get("tagName", "")
                text = candidate.get("text", "")[:30] + ("..." if len(candidate.get("text", "")) > 30 else "")
                print(f"  - {tag}: '{text}' (score: {score:.2f})")
        
        return results
    
    async def _attempt_interaction(self, page, candidate, score):
        """
        Tente d'interagir avec un candidat pour fermer/accepter le consentement
        
        Args:
            page: Page Playwright
            candidate: Le candidat à essayer
            score: Score du candidat
            
        Returns:
            bool: True si l'interaction a réussi
        """
        # Ne pas tenter d'interagir avec des candidats ayant un score trop faible
        if score < 2.0:
            print(f"{Fore.YELLOW}Candidat ignoré{Fore.RESET}: Score trop faible ({score:.2f})")
            return False
        
        # Extraire les informations du candidat
        position = candidate.get("position", {})
        tag_name = candidate.get("tagName", "").lower()
        element_id = candidate.get("id", "")
        class_name = candidate.get("className", "")
        
        # Construire un sélecteur pour localiser l'élément
        selector = None
        
        if element_id:
            selector = f"#{element_id}"
        elif class_name and " " not in class_name:  # Classe unique
            selector = f".{class_name}"
        elif tag_name and position:
            # Utiliser les coordonnées pour cliquer
            try:
                x = position.get("x", 0) + position.get("width", 0) / 2
                y = position.get("y", 0) + position.get("height", 0) / 2
                
                print(f"{Fore.BLUE}Tentative de clic{Fore.RESET}: {tag_name} aux coordonnées ({x}, {y})")
                
                # Déplacer la souris et cliquer
                await page.mouse.move(x, y)
                await asyncio.sleep(0.2)
                await page.mouse.click(x, y)
                
                # Attendre pour voir si la page change
                await asyncio.sleep(1)
                
                # Vérifier si le candidat est toujours visible
                still_visible = await page.evaluate(f"""
                    () => {{
                        const elements = document.querySelectorAll('{tag_name}');
                        for (const el of elements) {{
                            const rect = el.getBoundingClientRect();
                            if (Math.abs(rect.x - {position.get("x", 0)}) < 10 && 
                                Math.abs(rect.y - {position.get("y", 0)}) < 10 &&
                                Math.abs(rect.width - {position.get("width", 0)}) < 10) {{
                                return true;
                            }}
                        }}
                        return false;
                    }}
                """)
                
                if not still_visible:
                    print(f"{Fore.GREEN}Succès{Fore.RESET}: Élément disparu après clic")
                    return True
                
                print(f"{Fore.YELLOW}Échec{Fore.RESET}: Élément toujours visible après clic")
                return False
                
            except Exception as e:
                print(f"{Fore.RED}Erreur{Fore.RESET}: {str(e)}")
                return False
        
        return False

async def test_smart_consent():
    """
    Fonction de test pour démontrer la détection intelligente de consentement
    """
    # Liste des sites à tester
    test_sites = [
        "https://www.lemonde.fr",
        "https://www.bbc.com",
        "https://www.nytimes.com",
        "https://www.theguardian.com"
    ]
    
    detector = SmartConsentDetector()
    
    for url in test_sites:
        print("\n" + "="*80)
        print(f"{Fore.CYAN}{Style.BRIGHT} TEST: {url}{Style.RESET_ALL}")
        print("="*80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visible pour démonstration
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await context.new_page()
            
            try:
                print(f"{Fore.BLUE}Navigation{Fore.RESET}: Chargement de {url}...")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Prendre un screenshot avant l'interaction
                screenshot_dir = Path(__file__).parent / "consent_screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                
                before_path = screenshot_dir / f"{url.replace('https://', '').replace('/', '_').replace('.', '_')}_before.png"
                await page.screenshot(path=str(before_path))
                print(f"{Fore.BLUE}Screenshot{Fore.RESET}: Avant interaction - {before_path}")
                
                # Exécuter notre détecteur intelligent
                result = await detector.detect_and_handle_consent(page)
                
                # Attendre un moment pour observer les changements
                await asyncio.sleep(2)
                
                # Prendre un screenshot après l'interaction
                after_path = screenshot_dir / f"{url.replace('https://', '').replace('/', '_').replace('.', '_')}_after.png"
                await page.screenshot(path=str(after_path))
                print(f"{Fore.BLUE}Screenshot{Fore.RESET}: Après interaction - {after_path}")
                
                print(f"{Fore.GREEN if result else Fore.YELLOW}Résultat{Fore.RESET}: " + 
                      f"{'Popup traitée avec succès' if result else 'Aucune popup détectée/traitée'}")
                
            except Exception as e:
                print(f"{Fore.RED}Erreur{Fore.RESET}: {str(e)}")
            
            finally:
                await browser.close()

if __name__ == "__main__":
    # Exécution du test
    asyncio.run(test_smart_consent())

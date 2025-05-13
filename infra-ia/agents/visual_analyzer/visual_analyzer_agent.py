#!/usr/bin/env python3
"""
Module d'analyse de sites web intelligent utilisant GPT-4 Vision pour:
1. Détecter les popups de consentement
2. Déterminer leur emplacement et la méthode pour les fermer
3. Vérifier que la fermeture a bien fonctionné
4. Permettre l'analyse du site après suppression des obstacles
"""
import os
import sys
import asyncio
import base64
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from io import BytesIO

import httpx
from openai import OpenAI
from playwright.async_api import async_playwright, Page, Browser
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Initialiser colorama pour les couleurs dans le terminal
init(autoreset=True)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("BerinIA-VisionAnalyzer")

# Chargement des variables d'environnement
load_dotenv()

class VisualAnalyzer:
    """
    Analyseur visuel intelligent utilisant GPT-4 Vision pour:
    1. Détecter et interagir avec les popups de consentement et autres obstacles
    2. Analyser visuellement la structure et le design des sites web
    3. Extraire des métriques de qualité visuelle et professionnalisme
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'analyseur avec les clés API nécessaires.
        
        Args:
            api_key: Clé API OpenAI (optionnel, utilise OPENAI_API_KEY par défaut)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.screenshots_dir = Path(__file__).parent / "vision_screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Système de mémoire pour stocker les analyses précédentes
        self.memory = {}
        
    async def analyze_website(self, url: str) -> Dict[str, Any]:
        """
        Analyse complète d'un site web avec détection de popups.
        
        Args:
            url: URL du site à analyser
            
        Returns:
            Dict contenant les résultats d'analyse
        """
        print(f"{Fore.CYAN}{Style.BRIGHT}ANALYSE INTELLIGENTE DE: {url}{Style.RESET_ALL}")
        print("="*80)
        
        # Formatage du nom de domaine pour les fichiers
        domain = url.replace("https://", "").replace("http://", "").split('/')[0]
        domain_key = domain.replace(".", "-")
        
        results = {
            "url": url,
            "domain": domain,
            "success": False,
            "has_popup": False,
            "popup_removed": False,
            "screenshots": {},
            "analysis": {}
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                device_scale_factor=1
            )
            page = await context.new_page()
            
            try:
                # 1. Navigation et premier screenshot
                print(f"{Fore.BLUE}Navigation{Fore.RESET}: Chargement de {url}...")
                await page.goto(url, wait_until="networkidle", timeout=45000)
                
                # Attendre un peu pour que les popups apparaissent
                await asyncio.sleep(3)
                
                # 2. Premier screenshot
                initial_screenshot_path = str(self.screenshots_dir / f"{domain_key}_initial.png")
                await page.screenshot(path=initial_screenshot_path)
                results["screenshots"]["initial"] = initial_screenshot_path
                print(f"{Fore.GREEN}Screenshot{Fore.RESET}: Capture initiale sauvegardée")
                
                # 3. Analyse avec Vision pour détecter les popups
                initial_analysis = await self._analyze_with_vision(
                    initial_screenshot_path,
                    prompt=self._get_popup_detection_prompt()
                )
                results["analysis"]["initial"] = initial_analysis
                
                # 4. Interpréter les résultats pour déterminer s'il y a un popup
                has_popup, popup_info = self._interpret_popup_analysis(initial_analysis)
                results["has_popup"] = has_popup
                
                if has_popup:
                    print(f"{Fore.YELLOW}Popup détecté{Fore.RESET}: {popup_info.get('description', 'Type inconnu')}")
                    
                    # 5. Tenter de fermer le popup en suivant les instructions
                    popup_removed = await self._handle_popup(page, popup_info)
                    results["popup_removed"] = popup_removed
                    
                    if popup_removed:
                        print(f"{Fore.GREEN}Succès{Fore.RESET}: Popup fermé avec succès")
                        
                        # 6. Capture après fermeture
                        clean_screenshot_path = str(self.screenshots_dir / f"{domain_key}_clean.png")
                        await asyncio.sleep(1)  # Attendre que tout soit stabilisé
                        await page.screenshot(path=clean_screenshot_path)
                        results["screenshots"]["clean"] = clean_screenshot_path
                        
                        # 7. Vérification avec Vision
                        verification_analysis = await self._analyze_with_vision(
                            clean_screenshot_path,
                            prompt=self._get_verification_prompt(popup_info)
                        )
                        results["analysis"]["verification"] = verification_analysis
                        
                        # Confirmer la suppression
                        popup_gone = self._confirm_popup_removal(verification_analysis)
                        results["popup_confirmed_gone"] = popup_gone
                        
                        if popup_gone:
                            print(f"{Fore.GREEN}Vérification{Fore.RESET}: Popup confirmé comme supprimé")
                        else:
                            print(f"{Fore.RED}Vérification{Fore.RESET}: Popup toujours présent ou partiellement visible")
                    else:
                        print(f"{Fore.RED}Échec{Fore.RESET}: Impossible de fermer le popup")
                else:
                    print(f"{Fore.GREEN}Aucun popup{Fore.RESET}: Aucun obstacle détecté")
                
                # 8. Analyse complète du site
                print(f"{Fore.BLUE}Analyse finale{Fore.RESET}: Analyse du contenu du site...")
                final_screenshot_path = str(self.screenshots_dir / f"{domain_key}_final.png")
                await page.screenshot(path=final_screenshot_path, full_page=True)
                results["screenshots"]["final"] = final_screenshot_path
                
                site_analysis = await self._analyze_with_vision(
                    final_screenshot_path,
                    prompt=self._get_site_analysis_prompt(url)
                )
                results["analysis"]["site"] = site_analysis
                results["site_content"] = self._extract_site_info(site_analysis)
                
                # Succès global
                results["success"] = True
                
            except Exception as e:
                error_message = f"Erreur lors de l'analyse: {str(e)}"
                print(f"{Fore.RED}Erreur{Fore.RESET}: {error_message}")
                results["error"] = error_message
                
                # Capturer l'état actuel si possible
                try:
                    error_screenshot_path = str(self.screenshots_dir / f"{domain_key}_error.png")
                    await page.screenshot(path=error_screenshot_path)
                    results["screenshots"]["error"] = error_screenshot_path
                except:
                    pass
            
            finally:
                await browser.close()
        
        # Afficher un résumé des résultats
        self._print_analysis_summary(results)
        
        # Enregistrer les résultats dans la mémoire
        self.memory[domain] = results
        
        return results
    
    async def _analyze_with_vision(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        Analyse une image avec GPT-4 Vision.
        
        Args:
            image_path: Chemin vers l'image à analyser
            prompt: Instructions pour l'analyse
            
        Returns:
            Dict contenant les résultats d'analyse
        """
        print(f"{Fore.BLUE}Vision AI{Fore.RESET}: Analyse de l'image...")
        
        try:
            # Lire l'image et l'encoder en base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Création de la requête à l'API
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {
                        "role": "system",
                        "content": "Vous êtes un analyste expert en interfaces web qui examine des captures d'écran de sites web."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            # Traiter la réponse
            analysis_text = response.choices[0].message.content
            
            # Tenter d'extraire un JSON de la réponse si présent
            json_data = self._extract_json_from_text(analysis_text)
            
            if json_data:
                return {
                    "structured": json_data,
                    "raw": analysis_text
                }
            else:
                return {
                    "structured": None,
                    "raw": analysis_text
                }
            
        except Exception as e:
            print(f"{Fore.RED}Erreur API Vision{Fore.RESET}: {str(e)}")
            return {
                "error": str(e),
                "raw": None,
                "structured": None
            }
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """
        Extrait un JSON d'un texte libre, si présent.
        
        Args:
            text: Le texte à analyser
            
        Returns:
            Dict ou None si aucun JSON valide n'est trouvé
        """
        try:
            # Chercher des séquences potentielles de JSON
            potential_json = ""
            in_json = False
            
            # Repérer un bloc de code JSON (entre ```, ```json ou {})
            lines = text.split('\n')
            
            # Méthode 1: Chercher entre ```
            json_block = []
            in_code_block = False
            for line in lines:
                if "```" in line and not in_code_block:
                    in_code_block = True
                    continue
                elif "```" in line and in_code_block:
                    in_code_block = False
                    break
                elif in_code_block:
                    json_block.append(line)
            
            if json_block:
                try:
                    return json.loads('\n'.join(json_block))
                except:
                    pass
            
            # Méthode 2: Chercher un objet JSON directement (entre accolades)
            try:
                # Trouver la première accolade ouvrante et la dernière fermante
                start_idx = text.find('{')
                end_idx = text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    json_str = text[start_idx:end_idx+1]
                    return json.loads(json_str)
            except:
                pass
            
            # Si aucune méthode n'a fonctionné, retourner None
            return None
            
        except Exception as e:
            print(f"{Fore.RED}Erreur d'extraction JSON{Fore.RESET}: {str(e)}")
            return None
    
    def _get_popup_detection_prompt(self) -> str:
        """
        Génère le prompt pour détecter les popups.
        
        Returns:
            Prompt formaté
        """
        return """
        Vous êtes un expert en analyse de popups de consentement pour sites web. Examinez attentivement cette capture d'écran.
        
        TÂCHE PRIORITAIRE: 
        1. Déterminer s'il y a un popup ou une bannière de consentement qui bloque l'accès au contenu
        2. Si oui, identifier EXACTEMENT où l'utilisateur devrait cliquer pour accepter ou fermer ce popup
        
        INSTRUCTIONS PRÉCISES:
        - Fournir les coordonnées pixel exactes (x,y) où cliquer pour fermer ou accepter le popup
        - Décrire précisément le texte visible sur le bouton d'acceptation
        - Indiquer l'endroit exact où le bouton se trouve (ex: en bas à droite du popup, centré, etc.)
        - Si plusieurs options existent, indiquer uniquement la plus directe pour accepter/continuer
        
        IMPORTANT: Si plusieurs boutons sont présents, privilégiez toujours celui avec des textes comme:
        "Accepter", "Accepter tout", "Accepter et continuer", "J'accepte", "OK", "Continuer", "Got it", etc.
        
        Si aucun popup n'est présent, indiquez-le clairement.
        
        Répondre OBLIGATOIREMENT au format JSON structuré suivant:
        {
            "has_popup": true/false,
            "popup_type": "type précis de popup", 
            "close_button_text": "texte exact sur le bouton à cliquer",
            "close_coordinates": {"x": X_EXACT, "y": Y_EXACT},
            "close_button_location": "description précise de l'emplacement",
            "description": "description complète et détaillée",
            "confidence": 0-100
        }
        """
    
    def _get_verification_prompt(self, popup_info: Dict[str, Any]) -> str:
        """
        Génère le prompt pour vérifier si un popup a bien été supprimé.
        
        Args:
            popup_info: Informations sur le popup détecté précédemment
            
        Returns:
            Prompt formaté
        """
        popup_description = popup_info.get('description', 'un popup')
        popup_type = popup_info.get('popup_type', 'élément')
        
        return f"""
        Vérifier si {popup_description} a été correctement supprimé de la page.
        
        Précédemment, j'ai détecté: {popup_type} à la position approximative 
        x={popup_info.get('popup_coordinates', {}).get('x', 'inconnu')}, 
        y={popup_info.get('popup_coordinates', {}).get('y', 'inconnu')}.
        
        Indiquer clairement si cet élément est:
        1. Complètement supprimé (plus visible du tout)
        2. Partiellement visible (réduit, déplacé, etc.)
        3. Toujours entièrement visible (aucun changement)
        
        Répondre au format JSON avec la structure suivante:
        {{
            "popup_removed": true/false,
            "removal_status": "complete/partial/none",
            "description": "description détaillée",
            "confidence": 0-100,
            "remaining_elements": ["élément1", "élément2"] (si applicable)
        }}
        """
    
    def _get_site_analysis_prompt(self, url: str) -> str:
        """
        Génère le prompt pour l'analyse complète du site.
        
        Args:
            url: URL du site analysé
            
        Returns:
            Prompt formaté
        """
        return f"""
        Analyser cette capture d'écran du site {url} et fournir une évaluation complète:
        
        1. Type de site (e-commerce, blog, site corporate, etc.)
        2. Qualité visuelle générale (échelle de 1-10)
        3. Éléments principaux visibles (navigation, en-tête, pied de page, etc.)
        4. Points forts visuels et ergonomiques
        5. Points faibles ou problèmes détectés
        6. Estimation du niveau de professionnalisme (échelle de 1-10)
        7. Technologies potentiellement utilisées (framework UI, etc.)
        
        Répondre au format JSON avec la structure suivante:
        {{
            "site_type": "type de site",
            "visual_quality": 1-10,
            "key_elements": ["élément1", "élément2", ...],
            "strengths": ["force1", "force2", ...],
            "weaknesses": ["faiblesse1", "faiblesse2", ...],
            "professionalism": 1-10,
            "technologies": ["tech1", "tech2", ...],
            "description": "description synthétique",
            "content_focus": "sujet principal du site",
            "target_audience": "audience visée"
        }}
        """
    
    def _interpret_popup_analysis(self, analysis: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Interprète les résultats de l'analyse pour déterminer s'il y a un popup.
        
        Args:
            analysis: Résultats de l'analyse par Vision
            
        Returns:
            Tuple contenant:
                - Boolean indiquant si un popup est présent
                - Dict avec les informations sur le popup
        """
        popup_info = {}
        
        # Imprimer l'analyse brute pour debug
        print(f"{Fore.CYAN}Analyse brute:{Fore.RESET}")
        raw_text = analysis.get('raw', '')
        print(raw_text[:200] + "..." if len(raw_text) > 200 else raw_text)
        
        # Vérifier si l'analyse structurée est disponible
        if analysis.get('structured'):
            structured_data = analysis['structured']
            print(f"{Fore.CYAN}Données structurées:{Fore.RESET}")
            print(json.dumps(structured_data, indent=2))
            
            has_popup = structured_data.get('has_popup', False)
            
            if has_popup:
                popup_info = structured_data
                
                # S'assurer que close_coordinates est correctement formaté
                if "close_coordinates" in popup_info and isinstance(popup_info["close_coordinates"], dict):
                    x = popup_info["close_coordinates"].get("x", 0)
                    y = popup_info["close_coordinates"].get("y", 0)
                    print(f"{Fore.GREEN}Coordonnées de clic détectées:{Fore.RESET} x={x}, y={y}")
                    
                # S'assurer que close_button_text est présent
                if "close_button_text" in popup_info:
                    print(f"{Fore.GREEN}Texte du bouton:{Fore.RESET} {popup_info['close_button_text']}")
        else:
            # Analyse par mots-clés dans la réponse textuelle
            raw_text = raw_text.lower()
            
            # Phrases indiquant qu'il y a un popup
            popup_indicators = [
                "popup est présent",
                "bannière est visible",
                "popup de consentement",
                "bannière de cookies",
                "consent dialog",
                "cookie banner",
                "popup detected",
                "il y a un popup",
                "obstruction détectée"
            ]
            
            # Phrases indiquant qu'il n'y a pas de popup
            no_popup_indicators = [
                "aucun popup",
                "pas de popup",
                "page est propre",
                "no popup",
                "no consent dialog",
                "page is clean",
                "pas d'élément obstructif"
            ]
            
            # Déterminer si un popup est présent
            has_popup = any(indicator in raw_text for indicator in popup_indicators)
            
            # Si des indicateurs contradictoires sont présents, privilégier l'absence de popup
            if any(indicator in raw_text for indicator in no_popup_indicators):
                has_popup = False
            
            # Extraire des informations sur le popup si présent
            if has_popup:
                popup_info = {
                    "has_popup": True,
                    "popup_type": "indéterminé",
                    "description": "Un élément obstructif est présent sur la page"
                }
                
                # Tenter d'extraire des coordonnées si présentes dans le texte
                import re
                
                # Chercher des coordonnées x,y
                coords_match = re.search(r'coordonnées.*?[xX]\s*[=:]\s*(\d+).*?[yY]\s*[=:]\s*(\d+)', raw_text, re.DOTALL)
                if coords_match:
                    x, y = coords_match.groups()
                    popup_info["close_coordinates"] = {"x": int(x), "y": int(y)}
                    print(f"{Fore.GREEN}Coordonnées extraites du texte:{Fore.RESET} x={x}, y={y}")
                
                # Chercher du texte de bouton
                button_match = re.search(r'bouton.*?["\']([^"\']+)["\']', raw_text, re.DOTALL | re.IGNORECASE)
                if button_match:
                    popup_info["close_button_text"] = button_match.group(1)
                    print(f"{Fore.GREEN}Texte du bouton extrait:{Fore.RESET} {popup_info['close_button_text']}")
        
        return has_popup, popup_info
    
    async def _handle_popup(self, page: Page, popup_info: Dict[str, Any]) -> bool:
        """
        Tente de fermer un popup par analyse HTML intelligente.
        
        Args:
            page: Page Playwright
            popup_info: Informations sur le popup
            
        Returns:
            Boolean indiquant si l'opération a réussi
        """
        print(f"{Fore.BLUE}Interaction{Fore.RESET}: Tentative de suppression du popup par analyse HTML...")
        
        try:
            # Approche 1: Analyse HTML complète pour trouver des boutons d'acceptation
            print(f"{Fore.BLUE}Méthode{Fore.RESET}: Analyse HTML complète")
            
            # Utiliser JavaScript pour trouver et cliquer sur le bouton d'acceptation
            accept_result = await page.evaluate("""
                () => {
                    // Créer un score pour chaque élément cliquable
                    function scoreElement(element) {
                        if (!element) return 0;
                        
                        let score = 0;
                        const text = (element.innerText || element.textContent || element.value || '').toLowerCase();
                        const attributes = element.attributes ? Array.from(element.attributes).map(a => `${a.name}=${a.value}`).join(' ').toLowerCase() : '';
                        
                        // Mots-clés d'acceptation par importance
                        const textKeywords = [
                            {words: ['accepter et continuer', 'accept and continue'], value: 100},
                            {words: ['accepter tout', 'accept all'], value: 90},
                            {words: ['j\\'accepte', 'i accept', 'jaccepte'], value: 80},
                            {words: ['accepter', 'accept'], value: 70},
                            {words: ['continuer', 'continue'], value: 60},
                            {words: ['ok', 'agree', 'got it'], value: 50},
                            {words: ['fermer', 'close'], value: 40}
                        ];
                        
                        // Vérifier le texte pour des correspondances
                        for (const keyword of textKeywords) {
                            if (keyword.words.some(word => text.includes(word))) {
                                score += keyword.value;
                                break;
                            }
                        }
                        
                        // Types d'éléments
                        if (element.tagName.toLowerCase() === 'button') score += 30;
                        if (element.role === 'button' || attributes.includes('role=button')) score += 25;
                        if (element.tagName.toLowerCase() === 'a') score += 15;
                        if (element.tagName.toLowerCase() === 'input' && 
                           (element.type === 'button' || element.type === 'submit')) score += 20;
                        
                        // Attributs pertinents
                        if (attributes.includes('consent') || 
                            attributes.includes('cookie') || 
                            attributes.includes('accept') || 
                            attributes.includes('agree')) score += 25;
                        
                        // Visibilité et taille
                        const style = window.getComputedStyle(element);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && 
                            parseFloat(style.opacity) > 0.5) score += 20;
                        
                        // Position (préférer les éléments vers le bas des popups)
                        const rect = element.getBoundingClientRect();
                        if (rect.width > 30 && rect.height > 15) score += 10;  // Taille minimale décente
                        
                        return score;
                    }
                    
                    // Trouver tous les éléments cliquables
                    const clickableElements = [
                        ...document.querySelectorAll('button'),
                        ...document.querySelectorAll('a'),
                        ...document.querySelectorAll('[role="button"]'),
                        ...document.querySelectorAll('input[type="button"]'),
                        ...document.querySelectorAll('input[type="submit"]')
                    ];
                    
                    // Évaluer et scorer chaque élément
                    const scoredElements = clickableElements
                        .map(el => ({element: el, score: scoreElement(el)}))
                        .filter(item => item.score > 30)  // Ne garder que ceux avec un score minimum
                        .sort((a, b) => b.score - a.score);  // Trier par score décroissant
                    
                    console.log('Éléments trouvés:', scoredElements.length);
                    
                    // Cliquer sur l'élément avec le meilleur score s'il existe
                    if (scoredElements.length > 0) {
                        const best = scoredElements[0];
                        const text = best.element.innerText || best.element.textContent || best.element.value || '';
                        console.log('Meilleur élément:', text, 'Score:', best.score);
                        
                        // Simuler un clic
                        best.element.click();
                        return {success: true, text: text, score: best.score};
                    }
                    
                    return {success: false};
                }
            """)
            
            if accept_result.get('success', False):
                print(f"{Fore.GREEN}Succès analyse HTML{Fore.RESET}: Bouton '{accept_result.get('text', 'inconnu')}' cliqué (score: {accept_result.get('score', 0)})")
                await asyncio.sleep(2)  # Attendre que le popup disparaisse
                
                # Vérifier que le popup a disparu
                popup_gone = await page.evaluate("""
                    () => {
                        // Vérifier si des éléments liés aux cookies sont encore visibles
                        const cookieTexts = ['cookie', 'consent', 'gdpr', 'rgpd', 'accepter', 'accept'];
                        const visibleElements = Array.from(document.querySelectorAll('div, section, aside, dialog'));
                        
                        // Si le nombre d'éléments avec texte lié aux cookies a diminué, considérer le popup comme supprimé
                        return !visibleElements.some(el => {
                            if (el.style.display === 'none' || el.style.visibility === 'hidden') return false;
                            const text = el.innerText && el.innerText.toLowerCase();
                            return text && cookieTexts.some(t => text.includes(t));
                        });
                    }
                """)
                
                if popup_gone:
                    print(f"{Fore.GREEN}Vérification{Fore.RESET}: Popup supprimé avec succès")
                    return True
                else:
                    print(f"{Fore.YELLOW}Avertissement{Fore.RESET}: Popup peut-être toujours présent malgré le clic")
            
            # Approche 2: Si le texte du bouton est connu, recherche directe
            if "close_button_text" in popup_info and popup_info["close_button_text"]:
                button_text = popup_info["close_button_text"]
                print(f"{Fore.BLUE}Méthode{Fore.RESET}: Recherche par texte exact '{button_text}'")
                
                # Utiliser JavaScript pour trouver et cliquer sur le bouton avec ce texte
                text_result = await page.evaluate(f"""
                    () => {{
                        const targetText = "{button_text}";
                        
                        // Fonction qui vérifie si le texte d'un élément correspond approximativement
                        function textMatches(element) {{
                            const text = (element.innerText || element.textContent || element.value || '').trim();
                            return text.includes(targetText) || 
                                  targetText.includes(text) || 
                                  text.toLowerCase() === targetText.toLowerCase();
                        }}
                        
                        // Trouver tous les éléments cliquables
                        const clickableElements = [
                            ...document.querySelectorAll('button'),
                            ...document.querySelectorAll('a'),
                            ...document.querySelectorAll('[role="button"]'),
                            ...document.querySelectorAll('input[type="button"]'),
                            ...document.querySelectorAll('input[type="submit"]')
                        ];
                        
                        // Chercher un élément avec le texte exact
                        const exactMatch = clickableElements.find(el => textMatches(el));
                        
                        if (exactMatch) {{
                            console.log('Élément correspondant trouvé:', exactMatch.innerText || exactMatch.textContent);
                            exactMatch.click();
                            return true;
                        }}
                        
                        return false;
                    }}
                """)
                
                if text_result:
                    print(f"{Fore.GREEN}Succès recherche texte{Fore.RESET}: Bouton avec texte '{button_text}' trouvé et cliqué")
                    await asyncio.sleep(2)
                    return True
            
            # Approche 3: Si des coordonnées sont disponibles, dernier recours avec clic à cet endroit
            if "close_coordinates" in popup_info and popup_info["close_coordinates"]:
                x = popup_info["close_coordinates"].get("x", 0)
                y = popup_info["close_coordinates"].get("y", 0)
                
                print(f"{Fore.BLUE}Méthode{Fore.RESET}: Clic direct aux coordonnées fournies ({x}, {y})")
                await page.mouse.click(x, y)
                await asyncio.sleep(2)  # Attendre pour voir si ça a fonctionné
                
                # Vérifier si le popup est toujours visible
                popup_gone = await page.evaluate("""
                    () => {
                        // Vérifier si des éléments liés aux cookies sont encore visibles
                        const cookieTexts = ['cookie', 'consent', 'gdpr', 'rgpd', 'accepter', 'accept'];
                        const visibleElements = Array.from(document.querySelectorAll('div, section, aside, dialog'));
                        
                        return !visibleElements.some(el => {
                            if (el.style.display === 'none' || el.style.visibility === 'hidden') return false;
                            const text = el.innerText && el.innerText.toLowerCase();
                            return text && cookieTexts.some(t => text.includes(t));
                        });
                    }
                """)
                
                if popup_gone:
                    print(f"{Fore.GREEN}Vérification{Fore.RESET}: Popup supprimé après clic aux coordonnées")
                    return True
            
            # Si toutes les méthodes ont échoué
            print(f"{Fore.RED}Échec{Fore.RESET}: Aucune méthode n'a permis de fermer le popup")
            return False
            
        except Exception as e:
            print(f"{Fore.RED}Erreur{Fore.RESET}: {str(e)}")
            return False
    
    def _confirm_popup_removal(self, verification_analysis: Dict[str, Any]) -> bool:
        """
        Confirme si un popup a bien été supprimé.
        
        Args:
            verification_analysis: Résultats de l'analyse de vérification
            
        Returns:
            Boolean indiquant si le popup a été supprimé
        """
        # Vérifier si l'analyse structurée est disponible
        if verification_analysis.get('structured'):
            data = verification_analysis['structured']
            return data.get('popup_removed', False)
        else:
            # Analyse par mots-clés dans la réponse textuelle
            raw_text = verification_analysis.get('raw', '').lower()
            
            # Phrases indiquant que le popup a été supprimé
            removed_indicators = [
                "popup supprimé",
                "popup a été supprimé",
                "popup removed",
                "no longer visible",
                "plus visible",
                "complètement disparu",
                "completely removed",
                "successfully removed",
                "suppression réussie"
            ]
            
            # Phrases indiquant que le popup est toujours présent
            still_present_indicators = [
                "popup toujours présent",
                "popup still present",
                "still visible",
                "toujours visible",
                "not removed",
                "non supprimé"
            ]
            
            # Déterminer si le popup a été supprimé
            is_removed = any(indicator in raw_text for indicator in removed_indicators)
            
            # Si des indicateurs contradictoires sont présents, privilégier la présence du popup
            if any(indicator in raw_text for indicator in still_present_indicators):
                is_removed = False
            
            return is_removed
    
    def _extract_site_info(self, site_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait les informations pertinentes de l'analyse du site.
        
        Args:
            site_analysis: Résultats de l'analyse du site
            
        Returns:
            Dict d'informations pertinentes
        """
        # Si l'analyse structurée est disponible
        if site_analysis.get('structured'):
            return site_analysis['structured']
        else:
            # Analyse par recherche de phrases-clés
            info = {
                "site_type": "indéterminé",
                "visual_quality": 5,
                "professionalism": 5,
                "key_elements": [],
                "strengths": [],
                "weaknesses": [],
                "description": "Analyse textuelle limitée"
            }
            
            raw_text = site_analysis.get('raw', '')
            
            # Extraire le type de site
            site_types = {
                "e-commerce": ["e-commerce", "boutique en ligne", "shop", "achat", "vente", "panier"],
                "blog": ["blog", "article", "post"],
                "corporate": ["corporate", "entreprise", "société", "company", "business"],
                "portfolio": ["portfolio", "showcase", "vitrine", "travaux", "works"],
                "média": ["actualité", "news", "presse", "journal", "magazine"]
            }
            
            for site_type, keywords in site_types.items():
                if any(kw in raw_text.lower() for kw in keywords):
                    info["site_type"] = site_type
                    break
            
            # Extraire le score de qualité visuelle
            import re
            quality_match = re.search(r'qualité visuelle.*?(\d+)[/\s]*10', raw_text, re.IGNORECASE)
            if quality_match:
                try:
                    info["visual_quality"] = int(quality_match.group(1))
                except:
                    pass
            
            # Extraire le niveau de professionnalisme
            prof_match = re.search(r'professionnalisme.*?(\d+)[/\s]*10', raw_text, re.IGNORECASE)
            if prof_match:
                try:
                    info["professionalism"] = int(prof_match.group(1))
                except:
                    pass
            
            # Extraire la description
            # Chercher une phrase qui résume le site
            description_patterns = [
                r'le site est (.*?)\.',
                r'il s\'agit d\'(.*?)\.',
                r'ce site (.*?)\.',
                r'en résumé, (.*?)\.',
                r'synthèse: (.*?)\.'
            ]
            
            for pattern in description_patterns:
                desc_match = re.search(pattern, raw_text, re.IGNORECASE)
                if desc_match:
                    info["description"] = desc_match.group(1).strip()
                    break
            
            return info
    
    def _print_analysis_summary(self, results: Dict[str, Any]) -> None:
        """
        Affiche un résumé des résultats d'analyse.
        
        Args:
            results: Résultats de l'analyse
        """
        print("\n" + "="*80)
        print(f"{Fore.CYAN}{Style.BRIGHT} RÉSUMÉ DE L'ANALYSE: {results.get('url')}{Style.RESET_ALL}")
        print("="*80)
        
        # Popups
        if results.get("has_popup", False):
            if results.get("popup_removed", False):
                print(f"{Fore.GREEN}✓ Popup détecté et supprimé avec succès")
            else:
                print(f"{Fore.RED}✗ Popup détecté mais n'a pas pu être supprimé")
        else:
            print(f"{Fore.GREEN}✓ Aucun popup détecté")
        
        # Site info
        site_content = results.get("site_content", {})
        if site_content:
            print(f"\n{Fore.YELLOW}INFORMATIONS SUR LE SITE:")
            print(f"{Fore.BLUE}Type: {Fore.WHITE}{site_content.get('site_type', 'Indéterminé')}")
            
            visual_quality = site_content.get('visual_quality', 0)
            quality_color = Fore.GREEN if visual_quality >= 7 else (Fore.YELLOW if visual_quality >= 5 else Fore.RED)
            print(f"{Fore.BLUE}Qualité visuelle: {quality_color}{visual_quality}/10")
            
            prof_level = site_content.get('professionalism', 0)
            prof_color = Fore.GREEN if prof_level >= 7 else (Fore.YELLOW if prof_level >= 5 else Fore.RED)
            print(f"{Fore.BLUE}Niveau de professionnalisme: {prof_color}{prof_level}/10")
            
            if site_content.get('description'):
                print(f"\n{Fore.BLUE}Description: {Fore.WHITE}{site_content.get('description')}")
            
            # Forces et faiblesses
            strengths = site_content.get('strengths', [])
            if strengths:
                print(f"\n{Fore.GREEN}Forces:")
                for strength in strengths[:3]:  # Afficher les 3 premières forces
                    print(f"{Fore.GREEN}✓ {strength}")
            
            weaknesses = site_content.get('weaknesses', [])
            if weaknesses:
                print(f"\n{Fore.RED}Faiblesses:")
                for weakness in weaknesses[:3]:  # Afficher les 3 premières faiblesses
                    print(f"{Fore.RED}✗ {weakness}")
        
        # Chemins des captures d'écran
        screenshots = results.get("screenshots", {})
        if screenshots:
            print(f"\n{Fore.YELLOW}CAPTURES D'ÉCRAN:")
            for screenshot_type, path in screenshots.items():
                print(f"{Fore.BLUE}{screenshot_type}: {Fore.WHITE}{path}")
        
        print("\n" + "="*80)


# Code de test pour exécuter l'analyseur
async def test_analyzer(urls):
    """
    Fonction de test pour l'analyseur de sites web.
    
    Args:
        urls: Liste d'URLs à analyser
    """
    analyzer = VisualAnalyzer()
    
    for url in urls:
        await analyzer.analyze_website(url)
        print("\n")
        print(f"{Fore.CYAN}Appuyez sur Entrée pour continuer vers le site suivant...{Fore.RESET}")
        input()

if __name__ == "__main__":
    # URLs à analyser
    test_urls = [
        "https://www.lemonde.fr",
        "https://www.nytimes.com",
        "https://www.amazon.fr",
        "https://www.bbc.com"
    ]
    
    print(f"{Fore.YELLOW}BerinIA - Analyseur intelligent de sites web{Fore.RESET}")
    print(f"{Fore.YELLOW}Utilisation de GPT-4 Vision pour détecter et gérer les popups{Fore.RESET}")
    print("="*80)
    
    # Si des arguments sont passés, les utiliser comme URLs
    if len(sys.argv) > 1:
        test_urls = sys.argv[1:]
    
    try:
        asyncio.run(test_analyzer(test_urls))
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Analyse interrompue par l'utilisateur.{Fore.RESET}")
    except Exception as e:
        print(f"\n{Fore.RED}Erreur lors de l'exécution de l'analyse: {str(e)}{Fore.RESET}")

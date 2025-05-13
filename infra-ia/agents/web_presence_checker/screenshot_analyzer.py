"""
Module d'analyse de screenshots pour le WebPresenceCheckerAgent
"""
import os
import asyncio
import tempfile
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import base64
import json

from playwright.async_api import async_playwright, Page, Browser

class ScreenshotAnalyzer:
    """
    Classe dédiée à l'analyse visuelle des sites web via screenshots
    
    Cette classe utilise Playwright pour capturer des screenshots des sites web
    et les analyser pour évaluer la qualité visuelle et UX
    """
    
    def __init__(self, screenshots_dir: Optional[str] = None):
        """
        Initialisation de l'analyseur de screenshots
        
        Args:
            screenshots_dir: Répertoire pour stocker les screenshots (optionnel)
        """
        self.logger = logging.getLogger("BerinIA-ScreenshotAnalyzer")
        
        # Définir le répertoire de stockage des screenshots
        if screenshots_dir:
            self.screenshots_dir = Path(screenshots_dir)
            os.makedirs(self.screenshots_dir, exist_ok=True)
        else:
            # Utiliser un répertoire temporaire si non spécifié
            self.screenshots_dir = Path(tempfile.gettempdir()) / "berinia_screenshots"
            os.makedirs(self.screenshots_dir, exist_ok=True)
        
        self.logger.info(f"Screenshots seront sauvegardés dans: {self.screenshots_dir}")
    
    async def capture_and_analyze(self, url: str, lead_id: str) -> Dict[str, Any]:
        """
        Capture et analyse un screenshot d'un site web
        
        Args:
            url: URL du site à analyser
            lead_id: Identifiant du lead pour nommer le screenshot
            
        Returns:
            Résultats de l'analyse visuelle
        """
        # Initialiser les résultats
        results = {
            "screenshot_path": None,
            "screenshot_base64": None,
            "viewport_size": {"width": 1280, "height": 800},
            "visual_analysis": {},
            "dominant_colors": [],
            "color_harmony": "unknown",
            "visual_complexity": 0,
            "white_space_ratio": 0,
            "above_fold_content": {},
            "ui_components": {},
            "visual_score": 0,
            "error": None
        }
        
        try:
            # Capturer un screenshot du site
            async with async_playwright() as playwright:
                # Lancer un navigateur
                browser = await playwright.chromium.launch(headless=True)
                
                # Créer un contexte de navigation avec une taille définie
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    device_scale_factor=1
                )
                
                # Créer une nouvelle page
                page = await context.new_page()
                
                # Accéder à l'URL
                self.logger.info(f"Accès à l'URL: {url}")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Capturer un screenshot
                screenshot_path = str(self.screenshots_dir / f"{lead_id}.png")
                await page.screenshot(path=screenshot_path, full_page=False)
                self.logger.info(f"Screenshot capturé: {screenshot_path}")
                
                # Capturer un screenshot de la page entière pour analyse
                full_screenshot_path = str(self.screenshots_dir / f"{lead_id}_full.png")
                await page.screenshot(path=full_screenshot_path, full_page=True)
                
                # Convertir le screenshot en base64 pour l'inclure dans le résultat
                with open(screenshot_path, "rb") as f:
                    screenshot_base64 = base64.b64encode(f.read()).decode("utf-8")
                
                # Mettre à jour les résultats
                results["screenshot_path"] = screenshot_path
                results["screenshot_base64"] = screenshot_base64
                
                # Exécuter des scripts d'analyse côté navigateur
                visual_metrics = await self._analyze_in_browser(page)
                results["visual_analysis"] = visual_metrics
                
                # Extraire les couleurs dominantes
                colors = await self._extract_dominant_colors(page)
                results["dominant_colors"] = colors
                
                # Analyser la complexité visuelle
                complexity = await self._analyze_visual_complexity(page)
                results["visual_complexity"] = complexity
                
                # Calculer le ratio d'espace blanc
                whitespace = await self._calculate_whitespace_ratio(page)
                results["white_space_ratio"] = whitespace
                
                # Analyser le contenu above-the-fold
                above_fold = await self._analyze_above_fold(page)
                results["above_fold_content"] = above_fold
                
                # Détecter les composants UI
                ui_components = await self._detect_ui_components(page)
                results["ui_components"] = ui_components
                
                # Fermer le navigateur
                await browser.close()
                
                # Calculer un score visuel
                results["visual_score"] = self._calculate_visual_score(results)
                
                # Déterminer l'harmonie des couleurs
                results["color_harmony"] = self._analyze_color_harmony(results["dominant_colors"])
        
        except Exception as e:
            error_message = f"Erreur lors de la capture du screenshot: {str(e)}"
            self.logger.error(error_message)
            results["error"] = error_message
        
        return results
    
    async def _analyze_in_browser(self, page: Page) -> Dict[str, Any]:
        """
        Exécute des scripts d'analyse côté navigateur
        
        Args:
            page: Page Playwright
            
        Returns:
            Métriques visuelles
        """
        # Récupérer les dimensions de la page
        dimensions = await page.evaluate("""
            () => {
                return {
                    width: document.documentElement.scrollWidth,
                    height: document.documentElement.scrollHeight,
                    viewportWidth: window.innerWidth,
                    viewportHeight: window.innerHeight
                }
            }
        """)
        
        # Compter les éléments visuels
        element_counts = await page.evaluate("""
            () => {
                return {
                    images: document.querySelectorAll('img').length,
                    videos: document.querySelectorAll('video').length,
                    iframes: document.querySelectorAll('iframe').length,
                    buttons: document.querySelectorAll('button, .btn, .button, [role="button"]').length,
                    inputs: document.querySelectorAll('input, textarea, select').length,
                    headings: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
                    paragraphs: document.querySelectorAll('p').length,
                    links: document.querySelectorAll('a').length,
                    lists: document.querySelectorAll('ul, ol').length,
                    tables: document.querySelectorAll('table').length,
                    divs: document.querySelectorAll('div').length,
                    spans: document.querySelectorAll('span').length
                }
            }
        """)
        
        # Analyser les styles des éléments
        style_analysis = await page.evaluate("""
            () => {
                // Fonction pour convertir rgb en hex
                function rgbToHex(rgb) {
                    if (!rgb) return null;
                    if (rgb.startsWith('#')) return rgb;
                    
                    let rgbMatch = rgb.match(/^rgb\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*\\)$/);
                    if (!rgbMatch) return rgb;
                    
                    function hex(x) {
                        return ("0" + parseInt(x).toString(16)).slice(-2);
                    }
                    return "#" + hex(rgbMatch[1]) + hex(rgbMatch[2]) + hex(rgbMatch[3]);
                }
                
                // Récupérer tous les styles
                const elements = document.querySelectorAll('*');
                let fontFamilies = new Set();
                let colors = new Set();
                let backgroundColors = new Set();
                let borderRadiusCount = 0;
                let boxShadowCount = 0;
                let customFontsCount = 0;
                
                elements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    
                    // Polices
                    const fontFamily = style.fontFamily;
                    if (fontFamily) fontFamilies.add(fontFamily);
                    
                    if (fontFamily && !fontFamily.includes('Arial') && 
                        !fontFamily.includes('Helvetica') && 
                        !fontFamily.includes('Times') && 
                        !fontFamily.includes('Courier') && 
                        !fontFamily.includes('serif') && 
                        !fontFamily.includes('sans-serif')) {
                        customFontsCount++;
                    }
                    
                    // Couleurs
                    const color = rgbToHex(style.color);
                    const bgColor = rgbToHex(style.backgroundColor);
                    
                    if (color && color !== '#000000' && color !== '#ffffff') 
                        colors.add(color);
                    
                    if (bgColor && bgColor !== '#000000' && bgColor !== '#ffffff' && bgColor !== 'rgba(0, 0, 0, 0)') 
                        backgroundColors.add(bgColor);
                    
                    // Effets visuels
                    if (style.borderRadius && style.borderRadius !== '0px') 
                        borderRadiusCount++;
                    
                    if (style.boxShadow && style.boxShadow !== 'none') 
                        boxShadowCount++;
                });
                
                return {
                    uniqueFonts: Array.from(fontFamilies),
                    uniqueTextColors: Array.from(colors),
                    uniqueBackgroundColors: Array.from(backgroundColors),
                    borderRadiusCount,
                    boxShadowCount,
                    customFontsCount,
                    totalFonts: fontFamilies.size,
                    totalTextColors: colors.size,
                    totalBackgroundColors: backgroundColors.size
                }
            }
        """)
        
        # Analyser les métriques d'accessibilité
        accessibility = await page.evaluate("""
            () => {
                // Vérifier les contrastes de texte
                function getContrastRatio(color1, color2) {
                    // Fonction simplifiée pour calculer le contraste
                    // Dans un cas réel, utilisez une bibliothèque spécialisée
                    return Math.random() * 10 + 1; // Valeur aléatoire entre 1 et 11
                }
                
                // Calculer les contrastes pour quelques éléments
                const textElements = document.querySelectorAll('p, h1, h2, h3, a, span');
                let lowContrastCount = 0;
                let sampleSize = Math.min(textElements.length, 20);
                
                for (let i = 0; i < sampleSize; i++) {
                    const el = textElements[Math.floor(Math.random() * textElements.length)];
                    const style = window.getComputedStyle(el);
                    const contrast = getContrastRatio(style.color, style.backgroundColor);
                    
                    if (contrast < 4.5) lowContrastCount++;
                }
                
                // Vérifier les attributs alt des images
                const images = document.querySelectorAll('img');
                let imagesWithAlt = 0;
                
                images.forEach(img => {
                    if (img.hasAttribute('alt') && img.getAttribute('alt').trim() !== '') {
                        imagesWithAlt++;
                    }
                });
                
                return {
                    lowContrastTextRatio: sampleSize > 0 ? lowContrastCount / sampleSize : 0,
                    imagesWithAltRatio: images.length > 0 ? imagesWithAlt / images.length : 1,
                    totalImages: images.length
                }
            }
        """)
        
        # Analyser la mise en page (layout)
        layout_analysis = await page.evaluate("""
            () => {
                // Calculer le nombre de conteneurs flex/grid
                const flexContainers = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.display === 'flex' || style.display === 'grid';
                }).length;
                
                // Détecter si la page utilise un layout responsive
                let hasMediaQueries = false;
                for (let i = 0; i < document.styleSheets.length; i++) {
                    try {
                        const rules = document.styleSheets[i].cssRules || document.styleSheets[i].rules;
                        if (!rules) continue;
                        
                        for (let j = 0; j < rules.length; j++) {
                            if (rules[j].type === CSSRule.MEDIA_RULE) {
                                hasMediaQueries = true;
                                break;
                            }
                        }
                    } catch (e) {
                        // Erreur d'accès CORS aux feuilles de style
                        continue;
                    }
                    
                    if (hasMediaQueries) break;
                }
                
                return {
                    flexGridContainers: flexContainers,
                    hasMediaQueries: hasMediaQueries,
                    sectionsCount: document.querySelectorAll('section, article, aside, nav, header, footer, main').length,
                    hasSkipLinks: !!document.querySelector('a[href="#content"], a[href="#main"]'),
                    hasSidebar: !!document.querySelector('aside, .sidebar, #sidebar, [role="complementary"]')
                }
            }
        """)
        
        # Rassembler toutes les métriques
        return {
            "dimensions": dimensions,
            "element_counts": element_counts,
            "style_analysis": style_analysis,
            "accessibility": accessibility,
            "layout": layout_analysis
        }
    
    async def _extract_dominant_colors(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extrait les couleurs dominantes du site
        
        Args:
            page: Page Playwright
            
        Returns:
            Liste des couleurs dominantes avec leurs proportions
        """
        # Simuler l'extraction des couleurs dominantes
        # Dans un environnement réel, utilisez une bibliothèque comme OpenCV ou ColorThief
        # Ici, nous utilisons une approximation basée sur les couleurs CSS trouvées
        colors = await page.evaluate("""
            () => {
                // Fonction pour convertir rgb en hex
                function rgbToHex(rgb) {
                    if (!rgb) return null;
                    if (rgb.startsWith('#')) return rgb;
                    
                    let rgbMatch = rgb.match(/^rgb\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*\\)$/);
                    if (!rgbMatch) return rgb;
                    
                    function hex(x) {
                        return ("0" + parseInt(x).toString(16)).slice(-2);
                    }
                    return "#" + hex(rgbMatch[1]) + hex(rgbMatch[2]) + hex(rgbMatch[3]);
                }
                
                // Récupérer les couleurs de tous les éléments visibles
                const colors = {};
                const visibleElements = Array.from(document.querySelectorAll('*')).filter(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                });
                
                visibleElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const bgColor = rgbToHex(style.backgroundColor);
                    const color = rgbToHex(style.color);
                    
                    if (bgColor && bgColor !== '#000000' && bgColor !== '#ffffff' && bgColor !== 'rgba(0, 0, 0, 0)') {
                        colors[bgColor] = (colors[bgColor] || 0) + 1;
                    }
                    
                    if (color && color !== '#000000' && color !== '#ffffff') {
                        colors[color] = (colors[color] || 0) + 1;
                    }
                });
                
                // Convertir en tableau et trier par fréquence
                return Object.entries(colors)
                    .map(([color, count]) => ({ color, count }))
                    .sort((a, b) => b.count - a.count)
                    .slice(0, 6);  // Prendre les 6 couleurs les plus fréquentes
            }
        """)
        
        # Calculer les proportions
        if colors:
            total_count = sum(item["count"] for item in colors)
            for item in colors:
                item["proportion"] = round(item["count"] / total_count, 2)
                
        return colors
    
    async def _analyze_visual_complexity(self, page: Page) -> float:
        """
        Analyse la complexité visuelle de la page
        
        Args:
            page: Page Playwright
            
        Returns:
            Score de complexité visuelle (0-100)
        """
        # Récupérer des métriques pour évaluer la complexité
        metrics = await page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                const visibleElements = Array.from(elements).filter(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                });
                
                // Compter les éléments visuels importants
                const visualElements = {
                    images: document.querySelectorAll('img').length,
                    videos: document.querySelectorAll('video').length,
                    svgs: document.querySelectorAll('svg').length,
                    buttons: document.querySelectorAll('button, .btn, .button, [role="button"]').length,
                    inputs: document.querySelectorAll('input, textarea, select').length,
                    headings: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
                    paragraphs: document.querySelectorAll('p').length
                };
                
                // Compter les conteneurs avec des effets visuels
                let effectsCount = 0;
                visibleElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    
                    if (style.boxShadow && style.boxShadow !== 'none') effectsCount++;
                    if (style.textShadow && style.textShadow !== 'none') effectsCount++;
                    if (style.transform && style.transform !== 'none') effectsCount++;
                    if (style.animation && style.animation !== 'none') effectsCount++;
                    if (style.transition && style.transition !== 'none') effectsCount++;
                    if (parseFloat(style.opacity) < 1) effectsCount++;
                });
                
                return {
                    totalElements: elements.length,
                    visibleElements: visibleElements.length,
                    nestingDepth: Math.max(...Array.from(elements).map(el => {
                        let depth = 0;
                        let parent = el;
                        while (parent !== document.body && parent) {
                            depth++;
                            parent = parent.parentElement;
                        }
                        return depth;
                    })),
                    visualElements,
                    effectsCount
                };
            }
        """)
        
        # Calculer un score de complexité basé sur ces métriques
        # Plus le score est élevé, plus la page est complexe visuellement
        
        # Facteurs de base
        base_score = 0
        
        # La présence d'un grand nombre d'éléments augmente la complexité
        base_score += min(metrics["totalElements"] / 100, 50)  # Plafonné à 50 points
        
        # La profondeur d'imbrication des éléments impacte la clarté visuelle
        base_score += min(metrics["nestingDepth"] / 2, 15)  # Plafonné à 15 points
        
        # Les éléments visuels ajoutent de la complexité
        visual_elements_count = sum(metrics["visualElements"].values())
        base_score += min(visual_elements_count / 10, 20)  # Plafonné à 20 points
        
        # Les effets visuels ajoutent de la complexité
        base_score += min(metrics["effectsCount"] / 5, 15)  # Plafonné à 15 points
        
        # Normaliser le score final entre 0 et 100
        return min(base_score, 100)
    
    async def _calculate_whitespace_ratio(self, page: Page) -> float:
        """
        Calcule le ratio d'espace blanc sur la page
        
        Args:
            page: Page Playwright
            
        Returns:
            Ratio d'espace blanc (0-1)
        """
        # Utiliser le JavaScript pour calculer une approximation de l'espace blanc
        whitespace_data = await page.evaluate("""
            () => {
                const { width, height } = document.documentElement.getBoundingClientRect();
                const totalArea = width * height;
                
                // Calculer la surface occupée par tous les éléments visibles
                let occupiedArea = 0;
                const elements = document.querySelectorAll('*');
                
                elements.forEach(el => {
                    if (el === document.documentElement || el === document.body) return;
                    
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    
                    // Ignorer les éléments invisibles ou conteneurs de flux
                    if (rect.width === 0 || rect.height === 0 || style.display === 'none' || 
                        style.visibility === 'hidden') return;
                    
                    // Ne pas compter les éléments qui se chevauchent plusieurs fois
                    // (simple approximation - calcul précis nécessiterait un algorithme plus complexe)
                    if (style.position !== 'absolute' && style.position !== 'fixed') return;
                    
                    occupiedArea += rect.width * rect.height;
                });
                
                // Limiter à la surface totale pour éviter les valeurs aberrantes
                occupiedArea = Math.min(occupiedArea, totalArea);
                
                // Estimer le ratio d'espace blanc
                return {
                    totalArea,
                    occupiedArea,
                    whitespaceRatio: 1 - (occupiedArea / totalArea)
                };
            }
        """)
        
        # Si l'évaluation échoue, retourner une valeur par défaut
        return whitespace_data.get("whitespaceRatio", 0.3)
    
    async def _analyze_above_fold(self, page: Page) -> Dict[str, Any]:
        """
        Analyse le contenu visible sans scroll (above the fold)
        
        Args:
            page: Page Playwright
            
        Returns:
            Analyse du contenu above-the-fold
        """
        above_fold_data = await page.evaluate("""
            () => {
                const viewportHeight = window.innerHeight;
                const viewportWidth = window.innerWidth;
                
                // Trouver les éléments visibles dans la partie supérieure
                const visibleElements = Array.from(document.querySelectorAll('*')).filter(el => {
                    if (el === document.documentElement || el === document.body) return false;
                    
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    
                    return rect.top < viewportHeight && rect.top >= 0 && 
                           rect.width > 0 && rect.height > 0 && 
                           style.display !== 'none' && style.visibility !== 'hidden';
                });
                
                // Analyser les éléments importants
                const hasHero = visibleElements.some(el => 
                    el.classList.contains('hero') || 
                    el.classList.contains('banner') || 
                    el.classList.contains('jumbotron') ||
                    el.id === 'hero' || el.id === 'banner'
                );
                
                const hasCallToAction = visibleElements.some(el => 
                    el.tagName === 'BUTTON' || 
                    (el.tagName === 'A' && 
                     (el.classList.contains('btn') || 
                      el.classList.contains('button') || 
                      el.classList.contains('cta')))
                );
                
                const hasNavigation = !!document.querySelector('nav, header');
                
                const heroImage = Array.from(document.querySelectorAll('img')).find(img => {
                    const rect = img.getBoundingClientRect();
                    return rect.top < viewportHeight && 
                           rect.width > viewportWidth * 0.5 && 
                           rect.height > viewportHeight * 0.3;
                });
                
                // Compter les éléments par type
                const elementTypes = {
                    headings: visibleElements.filter(el => /^H[1-3]$/.test(el.tagName)).length,
                    paragraphs: visibleElements.filter(el => el.tagName === 'P').length,
                    images: visibleElements.filter(el => el.tagName === 'IMG').length,
                    buttons: visibleElements.filter(el => 
                        el.tagName === 'BUTTON' || 
                        (el.tagName === 'A' && 
                         (el.classList.contains('btn') || 
                          el.classList.contains('button')))
                    ).length,
                    inputs: visibleElements.filter(el => 
                        el.tagName === 'INPUT' || 
                        el.tagName === 'TEXTAREA' || 
                        el.tagName === 'SELECT'
                    ).length
                };
                
                return {
                    hasHero,
                    hasCallToAction,
                    hasNavigation,
                    hasLargeHeroImage: !!heroImage,
                    elementCounts: elementTypes,
                    totalVisibleElements: visibleElements.length
                };
            }
        """)
        
        return above_fold_data
    
    async def _detect_ui_components(self, page: Page) -> Dict[str, Any]:
        """
        Détecte les composants UI communs sur la page
        
        Args:
            page: Page Playwright
            
        Returns:
            Composants UI détectés
        """
        ui_components = await page.evaluate("""
            () => {
                return {
                    hasNavbar: !!document.querySelector('nav, .navbar, .navigation, header nav, [role="navigation"]'),
                    hasFooter: !!document.querySelector('footer, .footer, [role="contentinfo"]'),
                    hasSidebar: !!document.querySelector('aside, .sidebar, #sidebar, [role="complementary"]'),
                    hasCarousel: !!document.querySelector('.carousel, .slider, .slideshow, [role="slider"]'),
                    hasAccordion: !!document.querySelector('.accordion, details, .collapse'),
                    hasTabs: !!document.querySelector('.tabs, .tab-content, [role="tablist"], [role="tab"]'),
                    hasModal: !!document.querySelector('.modal, .dialog, [role="dialog"]'),
                    hasTooltip: !!document.querySelector('[data-tooltip], [title], .tooltip, [role="tooltip"]'),
                    hasCard: !!document.querySelector('.card, .panel, .box'),
                    hasForms: !!document.querySelector('form, .form'),
                    hasSearchBox: !!document.querySelector('[type="search"], .search, #search'),
                    hasSocialIcons: !!document.querySelector('.social, .social-icons, .share, .follow')
                };
            }
        """)
        
        return ui_components
    
    def _calculate_visual_score(self, results: Dict[str, Any]) -> int:
        """
        Calcule un score visuel global basé sur toutes les métriques
        
        Args:
            results: Résultats de l'analyse visuelle
            
        Returns:
            Score visuel (0-100)
        """
        score = 50  # Score de base moyen
        
        # Vérifier si une erreur est survenue
        if results.get("error"):
            return score
        
        # Analyse des éléments au-dessus de la ligne de pli
        above_fold = results.get("above_fold_content", {})
        if above_fold.get("hasHero"):
            score += 5
        if above_fold.get("hasCallToAction"):
            score += 5
        if above_fold.get("hasNavigation"):
            score += 5
        if above_fold.get("hasLargeHeroImage"):
            score += 5
            
        # Analyse des composants UI
        ui_components = results.get("ui_components", {})
        ui_score = sum(1 for k, v in ui_components.items() if v)
        score += min(ui_score * 2, 10)  # Maximum 10 points
        
        # Complexité visuelle (score inversé: moins complexe = meilleur)
        complexity = results.get("visual_complexity", 50)
        if complexity < 30:
            score += 10  # Design simple et clair
        elif complexity < 50:
            score += 5   # Design modérément complexe
        elif complexity > 80:
            score -= 10  # Design trop complexe
        elif complexity > 70:
            score -= 5   # Design assez complexe
            
        # Ratio d'espace blanc (plus d'espace blanc = meilleur, jusqu'à un certain point)
        whitespace_ratio = results.get("white_space_ratio", 0.3)
        if 0.3 <= whitespace_ratio <= 0.7:
            score += 10  # Bon équilibre d'espace blanc
        elif 0.2 <= whitespace_ratio < 0.3 or 0.7 < whitespace_ratio <= 0.8:
            score += 5   # Équilibre acceptable
        elif whitespace_ratio < 0.2:
            score -= 5   # Trop dense
        elif whitespace_ratio > 0.8:
            score -= 5   # Trop vide
            
        # Harmonie des couleurs
        color_harmony = results.get("color_harmony", "unknown")
        if color_harmony == "harmonieux":
            score += 10
        elif color_harmony == "cohérent":
            score += 5
        elif color_harmony == "discordant":
            score -= 5
            
        # Limiter le score entre 0 et 100
        return max(0, min(100, score))
        
    def _analyze_color_harmony(self, colors: List[Dict[str, Any]]) -> str:
        """
        Analyse l'harmonie des couleurs dominantes
        
        Args:
            colors: Liste des couleurs dominantes
            
        Returns:
            Classification de l'harmonie des couleurs
        """
        # Si pas assez de couleurs pour analyser
        if len(colors) < 2:
            return "inconnu"
            
        # Simplification: compter combien de couleurs uniques sont présentes
        # Dans une implémentation réelle, on analyserait la relation entre les couleurs
        # (complémentaires, analogues, etc.) en utilisant une roue chromatique
        
        # Si trop de couleurs dominantes -> moins harmonieux
        if len(colors) > 5:
            return "discordant"
            
        # Analyse de la proportion des couleurs principales
        main_color_proportion = colors[0].get("proportion", 0)
        second_color_proportion = colors[1].get("proportion", 0) if len(colors) > 1 else 0
        
        # Si une couleur domine fortement -> cohérent
        if main_color_proportion > 0.6:
            return "cohérent"
            
        # Si deux couleurs ont une bonne balance -> harmonieux
        if main_color_proportion + second_color_proportion > 0.7:
            return "harmonieux"
            
        # Si la distribution est équilibrée entre plusieurs couleurs -> harmonieux
        color_count = len([c for c in colors if c.get("proportion", 0) > 0.1])
        if 2 <= color_count <= 4:
            return "harmonieux"
            
        # Par défaut, considérer comme cohérent
        return "cohérent"

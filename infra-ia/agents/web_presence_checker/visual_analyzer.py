"""
Module d'analyse visuelle pour le WebPresenceCheckerAgent
"""
import re
import json
import random
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from utils.llm import LLMService

class VisualAnalyzer:
    """
    Classe dédiée à l'analyse visuelle et esthétique des sites web
    
    Cette classe utilise BeautifulSoup pour analyser la structure HTML
    et le LLM pour évaluer la qualité visuelle et UX du site
    """
    
    def __init__(self):
        """
        Initialisation de l'analyseur visuel
        """
        self.llm_service = LLMService()
        
        # Patterns pour détecter les frameworks CSS modernes
        self.modern_css_frameworks = [
            r'bootstrap\.(?:min\.)?css',
            r'tailwind\.(?:min\.)?css',
            r'bulma\.(?:min\.)?css',
            r'foundation\.(?:min\.)?css',
            r'material[-_]ui',
            r'semantic[-_]ui',
            r'mui',
            r'chakra',
            r'uikit'
        ]
        
        # Noms de classes CSS qui indiquent un design moderne
        self.modern_design_classes = [
            'container', 'row', 'col', 'flex', 'grid', 'card', 'modal',
            'navbar', 'nav', 'header', 'footer', 'section', 'hero',
            'btn', 'button', 'alert', 'form-control', 'input-group'
        ]
        
        # Patterns d'attributs CSS modernes
        self.modern_css_patterns = [
            r'display:\s*(?:flex|grid)',
            r'transition',
            r'transform',
            r'animation',
            r'border-radius',
            r'box-shadow',
            r'gradient',
            r'rgba',
            r'var\(--'  # Variables CSS
        ]
    
    def analyze_visual_quality(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Analyse la qualité visuelle d'un site web
        
        Args:
            html_content: Contenu HTML brut du site
            url: URL du site
            
        Returns:
            Résultats de l'analyse visuelle
        """
        # Analyser le HTML avec BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialiser les résultats
        results = {
            "visual_score": 0,
            "design_quality": "unknown",
            "design_modernity": "unknown",
            "visual_coherence": "unknown",
            "design_issues": [],
            "design_strengths": [],
            "visual_analysis": {}
        }
        
        # Extraire des métriques visuelles
        visual_metrics = self._extract_visual_metrics(soup)
        results["visual_analysis"] = visual_metrics
        
        # Détecter les frameworks CSS modernes
        css_frameworks = self._detect_css_frameworks(soup, html_content)
        results["visual_analysis"]["css_frameworks"] = css_frameworks
        
        # Évaluer la modernité du design
        design_modernity = self._evaluate_design_modernity(soup, html_content)
        results["design_modernity"] = design_modernity["classification"]
        
        # Évaluer la cohérence visuelle
        visual_coherence = self._evaluate_visual_coherence(soup)
        results["visual_coherence"] = visual_coherence["classification"]
        
        # Calculer un score visuel préliminaire
        preliminary_score = self._calculate_preliminary_visual_score(visual_metrics, design_modernity, visual_coherence, css_frameworks)
        
        # Utiliser le LLM pour analyser en profondeur avec les métriques collectées
        llm_analysis = self._get_llm_visual_analysis(visual_metrics, url, preliminary_score)
        
        # Mettre à jour les résultats avec l'analyse du LLM
        if llm_analysis:
            results.update(llm_analysis)
            if "visual_score" not in llm_analysis or not isinstance(llm_analysis["visual_score"], int):
                results["visual_score"] = preliminary_score
        else:
            results["visual_score"] = preliminary_score
            
        return results
    
    def _extract_visual_metrics(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extrait des métriques visuelles du HTML
        
        Args:
            soup: Objet BeautifulSoup
            
        Returns:
            Métriques visuelles
        """
        metrics = {}
        
        # Compter les styles en ligne (mauvaise pratique)
        inline_styles = len(soup.select('[style]'))
        metrics["inline_styles_count"] = inline_styles
        
        # Compter les feuilles de style externes
        css_links = len(soup.select('link[rel="stylesheet"]'))
        metrics["external_css_count"] = css_links
        
        # Compter les balises de style internes
        style_tags = len(soup.select('style'))
        metrics["style_tags_count"] = style_tags
        
        # Compter les images
        images = soup.find_all('img')
        metrics["images_count"] = len(images)
        
        # Vérifier si les images ont des attributs alt (accessibilité)
        images_with_alt = sum(1 for img in images if img.get('alt'))
        metrics["images_with_alt_percentage"] = 0 if not images else round((images_with_alt / len(images)) * 100)
        
        # Analyser la structure des titres (H1, H2, etc.)
        headings = {f"h{i}": len(soup.find_all(f'h{i}')) for i in range(1, 7)}
        metrics["headings"] = headings
        
        # Vérifier la présence d'une hiérarchie correcte des titres
        has_h1 = headings.get("h1", 0) > 0
        has_h2 = headings.get("h2", 0) > 0
        has_proper_hierarchy = has_h1 and has_h2
        metrics["has_proper_heading_hierarchy"] = has_proper_hierarchy
        
        # Compter les sections sémantiques
        semantic_elements = ['header', 'footer', 'nav', 'section', 'article', 'aside', 'main']
        semantic_count = sum(len(soup.find_all(tag)) for tag in semantic_elements)
        metrics["semantic_elements_count"] = semantic_count
        
        # Compter les éléments visuels avancés (divs avec des classes ou id)
        styled_divs = len([div for div in soup.find_all('div') if div.get('class') or div.get('id')])
        metrics["styled_divs_count"] = styled_divs
        
        # Équilibre texte/images (approximation)
        text_length = len(soup.get_text())
        metrics["text_length"] = text_length
        metrics["text_to_image_ratio"] = round(text_length / (len(images) + 1))  # +1 pour éviter division par 0
        
        # Détecter les polices utilisées
        fonts = set()
        for style in soup.select('style'):
            # Chercher des déclarations de font-family
            font_families = re.findall(r'font-family\s*:\s*([^;}]+)', style.string or '')
            for family in font_families:
                fonts.update([f.strip(' \'"') for f in family.split(',')])
        
        # Chercher aussi dans les liens vers Google Fonts ou autres services de polices
        for link in soup.find_all('link', href=True):
            if 'fonts.googleapis.com' in link['href']:
                # Extraire les noms des polices de l'URL
                font_names = re.findall(r'family=([^&:]+)', link['href'])
                fonts.update([name.replace('+', ' ') for name in font_names])
        
        metrics["fonts_detected"] = list(fonts)
        metrics["fonts_count"] = len(fonts)
        
        # Détecter la présence de CSS custom/modern (variables CSS, etc.)
        custom_css = False
        for style in soup.select('style'):
            if style.string and ('--' in style.string or '@media' in style.string):
                custom_css = True
                break
        
        metrics["has_custom_css"] = custom_css
        
        return metrics
    
    def _detect_css_frameworks(self, soup: BeautifulSoup, html_content: str) -> List[str]:
        """
        Détecte l'utilisation de frameworks CSS modernes
        
        Args:
            soup: Objet BeautifulSoup
            html_content: Contenu HTML brut
            
        Returns:
            Liste des frameworks CSS détectés
        """
        frameworks = []
        
        # Vérifier les liens CSS pour détecter les CDN de frameworks
        for link in soup.find_all('link', rel='stylesheet', href=True):
            href = link['href'].lower()
            if 'bootstrap' in href:
                frameworks.append('Bootstrap')
            elif 'tailwind' in href:
                frameworks.append('Tailwind CSS')
            elif 'bulma' in href:
                frameworks.append('Bulma')
            elif 'foundation' in href:
                frameworks.append('Foundation')
            elif 'materialize' in href or 'material-ui' in href:
                frameworks.append('Material Design')
            elif 'semantic-ui' in href:
                frameworks.append('Semantic UI')
            elif 'fontawesome' in href:
                frameworks.append('Font Awesome')
        
        # Vérifier les classes pour détecter l'utilisation de frameworks
        if frameworks:
            return list(set(frameworks))  # Dédupliquer
            
        # Si aucun framework n'a été détecté par les liens, analyser les classes
        classes = []
        for tag in soup.find_all(class_=True):
            classes.extend(tag['class'])
        
        classes_text = ' '.join(classes)
        
        # Détecter Bootstrap par les classes
        bootstrap_classes = ['container', 'row', 'col-', 'btn-', 'card', 'navbar']
        if any(c in classes_text for c in bootstrap_classes):
            frameworks.append('Bootstrap')
        
        # Détecter Tailwind par les classes
        tailwind_classes = ['bg-', 'text-', 'p-', 'm-', 'flex', 'grid']
        tailwind_count = sum(1 for c in classes if any(t in c for t in tailwind_classes))
        if tailwind_count > 10:  # Si beaucoup de classes potentiellement Tailwind
            frameworks.append('Tailwind CSS')
        
        # Détecter Material Design
        material_classes = ['mat-', 'md-', 'mdc-']
        if any(c in classes_text for c in material_classes):
            frameworks.append('Material Design')
        
        return list(set(frameworks))  # Dédupliquer
    
    def _evaluate_design_modernity(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
        """
        Évalue à quel point le design est moderne ou obsolète
        
        Args:
            soup: Objet BeautifulSoup
            html_content: Contenu HTML brut
            
        Returns:
            Résultat de l'évaluation de modernité
        """
        modernity_score = 0
        total_checks = 0
        
        # 1. Vérifier l'utilisation de flexbox ou grid
        has_flexbox = re.search(r'display\s*:\s*flex', html_content, re.IGNORECASE) is not None
        has_grid = re.search(r'display\s*:\s*grid', html_content, re.IGNORECASE) is not None
        if has_flexbox or has_grid:
            modernity_score += 1
        total_checks += 1
        
        # 2. Vérifier l'utilisation des variables CSS
        has_css_vars = '--' in html_content and 'var(' in html_content
        if has_css_vars:
            modernity_score += 1
        total_checks += 1
        
        # 3. Vérifier la présence de requêtes média (@media)
        has_media_queries = '@media' in html_content
        if has_media_queries:
            modernity_score += 1
        total_checks += 1
        
        # 4. Vérifier les animations/transitions CSS
        has_animations = re.search(r'(animation|transition|transform)', html_content, re.IGNORECASE) is not None
        if has_animations:
            modernity_score += 1
        total_checks += 1
        
        # 5. Utilisation de frameworks CSS modernes (déjà compté dans detect_css_frameworks)
        
        # 6. Vérifier les aspects visuels modernes (ombres, coins arrondis)
        has_modern_visuals = re.search(r'(box-shadow|border-radius|gradient)', html_content, re.IGNORECASE) is not None
        if has_modern_visuals:
            modernity_score += 1
        total_checks += 1
        
        # 7. Utilisation des balises sémantiques HTML5
        semantic_tags = ['header', 'footer', 'nav', 'section', 'article', 'aside', 'main']
        has_semantic = any(soup.find(tag) for tag in semantic_tags)
        if has_semantic:
            modernity_score += 1
        total_checks += 1
        
        # 8. Utilisation des attributs data-* (souvent utilisés par les frameworks modernes)
        # Chercher des éléments avec des attributs data-*
        data_attr_elements = [tag for tag in soup.find_all() if any(attr.startswith('data-') for attr in tag.attrs)]
        has_data_attrs = len(data_attr_elements) > 0
        if has_data_attrs:
            modernity_score += 1
        total_checks += 1
        
        # 9. Utilisation des SVG (plus modernes que les images bitmap)
        has_svg = bool(soup.find_all('svg')) or 'svg' in html_content
        if has_svg:
            modernity_score += 1
        total_checks += 1
        
        # Calculer le pourcentage
        modernity_percentage = (modernity_score / total_checks) * 100 if total_checks > 0 else 0
        
        # Classifier
        if modernity_percentage >= 75:
            classification = "moderne"
        elif modernity_percentage >= 50:
            classification = "contemporain"
        elif modernity_percentage >= 25:
            classification = "daté"
        else:
            classification = "obsolète"
        
        return {
            "score": modernity_percentage,
            "classification": classification,
            "modern_features": modernity_score,
            "total_features_checked": total_checks
        }
    
    def _evaluate_visual_coherence(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Évalue la cohérence visuelle du site
        
        Args:
            soup: Objet BeautifulSoup
            
        Returns:
            Résultat de l'évaluation de cohérence
        """
        # Extraire toutes les classes CSS
        all_classes = []
        for tag in soup.find_all(class_=True):
            all_classes.extend(tag.get('class', []))
        
        # Compter les classes uniques
        unique_classes = set(all_classes)
        
        # Rechercher des patterns de nommage cohérents
        # (comme des préfixes communs ou des conventions BEM)
        prefixes = {}
        bem_pattern = re.compile(r'^[a-z]+-[a-z]+(?:__[a-z]+(?:--[a-z]+)?)?$')
        bem_classes = 0
        
        for cls in unique_classes:
            # Extraire le préfixe (première partie du nom de classe)
            parts = cls.split('-')
            if len(parts) > 1:
                prefix = parts[0]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
            
            # Vérifier si la classe suit une convention BEM
            if bem_pattern.match(cls):
                bem_classes += 1
        
        # Calculer le pourcentage de classes qui suivent un motif cohérent
        total_unique = len(unique_classes) if unique_classes else 1
        
        # Identifier les préfixes dominants (qui apparaissent souvent)
        dominant_prefixes = [prefix for prefix, count in prefixes.items() if count > 3]
        
        # Calculer le pourcentage de classes avec des préfixes dominants
        classes_with_dominant_prefixes = sum(prefixes.get(prefix, 0) for prefix in dominant_prefixes)
        coherent_percentage = (classes_with_dominant_prefixes + bem_classes) / total_unique * 100
        
        # Classifier la cohérence
        if coherent_percentage >= 75:
            classification = "très cohérent"
        elif coherent_percentage >= 50:
            classification = "cohérent"
        elif coherent_percentage >= 25:
            classification = "peu cohérent"
        else:
            classification = "incohérent"
        
        return {
            "score": coherent_percentage,
            "classification": classification,
            "unique_classes": len(unique_classes),
            "total_classes": len(all_classes),
            "bem_classes": bem_classes,
            "dominant_prefixes": dominant_prefixes
        }
    
    def _calculate_preliminary_visual_score(self, metrics: Dict[str, Any], 
                                          modernity: Dict[str, Any], 
                                          coherence: Dict[str, Any],
                                          frameworks: List[str]) -> int:
        """
        Calcule un score préliminaire basé sur les métriques collectées
        
        Args:
            metrics: Métriques visuelles extraites du HTML
            modernity: Résultat de l'évaluation de modernité
            coherence: Résultat de l'évaluation de cohérence
            frameworks: Frameworks CSS détectés
            
        Returns:
            Score visuel préliminaire (0-100)
        """
        score = 50  # Score de base moyen
        
        # Bonus pour la modernité du design
        modernity_bonus = {
            "moderne": 20,
            "contemporain": 15,
            "daté": 5,
            "obsolète": 0
        }
        score += modernity_bonus.get(modernity["classification"], 0)
        
        # Bonus pour la cohérence visuelle
        coherence_bonus = {
            "très cohérent": 15,
            "cohérent": 10,
            "peu cohérent": 0,
            "incohérent": -10
        }
        score += coherence_bonus.get(coherence["classification"], 0)
        
        # Bonus pour l'utilisation de frameworks CSS modernes
        if frameworks:
            score += min(len(frameworks) * 5, 10)  # Maximum 10 points
        
        # Bonus pour une bonne hiérarchie des titres
        if metrics.get("has_proper_heading_hierarchy", False):
            score += 5
        
        # Malus pour trop de styles en ligne
        inline_styles = metrics.get("inline_styles_count", 0)
        if inline_styles > 20:
            score -= 10
        elif inline_styles > 10:
            score -= 5
        
        # Bonus pour les éléments sémantiques
        semantic_count = metrics.get("semantic_elements_count", 0)
        if semantic_count > 10:
            score += 10
        elif semantic_count > 5:
            score += 5
        
        # Bonus pour les images accessibles (avec alt)
        alt_percentage = metrics.get("images_with_alt_percentage", 0)
        if alt_percentage >= 80:
            score += 5
        
        # Limiter le score entre 0 et 100
        return max(0, min(100, score))
    
    def _get_llm_visual_analysis(self, metrics: Dict[str, Any], url: str, preliminary_score: int) -> Dict[str, Any]:
        """
        Utilise le LLM pour analyser la qualité visuelle basée sur les métriques
        
        Args:
            metrics: Métriques visuelles extraites du HTML
            url: URL du site
            preliminary_score: Score préliminaire calculé
            
        Returns:
            Résultat de l'analyse LLM
        """
        # Construire le prompt pour le LLM
        prompt = f"""Analyse la qualité visuelle et esthétique du site web {url} en te basant sur ces métriques techniques:

```json
{json.dumps(metrics, indent=2)}
```

Le score préliminaire calculé est de {preliminary_score}/100.

Ton objectif est d'estimer la qualité visuelle et esthétique du site basée sur ces métriques techniques.
Examine les patterns dans le code pour déduire la qualité visuelle et l'expérience utilisateur.

Voici mon analyse complète:

"""
        
        try:
            # Appeler le LLM
            llm_response = self.llm_service.get_completion(prompt)
            
            # Tenter d'extraire un score du texte
            score_match = re.search(r'score\s*(?:visuel|esthétique)?\s*(?:de|:)\s*(\d+)', llm_response, re.IGNORECASE)
            design_quality_match = re.search(r'qualité\s*(?:visuelle|du design)\s*(?::|est)\s*["\']?(\w+)["\']?', llm_response, re.IGNORECASE)
            
            # Préparer le résultat
            result = {
                "llm_visual_analysis": llm_response
            }
            
            # Ajouter le score visuel s'il a été trouvé
            if score_match:
                try:
                    visual_score = int(score_match.group(1))
                    result["visual_score"] = min(100, max(0, visual_score))  # Limiter entre 0 et 100
                except ValueError:
                    result["visual_score"] = preliminary_score
            else:
                result["visual_score"] = preliminary_score
            
            # Ajouter la qualité du design si elle a été trouvée
            if design_quality_match:
                result["design_quality"] = design_quality_match.group(1).lower()
            
            # Extraire les forces et faiblesses du design
            strengths_match = re.search(r'Forces\s*(?:du design|visuelles)\s*:(.+?)(?:Faiblesses|$)', llm_response, re.IGNORECASE | re.DOTALL)
            weaknesses_match = re.search(r'Faiblesses\s*(?:du design|visuelles)\s*:(.+?)(?:Conclusion|$)', llm_response, re.IGNORECASE | re.DOTALL)
            
            if strengths_match:
                strengths_text = strengths_match.group(1).strip()
                strengths = [s.strip('- \t') for s in strengths_text.split('\n') if s.strip('- \t')]
                result["design_strengths"] = strengths
            
            if weaknesses_match:
                weaknesses_text = weaknesses_match.group(1).strip()
                weaknesses = [w.strip('- \t') for w in weaknesses_text.split('\n') if w.strip('- \t')]
                result["design_issues"] = weaknesses
            
            return result
            
        except Exception as e:
            # En cas d'erreur, retourner un résultat minimal
            return {
                "visual_score": preliminary_score,
                "design_quality": "unknown",
                "error": str(e)
            }

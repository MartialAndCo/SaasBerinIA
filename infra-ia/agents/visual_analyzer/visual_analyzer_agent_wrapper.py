"""
Module d'intégration de l'agent d'analyse visuelle dans le système BerinIA.
"""
import os
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.agent_base import Agent
from agents.visual_analyzer.visual_analyzer_agent import VisualAnalyzer

# Configuration du logging
logger = logging.getLogger("BerinIA-VisualAnalyzer")

class VisualAnalyzerAgent(Agent):
    """
    Agent d'analyse visuelle pour le système BerinIA.
    
    Cet agent utilise GPT-4 Vision pour:
    1. Analyser des sites web visuellement
    2. Détecter et contourner les popups
    3. Évaluer la qualité et le professionnalisme des sites
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation de l'agent d'analyse visuelle
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("VisualAnalyzerAgent", config_path)
        
        # Initialisation de l'analyseur visuel
        self.analyzer = VisualAnalyzer()
        
        # Création du répertoire de captures d'écran améliorées
        self.enhanced_dir = os.path.join(os.getcwd(), "enhanced_screenshots")
        os.makedirs(self.enhanced_dir, exist_ok=True)
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal de l'agent
        
        Args:
            input_data: Données d'entrée
                - action: Action à effectuer
                - url: URL du site à analyser (pour analyze_website)
                - lead_id: ID du lead (pour analyze_lead)
                
        Returns:
            Résultat de l'opération
        """
        action = input_data.get("action", "")
        
        if action == "analyze_website":
            url = input_data.get("url")
            if not url:
                return {
                    "status": "error",
                    "message": "URL manquante pour l'analyse"
                }
                
            return self._analyze_website(url)
            
        elif action == "analyze_lead":
            lead_id = input_data.get("lead_id")
            lead_data = input_data.get("lead_data")
            
            if not lead_id or not lead_data:
                return {
                    "status": "error",
                    "message": "Données de lead manquantes pour l'analyse"
                }
                
            return self._analyze_lead(lead_id, lead_data)
            
        elif action == "get_status":
            return {
                "status": "success",
                "agent_status": "active",
                "capabilities": [
                    "website_analysis",
                    "popup_detection",
                    "visual_quality_assessment",
                    "lead_enrichment"
                ]
            }
            
        else:
            return {
                "status": "error",
                "message": f"Action inconnue: {action}"
            }
    
    def _analyze_website(self, url: str) -> Dict[str, Any]:
        """
        Analyse un site web avec l'analyseur visuel
        
        Args:
            url: URL du site à analyser
            
        Returns:
            Résultat de l'analyse
        """
        self.speak(f"Début de l'analyse visuelle du site {url}", target="OverseerAgent")
        
        try:
            # Utilisation du module asyncio pour exécuter la fonction asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Analyse du site web
            results = loop.run_until_complete(self.analyzer.analyze_website(url))
            loop.close()
            
            # Format de sortie standardisé
            output = {
                "status": "success",
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
            
            # Journalisation des résultats clés
            self.speak(
                f"Analyse de {url} terminée: "
                f"Qualité visuelle {results.get('site_content', {}).get('visual_quality', 'N/A')}/10, "
                f"Type: {results.get('site_content', {}).get('site_type', 'indéterminé')}",
                target="OverseerAgent"
            )
            
            return output
            
        except Exception as e:
            error_message = f"Erreur lors de l'analyse du site {url}: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            
            return {
                "status": "error",
                "url": url,
                "message": error_message
            }
    
    def _analyze_lead(self, lead_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse le site web d'un lead et enrichit ses données
        
        Args:
            lead_id: ID du lead
            lead_data: Données du lead
            
        Returns:
            Données du lead enrichies
        """
        website = lead_data.get("website") or lead_data.get("company_website")
        
        if not website:
            return {
                "status": "error",
                "message": f"Le lead {lead_id} n'a pas de site web à analyser"
            }
            
        self.speak(f"Analyse du site du lead {lead_id}: {website}", target="OverseerAgent")
        
        try:
            # Analyse du site
            analysis_result = self._analyze_website(website)
            
            if analysis_result["status"] != "success":
                return analysis_result
                
            results = analysis_result["results"]
            
            # Enrichissement des données du lead
            enriched_data = {**lead_data}
            
            # Ajout des métadonnées web
            if "web_metadata" not in enriched_data:
                enriched_data["web_metadata"] = {}
                
            site_content = results.get("site_content", {})
            screenshots = results.get("screenshots", {})
            
            enriched_data["web_metadata"].update({
                "analyzed_at": datetime.now().isoformat(),
                "site_type": site_content.get("site_type", "unknown"),
                "visual_quality": site_content.get("visual_quality", 0),
                "professionalism": site_content.get("professionalism", 0),
                "strengths": site_content.get("strengths", []),
                "weaknesses": site_content.get("weaknesses", []),
                "has_popup": results.get("has_popup", False),
                "popup_removed": results.get("popup_removed", False),
                "screenshots": screenshots
            })
            
            # Calcul d'un score de maturité digitale
            web_maturity = self._calculate_maturity_score(site_content)
            enriched_data["web_metadata"]["maturity_score"] = web_maturity
            
            if web_maturity >= 75:
                enriched_data["web_metadata"]["maturity_tag"] = "advanced"
            elif web_maturity >= 50:
                enriched_data["web_metadata"]["maturity_tag"] = "intermediate"
            else:
                enriched_data["web_metadata"]["maturity_tag"] = "basic"
            
            return {
                "status": "success",
                "lead_id": lead_id,
                "enriched_data": enriched_data,
                "analysis_summary": {
                    "site_type": site_content.get("site_type", "unknown"),
                    "visual_quality": site_content.get("visual_quality", 0),
                    "maturity_score": web_maturity
                }
            }
            
        except Exception as e:
            error_message = f"Erreur lors de l'analyse du lead {lead_id}: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def _calculate_maturity_score(self, site_content: Dict[str, Any]) -> int:
        """
        Calcule un score de maturité digitale basé sur l'analyse du site
        
        Args:
            site_content: Données d'analyse du site
            
        Returns:
            Score de maturité (0-100)
        """
        # Valeurs par défaut
        visual_quality = site_content.get("visual_quality", 0)
        professionalism = site_content.get("professionalism", 0)
        
        # Autres facteurs possibles
        has_responsive = "mobile-friendly" in str(site_content)
        has_modern_tech = any(tech in str(site_content) for tech in 
                            ["react", "angular", "vue", "gatsby", "next.js", "bootstrap"])
        
        # Calcul du score
        score = 0
        
        # Qualité visuelle (poids 3)
        score += (visual_quality * 3)
        
        # Professionnalisme (poids 3)
        score += (professionalism * 3)
        
        # Responsive design (poids 2)
        if has_responsive:
            score += 20
            
        # Technologies modernes (poids 2)
        if has_modern_tech:
            score += 20
            
        # Normalisation du score sur 100 (maximum théorique: 100)
        normalized_score = min(100, score)
        
        return normalized_score

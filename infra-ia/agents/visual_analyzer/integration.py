#!/usr/bin/env python3
"""
Module d'intégration pour l'agent Visual Analyzer

Ce module fournit des fonctions utilitaires pour intégrer l'agent d'analyse 
visuelle au reste du système BerinIA.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import de l'agent d'analyse visuelle
from .visual_analyzer_agent import VisualAnalyzer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BerinIA-VisualAnalyzer-Integration")

class VisualIntegration:
    """
    Classe d'intégration pour l'agent d'analyse visuelle
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'intégration
        
        Args:
            api_key: Clé API OpenAI (optionnel)
        """
        self.analyzer = VisualAnalyzer(api_key)
        
    async def analyze_lead_website(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse le site web d'un lead et enrichit ses données
        
        Args:
            lead_data: Données du lead
            
        Returns:
            Dict contenant les données du lead enrichies
        """
        # Extraire l'URL du site web du lead
        website_url = lead_data.get("company_website")
        if not website_url:
            logger.warning(f"Lead {lead_data.get('lead_id', 'unknown')} n'a pas d'URL de site web")
            return lead_data
        
        # Analyser le site web
        logger.info(f"Analyse du site {website_url} pour le lead {lead_data.get('lead_id', 'unknown')}")
        try:
            analysis_results = await self.analyzer.analyze_website(website_url)
            
            # Enrichir les données du lead avec les résultats de l'analyse
            if not "web_metadata" in lead_data:
                lead_data["web_metadata"] = {}
                
            lead_data["web_metadata"].update({
                "analyzed_at": analysis_results.get("timestamp", ""),
                "reachable": analysis_results.get("success", False),
                "has_popup": analysis_results.get("has_popup", False),
                "popup_removed": analysis_results.get("popup_removed", False)
            })
            
            # Ajouter les informations sur le site si disponibles
            site_content = analysis_results.get("site_content", {})
            if site_content:
                web_metadata = lead_data["web_metadata"]
                web_metadata.update({
                    "site_type": site_content.get("site_type", "unknown"),
                    "visual_quality": site_content.get("visual_quality", 0),
                    "professionalism": site_content.get("professionalism", 0),
                    "strengths": site_content.get("strengths", []),
                    "weaknesses": site_content.get("weaknesses", []),
                    "technologies": site_content.get("technologies", []),
                    "main_colors": site_content.get("main_colors", []),
                    "target_audience": site_content.get("target_audience", "")
                })
                
                # Calculer un score de maturité digitale
                maturity_score = self._calculate_maturity_score(site_content)
                web_metadata["maturity_score"] = maturity_score
                
                # Déterminer une catégorie de maturité
                if maturity_score >= 75:
                    web_metadata["maturity_tag"] = "pro_site"
                    web_metadata["web_status_tag"] = "déjà bien équipé"
                elif maturity_score >= 50:
                    web_metadata["maturity_tag"] = "standard_site"
                    web_metadata["web_status_tag"] = "potentiel d'amélioration"
                else:
                    web_metadata["maturity_tag"] = "basic_site"
                    web_metadata["web_status_tag"] = "besoin urgent"
                
                # Ajouter des tags techniques
                tech_tags = []
                if site_content.get("mobile_friendly_assessment", "").lower().find("bon") >= 0:
                    tech_tags.append("mobile_friendly")
                    web_metadata["mobile_friendly"] = True
                
                web_metadata["tech_tags"] = tech_tags
                
                # Lien vers les captures d'écran
                screenshots = analysis_results.get("screenshots", {})
                if screenshots:
                    web_metadata["screenshots"] = screenshots
            
            logger.info(f"Analyse terminée pour {website_url}")
            return lead_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de {website_url}: {str(e)}")
            lead_data["web_metadata"] = {
                "reachable": False,
                "error": str(e)
            }
            return lead_data
    
    async def batch_analyze_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyse les sites web d'une liste de leads
        
        Args:
            leads: Liste de données de leads
            
        Returns:
            Liste des données de leads enrichies
        """
        enriched_leads = []
        
        for lead in leads:
            enriched_lead = await self.analyze_lead_website(lead)
            enriched_leads.append(enriched_lead)
        
        return enriched_leads
    
    def _calculate_maturity_score(self, site_content: Dict[str, Any]) -> int:
        """
        Calcule un score de maturité digitale basé sur l'analyse du site
        
        Args:
            site_content: Données d'analyse du site
            
        Returns:
            Score de maturité (0-100)
        """
        score = 0
        
        # Qualité visuelle (poids 3)
        visual_quality = site_content.get("visual_quality", 0)
        score += (visual_quality * 3)
        
        # Professionnalisme (poids 3)
        professionalism = site_content.get("professionalism", 0)
        score += (professionalism * 3)
        
        # Navigation (poids 2)
        navigation_quality = site_content.get("navigation_quality", 0)
        score += (navigation_quality * 2)
        
        # Technologies détectées (poids 1)
        tech_count = len(site_content.get("technologies", []))
        tech_score = min(tech_count, 10)
        score += tech_score
        
        # Forces vs faiblesses (poids 1)
        strengths = len(site_content.get("strengths", []))
        weaknesses = len(site_content.get("weaknesses", []))
        
        if strengths > weaknesses:
            score += 10
        elif strengths == weaknesses:
            score += 5
        
        # Normaliser le score sur 100
        # Base: 3*10 + 3*10 + 2*10 + 10 + 10 = 90
        normalized_score = int((score / 90) * 100)
        
        # Assurer que le score reste dans les limites
        return max(0, min(normalized_score, 100))

# Fonction simple d'analyse d'un site
async def analyze_site(url: str) -> Dict[str, Any]:
    """
    Fonction utilitaire pour analyser rapidement un site web
    
    Args:
        url: URL du site à analyser
        
    Returns:
        Résultats de l'analyse
    """
    analyzer = VisualAnalyzer()
    return await analyzer.analyze_website(url)

# Point d'entrée pour les tests
if __name__ == "__main__":
    async def test():
        # Exemple de données de lead
        test_lead = {
            "lead_id": "test123",
            "company": "Test Company",
            "company_website": "https://www.lemonde.fr"
        }
        
        integration = VisualIntegration()
        enriched_lead = await integration.analyze_lead_website(test_lead)
        
        print(json.dumps(enriched_lead, indent=2))
    
    asyncio.run(test())

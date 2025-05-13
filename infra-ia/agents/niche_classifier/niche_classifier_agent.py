import json
import os
import logging
from pathlib import Path
import re
from typing import Dict, List, Any, Optional, Tuple
import difflib
from datetime import datetime

from core.agent_base import Agent
from utils.llm import LLMService

logger = logging.getLogger(__name__)

class NicheClassifierAgent(Agent):
    """
    Agent responsable de la classification des niches en familles et de la personnalisation
    des approches en fonction des analyses visuelles et des caractéristiques de la niche.
    
    Cet agent combine les données de hiérarchie des niches avec les données d'analyse visuelle
    pour proposer des argumentaires et approches personnalisés pour chaque lead.
    """
    
    def __init__(self, config_path: str = None):
        """Initialise l'agent de classification de niches"""
        super().__init__("NicheClassifierAgent", config_path)
        self.niche_families = self._load_niche_families()
        self.niche_map = self._build_niche_map()
        
    def _load_niche_families(self) -> Dict:
        """Charge les données de hiérarchie des niches depuis le fichier JSON"""
        niche_families_path = Path(__file__).parent.parent.parent / "data" / "niche_families.json"
        try:
            with open(niche_families_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des familles de niches: {e}")
            return {"families": [], "fallback": {}}
    
    def _build_niche_map(self) -> Dict[str, str]:
        """Construit un dictionnaire de correspondance niche -> famille_id"""
        niche_map = {}
        for family in self.niche_families.get("families", []):
            family_id = family.get("id")
            for niche in family.get("niches", []):
                niche_map[niche.lower()] = family_id
        return niche_map
    
    def classify_niche(self, niche: str) -> Dict:
        """
        Classifie une niche dans sa famille et retourne les informations associées
        
        Args:
            niche: Nom de la niche à classifier
            
        Returns:
            Dict contenant les informations de la famille et la correspondance
        """
        niche_lower = niche.lower()
        
        # Vérifier si la niche est directement dans notre dictionnaire
        if niche_lower in self.niche_map:
            family_id = self.niche_map[niche_lower]
            family_info = next((f for f in self.niche_families["families"] if f["id"] == family_id), None)
            return {
                "family_id": family_id,
                "family_name": family_info["name"],
                "match_type": "exact",
                "confidence": 1.0,
                "family_info": family_info
            }
        
        # Si la niche n'est pas trouvée directement, utiliser le LLM pour classifier
        return self._classify_with_llm(niche)
    
    def _classify_with_llm(self, niche: str) -> Dict:
        """Utilise le LLM pour classifier une niche qui n'est pas dans notre liste"""
        prompt = self._build_classification_prompt(niche)
        response = LLMService.call_llm(prompt, complexity="medium")
        
        try:
            result = json.loads(response)
            family_id = result.get("family_id")
            family_info = next((f for f in self.niche_families["families"] if f["id"] == family_id), None)
            
            if not family_info:
                # Utiliser la meilleure correspondance par défaut
                closest_family = self._find_closest_family(niche)
                family_info = next((f for f in self.niche_families["families"] if f["id"] == closest_family), None)
                result["family_id"] = closest_family
                result["family_name"] = family_info["name"]
                result["match_type"] = "fallback"
                result["confidence"] = 0.5
            
            result["family_info"] = family_info
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la réponse LLM: {e}")
            # Utiliser la méthode de secours
            closest_family = self._find_closest_family(niche)
            family_info = next((f for f in self.niche_families["families"] if f["id"] == closest_family), None)
            return {
                "family_id": closest_family,
                "family_name": family_info["name"],
                "match_type": "fallback",
                "confidence": 0.3,
                "family_info": family_info
            }
    
    def _find_closest_family(self, niche: str) -> str:
        """Trouve la famille la plus proche en comparant avec les niches connues"""
        best_match = None
        best_score = 0
        
        for family in self.niche_families.get("families", []):
            for known_niche in family.get("niches", []):
                score = difflib.SequenceMatcher(None, niche.lower(), known_niche.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = family["id"]
        
        # Par défaut, retourner b2b_services si aucune correspondance n'est trouvée
        return best_match or "b2b_services"
    
    def _build_classification_prompt(self, niche: str) -> str:
        """Construit le prompt pour la classification par LLM"""
        with open(os.path.join(os.path.dirname(__file__), "prompt.txt"), "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # Créer une liste des familles et des niches connues pour le prompt
        families_info = []
        for family in self.niche_families.get("families", []):
            families_info.append({
                "id": family["id"],
                "name": family["name"],
                "niches": family["niches"]
            })
        
        return prompt_template.format(
            niche=niche,
            families_json=json.dumps(families_info, ensure_ascii=False, indent=2)
        )
    
    def generate_personalized_approach(self, niche: str, visual_analysis: Dict = None) -> Dict:
        """
        Génère une approche personnalisée en fonction de la niche et de l'analyse visuelle
        
        Args:
            niche: Nom de la niche
            visual_analysis: Données d'analyse visuelle (optionnel)
            
        Returns:
            Dict contenant l'approche personnalisée
        """
        # Classifier la niche
        classification = self.classify_niche(niche)
        family_info = classification.get("family_info", {})
        
        # Définir les conditions par défaut si l'analyse visuelle n'est pas disponible
        conditions = ["no_data"]
        proposal = "approche générique basée sur la famille"
        
        # Si nous avons des données d'analyse visuelle, déterminer la condition applicable
        if visual_analysis:
            conditions = self._determine_conditions(visual_analysis, family_info)
            
            # Trouver la proposition correspondante dans la logique de la famille
            logic_rules = family_info.get("logic", [])
            for rule in logic_rules:
                if rule.get("condition") in conditions:
                    proposal = rule.get("proposal")
                    break
        
        # Construire le résultat
        needs = family_info.get("needs", [])
        
        result = {
            "niche": niche,
            "family": classification.get("family_name"),
            "family_id": classification.get("family_id"),
            "match_confidence": classification.get("confidence", 0),
            "recommended_needs": needs,
            "conditions_detected": conditions,
            "proposal": proposal,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Si l'analyse visuelle existe, ajouter des détails supplémentaires
        if visual_analysis:
            result["visual_score"] = visual_analysis.get("visual_score", 0)
            result["site_quality"] = visual_analysis.get("visual_quality", 0)
            result["website_maturity"] = visual_analysis.get("website_maturity", "unknown")
        
        return result
    
    def _determine_conditions(self, visual_analysis: Dict, family_info: Dict) -> List[str]:
        """Détermine les conditions applicables en fonction de l'analyse visuelle"""
        conditions = []
        
        # Vérifier si le site existe
        has_website = visual_analysis.get("screenshot_path") is not None
        if not has_website:
            conditions.append("no_site")
            return conditions
            
        # Évaluer la qualité du site
        visual_quality = visual_analysis.get("visual_quality", 0)
        if visual_quality < 4:
            conditions.append("site_pauvre")
        elif visual_quality >= 7:
            conditions.append("site_complet")
            conditions.append("site_bon")
        else:
            conditions.append("site_moyen")
            
        # Vérifier la présence de popups (comme indicateur de fonctionnalités)
        has_popup = visual_analysis.get("has_popup", False)
        if has_popup:
            conditions.append("site_avec_popups")
            
        # Vérifier les spécificités par famille
        family_id = family_info.get("id", "")
        
        if family_id == "health":
            # Vérifier les indicateurs spécifiques à la santé
            if "doctolib" in str(visual_analysis.get("visual_analysis_data", {})):
                conditions.append("doctolib")
                
        elif family_id == "retail":
            # Vérifier les indicateurs spécifiques au commerce
            if visual_quality < 5:
                conditions.append("site_sans_ia")
                
        elif family_id == "real_estate":
            # Vérifier les indicateurs spécifiques à l'immobilier
            if visual_quality < 6 and not has_popup:
                conditions.append("formulaire_sans_reponse")
                
        elif family_id == "b2b_services":
            # Vérifier les indicateurs spécifiques aux services B2B
            if visual_quality < 6:
                conditions.append("site_flou")
            if has_popup:
                conditions.append("surcharge")
                
        elif family_id == "construction":
            # Vérifier les indicateurs spécifiques à la construction
            conditions.append("gmb_actif")  # Par défaut, supposer que GMB est actif
            
        return conditions
    
    def run(self, input_data: Dict) -> Dict:
        """
        Point d'entrée principal de l'agent
        
        Args:
            input_data: Dictionnaire contenant les données d'entrée
                - action: Action à effectuer (classify, generate_approach)
                - niche: Nom de la niche
                - visual_analysis: Données d'analyse visuelle (optionnel)
                
        Returns:
            Dict contenant le résultat de l'opération demandée
        """
        action = input_data.get("action", "classify")
        niche = input_data.get("niche")
        
        if not niche:
            return {"error": "Le nom de la niche doit être spécifié"}
            
        if action == "classify":
            return self.classify_niche(niche)
        elif action == "generate_approach":
            visual_analysis = input_data.get("visual_analysis")
            return self.generate_personalized_approach(niche, visual_analysis)
        else:
            return {"error": f"Action inconnue: {action}"}

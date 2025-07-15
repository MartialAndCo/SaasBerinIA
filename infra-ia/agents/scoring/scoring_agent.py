"""
Module du ScoringAgent - Agent qui attribue un score aux leads (REFONTE TPE/PME)
"""
import os
import json
from typing import Dict, Any, Optional, List
import datetime

from core.agent_base import Agent
from utils.llm import LLMService

class ScoringAgent(Agent):
    """
    ScoringAgent - Agent qui attribue un score intelligent aux leads avec LLM (TPE/PME focus)
    
    Cet agent est responsable de:
    - Évaluer la qualité des leads selon des critères business TPE/PME
    - Attribuer un score de 0 à 10 à chaque lead avec intelligence contextuelle
    - Déterminer la probabilité de conversion adaptée aux petites entreprises
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du ScoringAgent - MAINTENANT 100% LLM INTELLIGENT
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("ScoringAgent", config_path)
        
        # État de l'agent
        self.scoring_stats = {
            "total_leads_scored": 0,
            "avg_score": 0.0,
            "high_quality_leads": 0,
            "medium_quality_leads": 0,
            "low_quality_leads": 0
        }
        
        # Configuration LLM pour scoring intelligent
        self.llm_scoring_enabled = self.config.get("llm_scoring_enabled", True)
        self.scoring_complexity = self.config.get("scoring_complexity", "medium")
        
        # Configuration business TPE/PME
        self.business_model = self.config.get("business_model", "tpe_pme_ai_solutions")
        self.target_sectors = self.config.get("target_sectors", [
            "salon de coiffure", "garage automobile", "restaurant", 
            "cabinet médical", "cabinet dentaire", "plombier", "électricien",
            "commerce de proximité", "artisan", "services locaux"
        ])
        
        # Seuils de qualité (adaptés TPE/PME)
        self.quality_thresholds = self.config.get("quality_thresholds", {
            "high_quality": 7.0,
            "medium_quality": 4.0,
            "minimum_score": 1.0
        })
        
        self.speak("ScoringAgent initialisé avec intelligence LLM pour business TPE/PME", target="QualificationSupervisor")
    
    def score_leads(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attribue un score intelligent à chaque lead de la liste
        
        Args:
            input_data: Données d'entrée contenant les leads à scorer
            
        Returns:
            Leads avec scores attribués
        """
        leads = input_data.get("leads", [])
        niche = input_data.get("niche", "")
        context = input_data.get("context", {})
        
        if not leads:
            return {
                "status": "error",
                "message": "Aucun lead à scorer",
                "leads": []
            }
        
        self.speak(f"Scoring intelligent de {len(leads)} leads pour la niche '{niche}'", target="QualificationSupervisor")
        
        scored_leads = []
        total_score = 0.0
        high_quality = 0
        medium_quality = 0
        low_quality = 0
        
        for lead in leads:
            # Attribution d'un score intelligent au lead
            scored_lead = self._score_lead_with_llm(lead, niche, context)
            
            # Ajout du lead scoré à la liste
            scored_leads.append(scored_lead)
            
            # Mise à jour des statistiques
            score = scored_lead.get("score", 0)
            total_score += score
            
            if score >= self.quality_thresholds["high_quality"]:
                high_quality += 1
            elif score >= self.quality_thresholds["medium_quality"]:
                medium_quality += 1
            else:
                low_quality += 1
        
        # Mise à jour des statistiques globales
        count = len(leads)
        self.scoring_stats["total_leads_scored"] += count
        if self.scoring_stats["total_leads_scored"] > 0:
            total_previous = self.scoring_stats["total_leads_scored"] - count
            self.scoring_stats["avg_score"] = ((self.scoring_stats["avg_score"] * total_previous) + total_score) / self.scoring_stats["total_leads_scored"]
        self.scoring_stats["high_quality_leads"] += high_quality
        self.scoring_stats["medium_quality_leads"] += medium_quality
        self.scoring_stats["low_quality_leads"] += low_quality
        
        # Tri des leads par score (optionnel)
        if self.config.get("sort_by_score", True):
            scored_leads = sorted(scored_leads, key=lambda x: x.get("score", 0), reverse=True)
        
        # Log des résultats
        avg_score = total_score / count if count > 0 else 0
        self.speak(
            f"Scoring LLM terminé: {count} leads, score moyen: {avg_score:.1f}, {high_quality} high, {medium_quality} medium, {low_quality} low",
            target="QualificationSupervisor"
        )
        
        return {
            "status": "success",
            "niche": niche,
            "leads": scored_leads,
            "stats": {
                "count": count,
                "avg_score": avg_score,
                "high_quality": high_quality,
                "medium_quality": medium_quality,
                "low_quality": low_quality
            }
        }
    
    def _score_lead_with_llm(self, lead: Dict[str, Any], niche: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Attribue un score intelligent à un lead avec LLM (TPE/PME focus)
        
        Args:
            lead: Le lead à scorer
            niche: La niche du lead
            context: Contexte additionnel pour le scoring
            
        Returns:
            Lead avec un score et des détails sur le scoring
        """
        # Copie du lead pour ne pas modifier l'original
        scored_lead = lead.copy()
        
        if self.llm_scoring_enabled:
            try:
                # Scoring avec LLM intelligent
                score_result = self._get_llm_score(lead, niche, context)
                
                scored_lead["score"] = score_result["score"]
                scored_lead["score_reasoning"] = score_result["reasoning"]
                scored_lead["score_details"] = score_result["details"]
                scored_lead["conversion_probability"] = score_result["conversion_probability"]
                
            except Exception as e:
                self.speak(f"Erreur LLM scoring pour lead {lead.get('lead_id', 'unknown')}: {str(e)}", target="QualificationSupervisor")
                # Fallback vers scoring basique
                scored_lead = self._score_lead_fallback(lead, niche)
        else:
            # Scoring basique si LLM désactivé
            scored_lead = self._score_lead_fallback(lead, niche)
        
        # Horodatage
        scored_lead["scoring_date"] = datetime.datetime.now().isoformat()
        scored_lead["scoring_method"] = "llm" if self.llm_scoring_enabled else "fallback"
        
        return scored_lead
    
    def _get_llm_score(self, lead: Dict[str, Any], niche: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Utilise le LLM pour scorer un lead de manière intelligente
        
        Args:
            lead: Le lead à scorer
            niche: La niche du lead
            context: Contexte additionnel
            
        Returns:
            Résultat du scoring avec score, raisonnement et détails
        """
        # Construction du prompt intelligent pour TPE/PME
        # CORRECTION BUG: Conversion des datetime en string pour JSON
        lead_copy = self._convert_datetime_to_string(lead.copy())
        lead_info = json.dumps(lead_copy, indent=2, ensure_ascii=False)
        
        prompt = f"""
Tu es un expert en scoring de leads pour des solutions IA destinées aux TPE/PME françaises.

BUSINESS MODEL : 
Nous vendons des solutions d'automatisation IA (chatbots, téléphones IA, répondeurs intelligents) aux petites entreprises : artisans, commerçants, professions libérales, PME.

LEAD À SCORER :
{lead_info}

NICHE CIBLÉE : {niche}

CRITÈRES DE SCORING TPE/PME (score de 0 à 10) :

1. POUVOIR DE DÉCISION (30%) :
   - Patron/gérant/dirigeant = score élevé (même petite entreprise)
   - "Fondateur salon de coiffure" = 9/10 (décideur direct)
   - "Manager PME" = 7/10 (influence forte)
   - "Assistant" = 4/10 (peut orienter vers décideur)

2. ADÉQUATION BUSINESS (30%) :
   - Secteur parfait pour l'IA : cabinet médical, garage, salon = 9/10
   - Secteur compatible : restaurant, commerce = 7/10
   - Secteur moins adapté : industrie lourde = 4/10

3. TAILLE ENTREPRISE (20%) :
   - TPE/PME (1-50 salariés) = SCORE ÉLEVÉ (notre cible)
   - Artisan indépendant = 9/10
   - Commerce local = 8/10
   - Grande entreprise = 5/10 (pas notre cible principale)

4. QUALITÉ CONTACT (20%) :
   - Email perso patron TPE = OK (8/10) - "coiffure.martin@gmail.com" = normal
   - Email pro entreprise = 9/10
   - Téléphone direct = bonus
   - Données complètes = bonus

INSTRUCTIONS :
- Une petite entreprise avec un patron contactable = EXCELLENT SCORE
- Email Gmail d'un artisan = NORMAL, pas pénalisant
- Privilégier accessibilité du décideur vs taille entreprise
- Comprendre les enjeux TPE : simplicité, ROI rapide, gain de temps

Réponds UNIQUEMENT en JSON :
{{
  "score": X.X (nombre entre 0 et 10),
  "reasoning": "Explication courte du score attribué",
  "details": {{
    "decision_power": X.X,
    "business_fit": X.X,
    "company_size": X.X,
    "contact_quality": X.X
  }},
  "conversion_probability": X.X (probabilité de 0 à 1),
  "key_strengths": ["point fort 1", "point fort 2"],
  "potential_concerns": ["préoccupation 1", "préoccupation 2"]
}}
"""
        
        try:
            # Appel au LLM
            response = LLMService.call_llm(prompt, complexity=self.scoring_complexity)
            
            # Parsing de la réponse JSON
            try:
                result = json.loads(response.strip())
                
                # Validation des données
                score = float(result.get("score", 5.0))
                score = max(0.0, min(10.0, score))  # Clamp entre 0 et 10
                
                conversion_prob = float(result.get("conversion_probability", 0.5))
                conversion_prob = max(0.0, min(1.0, conversion_prob))  # Clamp entre 0 et 1
                
                return {
                    "score": round(score, 1),
                    "reasoning": result.get("reasoning", "Score attribué par LLM"),
                    "details": result.get("details", {}),
                    "conversion_probability": round(conversion_prob, 2),
                    "key_strengths": result.get("key_strengths", []),
                    "potential_concerns": result.get("potential_concerns", [])
                }
                
            except json.JSONDecodeError:
                # Si la réponse n'est pas du JSON valide, extraire le score manuellement
                import re
                score_match = re.search(r'"score":\s*([0-9.]+)', response)
                if score_match:
                    score = float(score_match.group(1))
                    score = max(0.0, min(10.0, score))
                    return {
                        "score": round(score, 1),
                        "reasoning": "Score extrait de réponse LLM non-JSON",
                        "details": {},
                        "conversion_probability": 0.5,
                        "key_strengths": [],
                        "potential_concerns": []
                    }
                else:
                    raise ValueError("Impossible d'extraire le score de la réponse LLM")
            
        except Exception as e:
            self.speak(f"Erreur lors du scoring LLM: {str(e)}", target="QualificationSupervisor")
            raise e
    
    def _convert_datetime_to_string(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CORRECTION BUG: Convertit récursivement tous les objets datetime en strings
        pour éviter les erreurs JSON "Object of type datetime is not JSON serializable"
        
        Args:
            data: Dictionnaire contenant potentiellement des objets datetime
            
        Returns:
            Dictionnaire avec les datetime convertis en strings
        """
        if isinstance(data, dict):
            return {k: self._convert_datetime_to_string(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_datetime_to_string(item) for item in data]
        elif isinstance(data, datetime.datetime):
            return data.isoformat()
        elif isinstance(data, datetime.date):
            return data.isoformat()
        else:
            return data
    
    def _score_lead_fallback(self, lead: Dict[str, Any], niche: str) -> Dict[str, Any]:
        """
        Méthode de scoring de secours (simple mais adaptée TPE/PME)
        
        Args:
            lead: Le lead à scorer
            niche: La niche du lead
            
        Returns:
            Lead scoré avec méthode simple
        """
        scored_lead = lead.copy()
        
        # Scoring simple mais intelligent pour TPE/PME
        score = 5.0  # Score de base
        reasoning_parts = []
        
        # Vérification des champs essentiels
        if lead.get("email"):
            score += 1.0
            reasoning_parts.append("Email présent")
        
        if lead.get("company"):
            score += 1.0
            reasoning_parts.append("Entreprise identifiée")
        
        if lead.get("first_name") and lead.get("last_name"):
            score += 0.5
            reasoning_parts.append("Contact personnalisé")
        
        # Bonus pour TPE/PME (logique inversée par rapport à l'ancien système)
        position = lead.get("position", "").lower()
        if any(word in position for word in ["patron", "gérant", "directeur", "fondateur", "owner"]):
            score += 2.0
            reasoning_parts.append("Décideur TPE/PME")
        elif any(word in position for word in ["manager", "responsable"]):
            score += 1.0
            reasoning_parts.append("Position de responsabilité")
        
        # Email perso acceptable pour TPE
        email = lead.get("email", "").lower()
        if any(domain in email for domain in ["gmail.com", "yahoo.com", "hotmail.com"]):
            score += 0.5  # Bonus au lieu de pénalité !
            reasoning_parts.append("Email personnel TPE (normal)")
        elif "@" in email and "." in email:
            score += 1.0
            reasoning_parts.append("Email professionnel")
        
        # Secteur compatible
        industry = lead.get("industry", "").lower()
        if any(sector in industry for sector in self.target_sectors):
            score += 1.5
            reasoning_parts.append("Secteur cible")
        
        # Limitation du score à 10
        score = min(10.0, score)
        
        scored_lead["score"] = round(score, 1)
        scored_lead["score_reasoning"] = "Scoring simple: " + ", ".join(reasoning_parts)
        scored_lead["score_details"] = {"method": "fallback", "base_score": 5.0, "adjustments": score - 5.0}
        scored_lead["conversion_probability"] = min(0.9, score / 10.0)
        
        return scored_lead
    
    def update_scoring_criteria(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour les paramètres de scoring
        
        Args:
            input_data: Nouvelles valeurs pour les paramètres
            
        Returns:
            Paramètres mis à jour
        """
        updates = input_data.get("updates", {})
        
        if not updates:
            return {
                "status": "error",
                "message": "Aucune mise à jour fournie",
                "current_config": {
                    "llm_scoring_enabled": self.llm_scoring_enabled,
                    "scoring_complexity": self.scoring_complexity,
                    "quality_thresholds": self.quality_thresholds
                }
            }
        
        # Mise à jour des paramètres
        if "llm_scoring_enabled" in updates:
            self.llm_scoring_enabled = updates["llm_scoring_enabled"]
            
        if "scoring_complexity" in updates:
            self.scoring_complexity = updates["scoring_complexity"]
            
        if "quality_thresholds" in updates:
            self.quality_thresholds.update(updates["quality_thresholds"])
            
        if "target_sectors" in updates:
            self.target_sectors = updates["target_sectors"]
        
        # Sauvegarde dans la configuration
        self.update_config("llm_scoring_enabled", self.llm_scoring_enabled)
        self.update_config("scoring_complexity", self.scoring_complexity)
        self.update_config("quality_thresholds", self.quality_thresholds)
        self.update_config("target_sectors", self.target_sectors)
        
        self.speak(f"Configuration de scoring mise à jour", target="QualificationSupervisor")
        
        return {
            "status": "success",
            "message": "Configuration de scoring mise à jour",
            "updated_config": {
                "llm_scoring_enabled": self.llm_scoring_enabled,
                "scoring_complexity": self.scoring_complexity,
                "quality_thresholds": self.quality_thresholds,
                "target_sectors": self.target_sectors
            }
        }
    
    def get_scoring_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de scoring
        
        Returns:
            Statistiques de scoring
        """
        return {
            "status": "success",
            "stats": self.scoring_stats,
            "config": {
                "llm_scoring_enabled": self.llm_scoring_enabled,
                "scoring_complexity": self.scoring_complexity,
                "quality_thresholds": self.quality_thresholds,
                "target_sectors": self.target_sectors
            }
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "score")
        
        if action == "score":
            return self.score_leads(input_data)
        
        elif action == "update_config":
            return self.update_scoring_criteria(input_data)
        
        elif action == "get_stats":
            return self.get_scoring_stats()
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du ScoringAgent
    agent = ScoringAgent()
    
    # Test de l'agent avec des données TPE/PME
    test_leads = [
        {
            "lead_id": "1",
            "first_name": "Marie",
            "last_name": "Dubois",
            "email": "marie.dubois.coiffure@gmail.com",
            "position": "Propriétaire",
            "company": "Salon Marie Coiffure",
            "company_website": "",
            "industry": "Salon de coiffure",
            "phone": "0123456789"
        },
        {
            "lead_id": "2",
            "first_name": "Pierre",
            "last_name": "Martin",
            "email": "contact@garage-martin.fr",
            "position": "Gérant",
            "company": "Garage Martin",
            "company_website": "https://www.garage-martin.fr",
            "industry": "Garage automobile",
            "phone": "0987654321"
        }
    ]
    
    result = agent.run({
        "action": "score",
        "leads": test_leads,
        "niche": "TPE services locaux"
    })
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

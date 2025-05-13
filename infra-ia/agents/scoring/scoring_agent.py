"""
Module du ScoringAgent - Agent qui attribue un score aux leads
"""
import os
import json
from typing import Dict, Any, Optional, List
import datetime

from core.agent_base import Agent
from utils.llm import LLMService

class ScoringAgent(Agent):
    """
    ScoringAgent - Agent qui attribue un score à chaque lead selon des critères business
    
    Cet agent est responsable de:
    - Évaluer la qualité des leads selon des critères prédéfinis
    - Attribuer un score de 0 à 10 à chaque lead
    - Déterminer la probabilité de conversion
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du ScoringAgent
        
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
        
        # Chargement des critères de scoring
        self.scoring_criteria = self.config.get("scoring_criteria", {
            "position_weight": 0.3,
            "company_size_weight": 0.2,
            "email_quality_weight": 0.15,
            "data_completeness_weight": 0.15,
            "industry_fit_weight": 0.2
        })
        
        # Dictionnaires de scoring
        self.position_scores = self.config.get("position_scores", {
            "CEO": 10,
            "CTO": 9,
            "CFO": 9,
            "CMO": 8,
            "COO": 8,
            "Founder": 10,
            "Co-founder": 9,
            "Owner": 9,
            "Director": 7,
            "VP": 7,
            "Head of": 6,
            "Manager": 5
        })
        
        self.company_size_scores = self.config.get("company_size_scores", {
            "1-10": 3,
            "11-50": 5,
            "51-200": 7,
            "201-500": 9,
            "501-1000": 8,
            "1001-5000": 6,
            "5001-10000": 4,
            "10000+": 3
        })
    
    def score_leads(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attribue un score à chaque lead de la liste
        
        Args:
            input_data: Données d'entrée contenant les leads à scorer
            
        Returns:
            Leads avec scores attribués
        """
        leads = input_data.get("leads", [])
        niche = input_data.get("niche", "")
        
        if not leads:
            return {
                "status": "error",
                "message": "Aucun lead à scorer",
                "leads": []
            }
        
        self.speak(f"Scoring de {len(leads)} leads pour la niche '{niche}'", target="QualificationSupervisor")
        
        scored_leads = []
        total_score = 0.0
        high_quality = 0
        medium_quality = 0
        low_quality = 0
        
        for lead in leads:
            # Attribution d'un score au lead
            scored_lead = self._score_lead(lead, niche)
            
            # Ajout du lead scoré à la liste
            scored_leads.append(scored_lead)
            
            # Mise à jour des statistiques
            score = scored_lead.get("score", 0)
            total_score += score
            
            if score >= 7:
                high_quality += 1
            elif score >= 5:
                medium_quality += 1
            else:
                low_quality += 1
        
        # Mise à jour des statistiques globales
        count = len(leads)
        self.scoring_stats["total_leads_scored"] += count
        self.scoring_stats["avg_score"] = ((self.scoring_stats["avg_score"] * (self.scoring_stats["total_leads_scored"] - count)) + total_score) / self.scoring_stats["total_leads_scored"] if self.scoring_stats["total_leads_scored"] > 0 else 0
        self.scoring_stats["high_quality_leads"] += high_quality
        self.scoring_stats["medium_quality_leads"] += medium_quality
        self.scoring_stats["low_quality_leads"] += low_quality
        
        # Tri des leads par score (optionnel)
        if self.config.get("sort_by_score", True):
            scored_leads = sorted(scored_leads, key=lambda x: x.get("score", 0), reverse=True)
        
        # Log des résultats
        avg_score = total_score / count if count > 0 else 0
        self.speak(
            f"Scoring terminé: {count} leads, score moyen: {avg_score:.1f}, {high_quality} high, {medium_quality} medium, {low_quality} low",
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
    
    def _score_lead(self, lead: Dict[str, Any], niche: str) -> Dict[str, Any]:
        """
        Attribue un score à un lead individuel
        
        Args:
            lead: Le lead à scorer
            niche: La niche du lead
            
        Returns:
            Lead avec un score et des détails sur le scoring
        """
        # Copie du lead pour ne pas modifier l'original
        scored_lead = lead.copy()
        score_details = {}
        
        # 1. Score basé sur la position
        position_score = 0
        if "position" in lead and lead["position"]:
            position = lead["position"]
            
            # Recherche de correspondance exacte ou partielle
            if position in self.position_scores:
                position_score = self.position_scores[position]
            else:
                # Recherche par mots-clés
                for key, value in self.position_scores.items():
                    if key.lower() in position.lower():
                        position_score = value
                        break
            
            # Score par défaut si aucune correspondance
            if position_score == 0:
                position_score = 3  # Score de base pour position inconnue
        
        # 2. Score basé sur la taille de l'entreprise
        company_size_score = 0
        if "company_size" in lead and lead["company_size"]:
            company_size = lead["company_size"]
            company_size_score = self.company_size_scores.get(company_size, 5)  # Valeur par défaut: 5
        
        # 3. Score basé sur la qualité de l'email
        email_quality_score = 0
        if "email" in lead and lead["email"]:
            email = lead["email"].lower()
            
            # Email professionnel vs personnel
            if any(domain in email for domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]):
                email_quality_score = 3  # Email personnel
            else:
                email_quality_score = 8  # Email professionnel
                
                # Bonus pour email direct (vs email générique)
                if any(prefix in email for prefix in ["contact@", "info@", "hello@", "support@"]):
                    email_quality_score = 5  # Email générique
        
        # 4. Score basé sur la complétude des données
        data_completeness_score = 0
        required_fields = [
            "email", "first_name", "last_name", "company", "position", 
            "company_website", "company_size", "industry", "country"
        ]
        
        filled_fields = sum(1 for field in required_fields if field in lead and lead[field])
        data_completeness_score = (filled_fields / len(required_fields)) * 10
        
        # 5. Score basé sur l'adéquation du secteur d'activité
        industry_fit_score = 0
        if "industry" in lead and lead["industry"]:
            # Utilisation de LLM pour évaluer l'adéquation
            if self.config.get("use_llm_for_industry_fit", False):
                industry_fit_score = self._evaluate_industry_fit_with_llm(lead["industry"], niche)
            else:
                # Logique simple de scoring par défaut
                relevant_industries = self.config.get("relevant_industries", {}).get(niche, [])
                
                if lead["industry"] in relevant_industries:
                    industry_fit_score = 9  # Haute pertinence
                else:
                    # Recherche par mots-clés
                    industry_keywords = self.config.get("industry_keywords", {}).get(niche, [])
                    if any(keyword.lower() in lead["industry"].lower() for keyword in industry_keywords):
                        industry_fit_score = 7  # Pertinence moyenne
                    else:
                        industry_fit_score = 5  # Pertinence faible
        
        # Calcul du score final pondéré
        weighted_scores = {
            "position": position_score * self.scoring_criteria.get("position_weight", 0.3),
            "company_size": company_size_score * self.scoring_criteria.get("company_size_weight", 0.2),
            "email_quality": email_quality_score * self.scoring_criteria.get("email_quality_weight", 0.15),
            "data_completeness": data_completeness_score * self.scoring_criteria.get("data_completeness_weight", 0.15),
            "industry_fit": industry_fit_score * self.scoring_criteria.get("industry_fit_weight", 0.2)
        }
        
        # Score final (arrondi à 1 décimale)
        final_score = round(sum(weighted_scores.values()), 1)
        
        # Stockage des détails du scoring dans le lead
        scored_lead["score"] = final_score
        scored_lead["score_details"] = weighted_scores
        scored_lead["scoring_date"] = datetime.datetime.now().isoformat()
        
        return scored_lead
    
    def _evaluate_industry_fit_with_llm(self, industry: str, niche: str) -> float:
        """
        Évalue l'adéquation entre un secteur d'activité et une niche en utilisant un LLM
        
        Args:
            industry: Le secteur d'activité du lead
            niche: La niche ciblée
            
        Returns:
            Score d'adéquation de 0 à 10
        """
        # Construction du prompt pour le LLM
        prompt = f"""
        Évalue la pertinence du secteur d'activité "{industry}" pour une prospection B2B ciblant la niche "{niche}".
        Donne un score de 0 à 10, où:
        - 0-3: Faible pertinence, peu d'intérêt pour cette offre
        - 4-6: Pertinence moyenne, potentiellement intéressé
        - 7-10: Haute pertinence, cible idéale
        
        Réponds uniquement avec un nombre entre 0 et 10.
        """
        
        try:
            # Appel au LLM
            response = LLMService.call_llm(prompt, complexity="low")
            
            # Extraction du score (en supposant que le LLM répond avec un nombre)
            score = float(response.strip())
            
            # Validation du score
            score = max(0, min(10, score))  # Clamp entre 0 et 10
            
            return score
            
        except Exception as e:
            # En cas d'erreur, retourne un score par défaut
            self.speak(f"Erreur lors de l'évaluation de l'adéquation avec LLM: {str(e)}", target="QualificationSupervisor")
            return 5.0  # Score moyen par défaut
    
    def update_scoring_criteria(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour les critères de scoring
        
        Args:
            input_data: Nouvelles valeurs pour les critères
            
        Returns:
            Critères mis à jour
        """
        criteria = input_data.get("criteria", {})
        
        if not criteria:
            return {
                "status": "error",
                "message": "Aucun critère fourni",
                "scoring_criteria": self.scoring_criteria
            }
        
        # Mise à jour des critères spécifiés
        for key, value in criteria.items():
            self.scoring_criteria[key] = value
        
        # Validation que la somme des poids est égale à 1
        total_weight = sum(self.scoring_criteria.values())
        if abs(total_weight - 1.0) > 0.01:  # Tolérance de 0.01
            # Normalisation des poids
            for key in self.scoring_criteria:
                self.scoring_criteria[key] /= total_weight
        
        # Sauvegarde dans la configuration
        self.update_config("scoring_criteria", self.scoring_criteria)
        
        self.speak(f"Critères de scoring mis à jour: {json.dumps(self.scoring_criteria)}", target="QualificationSupervisor")
        
        return {
            "status": "success",
            "message": "Critères de scoring mis à jour",
            "scoring_criteria": self.scoring_criteria
        }
    
    def get_scoring_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de scoring
        
        Returns:
            Statistiques de scoring
        """
        return {
            "status": "success",
            "stats": self.scoring_stats
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
        
        elif action == "update_criteria":
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
    
    # Test de l'agent avec des données de test
    test_leads = [
        {
            "lead_id": "1",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "position": "CEO",
            "company": "Test Company",
            "company_website": "https://www.testcompany.com",
            "company_size": "51-200",
            "industry": "Technology",
            "country": "France"
        },
        {
            "lead_id": "2",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "info@anothercompany.com",
            "position": "Marketing Manager",
            "company": "Another Company",
            "company_website": "https://www.anothercompany.com",
            "company_size": "11-50",
            "industry": "Marketing",
            "country": "France"
        }
    ]
    
    result = agent.run({
        "action": "score",
        "leads": test_leads,
        "niche": "test"
    })
    
    print(json.dumps(result, indent=2))

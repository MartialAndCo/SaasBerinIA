"""
Module du QualificationSupervisor - Superviseur des agents de qualification des leads
"""
import os
import json
from typing import Dict, Any, Optional, List
import datetime

from core.agent_base import Agent
from utils.llm import LLMService

class QualificationSupervisor(Agent):
    """
    QualificationSupervisor - Superviseur des agents qui analysent et valident les leads
    
    Ce superviseur est responsable de:
    - Coordonner les agents de qualification
    - Appliquer les règles business (score, email pro, entreprise identifiable...)
    - Décider du rejet ou de l'acceptation des leads
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du QualificationSupervisor
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("QualificationSupervisor", config_path)
        
        # État du superviseur
        self.qualification_stats = {
            "total_processed": 0,
            "qualified": 0,
            "rejected": 0,
            "blacklisted": 0
        }
        
        # Chargement des critères de qualification
        self.qualification_criteria = self.config.get("qualification_criteria", {
            "min_score": 5.0,
            "require_professional_email": True,
            "require_company_website": True,
            "valid_company_sizes": ["11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10000+"]
        })
        
        # Chargement des domaines blacklistés
        self.blacklisted_domains = self.config.get("blacklisted_domains", [])
    
    def coordinate_qualification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordonne le processus de qualification complet des leads
        
        Args:
            input_data: Données d'entrée avec les leads à qualifier
            
        Returns:
            Leads qualifiés et rejetés
        """
        leads = input_data.get("leads", [])
        niche = input_data.get("niche", "")
        
        if not leads:
            return {
                "status": "error",
                "message": "Aucun lead à qualifier",
                "leads": []
            }
        
        self.speak(f"Coordination de la qualification de {len(leads)} leads pour la niche '{niche}'", target="OverseerAgent")
        
        # Étape 1: Vérification des doublons par le DuplicateCheckerAgent
        from agents.overseer.overseer_agent import OverseerAgent
        overseer = OverseerAgent()
        
        duplicate_check_result = overseer.execute_agent("DuplicateCheckerAgent", {
            "leads": leads,
            "niche": niche
        })
        
        if duplicate_check_result.get("status") != "success":
            self.speak(f"Erreur lors de la vérification des doublons: {duplicate_check_result.get('message')}", target="OverseerAgent")
            return duplicate_check_result
        
        # Récupération des leads sans doublons
        unique_leads = duplicate_check_result.get("unique_leads", [])
        duplicates = duplicate_check_result.get("duplicates", [])
        
        self.speak(f"{len(duplicates)} doublons identifiés sur {len(leads)} leads", target="OverseerAgent")
        
        # Étape 2: Validation des leads par le ValidatorAgent
        validation_result = overseer.execute_agent("ValidatorAgent", {
            "leads": unique_leads,
            "niche": niche,
            "criteria": self.qualification_criteria
        })
        
        if validation_result.get("status") != "success":
            self.speak(f"Erreur lors de la validation des leads: {validation_result.get('message')}", target="OverseerAgent")
            return validation_result
        
        # Récupération des leads valides et invalides
        valid_leads = validation_result.get("valid_leads", [])
        invalid_leads = validation_result.get("invalid_leads", [])
        
        self.speak(f"{len(valid_leads)} leads valides et {len(invalid_leads)} invalides identifiés", target="OverseerAgent")
        
        # Étape 3: Attribution d'un score aux leads valides par le ScoringAgent
        scoring_result = overseer.execute_agent("ScoringAgent", {
            "leads": valid_leads,
            "niche": niche
        })
        
        if scoring_result.get("status") != "success":
            self.speak(f"Erreur lors du scoring des leads: {scoring_result.get('message')}", target="OverseerAgent")
            return scoring_result
        
        # Récupération des leads avec score
        scored_leads = scoring_result.get("leads", [])
        
        # Étape 4: Filtrage final selon les critères de qualification
        qualified_leads = []
        rejected_leads = []
        
        for lead in scored_leads:
            score = lead.get("score", 0)
            
            if score >= self.qualification_criteria.get("min_score", 5.0):
                qualified_leads.append(lead)
            else:
                rejected_leads.append({
                    "lead": lead,
                    "reason": f"Score insuffisant: {score}"
                })
        
        # Mise à jour des statistiques
        self.qualification_stats["total_processed"] += len(leads)
        self.qualification_stats["qualified"] += len(qualified_leads)
        self.qualification_stats["rejected"] += len(rejected_leads) + len(invalid_leads)
        
        # Log des résultats
        self.speak(
            f"Qualification terminée: {len(qualified_leads)} qualifiés, {len(rejected_leads)} rejetés, {len(invalid_leads)} invalides, {len(duplicates)} doublons",
            target="OverseerAgent"
        )
        
        return {
            "status": "success",
            "niche": niche,
            "qualified_leads": qualified_leads,
            "rejected_leads": rejected_leads + invalid_leads,
            "duplicates": duplicates,
            "stats": {
                "total": len(leads),
                "qualified": len(qualified_leads),
                "rejected": len(rejected_leads),
                "invalid": len(invalid_leads),
                "duplicates": len(duplicates)
            }
        }
    
    def update_qualification_criteria(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour les critères de qualification
        
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
                "qualification_criteria": self.qualification_criteria
            }
        
        # Mise à jour des critères spécifiés
        for key, value in criteria.items():
            self.qualification_criteria[key] = value
        
        # Sauvegarde dans la configuration
        self.update_config("qualification_criteria", self.qualification_criteria)
        
        self.speak(f"Critères de qualification mis à jour: {json.dumps(criteria)}", target="OverseerAgent")
        
        return {
            "status": "success",
            "message": "Critères de qualification mis à jour",
            "qualification_criteria": self.qualification_criteria
        }
    
    def manage_blacklist(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère la liste noire des domaines à rejeter
        
        Args:
            input_data: Données pour la gestion de la blacklist
            
        Returns:
            État actuel de la blacklist
        """
        action = input_data.get("action", "list")
        
        if action == "list":
            return {
                "status": "success",
                "blacklisted_domains": self.blacklisted_domains
            }
        
        elif action == "add":
            domain = input_data.get("domain", "")
            if domain and domain not in self.blacklisted_domains:
                self.blacklisted_domains.append(domain)
                self.update_config("blacklisted_domains", self.blacklisted_domains)
                
                self.speak(f"Domaine {domain} ajouté à la blacklist", target="OverseerAgent")
                
                return {
                    "status": "success",
                    "message": f"Domaine {domain} ajouté à la blacklist",
                    "blacklisted_domains": self.blacklisted_domains
                }
            else:
                return {
                    "status": "error",
                    "message": f"Domaine {domain} invalide ou déjà dans la blacklist",
                    "blacklisted_domains": self.blacklisted_domains
                }
        
        elif action == "remove":
            domain = input_data.get("domain", "")
            if domain in self.blacklisted_domains:
                self.blacklisted_domains.remove(domain)
                self.update_config("blacklisted_domains", self.blacklisted_domains)
                
                self.speak(f"Domaine {domain} retiré de la blacklist", target="OverseerAgent")
                
                return {
                    "status": "success",
                    "message": f"Domaine {domain} retiré de la blacklist",
                    "blacklisted_domains": self.blacklisted_domains
                }
            else:
                return {
                    "status": "error",
                    "message": f"Domaine {domain} non trouvé dans la blacklist",
                    "blacklisted_domains": self.blacklisted_domains
                }
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}",
                "blacklisted_domains": self.blacklisted_domains
            }
    
    def get_qualification_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de qualification
        
        Returns:
            Statistiques de qualification
        """
        return {
            "status": "success",
            "stats": self.qualification_stats
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "qualify")
        
        if action == "qualify":
            return self.coordinate_qualification(input_data)
        
        elif action == "update_criteria":
            return self.update_qualification_criteria(input_data)
        
        elif action == "manage_blacklist":
            return self.manage_blacklist(input_data)
        
        elif action == "get_stats":
            return self.get_qualification_stats()
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du QualificationSupervisor
    supervisor = QualificationSupervisor()
    
    # Test de l'agent
    result = supervisor.run({
        "action": "get_stats"
    })
    
    print(json.dumps(result, indent=2))

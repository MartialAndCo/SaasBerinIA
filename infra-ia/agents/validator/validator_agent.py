"""
Module du ValidatorAgent - Agent de validation des leads
"""
import os
import json
import re
from typing import Dict, Any, Optional, List
import datetime

from core.agent_base import Agent

class ValidatorAgent(Agent):
    """
    ValidatorAgent - Agent qui vérifie la validité des leads selon des critères business
    
    Cet agent est responsable de:
    - Vérifier que le lead est exploitable
    - Valider les critères business (email pro, site web, etc.)
    - Rejeter les leads non conformes
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du ValidatorAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("ValidatorAgent", config_path)
        
        # État de l'agent
        self.validation_stats = {
            "total_processed": 0,
            "valid": 0,
            "invalid": 0
        }
        
        # Expressions régulières pour les validations
        self.email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.url_regex = re.compile(r'^https?://(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)(?:/.*)?$')
    
    def validate_leads(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide une liste de leads selon les critères spécifiés
        
        Args:
            input_data: Données d'entrée contenant les leads à valider et les critères
            
        Returns:
            Leads valides et invalides
        """
        leads = input_data.get("leads", [])
        niche = input_data.get("niche", "")
        criteria = input_data.get("criteria", self.config.get("default_criteria", {}))
        
        if not leads:
            return {
                "status": "error",
                "message": "Aucun lead à valider",
                "leads": []
            }
        
        self.speak(f"Validation de {len(leads)} leads pour la niche '{niche}'", target="QualificationSupervisor")
        
        valid_leads = []
        invalid_leads = []
        
        for lead in leads:
            # Validation du lead selon les critères
            result = self._validate_lead(lead, criteria)
            
            if result["valid"]:
                valid_leads.append(lead)
            else:
                invalid_leads.append({
                    "lead": lead,
                    "reason": result["reason"]
                })
        
        # Mise à jour des statistiques
        self.validation_stats["total_processed"] += len(leads)
        self.validation_stats["valid"] += len(valid_leads)
        self.validation_stats["invalid"] += len(invalid_leads)
        
        # Log des résultats
        self.speak(
            f"Validation terminée: {len(valid_leads)} valides, {len(invalid_leads)} invalides",
            target="QualificationSupervisor"
        )
        
        return {
            "status": "success",
            "niche": niche,
            "valid_leads": valid_leads,
            "invalid_leads": invalid_leads,
            "stats": {
                "total": len(leads),
                "valid": len(valid_leads),
                "invalid": len(invalid_leads)
            }
        }
    
    def _validate_lead(self, lead: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide un lead individuel selon les critères
        
        Args:
            lead: Le lead à valider
            criteria: Les critères de validation
            
        Returns:
            Résultat de la validation avec statut et raison si invalide
        """
        # Vérification des champs obligatoires
        required_fields = self.config.get("required_fields", ["email", "first_name", "last_name", "company"])
        missing_fields = [field for field in required_fields if not lead.get(field)]
        
        if missing_fields:
            return {
                "valid": False,
                "reason": f"Champs obligatoires manquants: {', '.join(missing_fields)}"
            }
        
        # Vérification de l'email professionnel
        if criteria.get("require_professional_email", True) and "email" in lead:
            email = lead["email"].lower()
            domain = email.split("@")[-1] if "@" in email else ""
            
            # Blacklist de domaines non professionnels
            blacklisted_domains = self.config.get("blacklisted_domains", []) + criteria.get("blacklisted_domains", [])
            
            if domain in blacklisted_domains:
                return {
                    "valid": False,
                    "reason": f"Email non professionnel (domaine blacklisté: {domain})"
                }
        
        # Vérification du site web de l'entreprise
        if criteria.get("require_company_website", True) and (
            "company_website" not in lead or not lead["company_website"]
        ):
            return {
                "valid": False,
                "reason": "Site web de l'entreprise manquant"
            }
        
        # Vérification du poste
        if criteria.get("require_position", True) and (
            "position" not in lead or not lead["position"]
        ):
            return {
                "valid": False,
                "reason": "Poste/Position manquant"
            }
        
        # Vérification de la taille de l'entreprise
        if "valid_company_sizes" in criteria and "company_size" in lead:
            if lead["company_size"] not in criteria["valid_company_sizes"]:
                return {
                    "valid": False,
                    "reason": f"Taille d'entreprise non ciblée: {lead['company_size']}"
                }
        
        # Vérification du secteur d'activité
        if criteria.get("require_industry", True) and (
            "industry" not in lead or not lead["industry"]
        ):
            return {
                "valid": False,
                "reason": "Secteur d'activité manquant"
            }
        
        # Vérification de la complétion des champs
        if "min_fields_completion" in criteria:
            required_completion_fields = self.config.get("completion_fields", [
                "email", "first_name", "last_name", "company", "position", "industry", 
                "company_website", "company_size", "country"
            ])
            
            filled_fields = sum(1 for field in required_completion_fields if field in lead and lead[field])
            completion_rate = filled_fields / len(required_completion_fields)
            
            if completion_rate < criteria["min_fields_completion"]:
                return {
                    "valid": False,
                    "reason": f"Taux de complétion insuffisant: {completion_rate:.0%} (minimum requis: {criteria['min_fields_completion']:.0%})"
                }
        
        # Toutes les validations ont réussi
        return {
            "valid": True
        }
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de validation
        
        Returns:
            Statistiques de validation
        """
        return {
            "status": "success",
            "stats": self.validation_stats
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "validate")
        
        if action == "validate":
            return self.validate_leads(input_data)
        
        elif action == "get_stats":
            return self.get_validation_stats()
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du ValidatorAgent
    agent = ValidatorAgent()
    
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
            "email": "jane.smith@gmail.com",  # Email non professionnel
            "position": "CTO",
            "company": "Another Company",
            "company_size": "201-500",
            "industry": "Finance",
            "country": "France"
        }
    ]
    
    result = agent.run({
        "action": "validate",
        "leads": test_leads,
        "niche": "test"
    })
    
    print(json.dumps(result, indent=2))

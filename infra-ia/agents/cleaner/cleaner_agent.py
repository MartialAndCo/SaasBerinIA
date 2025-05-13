"""
Module du CleanerAgent - Agent de nettoyage des leads
"""
import os
import json
import re
from typing import Dict, Any, Optional, List
import datetime

from core.agent_base import Agent
from utils.llm import LLMService

class CleanerAgent(Agent):
    """
    CleanerAgent - Agent qui nettoie les leads bruts récupérés par le ScraperAgent
    
    Cet agent est responsable de:
    - Nettoyer et standardiser les données des leads
    - Vérifier la validité des emails
    - Compléter les données manquantes lorsque possible
    - Préparer les leads pour la qualification
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du CleanerAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("CleanerAgent", config_path)
        
        # État de l'agent
        self.cleaning_stats = {
            "total_leads_processed": 0,
            "valid_leads": 0,
            "invalid_leads": 0,
            "fixed_leads": 0
        }
        
        # Expressions régulières pour les validations
        self.email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.url_regex = re.compile(r'^https?://(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)(?:/.*)?$')
    
    def clean_leads(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nettoie une liste de leads
        
        Args:
            input_data: Données d'entrée contenant les leads à nettoyer
            
        Returns:
            Leads nettoyés
        """
        leads = input_data.get("leads", [])
        niche = input_data.get("niche", "")
        
        if not leads:
            return {
                "status": "error",
                "message": "Aucun lead à nettoyer",
                "leads": []
            }
        
        self.speak(f"Nettoyage de {len(leads)} leads pour la niche '{niche}'", target="ScrapingSupervisor")
        
        cleaned_leads = []
        invalid_leads = []
        fixed_leads = []
        
        for lead in leads:
            # Validation et nettoyage du lead
            result = self._clean_lead(lead)
            
            if result["status"] == "valid":
                cleaned_leads.append(result["lead"])
            elif result["status"] == "fixed":
                fixed_leads.append(result["lead"])
                cleaned_leads.append(result["lead"])
            else:
                invalid_leads.append({
                    "lead": lead,
                    "reason": result["reason"]
                })
        
        # Mise à jour des statistiques
        self.cleaning_stats["total_leads_processed"] += len(leads)
        self.cleaning_stats["valid_leads"] += len(cleaned_leads)
        self.cleaning_stats["invalid_leads"] += len(invalid_leads)
        self.cleaning_stats["fixed_leads"] += len(fixed_leads)
        
        # Log des résultats
        self.speak(
            f"Nettoyage terminé: {len(cleaned_leads)} valides, {len(invalid_leads)} invalides, {len(fixed_leads)} corrigés",
            target="ScrapingSupervisor"
        )
        
        return {
            "status": "success",
            "niche": niche,
            "leads": cleaned_leads,
            "invalid_leads": invalid_leads,
            "stats": {
                "total": len(leads),
                "valid": len(cleaned_leads),
                "invalid": len(invalid_leads),
                "fixed": len(fixed_leads)
            }
        }
    
    def _clean_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nettoie un lead individuel
        
        Args:
            lead: Lead à nettoyer
            
        Returns:
            Statut du nettoyage et lead nettoyé ou raison de l'invalidité
        """
        # Copie du lead pour ne pas modifier l'original
        cleaned_lead = lead.copy()
        fixed_fields = []
        
        # Vérification des champs obligatoires
        required_fields = self.config.get("required_fields", ["email", "first_name", "last_name", "company"])
        missing_fields = [field for field in required_fields if not cleaned_lead.get(field)]
        
        if missing_fields and not self.config.get("allow_incomplete_leads", False):
            return {
                "status": "invalid",
                "reason": f"Champs obligatoires manquants: {', '.join(missing_fields)}",
                "lead": cleaned_lead
            }
        
        # Nettoyage et normalisation des champs
        
        # 1. Email
        if "email" in cleaned_lead:
            # Passage en minuscules et suppression des espaces
            email = cleaned_lead["email"].lower().strip()
            
            # Validation de l'email
            if not self.email_regex.match(email):
                if self.config.get("reject_invalid_emails", True):
                    return {
                        "status": "invalid",
                        "reason": "Email invalide",
                        "lead": cleaned_lead
                    }
            else:
                # Email valide, on le met à jour
                if email != cleaned_lead["email"]:
                    cleaned_lead["email"] = email
                    fixed_fields.append("email")
        
        # 2. Noms
        for field in ["first_name", "last_name"]:
            if field in cleaned_lead and cleaned_lead[field]:
                # Capitalisation du nom (première lettre en majuscule)
                name = cleaned_lead[field].strip()
                capitalized = name.capitalize()
                
                if capitalized != cleaned_lead[field]:
                    cleaned_lead[field] = capitalized
                    fixed_fields.append(field)
        
        # 3. Nom de l'entreprise
        if "company" in cleaned_lead and cleaned_lead["company"]:
            company = cleaned_lead["company"].strip()
            
            # Suppression des suffixes légaux communs si configuré ainsi
            if self.config.get("strip_legal_suffixes", True):
                suffixes = ["Inc", "LLC", "Ltd", "SARL", "SAS", "SA", "GmbH"]
                for suffix in suffixes:
                    if company.endswith(f" {suffix}"):
                        company = company[:-len(suffix)].strip()
                        fixed_fields.append("company")
            
            if company != cleaned_lead["company"]:
                cleaned_lead["company"] = company
                fixed_fields.append("company")
        
        # 4. Site web de l'entreprise
        if "company_website" in cleaned_lead and cleaned_lead["company_website"]:
            website = cleaned_lead["company_website"].strip().lower()
            
            # Ajout du protocole si manquant
            if not website.startswith(("http://", "https://")):
                website = "https://" + website
                fixed_fields.append("company_website")
            
            # Validation de l'URL
            if not self.url_regex.match(website):
                if self.config.get("fix_urls", True):
                    # Tentative de correction simple
                    website = re.sub(r'\s+', '', website)  # Suppression des espaces
                    
                    if not self.url_regex.match(website):
                        # Si toujours invalide, on extrait simplement le domaine à partir de l'email
                        if "email" in cleaned_lead and "@" in cleaned_lead["email"]:
                            domain = cleaned_lead["email"].split("@")[1]
                            website = f"https://www.{domain}"
                            fixed_fields.append("company_website")
            
            if website != cleaned_lead["company_website"]:
                cleaned_lead["company_website"] = website
                if "company_website" not in fixed_fields:
                    fixed_fields.append("company_website")
        
        # 5. LinkedIn URL
        if "linkedin_url" in cleaned_lead and cleaned_lead["linkedin_url"]:
            linkedin = cleaned_lead["linkedin_url"].strip()
            
            # Correction de l'URL LinkedIn si nécessaire
            if not linkedin.startswith("https://www.linkedin.com/"):
                # Si c'est juste un username LinkedIn
                if not "/" in linkedin and not "." in linkedin:
                    linkedin = f"https://www.linkedin.com/in/{linkedin}"
                    fixed_fields.append("linkedin_url")
            
            if linkedin != cleaned_lead["linkedin_url"]:
                cleaned_lead["linkedin_url"] = linkedin
                if "linkedin_url" not in fixed_fields:
                    fixed_fields.append("linkedin_url")
        
        # Ajout des métadonnées de nettoyage
        cleaned_lead["cleaned"] = True
        cleaned_lead["cleaning_date"] = datetime.datetime.now().isoformat()
        
        if fixed_fields:
            cleaned_lead["fixed_fields"] = fixed_fields
            return {
                "status": "fixed",
                "lead": cleaned_lead,
                "fixed_fields": fixed_fields
            }
        else:
            return {
                "status": "valid",
                "lead": cleaned_lead
            }
    
    def complete_missing_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tente de compléter les données manquantes dans les leads en utilisant un LLM
        
        Args:
            input_data: Données d'entrée contenant les leads à compléter
            
        Returns:
            Leads avec données complétées
        """
        leads = input_data.get("leads", [])
        
        if not leads:
            return {
                "status": "error",
                "message": "Aucun lead à compléter",
                "leads": []
            }
        
        self.speak(f"Tentative de complétion des données manquantes pour {len(leads)} leads", target="ScrapingSupervisor")
        
        completed_leads = []
        completion_stats = {
            "attempted": 0,
            "succeeded": 0,
            "failed": 0
        }
        
        for lead in leads:
            # Vérification des champs manquants mais requis
            missing_fields = []
            for field in self.config.get("completion_fields", ["position", "company", "industry"]):
                if field not in lead or not lead[field]:
                    missing_fields.append(field)
            
            # Si aucun champ manquant, on garde le lead tel quel
            if not missing_fields:
                completed_leads.append(lead)
                continue
            
            # Si des champs manquent, tentative de complétion avec LLM
            completion_stats["attempted"] += 1
            
            # Construction du prompt avec le contexte du lead
            prompt = self.build_prompt({
                "action": "complete",
                "lead": lead,
                "missing_fields": missing_fields
            })
            
            try:
                # Appel au LLM pour compléter les données
                response = LLMService.call_llm(prompt, complexity="medium")
                
                # Parsing du résultat (supposé être au format JSON)
                completion_result = json.loads(response)
                
                # Mise à jour des champs manquants
                updated_lead = lead.copy()
                for field in missing_fields:
                    if field in completion_result and completion_result[field]:
                        updated_lead[field] = completion_result[field]
                
                # Ajout des métadonnées de complétion
                updated_lead["completion_date"] = datetime.datetime.now().isoformat()
                updated_lead["completed_fields"] = [f for f in missing_fields if f in completion_result]
                
                completed_leads.append(updated_lead)
                completion_stats["succeeded"] += 1
                
            except Exception as e:
                # En cas d'erreur, on garde le lead original
                self.speak(f"Erreur lors de la complétion des données: {str(e)}", target="ScrapingSupervisor")
                completed_leads.append(lead)
                completion_stats["failed"] += 1
        
        # Log des résultats
        self.speak(
            f"Complétion terminée: {completion_stats['succeeded']} réussis sur {completion_stats['attempted']} tentatives",
            target="ScrapingSupervisor"
        )
        
        return {
            "status": "success",
            "leads": completed_leads,
            "stats": completion_stats
        }
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de nettoyage
        
        Returns:
            Statistiques de nettoyage
        """
        return {
            "status": "success",
            "stats": self.cleaning_stats
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "clean")
        
        if action == "clean":
            result = self.clean_leads(input_data)
            
            # Si la complétion automatique est activée, on tente de compléter les données manquantes
            if self.config.get("auto_complete", False) and result["status"] == "success":
                completion_result = self.complete_missing_data({"leads": result["leads"]})
                
                if completion_result["status"] == "success":
                    result["leads"] = completion_result["leads"]
                    result["completion_stats"] = completion_result["stats"]
            
            return result
        
        elif action == "complete":
            return self.complete_missing_data(input_data)
        
        elif action == "get_stats":
            return self.get_cleaning_stats()
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du CleanerAgent
    agent = CleanerAgent()
    
    # Test de l'agent avec des données de test
    test_leads = [
        {
            "lead_id": "1",
            "first_name": "john",
            "last_name": "doe",
            "email": "john.doe@example.com",
            "position": "CEO",
            "company": "Example Inc",
            "company_website": "example.com",
            "linkedin_url": "linkedin.com/in/johndoe"
        },
        {
            "lead_id": "2",
            "first_name": "Jane",
            "last_name": "SMITH",
            "email": "jane.smith@invalid@email",
            "position": "CTO",
            "company": "Test Company",
            "company_website": "https://www.testcompany.com",
            "linkedin_url": "https://www.linkedin.com/in/janesmith"
        }
    ]
    
    result = agent.run({
        "action": "clean",
        "leads": test_leads,
        "niche": "test"
    })
    
    print(json.dumps(result, indent=2))

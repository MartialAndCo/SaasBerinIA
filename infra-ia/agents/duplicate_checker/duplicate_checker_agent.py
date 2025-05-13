"""
Module du DuplicateCheckerAgent - Agent de vérification des doublons
"""
import os
import json
from typing import Dict, Any, Optional, List
import datetime
import hashlib

from core.agent_base import Agent
from core.db import DatabaseService

class DuplicateCheckerAgent(Agent):
    """
    DuplicateCheckerAgent - Agent qui vérifie l'unicité des leads dans la base de données
    
    Cet agent est responsable de:
    - Vérifier si un lead existe déjà dans la mémoire (via PostgreSQL)
    - Identifier les doublons au sein d'un même lot
    - Prévenir les duplications de prospection
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du DuplicateCheckerAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("DuplicateCheckerAgent", config_path)
        
        # État de l'agent
        self.duplicate_stats = {
            "total_processed": 0,
            "duplicates_found": 0,
            "unique_leads": 0
        }
        
        # Initialisation de la connexion à la base de données
        self.db = DatabaseService()
    
    def check_duplicates(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Vérifie les doublons dans une liste de leads
        
        Args:
            input_data: Données d'entrée contenant les leads à vérifier
            
        Returns:
            Leads uniques et doublons identifiés
        """
        leads = input_data.get("leads", [])
        niche = input_data.get("niche", "")
        check_internal = input_data.get("check_internal", True)
        check_database = input_data.get("check_database", True)
        
        if not leads:
            return {
                "status": "error",
                "message": "Aucun lead à vérifier",
                "leads": []
            }
        
        self.speak(f"Vérification des doublons pour {len(leads)} leads de la niche '{niche}'", target="QualificationSupervisor")
        
        # Étape 1: Vérification des doublons au sein du lot actuel (si configuré)
        unique_leads = []
        internal_duplicates = []
        
        if check_internal:
            # Dictionnaire pour stocker les leads par clé d'unicité
            unique_keys = {}
            
            for lead in leads:
                # Génération de la clé d'unicité
                uniqueness_key = self._generate_uniqueness_key(lead)
                
                if uniqueness_key in unique_keys:
                    # Doublon interne trouvé
                    internal_duplicates.append({
                        "lead": lead,
                        "duplicate_of": unique_keys[uniqueness_key],
                        "key": uniqueness_key
                    })
                else:
                    # Lead unique dans ce lot
                    unique_keys[uniqueness_key] = lead.get("lead_id", "")
                    unique_leads.append(lead)
            
            self.speak(f"{len(internal_duplicates)} doublons internes identifiés", target="QualificationSupervisor")
        else:
            # Si la vérification interne est désactivée, tous les leads sont considérés comme uniques
            unique_leads = leads
        
        # Étape 2: Vérification des doublons dans la base de données (si configuré)
        database_duplicates = []
        leads_to_return = []
        
        if check_database:
            for lead in unique_leads:
                # Vérification en base de données
                is_duplicate = self._check_database_duplicate(lead)
                
                if is_duplicate:
                    # Doublon en base trouvé
                    database_duplicates.append({
                        "lead": lead,
                        "duplicate_type": "database",
                        "key": self._generate_uniqueness_key(lead)
                    })
                else:
                    # Lead unique dans la base
                    leads_to_return.append(lead)
            
            self.speak(f"{len(database_duplicates)} doublons trouvés en base de données", target="QualificationSupervisor")
        else:
            # Si la vérification en base est désactivée, tous les leads sont retournés
            leads_to_return = unique_leads
        
        # Mise à jour des statistiques
        total_duplicates = len(internal_duplicates) + len(database_duplicates)
        self.duplicate_stats["total_processed"] += len(leads)
        self.duplicate_stats["duplicates_found"] += total_duplicates
        self.duplicate_stats["unique_leads"] += len(leads_to_return)
        
        # Résultat global
        result = {
            "status": "success",
            "niche": niche,
            "unique_leads": leads_to_return,
            "duplicates": internal_duplicates + database_duplicates,
            "stats": {
                "total": len(leads),
                "unique": len(leads_to_return),
                "internal_duplicates": len(internal_duplicates),
                "database_duplicates": len(database_duplicates)
            }
        }
        
        return result
    
    def _generate_uniqueness_key(self, lead: Dict[str, Any]) -> str:
        """
        Génère une clé d'unicité pour un lead
        
        Args:
            lead: Le lead pour lequel générer une clé
            
        Returns:
            Clé d'unicité
        """
        # Utilisation de différents critères selon la configuration
        criteria = self.config.get("uniqueness_criteria", ["email", "linkedin_url"])
        
        if self.config.get("use_email_as_primary", True) and "email" in lead and lead["email"]:
            # Si configuré pour utiliser l'email comme critère principal
            email = lead["email"].lower().strip()
            return f"email:{email}"
        
        if self.config.get("use_linkedin_as_primary", False) and "linkedin_url" in lead and lead["linkedin_url"]:
            # Si configuré pour utiliser LinkedIn comme critère principal
            linkedin = lead["linkedin_url"].lower().strip()
            return f"linkedin:{linkedin}"
        
        # Génération d'une clé combinée à partir des critères configurés
        parts = []
        for criterion in criteria:
            if criterion in lead and lead[criterion]:
                value = str(lead[criterion]).lower().strip()
                parts.append(f"{criterion}:{value}")
        
        if not parts:
            # Si aucun critère n'est disponible, on utilise les champs nom + entreprise
            full_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".lower().strip()
            company = lead.get("company", "").lower().strip()
            
            # Création d'un hash comme clé de fallback
            if full_name and company:
                hash_input = f"{full_name}:{company}"
                return f"name_company:{hashlib.md5(hash_input.encode()).hexdigest()}"
        
        # Jointure des parties pour former la clé
        return "||".join(parts)
    
    def _check_database_duplicate(self, lead: Dict[str, Any]) -> bool:
        """
        Vérifie si un lead est un doublon dans la base de données
        
        Args:
            lead: Le lead à vérifier
            
        Returns:
            True si c'est un doublon, False sinon
        """
        try:
            # Vérification par email
            if "email" in lead and lead["email"]:
                email = lead["email"].lower().strip()
                
                query = "SELECT id FROM leads WHERE email = :email LIMIT 1"
                result = self.db.fetch_one(query, {"email": email})
                
                if result:
                    return True
            
            # Vérification par URL LinkedIn
            if "linkedin_url" in lead and lead["linkedin_url"]:
                linkedin_url = lead["linkedin_url"].lower().strip()
                
                query = "SELECT id FROM leads WHERE linkedin_url = :linkedin_url LIMIT 1"
                result = self.db.fetch_one(query, {"linkedin_url": linkedin_url})
                
                if result:
                    return True
            
            # Vérification par nom + entreprise (si configuré)
            if self.config.get("check_name_company", True):
                if all(key in lead and lead[key] for key in ["first_name", "last_name", "company"]):
                    first_name = lead["first_name"].lower().strip()
                    last_name = lead["last_name"].lower().strip()
                    company = lead["company"].lower().strip()
                    
                    query = """
                    SELECT id FROM leads 
                    WHERE LOWER(first_name) = :first_name 
                    AND LOWER(last_name) = :last_name 
                    AND LOWER(company) = :company 
                    LIMIT 1
                    """
                    
                    params = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "company": company
                    }
                    
                    result = self.db.fetch_one(query, params)
                    
                    if result:
                        return True
            
            # Aucun doublon trouvé
            return False
            
        except Exception as e:
            # En cas d'erreur de base de données, on log et on considère comme non-doublon
            self.speak(f"Erreur lors de la vérification des doublons en BDD: {str(e)}", target="QualificationSupervisor")
            
            # Si configuré pour être strict en cas d'erreur
            if self.config.get("strict_on_db_error", False):
                return True  # Considérer comme doublon en cas de doute
            else:
                return False  # Laisser passer en cas d'erreur
    
    def get_duplicate_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de vérification des doublons
        
        Returns:
            Statistiques de vérification
        """
        return {
            "status": "success",
            "stats": self.duplicate_stats
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "check")
        
        if action == "check":
            return self.check_duplicates(input_data)
        
        elif action == "get_stats":
            return self.get_duplicate_stats()
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du DuplicateCheckerAgent
    agent = DuplicateCheckerAgent()
    
    # Test de l'agent avec des données de test
    test_leads = [
        {
            "lead_id": "1",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "position": "CEO",
            "company": "Test Company",
            "linkedin_url": "https://www.linkedin.com/in/johndoe"
        },
        {
            "lead_id": "2",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@company.com",
            "position": "CTO",
            "company": "Another Company",
            "linkedin_url": "https://www.linkedin.com/in/janesmith"
        },
        {
            "lead_id": "3",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",  # Doublon de l'ID 1
            "position": "CEO",
            "company": "Test Company",
            "linkedin_url": "https://www.linkedin.com/in/johndoe"
        }
    ]
    
    result = agent.run({
        "action": "check",
        "leads": test_leads,
        "niche": "test",
        "check_database": False  # Désactivation de la vérification en base pour le test
    })
    
    print(json.dumps(result, indent=2))

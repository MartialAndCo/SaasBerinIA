"""
Module du ScrapingSupervisor - Superviseur de tous les agents liés au scraping
"""
import os
import json
from typing import Dict, Any, Optional, List
import datetime

from core.agent_base import Agent
from utils.llm import LLMService

class ScrapingSupervisor(Agent):
    """
    ScrapingSupervisor - Superviseur des agents de scraping
    
    Ce superviseur est responsable de :
    - Coordonner les agents de recherche de leads
    - Gérer les niches à scraper
    - Planifier les sessions de scraping
    - Superviser les étapes de nettoyage
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du ScrapingSupervisor
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("ScrapingSupervisor", config_path)
        
        # État du superviseur
        self.current_tasks = []
        self.active_niches = []
        self.scraping_stats = {}
        
    def coordinate_niche_exploration(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordonne l'exploration de nouvelles niches
        
        Args:
            input_data: Données d'entrée
            
        Returns:
            Résultat de l'exploration
        """
        self.speak("Coordination de l'exploration de nouvelles niches", target="NicheExplorerAgent")
        
        # Appel à l'agent d'exploration de niches
        from agents.overseer.overseer_agent import OverseerAgent
        overseer = OverseerAgent()
        
        result = overseer.execute_agent("NicheExplorerAgent", input_data)
        
        if result.get("status") == "success":
            # Traitement des niches découvertes
            discovered_niches = result.get("niches", [])
            self.active_niches.extend(discovered_niches)
            
            self.speak(
                f"Nouvelles niches découvertes: {', '.join(discovered_niches)}",
                target="OverseerAgent"
            )
        else:
            self.speak(
                f"Échec de l'exploration de niches: {result.get('message')}",
                target="OverseerAgent"
            )
        
        return result
    
    def coordinate_scraping(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordonne le scraping de leads
        
        Args:
            input_data: Données d'entrée
            
        Returns:
            Résultat du scraping
        """
        niche = input_data.get("niche", "")
        source = input_data.get("source", "apify")
        limit = input_data.get("limit", self.config.get("limit_per_run", 50))
        
        self.speak(f"Coordination du scraping pour la niche: {niche}", target="ScraperAgent")
        
        # Ajout d'informations au contexte
        context = {
            **input_data,
            "limit": limit,
            "source": source
        }
        
        # Appel à l'agent de scraping
        from agents.overseer.overseer_agent import OverseerAgent
        overseer = OverseerAgent()
        
        result = overseer.execute_agent("ScraperAgent", context)
        
        if result.get("status") == "success":
            # Traitement des leads scrapés
            leads_count = len(result.get("leads", []))
            
            # Mise à jour des statistiques
            if niche not in self.scraping_stats:
                self.scraping_stats[niche] = {
                    "total_leads": 0,
                    "sessions": 0,
                    "last_scrape": None
                }
            
            self.scraping_stats[niche]["total_leads"] += leads_count
            self.scraping_stats[niche]["sessions"] += 1
            self.scraping_stats[niche]["last_scrape"] = datetime.datetime.now().isoformat()
            
            self.speak(
                f"Scraping terminé pour {niche}: {leads_count} leads récupérés",
                target="OverseerAgent"
            )
            
            # Transition vers le nettoyage si des leads ont été trouvés
            if leads_count > 0:
                self.speak(f"Envoi de {leads_count} leads au CleanerAgent", target="CleanerAgent")
                
                # Appel à l'agent de nettoyage
                cleaning_result = overseer.execute_agent("CleanerAgent", {
                    "leads": result.get("leads", []),
                    "niche": niche
                })
                
                result["cleaning_result"] = cleaning_result
        else:
            self.speak(
                f"Échec du scraping pour {niche}: {result.get('message')}",
                target="OverseerAgent"
            )
        
        return result
    
    def manage_niches(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère les niches actives et inactives
        
        Args:
            input_data: Données d'entrée
            
        Returns:
            État des niches
        """
        action = input_data.get("action", "list")
        
        if action == "list":
            # Liste des niches actives
            return {
                "status": "success",
                "active_niches": self.active_niches,
                "niche_stats": self.scraping_stats
            }
        
        elif action == "add":
            # Ajout d'une nouvelle niche
            new_niche = input_data.get("niche", "")
            if new_niche and new_niche not in self.active_niches:
                self.active_niches.append(new_niche)
                self.speak(f"Nouvelle niche ajoutée: {new_niche}", target="OverseerAgent")
                
                return {
                    "status": "success",
                    "message": f"Niche {new_niche} ajoutée avec succès",
                    "active_niches": self.active_niches
                }
            else:
                return {
                    "status": "error",
                    "message": f"Niche {new_niche} invalide ou déjà existante",
                    "active_niches": self.active_niches
                }
        
        elif action == "remove":
            # Suppression d'une niche
            niche_to_remove = input_data.get("niche", "")
            if niche_to_remove in self.active_niches:
                self.active_niches.remove(niche_to_remove)
                self.speak(f"Niche supprimée: {niche_to_remove}", target="OverseerAgent")
                
                return {
                    "status": "success",
                    "message": f"Niche {niche_to_remove} supprimée avec succès",
                    "active_niches": self.active_niches
                }
            else:
                return {
                    "status": "error",
                    "message": f"Niche {niche_to_remove} non trouvée",
                    "active_niches": self.active_niches
                }
        
        elif action == "pause":
            # Pause d'une niche (déplacement vers les niches inactives)
            niche_to_pause = input_data.get("niche", "")
            if niche_to_pause in self.active_niches:
                self.active_niches.remove(niche_to_pause)
                
                # On pourrait avoir une liste de niches en pause
                self.speak(f"Niche mise en pause: {niche_to_pause}", target="OverseerAgent")
                
                return {
                    "status": "success",
                    "message": f"Niche {niche_to_pause} mise en pause",
                    "active_niches": self.active_niches
                }
            else:
                return {
                    "status": "error",
                    "message": f"Niche {niche_to_pause} non trouvée",
                    "active_niches": self.active_niches
                }
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}",
                "active_niches": self.active_niches
            }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "")
        
        if action == "coordinate_niche_exploration":
            return self.coordinate_niche_exploration(input_data)
        
        elif action == "coordinate_scraping":
            return self.coordinate_scraping(input_data)
        
        elif action == "manage_niches":
            return self.manage_niches(input_data)
        
        elif action == "get_status":
            # Retourne l'état actuel du superviseur
            return {
                "status": "success",
                "active_niches": self.active_niches,
                "current_tasks": self.current_tasks,
                "scraping_stats": self.scraping_stats
            }
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du ScrapingSupervisor
    supervisor = ScrapingSupervisor()
    
    # Test de l'agent
    result = supervisor.run({
        "action": "get_status"
    })
    
    print(json.dumps(result, indent=2))

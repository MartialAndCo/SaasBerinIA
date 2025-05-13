"""
Module du NicheExplorerAgent - Agent d'exploration de niches pour le scraping
"""
import os
import json
from typing import Dict, Any, Optional, List
import datetime

from core.agent_base import Agent
from utils.llm import LLMService
from utils.qdrant import query_knowledge

class NicheExplorerAgent(Agent):
    """
    NicheExplorerAgent - Agent qui analyse le marché pour trouver des niches à fort potentiel
    
    Cet agent est responsable de:
    - Rechercher des niches à fort potentiel
    - Analyser le marché et les tendances
    - Proposer des niches viables au ScrapingSupervisor
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du NicheExplorerAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("NicheExplorerAgent", config_path)
        
        # État de l'agent
        self.explored_niches = []
        self.recommended_niches = []
        self.blacklisted_niches = self.config.get("blacklisted_niches", [])
        
    def explore_niches(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Explore de nouvelles niches en fonction des critères fournis
        
        Args:
            input_data: Données d'entrée avec les critères
            
        Returns:
            Liste des niches trouvées
        """
        self.speak("Exploration de nouvelles niches...", target="ScrapingSupervisor")
        
        # Critères d'exploration
        industries = input_data.get("industries", [])
        locations = input_data.get("locations", [])
        keywords = input_data.get("keywords", [])
        limit = input_data.get("limit", self.config.get("niches_per_exploration", 5))
        
        # Construction du prompt pour le LLM
        prompt = self.build_prompt({
            "industries": industries,
            "locations": locations,
            "keywords": keywords,
            "blacklisted_niches": self.blacklisted_niches,
            "previously_explored": self.explored_niches,
            "limit": limit
        })
        
        # Si Qdrant est disponible, on récupère des connaissances supplémentaires
        try:
            market_knowledge = query_knowledge(" ".join(keywords) + " " + " ".join(industries))
            market_insights = "\n".join([k.get("document", "") for k in market_knowledge])
            prompt += f"\n\nVoici des insights supplémentaires sur le marché :\n{market_insights}"
        except Exception as e:
            self.speak(f"Impossible de récupérer des connaissances Qdrant: {e}", target="ScrapingSupervisor")
        
        # Appel au LLM pour générer des suggestions de niches
        response = LLMService.call_llm(prompt, complexity="medium")
        
        try:
            # Parsing du résultat (supposé être au format JSON)
            result = json.loads(response)
            niches = result.get("niches", [])
            reasoning = result.get("reasoning", "")
            
            # Mise à jour de l'état
            self.explored_niches.extend(niches)
            self.recommended_niches.extend(niches)
            
            # Message de log
            self.speak(
                f"Exploration terminée. {len(niches)} niches trouvées: {', '.join(niches)}",
                target="ScrapingSupervisor"
            )
            
            return {
                "status": "success",
                "niches": niches,
                "reasoning": reasoning,
                "total_explored": len(self.explored_niches),
                "total_recommended": len(self.recommended_niches)
            }
        except json.JSONDecodeError:
            # Si le résultat n'est pas un JSON valide, on essaie de parser manuellement
            lines = response.split("\n")
            niches = []
            
            for line in lines:
                if ":" in line and not line.strip().startswith("#") and not line.strip().startswith("//"):
                    parts = line.split(":", 1)
                    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                        niches.append(parts[0].strip())
            
            if not niches:
                # Dernière tentative: on prend toutes les lignes qui ne sont pas vides
                niches = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
            
            # Mise à jour de l'état
            self.explored_niches.extend(niches)
            self.recommended_niches.extend(niches)
            
            self.speak(
                f"Exploration terminée (parsing manuel). {len(niches)} niches trouvées: {', '.join(niches)}",
                target="ScrapingSupervisor"
            )
            
            return {
                "status": "success",
                "niches": niches,
                "reasoning": "Parsing manuel du résultat",
                "total_explored": len(self.explored_niches),
                "total_recommended": len(self.recommended_niches)
            }
    
    def analyze_niche(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse une niche spécifique en profondeur
        
        Args:
            input_data: Données d'entrée avec la niche à analyser
            
        Returns:
            Analyse détaillée de la niche
        """
        niche = input_data.get("niche", "")
        
        if not niche:
            return {
                "status": "error",
                "message": "Niche non spécifiée"
            }
        
        self.speak(f"Analyse de la niche: {niche}", target="ScrapingSupervisor")
        
        # Construction du prompt pour le LLM
        prompt = self.build_prompt({
            "niche": niche,
            "action": "analyze",
            "blacklisted_niches": self.blacklisted_niches
        })
        
        # Si Qdrant est disponible, on récupère des connaissances supplémentaires
        try:
            niche_knowledge = query_knowledge(niche)
            niche_insights = "\n".join([k.get("document", "") for k in niche_knowledge])
            prompt += f"\n\nVoici des insights supplémentaires sur cette niche :\n{niche_insights}"
        except Exception as e:
            self.speak(f"Impossible de récupérer des connaissances Qdrant: {e}", target="ScrapingSupervisor")
        
        # Appel au LLM pour analyser la niche
        response = LLMService.call_llm(prompt, complexity="high")
        
        try:
            # Parsing du résultat (supposé être au format JSON)
            result = json.loads(response)
            
            # Message de log
            self.speak(
                f"Analyse de la niche {niche} terminée avec un score de potentiel de {result.get('potential_score', 'N/A')}/10",
                target="ScrapingSupervisor"
            )
            
            return {
                "status": "success",
                "niche": niche,
                "analysis": result
            }
        except json.JSONDecodeError:
            # Si le résultat n'est pas un JSON valide, on le retourne tel quel
            self.speak(
                f"Analyse de la niche {niche} terminée (format texte)",
                target="ScrapingSupervisor"
            )
            
            return {
                "status": "success",
                "niche": niche,
                "analysis": {
                    "raw_text": response
                }
            }
    
    def manage_blacklist(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère la liste noire des niches à éviter
        
        Args:
            input_data: Données d'entrée avec l'action à effectuer
            
        Returns:
            État actuel de la liste noire
        """
        action = input_data.get("action", "list")
        
        if action == "list":
            return {
                "status": "success",
                "blacklisted_niches": self.blacklisted_niches
            }
        
        elif action == "add":
            niche = input_data.get("niche", "")
            if niche and niche not in self.blacklisted_niches:
                self.blacklisted_niches.append(niche)
                self.update_config("blacklisted_niches", self.blacklisted_niches)
                
                self.speak(f"Niche {niche} ajoutée à la liste noire", target="ScrapingSupervisor")
                
                return {
                    "status": "success",
                    "message": f"Niche {niche} ajoutée à la liste noire",
                    "blacklisted_niches": self.blacklisted_niches
                }
            else:
                return {
                    "status": "error",
                    "message": f"Niche {niche} invalide ou déjà dans la liste noire",
                    "blacklisted_niches": self.blacklisted_niches
                }
        
        elif action == "remove":
            niche = input_data.get("niche", "")
            if niche in self.blacklisted_niches:
                self.blacklisted_niches.remove(niche)
                self.update_config("blacklisted_niches", self.blacklisted_niches)
                
                self.speak(f"Niche {niche} retirée de la liste noire", target="ScrapingSupervisor")
                
                return {
                    "status": "success",
                    "message": f"Niche {niche} retirée de la liste noire",
                    "blacklisted_niches": self.blacklisted_niches
                }
            else:
                return {
                    "status": "error",
                    "message": f"Niche {niche} non trouvée dans la liste noire",
                    "blacklisted_niches": self.blacklisted_niches
                }
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}",
                "blacklisted_niches": self.blacklisted_niches
            }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "explore")
        
        if action == "explore":
            return self.explore_niches(input_data)
        
        elif action == "analyze":
            return self.analyze_niche(input_data)
        
        elif action == "manage_blacklist":
            return self.manage_blacklist(input_data)
        
        elif action == "get_status":
            return {
                "status": "success",
                "explored_niches": self.explored_niches,
                "recommended_niches": self.recommended_niches,
                "blacklisted_niches": self.blacklisted_niches
            }
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du NicheExplorerAgent
    agent = NicheExplorerAgent()
    
    # Test de l'agent
    result = agent.run({
        "action": "explore",
        "industries": ["tech", "finance", "healthcare"],
        "keywords": ["innovation", "croissance", "B2B"],
        "limit": 5
    })
    
    print(json.dumps(result, indent=2))

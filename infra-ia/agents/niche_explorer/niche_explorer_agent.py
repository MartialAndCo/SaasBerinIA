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
    
    def _analyze_niche_potential(self, niche: str) -> Dict[str, Any]:
        """
        Analyse le potentiel d'une niche spécifique (méthode interne)
        
        Args:
            niche: La niche à analyser
            
        Returns:
            Dictionnaire avec score et raisonnement
        """
        try:
            # Critères de scoring pour TPE/PME
            score = 5  # Score de base
            reasoning_parts = []
            
            # Mots-clés positifs pour TPE/PME
            positive_keywords = [
                "local", "artisan", "salon", "garage", "restaurant", "cabinet", "boutique",
                "coiffure", "médical", "dentaire", "commerce", "service", "réparation"
            ]
            
            # Mots-clés négatifs (trop gros ou pas adaptés)
            negative_keywords = [
                "grande surface", "multinationale", "groupe", "holding", "corporation",
                "banque centrale", "gouvernement", "startup tech", "licorne"
            ]
            
            niche_lower = niche.lower()
            
            # Scoring basé sur les mots-clés
            for keyword in positive_keywords:
                if keyword in niche_lower:
                    score += 1
                    reasoning_parts.append(f"Secteur TPE/PME ({keyword})")
            
            for keyword in negative_keywords:
                if keyword in niche_lower:
                    score -= 2
                    reasoning_parts.append(f"Secteur non-TPE ({keyword})")
            
            # Bonus pour localisation géographique
            location_keywords = ["lyon", "marseille", "paris", "bordeaux", "toulouse", "france"]
            for location in location_keywords:
                if location in niche_lower:
                    score += 1
                    reasoning_parts.append(f"Localisation identifiée ({location})")
            
            # Limiter le score entre 0 et 10
            score = max(0, min(10, score))
            
            reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Analyse basique"
            
            return {
                "score": score,
                "reasoning": reasoning,
                "potential": "élevé" if score >= 7 else "moyen" if score >= 4 else "faible"
            }
            
        except Exception as e:
            return {
                "score": 0,
                "reasoning": f"Erreur d'analyse: {str(e)}",
                "potential": "indéterminé"
            }
    
    def discover_niches(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Découvre de nouvelles niches selon les critères TPE/PME
        
        Args:
            input_data: Données d'entrée avec focus et région
            
        Returns:
            Liste de nouvelles niches découvertes
        """
        focus = input_data.get("focus", "TPE/PME")
        region = input_data.get("region", "France")
        
        # Niches TPE/PME pré-définies par région
        discovered_niches = {
            "France": [
                "Salons de coiffure ruraux",
                "Garages automobiles de proximité", 
                "Cabinets vétérinaires locaux",
                "Restaurants familiaux",
                "Magasins de bricolage indépendants",
                "Pharmacies de quartier",
                "Boulangeries artisanales",
                "Agences immobilières locales"
            ]
        }
        
        niches = discovered_niches.get(region, discovered_niches["France"])
        
        # Analyser le potentiel de chaque niche
        analyzed_niches = []
        for niche in niches:
            analysis = self._analyze_niche_potential(niche)
            analyzed_niches.append({
                "niche": niche,
                "potential_score": analysis["score"],
                "reasoning": analysis["reasoning"]
            })
        
        self.speak(f"Découverte de {len(niches)} niches {focus} en {region}", target="ScrapingSupervisor")
        
        return {
            "status": "success",
            "discovered_niches": analyzed_niches,
            "region": region,
            "focus": focus,
            "total_count": len(niches)
        }
    
    def strategic_recommendations(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fournit des recommandations stratégiques basées sur les niches actuelles
        
        Args:
            input_data: Données d'entrée avec niches actuelles
            
        Returns:
            Recommandations stratégiques
        """
        current_niches = input_data.get("current_niches", [])
        
        recommendations = [
            {
                "type": "expansion",
                "recommendation": "Élargir vers les TPE/PME de services",
                "priority": "haute",
                "reason": "Secteur moins saturé avec fort potentiel"
            },
            {
                "type": "geographic", 
                "recommendation": "Cibler les zones rurales et périurbaines",
                "priority": "moyenne",
                "reason": "Moins de concurrence, forte demande de digitalisation"
            },
            {
                "type": "vertical",
                "recommendation": "Spécialisation secteur santé (cabinets, pharmacies)",
                "priority": "haute",
                "reason": "Réglementation forte = besoin d'outils conformes"
            }
        ]
        
        # Analyser les niches actuelles pour des recommandations personnalisées
        if current_niches:
            for niche in current_niches:
                analysis = self._analyze_niche_potential(niche)
                if analysis["score"] < 5:
                    recommendations.append({
                        "type": "optimize",
                        "recommendation": f"Revoir la stratégie pour {niche}",
                        "priority": "urgente",
                        "reason": f"Potentiel faible détecté (score: {analysis['score']}/10)"
                    })
        
        self.speak(f"Génération de {len(recommendations)} recommandations stratégiques", target="ScrapingSupervisor")
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "based_on_niches": current_niches,
            "analysis_date": datetime.datetime.now().isoformat()
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal du NicheExplorerAgent
        
        Args:
            input_data: Données d'entrée avec l'action à effectuer
            
        Returns:
            Résultat de l'action demandée
        """
        action = input_data.get("action", "")
        
        if action == "discover_niches":
            return self.discover_niches(input_data)
        elif action == "analyze_niche_potential":
            return self.analyze_niche(input_data)
        elif action == "strategic_recommendations":
            return self.strategic_recommendations(input_data)
        elif action == "explore_niches":
            return self.explore_niches(input_data)
        elif action == "analyze_niche":
            return self.analyze_niche(input_data)
        elif action == "manage_blacklist":
            return self.manage_blacklist(input_data)
        elif action == "get_stats":
            return {
                "status": "success",
                "explored_niches_count": len(self.explored_niches),
                "recommended_niches_count": len(self.recommended_niches),
                "blacklisted_niches_count": len(self.blacklisted_niches)
            }
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}",
                "available_actions": [
                    "discover_niches",
                    "analyze_niche_potential",
                    "strategic_recommendations",
                    "explore_niches",
                    "analyze_niche",
                    "manage_blacklist",
                    "get_stats"
                ]
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

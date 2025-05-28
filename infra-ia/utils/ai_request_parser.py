"""
AIRequestParser - Parser intelligent 100% IA pour l'analyse des demandes utilisateur
Remplace les patterns hardcodés par une analyse LLM structurée
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from utils.llm import LLMService

class AIRequestParser:
    """
    Parser intelligent qui analyse toute demande utilisateur sans patterns hardcodés
    """
    
    def __init__(self):
        self.logger = logging.getLogger("BerinIA.AIRequestParser")
        
        # Intentions supportées (dynamique, peut être étendu)
        self.supported_intentions = [
            "query_data",      # Questions sur données existantes
            "scrape_leads",    # Récupération de nouveaux leads
            "send_messages",   # Envoi d'emails/SMS
            "analyze_data",    # Analyses et rapports
            "system_config",   # Modifications système
            "general_chat"     # Conversation générale
        ]
        
        # Cache des analyses récentes pour optimisation
        self.analysis_cache = {}
        
    def analyze_request(self, message: str, available_agents: List[str] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyse une demande utilisateur de manière complètement intelligente
        
        Args:
            message: Message utilisateur à analyser
            available_agents: Liste des agents disponibles
            context: Contexte additionnel (conversation, etc.)
            
        Returns:
            Analyse structurée avec intention, paramètres et agent cible
        """
        
        # Cache pour éviter de ré-analyser des messages identiques
        cache_key = f"{message}_{str(available_agents)}"
        if cache_key in self.analysis_cache:
            self.logger.info("Analyse trouvée en cache")
            return self.analysis_cache[cache_key]
        
        try:
            # Construction du prompt intelligent
            prompt = self._build_analysis_prompt(message, available_agents, context)
            
            # Analyse LLM
            self.logger.info(f"Analyse IA de: '{message[:50]}...'")
            llm_response = LLMService.call_llm(prompt, complexity="high")
            
            # Parsing JSON
            analysis = self._parse_llm_response(llm_response, message)
            
            # Validation et enrichissement
            analysis = self._validate_and_enrich(analysis, message, available_agents)
            
            # Mise en cache
            self.analysis_cache[cache_key] = analysis
            
            self.logger.info(f"Analyse réussie: {analysis['intention']} -> {analysis.get('agent_target', 'auto')}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erreur analyse IA: {e}")
            return self._fallback_analysis(message, available_agents)
    
    def _build_analysis_prompt(self, message: str, available_agents: List[str], context: Dict[str, Any]) -> str:
        """Construit le prompt d'analyse intelligent"""
        
        agents_list = available_agents or []
        context_info = ""
        
        if context:
            if context.get("conversation_history"):
                context_info += f"\nHISTORIQUE: {context['conversation_history'][-200:]}"
            if context.get("system_state"):
                context_info += f"\nÉTAT SYSTÈME: {context['system_state']}"
        
        prompt = f"""Tu es un parser intelligent expert qui analyse toute demande pour un système de prospection commerciale.

DEMANDE UTILISATEUR: "{message}"

AGENTS DISPONIBLES: {', '.join(agents_list)}

CONTEXTE ADDITIONNEL:{context_info}

ANALYSE CETTE DEMANDE ET EXTRAIT:

1. INTENTION (choisir parmi):
   - "query_data": Questions sur données/statistiques existantes (ex: "combien de leads", "stats campagne")
   - "scrape_leads": Récupération/scraping de nouveaux leads (ex: "trouve", "scrappe", "récupère")  
   - "send_messages": Envoi d'emails/SMS (ex: "envoie un message", "contact les leads")
   - "analyze_data": Analyses approfondies (ex: "analyse les performances", "rapport")
   - "system_config": Modifications système/config (ex: "change la limite", "modifie")
   - "general_chat": Conversation générale (ex: salutations, remerciements)

2. PARAMÈTRES (extraire automatiquement si présents):
   - niche: industrie/métier ciblé (restaurants, dentistes, avocats, etc.)
   - quantity: nombre/limite demandée (nombres explicites)
   - location: ville/région (Paris, Toulouse, Lyon, etc.)
   - source: plateforme mentionnée (Apify, Apollo, LinkedIn, etc.)
   - filters: critères supplémentaires
   - action_type: type d'action spécifique

3. AGENT_TARGET: 
   - Si évident → nom exact de l'agent approprié
   - Si incertain → "auto" pour sélection automatique
   - Agents typiques: ScraperAgent, DatabaseQueryAgent, MessagingAgent, etc.

4. CONFIDENCE: score de 0.0 à 1.0 de confiance dans l'analyse

RÈGLES IMPORTANTES:
- Sois flexible avec les variantes (scrappe=scrape, trouve=récupère, etc.)
- Extrait TOUS les paramètres présents, même implicites
- Privilégie l'intention la plus probable
- Utilise "auto" si l'agent n'est pas évident

RÉPONDS UNIQUEMENT EN JSON VALIDE:
{{
    "intention": "...",
    "parameters": {{
        "niche": "...",
        "quantity": 0,
        "location": "...",
        "source": "...",
        "filters": [...],
        "action_type": "..."
    }},
    "agent_target": "...",
    "confidence": 0.0,
    "reasoning": "explication courte"
}}"""

        return prompt
    
    def _parse_llm_response(self, llm_response: str, original_message: str) -> Dict[str, Any]:
        """Parse la réponse LLM en JSON structuré"""
        
        try:
            # Nettoyage de la réponse
            cleaned_response = llm_response.strip()
            
            # Extraction du JSON si entouré de texte
            if "```json" in cleaned_response:
                start = cleaned_response.find("```json") + 7
                end = cleaned_response.find("```", start)
                cleaned_response = cleaned_response[start:end].strip()
            elif "```" in cleaned_response:
                start = cleaned_response.find("```") + 3
                end = cleaned_response.rfind("```")
                cleaned_response = cleaned_response[start:end].strip()
            
            # Parsing JSON
            analysis = json.loads(cleaned_response)
            
            # Validation des champs obligatoires
            if "intention" not in analysis:
                raise ValueError("Champ 'intention' manquant")
            
            return analysis
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Erreur parsing JSON: {e}")
            self.logger.warning(f"Réponse LLM: {llm_response}")
            
            # Fallback: extraction manuelle
            return self._extract_from_text(llm_response, original_message)
    
    def _extract_from_text(self, text: str, original_message: str) -> Dict[str, Any]:
        """Extraction de fallback si le JSON échoue"""
        
        text_lower = text.lower()
        message_lower = original_message.lower()
        
        # Détection d'intention basique
        intention = "general_chat"  # Défaut
        
        if any(word in message_lower for word in ["scrappe", "scrape", "trouve", "récupère", "leads", "extraction"]):
            intention = "scrape_leads"
        elif any(word in message_lower for word in ["combien", "statistiques", "stats", "nombre", "count"]):
            intention = "query_data"
        elif any(word in message_lower for word in ["envoie", "message", "email", "sms", "contact"]):
            intention = "send_messages"
        elif any(word in message_lower for word in ["analyse", "rapport", "performance"]):
            intention = "analyze_data"
        
        # Extraction basique de paramètres
        parameters = {}
        
        # Niche
        for niche in ["restaurant", "dentiste", "avocat", "immobilier", "coaching", "consultant"]:
            if niche in message_lower:
                parameters["niche"] = niche + "s" if not niche.endswith("s") else niche
                break
        
        # Quantité
        import re
        numbers = re.findall(r'\d+', original_message)
        if numbers:
            parameters["quantity"] = int(numbers[0])
        
        # Localisation
        for city in ["paris", "toulouse", "lyon", "marseille", "nice", "bordeaux"]:
            if city in message_lower:
                parameters["location"] = city.capitalize()
                break
        
        return {
            "intention": intention,
            "parameters": parameters,
            "agent_target": "auto",
            "confidence": 0.7,
            "reasoning": "Extraction de fallback"
        }
    
    def _validate_and_enrich(self, analysis: Dict[str, Any], message: str, available_agents: List[str]) -> Dict[str, Any]:
        """Valide et enrichit l'analyse"""
        
        # Validation de l'intention
        if analysis.get("intention") not in self.supported_intentions:
            self.logger.warning(f"Intention non supportée: {analysis.get('intention')}")
            analysis["intention"] = "general_chat"
        
        # Validation de l'agent cible
        agent_target = analysis.get("agent_target", "auto")
        if agent_target != "auto" and available_agents and agent_target not in available_agents:
            self.logger.warning(f"Agent non disponible: {agent_target}")
            analysis["agent_target"] = "auto"
        
        # Enrichissement des paramètres
        if "parameters" not in analysis:
            analysis["parameters"] = {}
        
        # Nettoyage et normalisation
        parameters = analysis["parameters"]
        
        # Normalisation de la niche
        if "niche" in parameters:
            niche = parameters["niche"].lower()
            # Pluralisation automatique
            if not niche.endswith("s") and niche != "immobilier":
                parameters["niche"] = niche + "s"
        
        # Validation de la quantité
        if "quantity" in parameters:
            try:
                parameters["quantity"] = int(parameters["quantity"])
            except (ValueError, TypeError):
                parameters["quantity"] = 10  # Défaut
        
        # Ajout de métadonnées
        analysis["timestamp"] = datetime.now().isoformat()
        analysis["original_message"] = message
        
        return analysis
    
    def _fallback_analysis(self, message: str, available_agents: List[str]) -> Dict[str, Any]:
        """Analyse de fallback en cas d'erreur complète"""
        
        self.logger.warning("Utilisation de l'analyse de fallback")
        
        return {
            "intention": "general_chat",
            "parameters": {},
            "agent_target": "auto",
            "confidence": 0.3,
            "reasoning": "Analyse de fallback suite à erreur",
            "timestamp": datetime.now().isoformat(),
            "original_message": message
        }
    
    def suggest_agent(self, intention: str, parameters: Dict[str, Any], available_agents: List[str]) -> str:
        """Suggère l'agent le plus approprié pour une intention"""
        
        if not available_agents:
            return "auto"
        
        # Mapping intelligent intention -> agent
        agent_mapping = {
            "scrape_leads": ["ScraperAgent", "ScrapingSupervisor"],
            "query_data": ["DatabaseQueryAgent"],
            "send_messages": ["MessagingAgent", "ProspectionSupervisor"],
            "analyze_data": ["DatabaseQueryAgent", "AnalyzerAgent"],
            "system_config": ["OverseerAgent"],
            "general_chat": ["ConversationAgent"]
        }
        
        # Recherche de l'agent optimal
        for agent_name in agent_mapping.get(intention, []):
            if agent_name in available_agents:
                return agent_name
        
        # Fallback: premier agent disponible selon l'intention
        if intention == "scrape_leads":
            for agent in available_agents:
                if "scrap" in agent.lower():
                    return agent
        elif intention == "query_data":
            for agent in available_agents:
                if "database" in agent.lower() or "query" in agent.lower():
                    return agent
        elif intention == "send_messages":
            for agent in available_agents:
                if "messag" in agent.lower() or "prospect" in agent.lower():
                    return agent
        
        # Dernier recours
        return "OverseerAgent" if "OverseerAgent" in available_agents else available_agents[0] if available_agents else "auto"
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'analyse"""
        
        return {
            "total_analyses": len(self.analysis_cache),
            "cache_size": len(self.analysis_cache),
            "supported_intentions": self.supported_intentions
        }

# Instance globale
ai_parser = AIRequestParser()

# Export pour utilisation simple
def analyze_user_request(message: str, available_agents: List[str] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Fonction d'analyse simple"""
    return ai_parser.analyze_request(message, available_agents, context)

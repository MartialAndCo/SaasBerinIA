"""
Module du MetaAgent - Agent central d'intelligence conversationnelle
"""
import os
import re
import json
import glob
import logging
import inspect
import importlib
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from pathlib import Path
import traceback
from datetime import datetime

from core.agent_base import Agent
from utils.llm import LLMService
from utils.knowledge_utils_simple import enrich_prompt_with_knowledge, get_relevant_knowledge
from agents.registry import registry

class MetaAgent(Agent):
    """
    MetaAgent - Agent central d'intelligence conversationnelle
    
    Cet agent est responsable de:
    - Analyser les demandes utilisateur en langage naturel
    - Indexer et comprendre les capacités du système
    - Router dynamiquement les demandes vers les agents appropriés
    - Orchestrer des workflows complexes entre plusieurs agents
    - Assurer la cohérence des interactions conversationnelles
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du MetaAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("MetaAgent", config_path)
        
        # Logger dédié
        self.logger = logging.getLogger("BerinIA.MetaAgent")
        
        # Initialisation du cache des capacités
        self.capabilities_cache = {}
        self.capabilities_embeddings = {}
        self.system_structure = {}
        
        # Indexation des capacités du système
        self.index_system_capabilities()
        
        # Historique des conversations
        self.conversation_history = []
        self.max_history_entries = 10
        
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traitement principal des demandes
        
        Args:
            input_data: Données d'entrée contenant la demande utilisateur
            
        Returns:
            Résultat du traitement
        """
        # Vérifier s'il s'agit d'une demande de formatage de réponse
        action = input_data.get("action", "")
        if action == "format_response":
            return self.format_response(input_data)
            
        # Vérifier s'il s'agit d'une demande de gestion d'erreur
        if action == "handle_error":
            return self.handle_error(input_data)
            
        # Extraction du message et des métadonnées
        message = input_data.get("message", input_data.get("content", ""))
        source = input_data.get("source", "direct")
        author = input_data.get("author", "user")
        group = input_data.get("group", None)
        
        if not message:
            return {
                "status": "error",
                "message": "Aucun message fourni"
            }
            
        # Log de la demande reçue
        self.logger.info(f"Demande reçue: '{message}' (source: {source}, auteur: {author})")
        
        # Mise à jour de l'historique
        self.update_conversation_history(message, "user", author)
        
        # Analyse de la demande
        analysis = self.analyze_request(message)
        self.logger.info(f"Analyse: {json.dumps(analysis, ensure_ascii=False)}")
        
        # Si confiance basse, demander des précisions
        if analysis.get("confidence", 0) < 0.4 and analysis.get("intent") != "simple_response":
            clarification_msg = f"Je ne suis pas sûr de comprendre votre demande. Pourriez-vous préciser ce que vous souhaitez faire ?"
            self.update_conversation_history(clarification_msg, "system", "MetaAgent")
            return {
                "status": "need_clarification",
                "message": clarification_msg
            }
        
        # Exécution des actions
        result = self.execute_actions(analysis, input_data)
        
        # Mise à jour de l'historique avec la réponse
        if "message" in result:
            self.update_conversation_history(result["message"], "system", "MetaAgent")
            
        return result
        
    def format_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formate une réponse brute en une réponse conversationnelle et cohérente
        
        Args:
            input_data: Données d'entrée contenant la réponse brute à formater
            
        Returns:
            Réponse formatée
        """
        original_message = input_data.get("original_message", "")
        raw_response = input_data.get("raw_response", "")
        agent_used = input_data.get("agent_used", "")
        
        # Si la réponse est déjà bien formatée, la retourner telle quelle
        if isinstance(raw_response, str) and len(raw_response) > 3 and ("Il y a " in raw_response or "Voici " in raw_response):
            return {
                "status": "success",
                "formatted_response": raw_response,
                "message": raw_response
            }
            
        self.logger.info(f"Formatage de réponse: '{raw_response}' (agent: {agent_used}, message: '{original_message}')")
        
        # Formatage pour le cas où la réponse est juste un nombre (comme "0")
        if raw_response.strip().isdigit() or (raw_response.strip() == "0"):
            number = raw_response.strip()
            
            # Détection du contexte pour personnaliser la réponse
            if "leads" in original_message.lower() and "combien" in original_message.lower():
                if "contacté" in original_message.lower():
                    response = f"Il y a actuellement {number} leads qui ont été contactés dans la base de données."
                else:
                    response = f"Il y a actuellement {number} leads dans la base de données."
                return {
                    "status": "success",
                    "formatted_response": response,
                    "message": response
                }
                
        # Formatage pour les autres types de réponses
        prompt = f"""
        Tu es l'agent central de BerinIA, chargé de fournir des réponses conversationnelles et cohérentes.
        
        L'utilisateur a demandé: "{original_message}"
        
        L'agent {agent_used} a fourni cette réponse brute:
        ```
        {raw_response}
        ```
        
        Formate cette réponse brute en une réponse conversationnelle, claire et utile.
        Ne mentionne pas que tu as formaté la réponse ou que celle-ci provient d'un agent.
        Parle directement comme si tu étais BerinIA, l'assistant complet.
        """
        
        try:
            formatted_response = LLMService.call_llm(prompt, complexity="low")
            return {
                "status": "success",
                "formatted_response": formatted_response.strip(),
                "message": formatted_response.strip()
            }
        except Exception as e:
            self.logger.error(f"Erreur lors du formatage de la réponse: {str(e)}")
            # En cas d'erreur, retourner la réponse brute
            return {
                "status": "error",
                "formatted_response": raw_response,
                "message": raw_response,
                "error": str(e)
            }
    
    def handle_error(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère une erreur de manière intelligente en fournissant une réponse utile
        
        Args:
            input_data: Données d'entrée contenant l'erreur à gérer
            
        Returns:
            Réponse d'erreur conversationnelle
        """
        error_message = input_data.get("error_message", "Une erreur inconnue s'est produite")
        original_question = input_data.get("original_question", "")
        
        self.logger.info(f"Gestion d'erreur pour: '{original_question}', erreur: '{error_message}'")
        
        # Types d'erreurs courants avec réponses spécifiques
        error_patterns = {
            "no such table": "Je ne trouve pas cette information dans la base de données. Cette fonctionnalité n'est peut-être pas encore disponible.",
            "relation": "Je ne trouve pas cette information dans la base de données. Cette fonctionnalité n'est peut-être pas encore disponible.",
            "permission": "Je n'ai pas l'autorisation d'accéder à cette information. Veuillez contacter un administrateur.",
            "timeout": "La demande a pris trop de temps. Veuillez réessayer ou simplifier votre question.",
            "not found": "Je n'ai pas trouvé l'information demandée.",
            "invalid": "La demande contient des paramètres non valides."
        }
        
        # Vérifier si l'erreur correspond à un pattern connu
        for pattern, response in error_patterns.items():
            if pattern in error_message.lower():
                return {
                    "status": "error_handled",
                    "response": response,
                    "message": response
                }
                
        # Pour les erreurs inconnues, générer une réponse personnalisée
        prompt = f"""
        Tu es l'agent central de BerinIA, chargé de fournir des réponses utiles, même en cas d'erreur.
        
        L'utilisateur a demandé: "{original_question}"
        
        Une erreur s'est produite pendant le traitement: "{error_message}"
        
        Génère une réponse conviviale qui:
        1. Explique le problème de manière simple et compréhensible
        2. Suggère une alternative ou une action que l'utilisateur pourrait essayer
        3. Reste positif et serviable
        
        Ne mentionne pas de détails techniques de l'erreur sauf s'ils sont utiles pour l'utilisateur.
        """
        
        try:
            friendly_response = LLMService.call_llm(prompt, complexity="low")
            return {
                "status": "error_handled",
                "response": friendly_response.strip(),
                "message": friendly_response.strip()
            }
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de la réponse d'erreur: {str(e)}")
            # En cas d'erreur dans la gestion d'erreur, utiliser un message générique
            generic_response = "Je suis désolé, je n'ai pas pu traiter cette demande. Pourriez-vous reformuler ou essayer une autre requête?"
            return {
                "status": "error_handled",
                "response": generic_response,
                "message": generic_response
            }
        
    def analyze_request(self, message: str) -> Dict[str, Any]:
        """
        Analyse une demande utilisateur pour déterminer l'intention et les actions
        
        Args:
            message: Le message de l'utilisateur
            
        Returns:
            Analyse structurée de la demande
        """
        # Construction du prompt avec contexte
        system_capabilities = self.get_capabilities_summary()
        conversation_context = self.get_conversation_context()
        
        prompt_data = {
            "message": message,
            "capabilities": system_capabilities,
            "conversation_context": conversation_context,
            "all_agents": list(self.capabilities_cache.keys())
        }
        
        # Construction du prompt complet
        prompt = self._build_analysis_prompt(prompt_data)
        
        try:
            # Appel au LLM pour l'analyse
            llm_response = LLMService.call_llm(prompt, complexity="high")
            
            # Tentative de parsing JSON
            try:
                # Extraction du JSON si présent dans la réponse
                json_str = self._extract_json(llm_response)
                analysis = json.loads(json_str)
                
                # Validation des champs requis
                if "intent" not in analysis:
                    analysis["intent"] = "unknown"
                    
                if "confidence" not in analysis:
                    analysis["confidence"] = 0.5
                    
                if "actions" not in analysis or not analysis["actions"]:
                    analysis["actions"] = []
                    
                # Ajout de l'analyse brute pour debug
                analysis["_raw_analysis"] = llm_response
                
                return analysis
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Erreur de décodage JSON: {e}")
                self.logger.error(f"Réponse brute: {llm_response}")
                
                return {
                    "intent": "simple_response",
                    "confidence": 0.8,
                    "actions": [],
                    "response": "Je n'ai pas pu analyser correctement votre demande. Pourriez-vous la reformuler?"
                }
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            return {
                "intent": "simple_response",
                "confidence": 0.8, 
                "actions": [],
                "response": "Une erreur est survenue lors de l'analyse de votre demande."
            }
            
    def _extract_json(self, text: str) -> str:
        """
        Extrait un objet JSON d'un texte
        
        Args:
            text: Texte contenant potentiellement du JSON
            
        Returns:
            Chaîne JSON extraite
        """
        # Cas 1: Le texte entier est du JSON valide
        try:
            json.loads(text)
            return text
        except:
            pass
            
        # Cas 2: JSON délimité par des blocs de code
        json_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(json_block_pattern, text)
        
        if matches:
            for potential_json in matches:
                try:
                    json.loads(potential_json)
                    return potential_json
                except:
                    continue
        
        # Cas 3: Extraction basée sur les accolades
        try:
            start_idx = text.find('{')
            if start_idx != -1:
                # Trouver l'accolade fermante correspondante
                open_count = 0
                for i in range(start_idx, len(text)):
                    if text[i] == '{':
                        open_count += 1
                    elif text[i] == '}':
                        open_count -= 1
                        if open_count == 0:
                            potential_json = text[start_idx:i+1]
                            try:
                                json.loads(potential_json)
                                return potential_json
                            except:
                                # Continuer à chercher
                                pass
        except:
            pass
            
        # Fallback: Retourner le texte original pour un traitement ultérieur
        return text
        
    def execute_actions(self, analysis: Dict[str, Any], original_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute les actions identifiées lors de l'analyse
        
        Args:
            analysis: Résultat de l'analyse
            original_input: Données originales de la demande
            
        Returns:
            Résultat de l'exécution des actions
        """
        intent = analysis.get("intent", "unknown")
        
        # Cas spécial: réponse simple
        if intent == "simple_response":
            return {
                "status": "success",
                "message": analysis.get("response", "Je n'ai pas de réponse spécifique à cette demande.")
            }
            
        # Récupération des actions à exécuter
        actions = analysis.get("actions", [])
        
        if not actions:
            return {
                "status": "error",
                "message": "Aucune action à exécuter n'a été identifiée."
            }
            
        # Exécution séquentielle des actions
        results = []
        final_result = None
        
        for action in actions:
            try:
                agent_name = action.get("agent")
                action_name = action.get("action", "run")
                parameters = action.get("parameters", {})
                
                # Vérification de l'agent
                if not agent_name:
                    self.logger.error(f"Nom d'agent manquant dans l'action: {action}")
                    continue
                    
                # Récupération de l'agent - normalisation du nom pour la casse
                normalized_agent_name = self._normalize_agent_name(agent_name)
                agent = registry.get_or_create(normalized_agent_name)
                
                if not agent:
                    # Essayer avec la première lettre en majuscule (format standard)
                    standard_name = normalized_agent_name[0].upper() + normalized_agent_name[1:]
                    agent = registry.get_or_create(standard_name)
                    
                    if not agent:
                        self.logger.error(f"Agent non trouvé: {agent_name} (essayé aussi: {normalized_agent_name}, {standard_name})")
                        results.append({
                            "agent": agent_name,
                            "status": "error",
                            "message": f"Agent {agent_name} non trouvé"
                        })
                        continue
                
                # Préparation des paramètres avec contexte
                execution_params = {
                    **parameters,
                    "source": "MetaAgent",
                    "original_input": original_input
                }
                
                # Cas spécial pour le DatabaseQueryAgent - s'assurer que les paramètres message et question sont présents
                if normalized_agent_name == "DatabaseQueryAgent" or agent.__class__.__name__ == "DatabaseQueryAgent":
                    # Ajouter le message original si non présent dans les paramètres
                    if "message" not in execution_params and "question" not in execution_params:
                        original_message = original_input.get("message", original_input.get("content", ""))
                        self.logger.info(f"Ajout explicite du message '{original_message}' pour DatabaseQueryAgent")
                        execution_params["message"] = original_message
                        execution_params["question"] = original_message
                    
                    # Si une action spécifique comme count_leads est demandée, l'ajouter explicitement
                    if action_name in ["count_leads", "get_recent_leads", "count_contacted_leads"]:
                        execution_params["action"] = action_name
                        self.logger.info(f"Ajout de l'action explicite '{action_name}' pour DatabaseQueryAgent")
                
                # Exécution spécifique si action_name n'est pas "run"
                if action_name != "run" and hasattr(agent, action_name):
                    # Vérifier si la méthode existe et l'appeler
                    method = getattr(agent, action_name)
                    action_result = method(**execution_params)
                else:
                    # Sinon, utiliser la méthode run standard
                    action_result = agent.run(execution_params)
                
                # Stockage du résultat
                results.append({
                    "agent": agent_name,
                    "action": action_name,
                    "status": action_result.get("status"),
                    "result": action_result
                })
                
                # Mise à jour du résultat final (le dernier résultat sera retourné)
                final_result = action_result
                
            except Exception as e:
                self.logger.error(f"Erreur lors de l'exécution de l'action {action}: {str(e)}")
                self.logger.error(traceback.format_exc())
                
                results.append({
                    "agent": action.get("agent", "unknown"),
                    "status": "error",
                    "message": f"Erreur: {str(e)}"
                })
        
        # Post-traitement: génération d'une réponse cohérente basée sur tous les résultats
        response = self.generate_coherent_response(analysis, results, final_result)
        
        return response
        
    def generate_coherent_response(self, analysis: Dict[str, Any], action_results: List[Dict[str, Any]], 
                                  final_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère une réponse cohérente à partir des résultats des différentes actions
        
        Args:
            analysis: Analyse de la demande
            action_results: Résultats des actions exécutées
            final_result: Dernier résultat (potentiellement à retourner directement)
            
        Returns:
            Réponse cohérente
        """
        # Si aucun résultat d'action, message d'erreur
        if not action_results:
            return {
                "status": "error",
                "message": "Aucune action n'a pu être exécutée."
            }
            
        # Si une seule action et elle a un message, on peut le retourner directement
        if len(action_results) == 1 and final_result and "message" in final_result:
            return final_result
            
        # Sinon, générer une réponse synthétique basée sur tous les résultats
        success_results = [r for r in action_results if r.get("status") == "success"]
        error_results = [r for r in action_results if r.get("status") != "success"]
        
        # Construction du message de réponse
        if not success_results and error_results:
            # Tous les résultats sont des erreurs
            error_messages = [r.get("result", {}).get("message", "Erreur inconnue") for r in error_results]
            return {
                "status": "error",
                "message": f"Des erreurs sont survenues: {'; '.join(error_messages)}"
            }
            
        # Utilisation du LLM pour générer une réponse cohérente si nécessaire
        if len(action_results) > 1 or not final_result or "message" not in final_result:
            # Création d'un prompt pour synthétiser les résultats
            results_str = json.dumps(action_results, ensure_ascii=False, indent=2)
            original_query = analysis.get("original_query", "demande inconnue")
            
            prompt = f"""
            Tu es l'agent central de BerinIA, chargé de fournir des réponses claires et utiles.

            L'utilisateur a demandé: "{original_query}"
            
            J'ai exécuté plusieurs actions et obtenu les résultats suivants:
            ```
            {results_str}
            ```
            
            Crée une réponse cohérente qui synthétise ces résultats en une réponse utile pour l'utilisateur.
            Ta réponse doit être claire, concise et directement utile, sans mentionner les détails techniques de l'exécution.
            """
            
            try:
                response_text = LLMService.call_llm(prompt)
                return {
                    "status": "success",
                    "message": response_text.strip(),
                    "_action_results": action_results
                }
            except Exception as e:
                self.logger.error(f"Erreur lors de la génération de la réponse cohérente: {str(e)}")
                # Fallback - on utilise le dernier résultat
        
        # Fallback - retourner le dernier résultat ou un message générique
        if final_result and "message" in final_result:
            return final_result
        else:
            # Construction d'un message basique à partir des statuts
            statuses = [f"{r.get('agent', 'Agent')}: {r.get('status', 'inconnu')}" for r in action_results]
            return {
                "status": "mixed",
                "message": f"Résultats des actions: {', '.join(statuses)}",
                "_action_results": action_results
            }
    
    def index_system_capabilities(self) -> None:
        """
        Indexe les capacités du système en analysant tous les agents disponibles
        """
        self.logger.info("Indexation des capacités du système...")
        
        # Recherche de tous les dossiers d'agents
        agents_dir = Path("/root/berinia/infra-ia/agents")
        agent_dirs = [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith("__")]
        
        # Analyse de chaque dossier d'agent
        for agent_dir in agent_dirs:
            agent_name = f"{agent_dir.name.replace('_', '')}Agent"
            if agent_name == "metaAgent":
                agent_name = "MetaAgent"  # Exception pour nous-mêmes
                
            # Vérification si l'agent est déjà dans le cache
            if agent_name in self.capabilities_cache:
                continue
                
            # Tentative d'extraction des capacités de l'agent
            capabilities = self._extract_agent_capabilities(agent_dir, agent_name)
            if capabilities:
                self.capabilities_cache[agent_name] = capabilities
                self.logger.info(f"Capacités indexées pour {agent_name}")
            
        # Création de la structure du système
        self._build_system_structure()
        
        # Log du résultat
        self.logger.info(f"Indexation terminée: {len(self.capabilities_cache)} agents indexés")
        
    def _extract_agent_capabilities(self, agent_dir: Path, agent_name: str) -> Dict[str, Any]:
        """
        Extrait les capacités d'un agent à partir de ses fichiers
        
        Args:
            agent_dir: Chemin vers le dossier de l'agent
            agent_name: Nom de l'agent
            
        Returns:
            Dictionnaire des capacités de l'agent
        """
        capabilities = {
            "name": agent_name,
            "description": "",
            "methods": [],
            "keywords": []
        }
        
        try:
            # Recherche du fichier principal de l'agent
            agent_file = None
            for f in agent_dir.glob("*.py"):
                if f.name.endswith("_agent.py") or agent_name.lower() in f.name.lower():
                    agent_file = f
                    break
                    
            if not agent_file:
                self.logger.warning(f"Fichier d'agent non trouvé pour {agent_name}")
                return {}
                
            # Lecture du fichier pour extraire les informations
            with open(agent_file, "r") as f:
                content = f.read()
                
            # Extraction de la docstring de classe
            class_docstring_match = re.search(r'class\s+\w+\([^)]*\):\s*"""(.*?)"""', content, re.DOTALL)
            if class_docstring_match:
                capabilities["description"] = class_docstring_match.group(1).strip()
                
            # Extraction des méthodes
            method_matches = re.findall(r'def\s+(\w+)\s*\([^)]*\):\s*"""(.*?)"""', content, re.DOTALL)
            for method_name, method_doc in method_matches:
                if method_name.startswith("_"):
                    continue  # Ignorer les méthodes privées
                    
                capabilities["methods"].append({
                    "name": method_name,
                    "description": method_doc.strip()
                })
                
            # Extraction des mots-clés à partir du contenu
            # On fait simple: prendre tous les mots significatifs du fichier
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            word_counts = {}
            for word in words:
                if word in ["self", "none", "true", "false", "return", "import", "from"]:
                    continue
                word_counts[word] = word_counts.get(word, 0) + 1
                
            # Garder les mots les plus fréquents
            sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
            capabilities["keywords"] = [word for word, count in sorted_words[:20]]
            
            # Ajouter les mots du nom de l'agent
            agent_words = re.findall(r'[A-Z][a-z]+', agent_name)
            for word in agent_words:
                if word.lower() not in capabilities["keywords"] and word != "Agent":
                    capabilities["keywords"].append(word.lower())
            
            return capabilities
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction des capacités de {agent_name}: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {}
            
    def _normalize_agent_name(self, agent_name: str) -> str:
        """
        Normalise le nom d'un agent pour résoudre les problèmes de casse

        Args:
            agent_name: Nom de l'agent à normaliser

        Returns:
            Nom normalisé
        """
        # Cas spéciaux connus qui doivent être traités explicitement
        special_cases = {
            "databasequery": "DatabaseQueryAgent",
            "databasequeryagent": "DatabaseQueryAgent",
            "database_query": "DatabaseQueryAgent",
            "database_query_agent": "DatabaseQueryAgent",
            "databasequeryAgent": "DatabaseQueryAgent",
            "DatabasequeryAgent": "DatabaseQueryAgent",
            "sqlquery": "DatabaseQueryAgent",
            "sql": "DatabaseQueryAgent",
            "sqlqueryagent": "DatabaseQueryAgent",
            "db": "DatabaseQueryAgent",
            "dbquery": "DatabaseQueryAgent",
            "dbqueryagent": "DatabaseQueryAgent",
        }
        
        # Vérifier les cas spéciaux d'abord
        normalized_name_lower = agent_name.lower().replace("_", "").replace("-", "")
        if normalized_name_lower in special_cases:
            normalized_name = special_cases[normalized_name_lower]
            self.logger.info(f"Cas spécial: '{agent_name}' -> '{normalized_name}'")
            return normalized_name
            
        # Utilisation de la fonction de normalisation avancée
        try:
            from utils.agent_finder import normalize_agent_name as advanced_normalize

            # Le agent finder utilise une approche différente, nous voulons préserver le suffixe Agent
            normalized_base = advanced_normalize(agent_name)

            # S'assurer que le nom se termine par "Agent"
            if not normalized_base.endswith("agent"):
                normalized_base = normalized_base + "agent"

            # Normaliser la casse: première lettre en majuscule, "Agent" avec A majuscule
            final_name = normalized_base[0].upper() + normalized_base[1:-5].lower() + "Agent"

            self.logger.info(f"Normalisation avancée: '{agent_name}' -> '{final_name}'")
            return final_name
            
        except ImportError:
            # Fallback à la méthode originale si le module n'est pas disponible
            if agent_name.lower().endswith("agent"):
                # Séparer le nom et le suffixe "Agent"
                base_name = agent_name[:-5]  # Retirer "Agent"
                # Normaliser la casse: première lettre en majuscule, reste en minuscule
                normalized = base_name[0].upper() + base_name[1:].lower() + "Agent"
                return normalized
            else:
                # Si le nom ne contient pas "Agent", juste normaliser la première lettre
                normalized = agent_name[0].upper() + agent_name[1:].lower()
                # Ajouter "Agent" s'il ne se termine pas par ce suffixe
                if not normalized.endswith("Agent"):
                    normalized += "Agent"
                return normalized
    
    def _build_system_structure(self) -> None:
        """
        Construit une représentation de la structure du système
        """
        structure = {
            "agents": list(self.capabilities_cache.keys()),
            "agent_groups": {
                "system": [],
                "lead_generation": [],
                "communication": [],
                "analytics": [],
                "utility": []
            }
        }
        
        # Classification simple des agents par groupe
        for agent_name, capabilities in self.capabilities_cache.items():
            keywords = capabilities.get("keywords", [])
            description = capabilities.get("description", "").lower()
            
            # Classification heuristique simplifiée
            if any(k in ["overseer", "admin", "meta"] for k in keywords) or "system" in description:
                structure["agent_groups"]["system"].append(agent_name)
            elif any(k in ["lead", "scraper", "extract", "collect"] for k in keywords):
                structure["agent_groups"]["lead_generation"].append(agent_name)
            elif any(k in ["message", "email", "sms", "whatsapp", "communication"] for k in keywords):
                structure["agent_groups"]["communication"].append(agent_name)
            elif any(k in ["analytic", "report", "stat", "performance"] for k in keywords):
                structure["agent_groups"]["analytics"].append(agent_name)
            else:
                structure["agent_groups"]["utility"].append(agent_name)
                
        self.system_structure = structure
        
    def get_capabilities_summary(self) -> str:
        """
        Génère un résumé des capacités du système pour utilisation dans les prompts
        
        Returns:
            Résumé textuel des capacités
        """
        summary = "CAPACITÉS DU SYSTÈME:\n\n"
        
        # Groupes d'agents
        summary += "Groupes d'agents:\n"
        for group, agents in self.system_structure.get("agent_groups", {}).items():
            if agents:
                summary += f"- {group.upper()}: {', '.join(agents)}\n"
                
        # Détails des agents
        summary += "\nDétails des agents:\n"
        for agent_name, capabilities in self.capabilities_cache.items():
            desc = capabilities.get("description", "Pas de description").split("\n")[0]
            methods = capabilities.get("methods", [])
            
            summary += f"- {agent_name}: {desc}\n"
            if methods:
                methods_str = ", ".join([m["name"] for m in methods if m["name"] != "run"][:5])
                if methods_str:
                    summary += f"  Méthodes: {methods_str}\n"
                    
        return summary
        
    def get_conversation_context(self) -> str:
        """
        Génère un contexte de conversation basé sur l'historique récent
        
        Returns:
            Contexte textuel
        """
        if not self.conversation_history:
            return "Pas d'historique de conversation."
            
        context = "HISTORIQUE RÉCENT:\n"
        
        # N'inclure que les 5 derniers échanges
        recent_history = self.conversation_history[-5:]
        
        for i, entry in enumerate(recent_history):
            role = entry.get("role", "user")
            author = entry.get("author", "inconnu")
            message = entry.get("message", "")
            
            if role == "user":
                context += f"[Utilisateur {author}]: {message}\n"
            else:
                context += f"[Système {author}]: {message}\n"
                
        return context
                
    def update_conversation_history(self, message: str, role: str, author: str) -> None:
        """
        Met à jour l'historique des conversations
        
        Args:
            message: Message à ajouter
            role: Rôle ('user' ou 'system')
            author: Auteur du message
        """
        self.conversation_history.append({
            "message": message,
            "role": role,
            "author": author,
            "timestamp": datetime.now().isoformat()
        })
        
        # Limitation de la taille de l'historique
        if len(self.conversation_history) > self.max_history_entries:
            self.conversation_history = self.conversation_history[-self.max_history_entries:]
            
    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """
        Construit le prompt pour l'analyse des demandes
        
        Args:
            data: Données pour le prompt
            
        Returns:
            Prompt formaté
        """
        message = data.get("message", "")
        
        try:
            prompt_path = Path(self.prompt_path)
            if prompt_path.exists():
                with open(prompt_path, "r") as f:
                    template = f.read()
                    
                # Remplacements manuels (méthode simplifiée)
                template = template.replace("{message}", message)
                template = template.replace("{capabilities}", data.get("capabilities", ""))
                template = template.replace("{conversation_context}", data.get("conversation_context", ""))
                template = template.replace("{all_agents}", ", ".join(data.get("all_agents", [])))
                
                # Enrichir le prompt avec les connaissances pertinentes
                template = enrich_prompt_with_knowledge(message, template)
                
                return template
        except Exception as e:
            self.logger.error(f"Erreur lors de la construction du prompt: {str(e)}")
            
        # Fallback: prompt simple
        simple_prompt = f"""
        Tu es l'agent d'intelligence centrale du système BerinIA.
        
        CAPACITÉS DU SYSTÈME:
        {data.get("capabilities", "")}
        
        HISTORIQUE:
        {data.get("conversation_context", "")}
        
        DEMANDE DE L'UTILISATEUR:
        {message}
        
        Analyse la demande de l'utilisateur et identifie:
        1. L'intention principale
        2. Les agents à impliquer
        3. Les actions à effectuer
        4. Les paramètres nécessaires
        
        Réponds au format JSON avec les champs suivants:
        - intent: l'intention principale
        - confidence: niveau de confiance (0-1)
        - original_query: la demande originale
        - actions: liste des actions à effectuer, chacune avec:
          - agent: nom de l'agent à appeler
          - action: méthode à appeler (default: run)
          - parameters: paramètres à passer
        
        Si la demande ne nécessite pas d'agent spécifique, utilise "intent": "simple_response" et ajoute un champ "response".
        """
        
        # Enrichir le prompt avec les connaissances pertinentes
        enriched_prompt = enrich_prompt_with_knowledge(message, simple_prompt)
        return enriched_prompt
            
# Si exécuté directement
if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test de l'agent
    meta = MetaAgent()
    
    # Index des capacités
    meta.index_system_capabilities()
    summary = meta.get_capabilities_summary()
    print("Résumé des capacités:")
    print(summary)
    
    # Test d'analyse
    result = meta.analyze_request("Combien de leads avons-nous actuellement?")
    print("\nAnalyse:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

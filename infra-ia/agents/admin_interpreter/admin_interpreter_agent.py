"""
Module de l'AdminInterpreterAgent - Interface utilisateur en langage naturel
"""
import os
import re
import json
import logging
from typing import Dict, Any, Optional, List, Union, Set
import datetime

from core.agent_base import Agent
from utils.llm import LLMService
from agents.registry import registry

class AdminInterpreterAgent(Agent):
    """
    AdminInterpreterAgent - Agent d'interprétation des commandes administrateur en langage naturel
    
    Cet agent est responsable de:
    - Recevoir les messages en langage naturel de l'admin
    - Analyser l'intention et la tâche demandée
    - Convertir ces demandes en commandes structurées pour l'OverseerAgent
    - Demander des clarifications si nécessaire
    - Confirmer la bonne compréhension avant transmission
    """
    
    # Registre des agents valides avec leurs capacités
    VALID_AGENTS = {
        "OverseerAgent": ["supervision", "orchestration", "coordination", "système", "global", "état"],
        "AdminInterpreterAgent": ["interprétation", "commandes", "langage naturel", "admin"],
        "ScraperAgent": ["scraping", "extraction", "leads", "prospection"],
        "CleanerAgent": ["nettoyage", "données", "formatage"],
        "ScoringAgent": ["scoring", "évaluation", "notation", "leads"],
        "ValidatorAgent": ["validation", "données", "vérification"],
        "MessagingAgent": ["messages", "emails", "sms", "envoi", "communication"],
        "FollowUpAgent": ["relance", "suivi", "séquence"],
        "ResponseInterpreterAgent": ["interprétation", "réponses", "analyse"],
        "NicheExplorerAgent": ["exploration", "niches", "marchés"],
        "NicheClassifierAgent": ["classification", "niches", "catégories"],
        "VisualAnalyzerAgent": ["analyse", "visuelle", "sites", "web"],
        "LoggerAgent": ["logs", "journalisation", "enregistrement"],
        "PivotStrategyAgent": ["stratégie", "pivot", "performances", "statistiques"],
        "SchedulerAgent": ["planification", "tâches", "récurrence"],
        "DuplicateCheckerAgent": ["doublons", "duplications", "vérification"],
        "ResponseListenerAgent": ["écoute", "réponses", "webhook"],
        "ScrapingSupervisor": ["supervision", "scraping", "global"],
        "QualificationSupervisor": ["supervision", "qualification", "global"],
        "ProspectionSupervisor": ["supervision", "prospection", "global"],
        "DatabaseQueryAgent": ["base de données", "requêtes", "statistiques", "comptage", "données", "leads contactés", "taux de conversion", "conversations actives"]
    }
    
    # Synonymes pour le routing intelligent
    AGENT_ALIASES = {
        "leads": ["ScraperAgent", "CleanerAgent", "ScoringAgent", "ValidatorAgent"],
        "messages": ["MessagingAgent", "FollowUpAgent"],
        "réponses": ["ResponseInterpreterAgent", "ResponseListenerAgent"],
        "niches": ["NicheExplorerAgent", "NicheClassifierAgent"],
        "analyses": ["PivotStrategyAgent", "VisualAnalyzerAgent"],
        "planifications": ["SchedulerAgent"],
        "supervision": ["OverseerAgent", "ScrapingSupervisor", "QualificationSupervisor", "ProspectionSupervisor"]
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation de l'AdminInterpreterAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("AdminInterpreterAgent", config_path)
        
        # Override the prompt path to use the correct directory name with underscores
        self.prompt_path = "agents/admin_interpreter/prompt.txt"
        
        # Logger dédié
        self.logger = logging.getLogger("BerinIA-AdminInterpreter")
        
        # Historique des conversations pour le contexte
        self.conversation_history = []
        self.max_history_length = self.config.get("max_history_length", 10)
        
        # Mapping des intentions aux actions
        self.intent_to_action = {
            "update_config": self._handle_update_config,
            "execute_agent": self._handle_execute_agent,
            "get_system_state": self._handle_get_system_state,
            "orchestrate_workflow": self._handle_orchestrate_workflow,
            "schedule_task": self._handle_schedule_task,
            "cancel_task": self._handle_cancel_task,
            "help": self._handle_help,
            "unknown": self._handle_unknown
        }
        
        # Préparation du contexte agent pour le prompt
        self.agent_context = self._prepare_agent_context()
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        # Extraction du message de l'admin
        admin_message = input_data.get("message", "")
        
        if not admin_message:
            return {
                "status": "error",
                "message": "Message de l'admin manquant"
            }
        
        # Mise à jour de l'historique des conversations
        self._update_conversation_history("admin", admin_message)
        
        # Vérification des commandes directes (pour le débogage)
        if admin_message.startswith("!"):
            return self._handle_direct_command(admin_message[1:])
        
        # Analyse du message avec LLM
        analysis_result = self._analyze_admin_message(admin_message)
        
        # Traitement selon le résultat de l'analyse
        confidence = analysis_result.get("confidence", 0.0)
        intent = analysis_result.get("intent", "unknown")
        
        # Si la confiance est faible, demander confirmation
        if confidence < self.config.get("confidence_threshold", 0.7):
            return self._request_confirmation(analysis_result)
        
        # Traitement de l'intention reconnue
        return self._process_intent(intent, analysis_result)
    
    def _update_conversation_history(self, sender: str, message: str) -> None:
        """
        Met à jour l'historique des conversations
        
        Args:
            sender: Expéditeur du message (admin ou agent)
            message: Contenu du message
        """
        # Ajout du nouveau message
        self.conversation_history.append({
            "sender": sender,
            "message": message,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # Limitation de la taille de l'historique
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def _prepare_agent_context(self) -> str:
        """
        Prépare le contexte des agents disponibles pour le prompt
        
        Returns:
            Context string listing available agents and their capabilities
        """
        context = "AGENTS DISPONIBLES:\n"
        
        for agent_name, capabilities in self.VALID_AGENTS.items():
            capabilities_str = ", ".join(capabilities[:3])  # Limiter à 3 capacités pour la lisibilité
            context += f"- {agent_name}: {capabilities_str}\n"
            
        return context
    
    def _analyze_admin_message(self, message: str) -> Dict[str, Any]:
        """
        Analyse le message de l'admin avec LLM
        
        Args:
            message: Message de l'admin
            
        Returns:
            Résultat de l'analyse
        """
        # Construction du prompt avec contexte
        prompt_data = {
            "message": message,
            "conversation_history": self.conversation_history[-5:] if self.conversation_history else [],
            "agent_context": self.agent_context
        }
        
        # Utilisation du template personnalisé avec Jinja-style
        prompt = self._build_jinja_prompt(prompt_data)
        
        try:
            # Appel au LLM
            llm_response = LLMService.call_llm(prompt, complexity="high")
            
            # Debug: Affichage de la réponse brute
            self.logger.info(f"Réponse brute du LLM: {llm_response}")
            
            # Tentative de parsing du résultat JSON
            try:
                # Extraction du JSON si la réponse contient du texte supplémentaire
                if '```' in llm_response:
                    # Le texte peut contenir des blocs JSON délimités par des ```
                    start_idx = llm_response.find('```json')
                    if start_idx == -1:
                        start_idx = llm_response.find('```')
                    
                    start_idx = llm_response.find('{', start_idx)
                    end_idx = llm_response.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = llm_response[start_idx:end_idx]
                    else:
                        json_str = llm_response
                else:
                    # Sinon, considérer le texte entier comme du JSON
                    json_str = llm_response
                
                # Nettoyer et parser le JSON
                analysis_result = json.loads(json_str)
                
                # Vérification des champs obligatoires
                if "intent" not in analysis_result:
                    self.logger.warning(f"Champ 'intent' manquant dans la réponse: {json_str}")
                    analysis_result["intent"] = "unknown"
                
                if "confidence" not in analysis_result:
                    analysis_result["confidence"] = 0.5
                
                if "action" not in analysis_result:
                    analysis_result["action"] = {}
                
                # Post-traitement pour valider la cohérence et corriger les hallucinations
                return self._validate_and_correct_analysis(analysis_result)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Erreur de décodage JSON: {e}. Réponse: {llm_response}")
                
                # Création d'une réponse par défaut
                return {
                    "intent": "unknown",
                    "confidence": 0.0,
                    "description": "Analyse du message impossible",
                    "action": {},
                    "message": "Impossible d'analyser l'intention"
                }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du message: {str(e)}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "message": f"Erreur d'analyse: {str(e)}"
            }
    
    def _validate_and_correct_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide et corrige le résultat de l'analyse pour éviter les hallucinations
        
        Args:
            analysis: Résultat brut de l'analyse LLM
            
        Returns:
            Résultat validé et corrigé
        """
        # Validation de l'agent cible pour les intentions qui en nécessitent un
        if analysis["intent"] in ["execute_agent", "update_config"]:
            action = analysis.get("action", {})
            target_agent = action.get("target_agent")
            
            # Si l'agent cible n'existe pas, le corriger
            if target_agent and target_agent not in self.VALID_AGENTS:
                # Tentative de correction basée sur la similarité partielle
                corrected_agent = self._find_closest_agent(target_agent)
                
                if corrected_agent:
                    self.logger.warning(f"Agent inexistant détecté: '{target_agent}', corrigé en '{corrected_agent}'")
                    action["target_agent"] = corrected_agent
                    action["original_target"] = target_agent  # Conserver la référence originale
                    analysis["confidence"] = max(0.1, analysis.get("confidence", 0.5) - 0.2)  # Réduire la confiance
                else:
                    # Fallback à OverseerAgent si aucune correction possible
                    self.logger.warning(f"Agent inexistant: '{target_agent}', redirigé vers OverseerAgent")
                    action["target_agent"] = "OverseerAgent"
                    action["original_target"] = target_agent
                    analysis["confidence"] = 0.3  # Confiance très basse
                    
                    # Modifier la description pour refléter la correction
                    if "description" in analysis:
                        analysis["description"] = (
                            f"[Agent inconnu '{target_agent}' remplacé par OverseerAgent] " + 
                            analysis["description"]
                        )
                
                analysis["action"] = action
        
        return analysis
    
    def _find_closest_agent(self, invalid_agent: str) -> Optional[str]:
        """
        Trouve l'agent valide le plus proche d'un nom invalide
        
        Args:
            invalid_agent: Nom d'agent invalide
            
        Returns:
            Nom d'agent valide le plus proche ou None
        """
        # Gérer les cas communs
        normalized = invalid_agent.lower().replace(" ", "").replace("_", "").replace("-", "")
        
        # Cas spécifiques fréquents
        if "lead" in normalized:
            return "ScraperAgent"
        if "message" in normalized or "email" in normalized or "sms" in normalized:
            return "MessagingAgent"
        if "score" in normalized or "eval" in normalized:
            return "ScoringAgent"
        if "plan" in normalized or "schedul" in normalized:
            return "SchedulerAgent"
        if "stat" in normalized or "performance" in normalized:
            return "PivotStrategyAgent"
        if "response" in normalized or "reply" in normalized:
            return "ResponseInterpreterAgent"
        
        # Vérifier les correspondances partielles avec les agents valides
        best_match = None
        highest_score = 0
        
        for valid_agent in self.VALID_AGENTS.keys():
            valid_norm = valid_agent.lower().replace("agent", "")
            
            # Score simple basé sur la présence de sous-chaînes
            if valid_norm in normalized or normalized in valid_norm:
                score = len(set(normalized) & set(valid_norm)) / max(len(normalized), len(valid_norm))
                
                if score > highest_score and score > 0.4:  # Seuil minimal de correspondance
                    highest_score = score
                    best_match = valid_agent
        
        return best_match
    
    def _request_confirmation(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Demande confirmation à l'admin avant d'exécuter une action
        
        Args:
            analysis: Résultat de l'analyse du message
            
        Returns:
            Réponse à l'admin
        """
        # Construction du message de confirmation
        intent = analysis.get("intent", "unknown")
        action = analysis.get("action", {})
        
        if intent == "unknown":
            confirmation_message = (
                "Je n'ai pas bien compris votre demande. "
                "Pouvez-vous la reformuler ou préciser ce que vous souhaitez faire ?"
            )
        else:
            # Formatage de l'action pour l'affichage
            action_str = json.dumps(action, indent=2, ensure_ascii=False)
            
            confirmation_message = (
                f"J'ai compris que vous souhaitez : {analysis.get('description', 'Effectuer une action')}. \n\n"
                f"Voici l'action que je vais exécuter :\n```json\n{action_str}\n```\n\n"
                f"Est-ce correct ? Répondez par 'oui' pour confirmer ou clarifiez votre demande."
            )
        
        # Mise à jour de l'historique
        self._update_conversation_history("agent", confirmation_message)
        
        return {
            "status": "confirmation_required",
            "message": confirmation_message,
            "pending_action": analysis
        }
    
    def _process_intent(self, intent: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite l'intention reconnue
        
        Args:
            intent: Intention reconnue
            analysis: Résultat complet de l'analyse
            
        Returns:
            Résultat du traitement
        """
        # Récupération du handler approprié
        handler = self.intent_to_action.get(intent, self._handle_unknown)
        
        # Exécution du handler
        result = handler(analysis)
        
        # Mise à jour de l'historique avec la réponse
        if "message" in result:
            self._update_conversation_history("agent", result["message"])
        
        return result
    
    def _handle_direct_command(self, command: str) -> Dict[str, Any]:
        """
        Traite une commande directe (pour le débogage)
        
        Args:
            command: Commande directe
            
        Returns:
            Résultat de la commande
        """
        try:
            # Parsing de la commande
            command_parts = command.strip().split(" ", 1)
            command_type = command_parts[0].lower()
            
            if command_type == "state":
                # Récupération de l'OverseerAgent depuis le registre
                overseer = registry.get_or_create("OverseerAgent")
                if not overseer:
                    return {
                        "status": "error",
                        "message": "OverseerAgent non disponible"
                    }
                
                state = overseer.get_system_state()
                
                return {
                    "status": "success",
                    "message": f"État du système: {json.dumps(state, indent=2)}",
                    "data": state
                }
            
            elif command_type == "history":
                # Affichage de l'historique des conversations
                history_str = json.dumps(self.conversation_history, indent=2)
                
                return {
                    "status": "success",
                    "message": f"Historique des conversations: {history_str}",
                    "data": self.conversation_history
                }
            
            else:
                return {
                    "status": "error",
                    "message": f"Commande directe non reconnue: {command_type}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de l'exécution de la commande directe: {str(e)}"
            }
    
    def _handle_update_config(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une demande de mise à jour de configuration
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            Résultat de la mise à jour
        """
        try:
            # Extraction des données
            action = analysis.get("action", {})
            target_agent = action.get("target_agent")
            key = action.get("key")
            value = action.get("value")
            
            # Vérification des champs obligatoires
            if not target_agent or not key or value is None:
                return {
                    "status": "error",
                    "message": "Informations de configuration incomplètes"
                }
            
            # Récupération de l'OverseerAgent depuis le registre
            overseer = registry.get_or_create("OverseerAgent")
            if not overseer:
                return {
                    "status": "error",
                    "message": "OverseerAgent non disponible"
                }
            
            result = overseer.run({
                "source": "AdminInterpreterAgent",
                "action": "update_config",
                "target_agent": target_agent,
                "key": key,
                "value": value
            })
            
            # Construction de la réponse
            if result.get("status") == "success":
                message = f"Configuration de {target_agent} mise à jour: {key} = {value}"
            else:
                message = f"Erreur lors de la mise à jour: {result.get('message', 'Raison inconnue')}"
            
            return {
                "status": result.get("status"),
                "message": message,
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de la mise à jour de la configuration: {str(e)}"
            }
    
    def _handle_execute_agent(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une demande d'exécution d'agent
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            Résultat de l'exécution
        """
        try:
            # Extraction des données
            action = analysis.get("action", {})
            target_agent = action.get("target_agent")
            input_data = action.get("input_data", {})
            
            # Si c'est un DatabaseQueryAgent, assurons-nous d'inclure le message original
            if target_agent == "DatabaseQueryAgent" and "message" not in input_data:
                # Si message n'est pas présent mais que nous avons une action, utilisons le message original
                original_message = analysis.get("original_query", "")
                if original_message and "action" in input_data:
                    input_data["message"] = original_message

            # Vérification des champs obligatoires
            if not target_agent:
                return {
                    "status": "error",
                    "message": "Agent cible non spécifié"
                }
            
            # Récupération de l'OverseerAgent depuis le registre
            overseer = registry.get_or_create("OverseerAgent")
            if not overseer:
                # Tentative d'exécution directe
                target = registry.get_or_create(target_agent)
                if not target:
                    return {
                        "status": "error",
                        "message": f"Agents {target_agent} et OverseerAgent non disponibles"
                    }
                
                try:
                    direct_result = target.run(input_data)
                    return {
                        "status": "success",
                        "message": f"Exécution directe de {target_agent} réussie",
                        "data": direct_result
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Erreur lors de l'exécution directe de {target_agent}: {str(e)}"
                    }
            
            result = overseer.run({
                "source": "AdminInterpreterAgent",
                "action": "execute_agent",
                "target_agent": target_agent,
                "input_data": input_data
            })
            
            # Construction de la réponse
            if result.get("status") == "success":
                message = f"Exécution de {target_agent} réussie"
            else:
                message = f"Erreur lors de l'exécution de {target_agent}: {result.get('message', 'Raison inconnue')}"
            
            return {
                "status": result.get("status"),
                "message": message,
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de l'exécution de l'agent: {str(e)}"
            }
    
    def _handle_get_system_state(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une demande d'état du système
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            État du système
        """
        try:
            # Récupération de l'OverseerAgent depuis le registre
            overseer = registry.get_or_create("OverseerAgent")
            if not overseer:
                # Si l'OverseerAgent n'est pas disponible, retourner un état partiel
                registered_agents = list(registry.list_agents().keys())
                
                return {
                    "status": "partial",
                    "message": "État partiel du système (OverseerAgent non disponible)",
                    "data": {
                        "registered_agents": registered_agents,
                        "registry_initialized": registry.initialized,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                }
            
            result = overseer.run({
                "source": "AdminInterpreterAgent",
                "action": "get_system_state"
            })
            
            # Construction de la réponse
            if result.get("status") == "success":
                state = result.get("system_state", {})
                
                # Formatage de l'état pour l'affichage
                supervisors_status = state.get("supervisors_status", {})
                agents_status = state.get("agents_status", {})
                
                summary = (
                    f"État du système: {state.get('status', 'inconnu')}\n"
                    f"Démarré le: {state.get('started_at', 'inconnu')}\n\n"
                    f"Superviseurs actifs: {sum(1 for s in supervisors_status.values() if s == 'active')}/{len(supervisors_status)}\n"
                    f"Agents actifs: {sum(1 for a in agents_status.values() if a == 'active')}/{len(agents_status)}\n"
                )
                
                message = summary
            else:
                message = f"Erreur lors de la récupération de l'état: {result.get('message', 'Raison inconnue')}"
            
            return {
                "status": result.get("status"),
                "message": message,
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de la récupération de l'état du système: {str(e)}"
            }
    
    def _handle_orchestrate_workflow(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une demande d'orchestration de workflow
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            Résultat de l'orchestration
        """
        try:
            # Extraction des données
            action = analysis.get("action", {})
            workflow_name = action.get("workflow_name")
            workflow_data = action.get("workflow_data", {})
            
            # Vérification des champs obligatoires
            if not workflow_name:
                return {
                    "status": "error",
                    "message": "Nom du workflow non spécifié"
                }
            
            # Transmission à l'OverseerAgent
            from agents.overseer.overseer_agent import OverseerAgent
            overseer = OverseerAgent()
            
            result = overseer.run({
                "source": "AdminInterpreterAgent",
                "action": "orchestrate_workflow",
                "workflow_name": workflow_name,
                "workflow_data": workflow_data
            })
            
            # Construction de la réponse
            if result.get("status") == "success":
                message = f"Workflow {workflow_name} exécuté avec succès"
            else:
                message = f"Erreur lors de l'exécution du workflow {workflow_name}: {result.get('message', 'Raison inconnue')}"
            
            return {
                "status": result.get("status"),
                "message": message,
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de l'orchestration du workflow: {str(e)}"
            }
    
    def _handle_schedule_task(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une demande de planification de tâche
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            Résultat de la planification
        """
        try:
            # Extraction des données
            action = analysis.get("action", {})
            task_data = action.get("task_data", {})
            execution_time = action.get("execution_time")
            recurring = action.get("recurring", False)
            recurrence_interval = action.get("recurrence_interval")
            priority = action.get("priority", 1)
            
            # Vérification des champs obligatoires
            if not task_data or not execution_time:
                return {
                    "status": "error",
                    "message": "Informations de tâche incomplètes"
                }
            
            # Transmission à l'AgentSchedulerAgent
            from agents.scheduler.agent_scheduler_agent import AgentSchedulerAgent
            scheduler = AgentSchedulerAgent()
            
            result = scheduler.run({
                "action": "schedule_task",
                "task_data": task_data,
                "execution_time": execution_time,
                "recurring": recurring,
                "recurrence_interval": recurrence_interval,
                "priority": priority
            })
            
            # Construction de la réponse
            if result.get("status") == "success":
                task_id = result.get("task_id", "inconnu")
                message = f"Tâche {task_id} planifiée avec succès pour {result.get('execution_time')}"
                
                if recurring:
                    interval_str = self._format_time_interval(recurrence_interval)
                    message += f" (récurrente, tous les {interval_str})"
            else:
                message = f"Erreur lors de la planification: {result.get('message', 'Raison inconnue')}"
            
            return {
                "status": result.get("status"),
                "message": message,
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de la planification de la tâche: {str(e)}"
            }
    
    def _handle_cancel_task(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une demande d'annulation de tâche
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            Résultat de l'annulation
        """
        try:
            # Extraction des données
            action = analysis.get("action", {})
            task_id = action.get("task_id")
            
            # Vérification des champs obligatoires
            if not task_id:
                return {
                    "status": "error",
                    "message": "ID de tâche non spécifié"
                }
            
            # Transmission à l'AgentSchedulerAgent
            from agents.scheduler.agent_scheduler_agent import AgentSchedulerAgent
            scheduler = AgentSchedulerAgent()
            
            result = scheduler.run({
                "action": "cancel_task",
                "task_id": task_id
            })
            
            # Construction de la réponse
            if result.get("status") == "success":
                message = f"Tâche {task_id} annulée avec succès"
            else:
                message = f"Erreur lors de l'annulation: {result.get('message', 'Raison inconnue')}"
            
            return {
                "status": result.get("status"),
                "message": message,
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de l'annulation de la tâche: {str(e)}"
            }
    
    def _handle_help(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une demande d'aide
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            Message d'aide
        """
        # Construction du message d'aide
        help_message = (
            "🤖 **BerinIA - Guide d'utilisation** 🤖\n\n"
            "Voici ce que vous pouvez me demander :\n\n"
            "1. **Scraper des leads**\n"
            "   Exemples : \"Trouve 30 leads dans la niche coaching\" ou \"Scrape 50 contacts dans l'immobilier\"\n\n"
            "2. **Configurer un agent**\n"
            "   Exemples : \"Limite le scraping à 20 leads par niche\" ou \"Modifie la priorité du ScoringAgent à 1\"\n\n"
            "3. **Exécuter des workflows**\n"
            "   Exemples : \"Lance le workflow de qualification\" ou \"Exécute le processus complet pour les leads immobilier\"\n\n"
            "4. **Planifier des tâches**\n"
            "   Exemples : \"Relance la campagne coaching demain à 10h\" ou \"Planifie un scraping tous les lundis à 9h\"\n\n"
            "5. **Obtenir des informations**\n"
            "   Exemples : \"Affiche-moi l'état du système\" ou \"Quels agents sont actifs actuellement ?\"\n\n"
            "Je suis conçu pour comprendre le langage naturel, donc n'hésitez pas à formuler vos demandes comme vous le feriez avec un humain."
        )
        
        return {
            "status": "success",
            "message": help_message
        }
    
    def _handle_unknown(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une intention inconnue
        
        Args:
            analysis: Résultat de l'analyse
            
        Returns:
            Message d'erreur
        """
        return {
            "status": "error",
            "message": (
                "Je ne comprends pas votre demande. "
                "Pouvez-vous reformuler ou demander de l'aide en tapant \"aide\" ou \"help\" ?"
            )
        }
    
    def _build_jinja_prompt(self, context: Dict[str, Any]) -> str:
        """
        Construit le prompt en utilisant un template style-Jinja
        
        Args:
            context: Contexte pour le template
            
        Returns:
            Le prompt formaté
        """
        try:
            # Lecture du template
            with open(self.prompt_path, "r") as f:
                template = f.read()
            
            # Remplacement simple des variables
            template = template.replace("{{ message }}", context.get("message", ""))
            
            # Ajout du contexte des agents disponibles
            agent_context = context.get("agent_context", "")
            template = template.replace("{{ agent_context }}", agent_context)
            
            # Traitement du bloc de l'historique de conversation
            conversation_history = context.get("conversation_history", [])
            
            if conversation_history:
                # Construction du bloc d'historique
                history_block = "Historique des échanges récents :\n"
                for exchange in conversation_history:
                    sender = exchange.get("sender", "Inconnu")
                    message = exchange.get("message", "")
                    history_block += f"- {sender} : {message}\n"
                
                # Remplacement du bloc conditionnel
                template = template.replace(
                    "{% if conversation_history %}\nHistorique des échanges récents :\n{% for exchange in conversation_history %}\n- {{ exchange.sender }} : {{ exchange.message }}\n{% endfor %}\n{% endif %}",
                    history_block
                )
            else:
                # Suppression du bloc conditionnel s'il n'y a pas d'historique
                template = template.replace(
                    "{% if conversation_history %}\nHistorique des échanges récents :\n{% for exchange in conversation_history %}\n- {{ exchange.sender }} : {{ exchange.message }}\n{% endfor %}\n{% endif %}",
                    ""
                )
            
            return template
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la construction du prompt: {str(e)}")
            return f"Tu es un agent nommé {self.name}. Réponds en JSON. Voici le message de l'admin: {context.get('message', '')}"
    
    def _format_time_interval(self, seconds: int) -> str:
        """
        Formate un intervalle de temps en secondes en une chaîne lisible
        
        Args:
            seconds: Nombre de secondes
            
        Returns:
            Chaîne formatée
        """
        if seconds < 60:
            return f"{seconds} secondes"
        
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} minutes"
        
        hours = minutes // 60
        if hours < 24:
            return f"{hours} heures"
        
        days = hours // 24
        if days < 7:
            return f"{days} jours"
        
        weeks = days // 7
        if weeks < 4:
            return f"{weeks} semaines"
        
        months = days // 30
        return f"{months} mois"

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Création d'une instance de l'AdminInterpreterAgent
    interpreter = AdminInterpreterAgent()
    
    # Demande d'aide
    result = interpreter.run({"message": "Aide-moi à comprendre comment utiliser le système"})
    print(result["message"])
    
    # Test avec une instruction
    result = interpreter.run({"message": "Scrape 20 leads dans la niche restauration"})
    print(result["message"])

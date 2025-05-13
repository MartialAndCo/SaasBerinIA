"""
Module de l'OverseerAgent - Cerveau central du système BerinIA
"""
import os
import json
import importlib
import inspect
from typing import Dict, Any, Optional, List, Type, Union
from pathlib import Path
import datetime

from core.agent_base import Agent
from utils.llm import LLMService

class OverseerAgent(Agent):
    """
    OverseerAgent - Le cerveau central qui supervise tous les agents
    
    Cet agent est responsable de:
    - Orchestrer l'ensemble des agents du système
    - Prendre les décisions stratégiques
    - Diriger le flux d'exécution entre les agents
    - Modifier les configurations des agents
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation de l'OverseerAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("OverseerAgent", config_path)
        
        # Initialisation du registre des agents (chargé dynamiquement)
        self.agent_registry = {}
        self.supervisors = {}
        self.operational_agents = {}
        
        # État du système
        self.system_state = {
            "status": "initialized",
            "started_at": datetime.datetime.now().isoformat(),
            "active_tasks": [],
            "supervisors_status": {},
            "agents_status": {}
        }
        
        # Chargement du registre des agents
        self._load_agent_registry()
    
    def _load_agent_registry(self) -> None:
        """
        Charge dynamiquement tous les agents disponibles dans le registre
        """
        # Liste des superviseurs selon la documentation
        supervisor_names = [
            "ScrapingSupervisor",
            "QualificationSupervisor",
            "ProspectionSupervisor"
        ]
        
        # Liste des agents opérationnels selon la documentation
        operational_agent_names = [
            "NicheExplorerAgent",
            "ScraperAgent",
            "CleanerAgent",
            "ScoringAgent",
            "ValidatorAgent",
            "DuplicateCheckerAgent",
            "MessagingAgent",
            "FollowUpAgent",
            "ResponseInterpreterAgent",
            "AgentSchedulerAgent",
            "PivotStrategyAgent",
            "LoggerAgent",
            "AdminInterpreterAgent",
            "NicheClassifierAgent",
            "VisualAnalyzerAgent",
            "DatabaseQueryAgent"  # Ajout de notre nouvel agent de requêtes de base de données
        ]
        
        # Construction des chemins de modules pour les superviseurs
        for name in supervisor_names:
            # Convert camelCase name to snake_case
            base_name = ''.join(['_' + c.lower() if c.isupper() else c.lower() for c in name]).lstrip('_')
            
            # Construct the correct module path with snake_case
            module_name = f"agents.{base_name}.{base_name}"
            
            self.supervisors[name] = {
                "module": module_name,
                "class": name,
                "status": "inactive"
            }
        
        # Construction des chemins de modules pour les agents opérationnels
        for name in operational_agent_names:
            # Convert camelCase agent name to snake_case module name
            base_name = name[:-5]  # Remove "Agent" suffix
            module_base = ''.join(['_' + c.lower() if c.isupper() else c.lower() for c in base_name]).lstrip('_')
            
            # Construct the correct module path with snake_case
            module_name = f"agents.{module_base}.{module_base}_agent"
            
            self.operational_agents[name] = {
                "module": module_name,
                "class": name,
                "status": "inactive"
            }
        
        # Mise à jour du registre global
        self.agent_registry = {
            **self.supervisors,
            **self.operational_agents
        }
        
        # Mise à jour de l'état du système
        self.system_state["supervisors_status"] = {
            name: info["status"] for name, info in self.supervisors.items()
        }
        self.system_state["agents_status"] = {
            name: info["status"] for name, info in self.operational_agents.items()
        }
    
    def _get_agent_instance(self, agent_name: str) -> Optional[Agent]:
        """
        Récupère une instance d'agent à partir de son nom

        Args:
            agent_name: Nom de l'agent à instancier

        Returns:
            Instance de l'agent ou None en cas d'erreur
        """
        if agent_name not in self.agent_registry:
            self.speak(f"Agent {agent_name} non trouvé dans le registre.", target="AdminInterpreterAgent")
            return None

        try:
            # Récupération des informations du module
            agent_info = self.agent_registry[agent_name]
            module_name = agent_info["module"]
            class_name = agent_info["class"]

            # Importation dynamique du module
            module = importlib.import_module(module_name)
            agent_class = getattr(module, class_name)

            # Instanciation de l'agent
            agent_instance = agent_class()
            return agent_instance
        except Exception as e:
            self.speak(f"Erreur lors de l'instanciation de {agent_name}: {str(e)}", target="AdminInterpreterAgent")
            return None
    
    def delegate_to_supervisor(self, supervisor_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Délègue une tâche à un superviseur spécifique

        Args:
            supervisor_name: Nom du superviseur (ex: 'ScrapingSupervisor')
            task_data: Données de la tâche à exécuter

        Returns:
            Résultat de l'exécution de la tâche par le superviseur
        """
        # Vérification que le superviseur existe dans le registre
        if supervisor_name not in self.supervisors:
            error_message = f"Superviseur {supervisor_name} non trouvé dans le registre."
            self.speak(error_message, target="AdminInterpreterAgent")
            return {
                "status": "error",
                "message": error_message
            }
        
        # Log de la délégation
        self.speak(f"Délégation de tâche au superviseur {supervisor_name}", target=supervisor_name)
        
        try:
            # Construction du chemin d'importation
            supervisor_info = self.supervisors[supervisor_name]
            module_name = supervisor_info["module"]
            class_name = supervisor_info["class"]
            
            # Importation dynamique du module du superviseur
            module = importlib.import_module(module_name)
            supervisor_class = getattr(module, class_name)
            
            # Instanciation du superviseur
            supervisor = supervisor_class()
            
            # Mise à jour du statut du superviseur
            self.supervisors[supervisor_name]["status"] = "active"
            
            # Exécution de la tâche par le superviseur
            result = supervisor.run(task_data)
            
            # Log du résultat
            if result.get("status") == "success":
                self.speak(f"Tâche exécutée avec succès par {supervisor_name}", target="AdminInterpreterAgent")
            else:
                self.speak(f"Échec de la tâche exécutée par {supervisor_name}: {result.get('message', 'Pas de détails')}", 
                         target="AdminInterpreterAgent")
            
            # Mise à jour du statut du superviseur
            self.supervisors[supervisor_name]["status"] = "inactive"
            
            return result
            
        except Exception as e:
            # En cas d'erreur
            error_message = f"Erreur lors de la délégation à {supervisor_name}: {str(e)}"
            self.speak(error_message, target="AdminInterpreterAgent")
            
            # Mise à jour du statut du superviseur
            self.supervisors[supervisor_name]["status"] = "error"
            
            return {
                "status": "error",
                "message": error_message
            }

    def execute_agent(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute un agent avec les données d'entrée fournies
        
        Args:
            agent_name: Nom de l'agent à exécuter
            input_data: Données d'entrée pour l'agent
            
        Returns:
            Résultat de l'exécution de l'agent
        """
        # Récupération de l'instance d'agent
        agent = self._get_agent_instance(agent_name)
        if not agent:
            return {
                "status": "error",
                "message": f"Agent {agent_name} non disponible"
            }
        
        # Mise à jour du statut de l'agent
        if agent_name in self.supervisors:
            self.supervisors[agent_name]["status"] = "active"
        elif agent_name in self.operational_agents:
            self.operational_agents[agent_name]["status"] = "active"
        
        # Exécution de l'agent
        self.speak(f"Exécution de {agent_name}", target=agent_name)
        
        try:
            # Exécution de la méthode run() de l'agent
            result = agent.run(input_data)
            
            # Log du résultat
            self.speak(f"Résultat de {agent_name} obtenu", target="AdminInterpreterAgent")
            
            # Mise à jour du statut de l'agent
            if agent_name in self.supervisors:
                self.supervisors[agent_name]["status"] = "inactive"
            elif agent_name in self.operational_agents:
                self.operational_agents[agent_name]["status"] = "inactive"
            
            return result
        except Exception as e:
            # En cas d'erreur
            error_message = f"Erreur lors de l'exécution de {agent_name}: {str(e)}"
            self.speak(error_message, target="AdminInterpreterAgent")
            
            # Mise à jour du statut de l'agent
            if agent_name in self.supervisors:
                self.supervisors[agent_name]["status"] = "error"
            elif agent_name in self.operational_agents:
                self.operational_agents[agent_name]["status"] = "error"
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def update_agent_config(self, agent_name: str, key: str, value: Any) -> Dict[str, Any]:
        """
        Met à jour la configuration d'un agent
        
        Args:
            agent_name: Nom de l'agent à mettre à jour
            key: Clé de configuration à modifier
            value: Nouvelle valeur
            
        Returns:
            Statut de la mise à jour
        """
        # Récupération de l'instance d'agent
        agent = self._get_agent_instance(agent_name)
        if not agent:
            return {
                "status": "error",
                "message": f"Agent {agent_name} non disponible"
            }
        
        try:
            # Mise à jour de la configuration
            agent.update_config(key, value)
            
            # Log de la mise à jour
            self.speak(
                f"Configuration de {agent_name} mise à jour: {key} = {value}",
                target="AdminInterpreterAgent"
            )
            
            return {
                "status": "success",
                "message": f"Configuration de {agent_name} mise à jour",
                "key": key,
                "value": value
            }
        except Exception as e:
            error_message = f"Erreur lors de la mise à jour de la configuration de {agent_name}: {str(e)}"
            self.speak(error_message, target="AdminInterpreterAgent")
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def get_system_state(self) -> Dict[str, Any]:
        """
        Récupère l'état actuel du système
        
        Returns:
            État complet du système
        """
        # Mise à jour des statuts
        self.system_state["supervisors_status"] = {
            name: info["status"] for name, info in self.supervisors.items()
        }
        self.system_state["agents_status"] = {
            name: info["status"] for name, info in self.operational_agents.items()
        }
        
        return self.system_state
    
    def handle_admin_instruction(self, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une instruction provenant de l'AdminInterpreterAgent
        
        Args:
            instruction: L'instruction structurée
            
        Returns:
            Résultat du traitement de l'instruction
        """
        action = instruction.get("action")
        
        if action == "update_config":
            # Mise à jour de configuration
            return self.update_agent_config(
                instruction.get("target_agent"),
                instruction.get("key"),
                instruction.get("value")
            )
        
        elif action == "execute_agent":
            # Exécution d'un agent
            return self.execute_agent(
                instruction.get("target_agent"),
                instruction.get("input_data", {})
            )
        
        elif action == "get_system_state":
            # Récupération de l'état du système
            return {
                "status": "success",
                "system_state": self.get_system_state()
            }
        
        elif action == "orchestrate_workflow":
            # Orchestration d'un workflow complet
            return self.orchestrate_workflow(
                instruction.get("workflow_name"),
                instruction.get("workflow_data", {})
            )
        
        else:
            # Action non reconnue
            error_message = f"Action non reconnue: {action}"
            self.speak(error_message, target="AdminInterpreterAgent")
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def orchestrate_workflow(self, workflow_name: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestre un workflow complet impliquant plusieurs agents
        
        Args:
            workflow_name: Nom du workflow à exécuter
            workflow_data: Données initiales pour le workflow
            
        Returns:
            Résultat du workflow
        """
        # Log du démarrage du workflow
        self.speak(f"Démarrage du workflow: {workflow_name}", target="AdminInterpreterAgent")
        
        # Workflows prédéfinis
        workflows = {
            "scraping_to_cleaning": [
                {"agent": "ScraperAgent", "input_key": None, "output_key": "leads"},
                {"agent": "CleanerAgent", "input_key": "leads", "output_key": "cleaned_leads"}
            ],
            "full_qualification": [
                {"agent": "ScraperAgent", "input_key": None, "output_key": "leads"},
                {"agent": "CleanerAgent", "input_key": "leads", "output_key": "cleaned_leads"},
                {"agent": "ScoringAgent", "input_key": "cleaned_leads", "output_key": "scored_leads"},
                {"agent": "ValidatorAgent", "input_key": "scored_leads", "output_key": "validated_leads"},
                {"agent": "DuplicateCheckerAgent", "input_key": "validated_leads", "output_key": "final_leads"}
            ],
            "messaging_workflow": [
                {"agent": "MessagingAgent", "input_key": None, "output_key": "sent_messages"},
                {"agent": "FollowUpAgent", "input_key": "sent_messages", "output_key": "follow_ups"}
            ],
            "visual_analysis_with_classification": [
                {"agent": "VisualAnalyzerAgent", "input_key": None, "output_key": "visual_analysis"},
                {"agent": "NicheClassifierAgent", "input_key": "visual_analysis", "output_key": "personalized_approach"}
            ],
            "lead_enrichment_with_classification": [
                {"agent": "NicheClassifierAgent", "input_key": None, "output_key": "niche_classification"},
                {"agent": "VisualAnalyzerAgent", "input_key": "niche_classification", "output_key": "visual_analysis"},
                {"agent": "NicheClassifierAgent", "input_key": "visual_analysis", "output_key": "personalized_approach"},
                {"agent": "MessagingAgent", "input_key": "personalized_approach", "output_key": "message"}
            ]
        }
        
        # Vérification de l'existence du workflow
        if workflow_name not in workflows:
            error_message = f"Workflow non reconnu: {workflow_name}"
            self.speak(error_message, target="AdminInterpreterAgent")
            
            return {
                "status": "error",
                "message": error_message
            }
        
        # Exécution séquentielle du workflow
        workflow_steps = workflows[workflow_name]
        current_data = workflow_data
        results = {}
        
        for step in workflow_steps:
            agent_name = step["agent"]
            input_key = step["input_key"]
            output_key = step["output_key"]
            
            # Préparation des données d'entrée pour cette étape
            if input_key is None:
                # Utilisation des données initiales
                step_input = current_data
            else:
                # Utilisation de la sortie d'une étape précédente
                step_input = {
                    "data": results.get(input_key, {})
                }
            
            # Exécution de l'agent pour cette étape
            step_result = self.execute_agent(agent_name, step_input)
            
            # Vérification du succès
            if step_result.get("status") == "error":
                self.speak(f"Erreur dans le workflow {workflow_name} à l'étape {agent_name}", target="AdminInterpreterAgent")
                return {
                    "status": "error",
                    "message": f"Erreur à l'étape {agent_name}",
                    "step_error": step_result,
                    "partial_results": results
                }
            
            # Stockage du résultat de cette étape
            results[output_key] = step_result
        
        # Workflow terminé avec succès
        self.speak(f"Workflow {workflow_name} terminé avec succès", target="AdminInterpreterAgent")
        
        return {
            "status": "success",
            "workflow": workflow_name,
            "results": results
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        # Si l'entrée provient de l'AdminInterpreterAgent
        if input_data.get("source") == "AdminInterpreterAgent":
            return self.handle_admin_instruction(input_data)
        
        # Si l'entrée est une demande d'état du système
        if input_data.get("action") == "get_system_state":
            return {
                "status": "success",
                "system_state": self.get_system_state()
            }
        
        # Si l'entrée est une demande d'exécution d'agent
        if input_data.get("action") == "execute_agent":
            return self.execute_agent(
                input_data.get("agent_name"),
                input_data.get("agent_input", {})
            )
        
        # Si l'entrée est une demande de mise à jour de configuration
        if input_data.get("action") == "update_config":
            return self.update_agent_config(
                input_data.get("agent_name"),
                input_data.get("config_key"),
                input_data.get("config_value")
            )
        
        # Si l'entrée est une demande d'orchestration de workflow
        if input_data.get("action") == "orchestrate_workflow":
            return self.orchestrate_workflow(
                input_data.get("workflow_name"),
                input_data.get("workflow_data", {})
            )
        
        # Si l'entrée est une demande de traitement d'interprétation de réponse
        if input_data.get("action") == "handle_response_interpretation":
            self.speak("Réception d'une interprétation de réponse", target="AdminInterpreterAgent")
            return self.handle_response_interpretation(input_data.get("interpretation", {}))
            
        # Si l'entrée est une demande de traitement d'événement
        if input_data.get("action") == "handle_event":
            event_type = input_data.get("event_type")
            event_data = input_data.get("event_data", {})
            
            # Log de la réception de l'événement
            self.speak(f"Réception d'un événement: {event_type}", target=None)
            
            # Décision basée sur le type d'événement
            if event_type == "email_response":
                # Traitement d'une réponse par email
                return self.execute_agent("ResponseInterpreterAgent", event_data)
            
            elif event_type == "sms_response":
                # Traitement d'une réponse par SMS
                return self.execute_agent("ResponseInterpreterAgent", event_data)
            
            elif event_type == "scheduled_task":
                # Traitement d'une tâche planifiée
                task_data = event_data.get("task_data", {})
                task_agent = task_data.get("agent")
                
                return self.execute_agent(task_agent, task_data)
            
            else:
                # Type d'événement non reconnu
                return {
                    "status": "error",
                    "message": f"Type d'événement non reconnu: {event_type}"
                }
        
        # Analyse des instructions avec LLM si l'entrée est complexe ou non structurée
        if "instruction" in input_data:
            instruction = input_data["instruction"]
            
            # Construction du prompt pour l'analyse
            prompt = self.build_prompt({
                "instruction": instruction,
                "context": json.dumps(self.get_system_state(), indent=2)
            })
            
            # Appel au LLM pour analyser l'instruction
            llm_response = LLMService.call_llm(prompt, complexity="high")
            
            try:
                # Tentative de parsing du résultat comme JSON
                parsed_response = json.loads(llm_response)
                
                # Traitement de l'instruction analysée
                return self.handle_admin_instruction(parsed_response)
            except json.JSONDecodeError:
                # Si le résultat n'est pas un JSON valide
                return {
                    "status": "error",
                    "message": "Impossible d'analyser l'instruction",
                    "raw_response": llm_response
                }
        
        # Cas par défaut
        return {
            "status": "error",
            "message": "Action non reconnue ou données d'entrée incomplètes"
        }

    def handle_response_interpretation(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite les résultats d'interprétation d'une réponse de lead
        et décide des actions à entreprendre (par exemple: envoyer une réponse,
        transférer au CRM, blacklister, etc.)
        
        Args:
            interpretation: Résultat de l'interprétation
            
        Returns:
            Résultat du traitement
        """
        self.speak("Traitement d'une interprétation de réponse", target="AdminInterpreterAgent")
        
        # Extraction des informations importantes
        interpretation_data = interpretation.get("interpretation", {})
        lead_data = interpretation.get("lead_data", {})
        original_message = interpretation.get("original_message", "")
        
        # Vérifier s'il y a des URLs détectés qui pourraient être le site du client
        urls = interpretation.get("urls", [])
        is_client_website = interpretation.get("is_client_website", False)
        site_analysis_results = None
        
        # Si un URL a été détecté comme le site probable du client, le faire analyser
        if urls and is_client_website:
            client_website_url = urls[0]  # Prendre le premier URL
            self.speak(f"URL de site client détecté: {client_website_url}. Lancement de l'analyse visuelle...", 
                      target="AdminInterpreterAgent")
            
            # Préparation des données pour le VisualAnalyzerAgent
            analysis_input = {
                "action": "analyze_website",
                "url": client_website_url,
                "lead_id": lead_data.get("lead_id", ""),
                "capture_screenshot": True,
                "deep_analysis": True
            }
            
            # Exécution du workflow d'analyse visuelle
            try:
                workflow_result = self.orchestrate_workflow(
                    "visual_analysis_with_classification", 
                    {"url": client_website_url, "lead_data": lead_data}
                )
                
                if workflow_result.get("status") == "success":
                    self.speak("Analyse visuelle terminée avec succès", target="AdminInterpreterAgent")
                    site_analysis_results = workflow_result.get("results", {}).get("personalized_approach", {})
                else:
                    self.speak(f"Erreur lors de l'analyse visuelle: {workflow_result.get('message')}", 
                             target="AdminInterpreterAgent")
            except Exception as e:
                self.speak(f"Exception lors de l'analyse visuelle: {str(e)}", target="AdminInterpreterAgent")
        
        if not interpretation_data:
            return {
                "status": "error",
                "message": "Données d'interprétation manquantes"
            }
        
        # Récupération de l'action recommandée
        action = interpretation_data.get("action", {})
        action_type = action.get("type", "none")
        
        self.speak(f"Action recommandée: {action_type}", target="AdminInterpreterAgent")
        
        # Avant toute autre action, nous envoyons toujours une réponse au message entrant
        if original_message:
            # Préparation des données pour le MessagingAgent
            response_data = {
                "action": "send_response",
                "lead_data": lead_data,
                "message": original_message,
                "campaign_id": interpretation.get("campaign_id", "general"),
                "channel": interpretation.get("channel", "sms")  # Le canal doit correspondre au canal d'entrée
            }
            
            # Envoi de la réponse via le MessagingAgent
            self.speak("Envoi d'une réponse contextuelle au message entrant", target="ProspectionSupervisor")
            response_result = self.execute_agent("MessagingAgent", response_data)
            
            # Log du résultat
            if response_result.get("status") == "success":
                self.speak("Réponse envoyée avec succès", target="ProspectionSupervisor")
            else:
                self.speak(f"Erreur lors de l'envoi de la réponse: {response_result.get('message')}", target="ProspectionSupervisor")
        
        # Exécution d'actions supplémentaires selon l'interprétation
        if action_type == "transfer_to_crm":
            # Transfert au CRM
            self.speak("Transfert de lead au CRM", target="ProspectionSupervisor")
            
            # En mode réel, on exécuterait un agent spécifique pour le transfert au CRM
            return {
                "status": "success",
                "message": "Lead transféré au CRM et réponse envoyée",
                "action_taken": "transfer_to_crm",
                "action_details": action.get("details", {}),
                "response_result": response_result if original_message else None
            }
            
        elif action_type == "send_follow_up":
            # Dans ce cas, on a déjà envoyé une réponse immédiate
            # On pourrait programmer une relance supplémentaire si nécessaire
            delay_days = action.get("details", {}).get("delay_days", 0)
            
            if delay_days > 0:
                self.speak(f"Programmation d'une relance dans {delay_days} jours", target="ProspectionSupervisor")
                # Ici, on pourrait appeler un agent de planification pour programmer la relance
            
            return {
                "status": "success",
                "message": "Réponse envoyée et relance programmée si nécessaire",
                "action_taken": "send_follow_up",
                "response_result": response_result if original_message else None
            }
            
        elif action_type == "blacklist":
            # Blacklister le lead
            self.speak("Blacklistage du lead", target="ProspectionSupervisor")
            
            # En mode réel, on mettrait à jour la base de données
            return {
                "status": "success",
                "message": "Lead blacklisté et réponse envoyée",
                "action_taken": "blacklist",
                "action_details": action.get("details", {}),
                "response_result": response_result if original_message else None
            }
            
        elif action_type == "flag":
            # Marquer le lead pour révision
            self.speak("Lead marqué pour révision", target="AdminInterpreterAgent")
            
            return {
                "status": "success",
                "message": "Lead marqué pour révision et réponse envoyée",
                "action_taken": "flag",
                "action_details": action.get("details", {}),
                "response_result": response_result if original_message else None
            }
            
        elif action_type == "continue_sequence":
            # Continuer la séquence normale
            self.speak("Poursuite de la séquence normale", target="ProspectionSupervisor")
            
            return {
                "status": "success",
                "message": "Réponse envoyée et séquence normale maintenue",
                "action_taken": "continue_sequence",
                "response_result": response_result if original_message else None
            }
            
        else:
            # Action non reconnue ou aucune action
            self.speak(f"Action non reconnue: {action_type}, mais réponse envoyée", target="AdminInterpreterAgent")
            
            return {
                "status": "warning",
                "message": f"Action non reconnue: {action_type}, mais réponse envoyée",
                "action_taken": "none",
                "response_result": response_result if original_message else None
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance de l'OverseerAgent
    overseer = OverseerAgent()
    
    # Affichage de l'état du système
    print(json.dumps(overseer.get_system_state(), indent=2))

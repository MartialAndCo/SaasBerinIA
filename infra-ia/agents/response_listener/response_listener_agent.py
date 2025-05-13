"""
Module du ResponseListenerAgent - Agent d'écoute des réponses entrantes
"""
import os
import json
import logging
import datetime
from typing import Dict, Any, Optional, List, Union

from core.agent_base import Agent
from utils.llm import LLMService
from utils.logger import get_logger

class ResponseListenerAgent(Agent):
    """
    ResponseListenerAgent - Agent responsable de l'écoute et du traitement initial des réponses
    
    Cet agent est responsable de:
    - Recevoir les notifications de réponses (emails, SMS)
    - Normaliser et structurer ces données
    - Extraire les métadonnées importantes (identifiants de campagne, etc.)
    - Transmettre les réponses structurées au ResponseInterpreterAgent
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du ResponseListenerAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("ResponseListenerAgent", config_path)
        
        # Configuration du logging
        self.logger = logging.getLogger("BerinIA-ResponseListener")
        
        # Statistiques de l'agent
        self.stats = {
            "emails_received": 0,
            "sms_received": 0,
            "processed_successfully": 0,
            "processing_errors": 0,
            "last_activity": None
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
        
        # Mise à jour des statistiques
        self.stats["last_activity"] = datetime.datetime.now().isoformat()
        
        # Traitement selon l'action demandée
        if action == "process_email_response":
            return self.process_email_response(input_data.get("data", {}))
        
        elif action == "process_sms_response":
            return self.process_sms_response(input_data.get("data", {}))
        
        elif action == "get_stats":
            return {
                "status": "success",
                "stats": self.stats
            }
        
        else:
            # Action non reconnue
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }
    
    def process_email_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une réponse d'email reçue via webhook
        
        Args:
            data: Données de la réponse email
            
        Returns:
            Résultat du traitement
        """
        self.speak(f"Réception d'une réponse par email de {data.get('sender')}", target="OverseerAgent")
        
        try:
            # Extraction des champs importants
            sender = data.get("sender", "")
            recipient = data.get("recipient", "")
            subject = data.get("subject", "")
            body = data.get("body", "")
            
            # Vérification des champs obligatoires
            if not sender or not body:
                error_message = "Champs obligatoires manquants (sender, body)"
                self.speak(error_message, target="OverseerAgent")
                
                self.stats["processing_errors"] += 1
                
                return {
                    "status": "error",
                    "message": error_message
                }
            
            # Extraction de l'identifiant de campagne depuis l'adresse email
            # Format attendu: campaign+ID@domain.com
            campaign_id = None
            
            if "+" in recipient:
                campaign_part = recipient.split("@")[0]
                if "+" in campaign_part:
                    campaign_id = campaign_part.split("+")[1]
            
            # Utilisation du LLM pour extraire des éléments clés si nécessaire
            # (pour des cas complexes où la structure n'est pas évidente)
            if self.config.get("use_llm_for_extraction", False) and LLMService:
                extraction_prompt = self.build_prompt({
                    "email_body": body,
                    "sender": sender,
                    "subject": subject
                })
                
                extracted_data_json = LLMService.call_llm(
                    extraction_prompt,
                    complexity="low"
                )
                
                try:
                    extracted_data = json.loads(extracted_data_json)
                except json.JSONDecodeError:
                    extracted_data = {}
            else:
                extracted_data = {}
            
            # Préparation des données pour le ResponseInterpreterAgent
            processed_data = {
                "source": "email",
                "sender": sender,
                "content": body,
                "campaign_id": campaign_id,
                "subject": subject,
                "received_at": data.get("timestamp", datetime.datetime.now().isoformat()),
                "extracted_data": extracted_data,
                "raw_data": data
            }
            
            # Transmission au ResponseInterpreterAgent
            self.transmit_to_interpreter(processed_data)
            
            # Mise à jour des statistiques
            self.stats["emails_received"] += 1
            self.stats["processed_successfully"] += 1
            
            return {
                "status": "success",
                "message": "Réponse email traitée",
                "data": processed_data
            }
            
        except Exception as e:
            error_message = f"Erreur lors du traitement de la réponse email: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            
            self.stats["emails_received"] += 1
            self.stats["processing_errors"] += 1
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def process_sms_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une réponse SMS reçue via webhook
        
        Args:
            data: Données de la réponse SMS
            
        Returns:
            Résultat du traitement
        """
        self.speak(f"Réception d'une réponse par SMS de {data.get('sender')}", target="OverseerAgent")
        
        try:
            # Extraction des champs importants
            sender = data.get("sender", "")
            recipient = data.get("recipient", "")
            body = data.get("body", "")
            
            # Vérification des champs obligatoires
            if not sender or not body:
                error_message = "Champs obligatoires manquants (sender, body)"
                self.speak(error_message, target="OverseerAgent")
                
                self.stats["processing_errors"] += 1
                
                return {
                    "status": "error",
                    "message": error_message
                }
            
            # Extraction de l'identifiant de campagne à partir du numéro de téléphone
            # ou d'un code dans le message si disponible
            campaign_id = None
            
            # Recherche d'un code de campagne dans le corps du message
            # Format attendu: #ID ou [ID] au début du message
            if body.startswith("#") or body.startswith("["):
                import re
                # Motif corrigé pour extraire correctement l'ID de campagne
                campaign_match = re.match(r'^#([a-zA-Z0-9_-]+)', body)
                if campaign_match:
                    campaign_id = campaign_match.group(1)
                else:
                    # Essai avec le format [ID]
                    campaign_match = re.match(r'^\[([a-zA-Z0-9_-]+)\]', body)
                    if campaign_match:
                        campaign_id = campaign_match.group(1)
            
            # Utilisation du LLM pour extraire des éléments clés si nécessaire
            if self.config.get("use_llm_for_extraction", False) and LLMService:
                extraction_prompt = self.build_prompt({
                    "sms_body": body,
                    "sender": sender
                })
                
                extracted_data_json = LLMService.call_llm(
                    extraction_prompt,
                    complexity="low"
                )
                
                try:
                    extracted_data = json.loads(extracted_data_json)
                except json.JSONDecodeError:
                    extracted_data = {}
            else:
                extracted_data = {}
            
            # Préparation des données pour le ResponseInterpreterAgent
            processed_data = {
                "source": "sms",
                "sender": sender,
                "content": body,
                "campaign_id": campaign_id,
                "received_at": data.get("timestamp", datetime.datetime.now().isoformat()),
                "extracted_data": extracted_data,
                "raw_data": data
            }
            
            # Transmission au ResponseInterpreterAgent
            self.transmit_to_interpreter(processed_data)
            
            # Mise à jour des statistiques
            self.stats["sms_received"] += 1
            self.stats["processed_successfully"] += 1
            
            return {
                "status": "success",
                "message": "Réponse SMS traitée",
                "data": processed_data
            }
            
        except Exception as e:
            error_message = f"Erreur lors du traitement de la réponse SMS: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            
            self.stats["sms_received"] += 1
            self.stats["processing_errors"] += 1
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def transmit_to_interpreter(self, processed_data: Dict[str, Any]) -> None:
        """
        Transmet les données traitées au ResponseInterpreterAgent
        
        Args:
            processed_data: Données à transmettre
        """
        # Import dynamique pour éviter les dépendances circulaires
        from agents.response_interpreter.response_interpreter_agent import ResponseInterpreterAgent
        
        try:
            # Création d'une instance de ResponseInterpreterAgent
            interpreter = ResponseInterpreterAgent()
            
            # Transmission des données
            result = interpreter.run({
                "action": "interpret_response",
                "data": processed_data
            })
            
            # Log du résultat
            status = result.get("status", "unknown")
            self.speak(
                f"Réponse transmise au ResponseInterpreterAgent - Résultat: {status}",
                target="OverseerAgent"
            )
            
        except Exception as e:
            error_message = f"Erreur lors de la transmission au ResponseInterpreterAgent: {str(e)}"
            self.speak(error_message, target="OverseerAgent")

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
from utils.qdrant import create_embedding, create_collection
from utils.api_clients.instantly_client import InstantlyClient
from core.db import DatabaseService

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
        
        # Initialisation du client Instantly.ai si nécessaire
        api_key = self.config.get("instantly_api_key") or os.getenv("INSTANTLY_API_KEY", "")
        if api_key:
            self.instantly_client = InstantlyClient(api_key=api_key)
            self.speak("Client Instantly.ai initialisé", target="OverseerAgent")
        else:
            self.instantly_client = None
        
        # Initialisation de la base de données
        self.db = DatabaseService()
        
        # Initialisation de la collection Qdrant pour les conversations
        try:
            create_collection("conversations", vector_size=1536)
            self.logger.info("Collection 'conversations' initialisée dans Qdrant")
        except Exception as e:
            self.logger.warning(f"Erreur lors de l'initialisation de la collection Qdrant: {str(e)}")
    
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
        # Vérifier si c'est un webhook Instantly.ai
        if "event_type" in data and self.instantly_client:
            return self._process_instantly_webhook(data)
        
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
            
            # Création de l'embedding pour le contenu du message
            try:
                message_embedding = create_embedding(body)
                self.speak(f"Embedding créé pour le message email", target="OverseerAgent")
            except Exception as e:
                self.speak(f"Erreur lors de la création de l'embedding: {str(e)}", target="OverseerAgent")
                message_embedding = None
            
            # Préparation des données pour le ResponseInterpreterAgent
            processed_data = {
                "source": "email",
                "sender": sender,
                "content": body,
                "campaign_id": campaign_id,
                "subject": subject,
                "received_at": data.get("timestamp", datetime.datetime.now().isoformat()),
                "extracted_data": extracted_data,
                "raw_data": data,
                "embedding": message_embedding
            }
            
            # Sauvegarde du message entrant en base de données
            try:
                lead_id = self._find_lead_by_email(sender)
                message_id = self._save_inbound_message_to_db(processed_data, lead_id, "email")
                processed_data["saved_message_id"] = message_id
                self.speak(f"Message email sauvegardé en base avec ID: {message_id}", target="OverseerAgent")
            except Exception as e:
                self.speak(f"Erreur lors de la sauvegarde du message: {str(e)}", target="OverseerAgent")
            
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
    
    def _process_instantly_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un webhook d'Instantly.ai
        
        Args:
            data: Données du webhook Instantly
            
        Returns:
            Résultat du traitement
        """
        self.speak(f"Réception d'un webhook Instantly.ai de type {data.get('event_type', 'inconnu')}", target="OverseerAgent")
        
        try:
            # Utiliser le client Instantly pour analyser le webhook
            webhook_data = self.instantly_client.parse_webhook(data)
            
            event_type = webhook_data.get("event_type", "unknown")
            lead_email = webhook_data.get("lead_email", "")
            campaign_id = webhook_data.get("campaign_id", "")
            timestamp = webhook_data.get("timestamp", datetime.datetime.now().isoformat())
            
            # Traiter différemment selon le type d'événement
            if event_type == "reply_received":
                # Récupérer le contenu de la réponse
                content = webhook_data.get("content", "")
                message_id = webhook_data.get("message_id", "")
                
                if not content:
                    self.speak("Webhook reply_received sans contenu", target="OverseerAgent")
                    self.stats["processing_errors"] += 1
                    return {
                        "status": "error",
                        "message": "Webhook reply_received sans contenu"
                    }
                
                # Création de l'embedding pour le contenu du message
                try:
                    message_embedding = create_embedding(content)
                    self.speak(f"Embedding créé pour la réponse Instantly", target="OverseerAgent")
                except Exception as e:
                    self.speak(f"Erreur lors de la création de l'embedding: {str(e)}", target="OverseerAgent")
                    message_embedding = None
                
                # Préparation des données pour le ResponseInterpreterAgent
                processed_data = {
                    "source": "email",
                    "sender": lead_email,
                    "content": content,
                    "campaign_id": campaign_id,
                    "message_id": message_id,  # Pour pouvoir répondre directement via Instantly
                    "received_at": timestamp,
                    "raw_data": webhook_data,
                    "embedding": message_embedding
                }
                
                # Transmission au ResponseInterpreterAgent
                self.transmit_to_interpreter(processed_data)
                
                # Mise à jour des statistiques
                self.stats["emails_received"] += 1
                self.stats["processed_successfully"] += 1
                
                return {
                    "status": "success",
                    "message": "Réponse email Instantly traitée",
                    "data": processed_data
                }
                
            elif event_type == "email_opened":
                # Enregistrer l'ouverture d'email mais pas d'action spécifique
                self.speak(f"Email ouvert par {lead_email} (campagne {campaign_id})", target="OverseerAgent")
                return {
                    "status": "success",
                    "message": "Événement d'ouverture d'email enregistré",
                    "event_type": event_type,
                    "lead_email": lead_email,
                    "campaign_id": campaign_id
                }
                
            elif event_type == "link_clicked":
                # Enregistrer le clic sur un lien
                link_url = data.get("link_url", "")
                self.speak(f"Lien cliqué par {lead_email}: {link_url}", target="OverseerAgent")
                return {
                    "status": "success",
                    "message": "Événement de clic sur lien enregistré",
                    "event_type": event_type,
                    "lead_email": lead_email,
                    "campaign_id": campaign_id,
                    "link_url": link_url
                }
                
            else:
                # Autres types d'événements
                self.speak(f"Événement Instantly.ai de type {event_type} reçu pour {lead_email}", target="OverseerAgent")
                return {
                    "status": "success",
                    "message": f"Événement Instantly.ai {event_type} enregistré",
                    "event_type": event_type,
                    "lead_email": lead_email,
                    "campaign_id": campaign_id
                }
                
        except Exception as e:
            error_message = f"Erreur lors du traitement du webhook Instantly: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            
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
            
            # Création de l'embedding pour le contenu du message
            try:
                message_embedding = create_embedding(body)
                self.speak(f"Embedding créé pour le message SMS", target="OverseerAgent")
            except Exception as e:
                self.speak(f"Erreur lors de la création de l'embedding: {str(e)}", target="OverseerAgent")
                message_embedding = None
            
            # Préparation des données pour le ResponseInterpreterAgent
            processed_data = {
                "source": "sms",
                "sender": sender,
                "content": body,
                "campaign_id": campaign_id,
                "received_at": data.get("timestamp", datetime.datetime.now().isoformat()),
                "extracted_data": extracted_data,
                "raw_data": data,
                "embedding": message_embedding
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
    
    def _find_lead_by_email(self, email: str) -> Optional[int]:
        """
        Trouve l'ID d'un lead par son email
        
        Args:
            email: Adresse email du lead
            
        Returns:
            ID du lead ou None si non trouvé
        """
        try:
            result = self.db.fetch_one(
                "SELECT id FROM leads WHERE email = :email",
                {"email": email}
            )
            return result["id"] if result else None
        except Exception as e:
            self.speak(f"Erreur lors de la recherche du lead: {str(e)}", target="OverseerAgent")
            return None
    
    def _save_inbound_message_to_db(self, processed_data: Dict[str, Any], lead_id: Optional[int], message_type: str) -> str:
        """
        Sauvegarde un message entrant en base de données
        
        Args:
            processed_data: Données du message traité
            lead_id: ID du lead expéditeur
            message_type: Type de message (email, sms)
            
        Returns:
            ID du message sauvegardé
        """
        import uuid
        
        message_id = str(uuid.uuid4())
        
        try:
            # Extraction des informations du lead depuis l'email ou le numéro
            sender = processed_data.get("sender", "")
            sender_name = sender.split("@")[0] if "@" in sender else sender
            
            # Préparation des données du message
            message_record = {
                "id": message_id,
                "lead_id": lead_id,
                "lead_name": sender_name,
                "lead_email": sender if "@" in sender else "",
                "subject": processed_data.get("subject", ""),
                "content": processed_data.get("content", ""),
                "status": "received",
                "campaign_id": processed_data.get("campaign_id"),
                "campaign_name": f"Campagne {processed_data.get('campaign_id', 'inconnue')}",
                "sent_date": None,  # Pas de date d'envoi pour les messages entrants
                "received_date": processed_data.get("received_at", datetime.datetime.now().isoformat()),
                "direction": "inbound",
                "sender_type": "lead",
                "thread_id": str(lead_id) if lead_id else sender,
                "message_type": message_type,
                "sender_name": sender_name,
                "message_id_external": processed_data.get("message_id", "")
            }
            
            # Insertion en base de données
            self.db.insert("messages", message_record)
            
            return message_id
            
        except Exception as e:
            self.speak(f"Erreur lors de la sauvegarde du message: {str(e)}", target="OverseerAgent")
            return message_id  # Retourner l'ID généré même en cas d'erreur
    
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

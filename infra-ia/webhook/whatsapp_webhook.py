#!/usr/bin/env python3
"""
Module de webhook pour l'intégration WhatsApp avec ConversationAgent Révolutionnaire.

Ce module gère la réception et le traitement des messages WhatsApp
via le webhook FastAPI en utilisant le nouveau ConversationAgent 100% IA.
"""
import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, Optional, Union

# Ajout du répertoire parent au path pour les imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import du système de logging unifié PostgreSQL
from utils.unified_logging import unified_logger

# Import direct du nouveau ConversationAgent révolutionnaire
from agents.conversation.conversation_agent import ConversationAgent

class WhatsAppWebhook:
    """
    Classe de gestion du webhook WhatsApp avec ConversationAgent Révolutionnaire
    """
    def __init__(self):
        """
        Initialise le gestionnaire de webhook WhatsApp
        """
        unified_logger.info("Initialisation du webhook WhatsApp avec ConversationAgent Révolutionnaire", "webhook.whatsapp")
        self.conversation_agent = None
        self.initialized = False
        
    async def initialize(self):
        """
        Initialise le ConversationAgent révolutionnaire pour le traitement des messages
        """
        if not self.initialized:
            unified_logger.info("Initialisation du ConversationAgent révolutionnaire pour le webhook WhatsApp", "webhook.whatsapp")
            try:
                # Création directe du nouveau ConversationAgent révolutionnaire
                self.conversation_agent = ConversationAgent()
                unified_logger.info("ConversationAgent révolutionnaire initialisé avec succès", "webhook.whatsapp")
                
                self.initialized = True
                unified_logger.info("Webhook WhatsApp initialisé avec ConversationAgent révolutionnaire 100% IA", "webhook.whatsapp")
                return True
                
            except Exception as e:
                unified_logger.error(f"Erreur lors de l'initialisation du webhook WhatsApp: {str(e)}", "webhook.whatsapp")
                import traceback
                unified_logger.error(traceback.format_exc(), "webhook.whatsapp")
                return False
        return True
    
    async def process_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un message WhatsApp reçu avec le ConversationAgent révolutionnaire

        Args:
            data: Message WhatsApp reçu

        Returns:
            Réponse à renvoyer
        """
        try:
            # S'assurer que le ConversationAgent est initialisé
            if not await self.initialize():
                unified_logger.error("Impossible de traiter le message: webhook non initialisé", "webhook.whatsapp")
                return {"error": "Webhook non initialisé", "debug": "Le ConversationAgent n'a pas pu être initialisé"}

            unified_logger.log("INFO", "webhook", f"Message WhatsApp reçu: {json.dumps(data)}", 
                             module="whatsapp", details={"raw_data": data})

            # Extraction des informations du message (support des deux formats)
            message_content = ""
            sender = ""
            source_info = ""

            # Format test (sender, profile_name, message.text)
            if "message" in data and isinstance(data["message"], dict):
                unified_logger.info(f"Extraction du message au format test: {json.dumps(data['message'])}", "webhook.whatsapp")
                message_content = data["message"].get("text", "")
                sender = data.get("sender", "")
                source_info = data.get("profile_name", "")

            # Format bot WhatsApp (author, content, group)
            elif "content" in data:
                message_content = data.get("content", "")
                sender = data.get("author", "")
                source_info = data.get("source", "WhatsApp")
                if "group" in data:
                    source_info = f"{data.get('group', '')} (WhatsApp)"

            if not message_content:
                unified_logger.warning("Message vide, impossible de traiter", "webhook.whatsapp")
                return {"error": "Message vide", "debug": f"Données reçues: {json.dumps(data)}"}

            if not sender:
                sender = "Utilisateur WhatsApp"

            unified_logger.log("INFO", "webhook", f"Message de '{source_info}' ({sender}): {message_content}",
                             module="whatsapp", details={
                                 "sender": sender,
                                 "source": source_info,
                                 "message": message_content,
                                 "group": data.get("group"),
                                 "messageId": data.get("messageId")
                             })

            # Vérifier que le ConversationAgent est disponible
            if not self.conversation_agent:
                unified_logger.error("ConversationAgent non disponible", "webhook.whatsapp")
                return {
                    "error": "ConversationAgent non disponible",
                    "response": "Désolé, le système n'est pas prêt pour traiter votre demande."
                }

            # Créer le contexte pour le ConversationAgent
            context = {
                "message": message_content,
                "source": "whatsapp",
                "author": sender,
                "group": data.get("group", "Direct Message"),
                "profile_name": source_info,
                "timestamp": data.get("timestamp"),
                "messageId": data.get("messageId"),
                "isVoiceMessage": data.get("isVoiceMessage", False)
            }

            # Traitement du message par le ConversationAgent révolutionnaire
            unified_logger.log("INFO", "webhook", f"Traitement du message par ConversationAgent révolutionnaire: '{message_content}'",
                             module="whatsapp", details={"context": context})

            try:
                # Le ConversationAgent révolutionnaire gère tout automatiquement
                result = self.conversation_agent.run(context)
                
                if not result:
                    raise ValueError("Aucun résultat reçu du ConversationAgent")
                
                # Extraction de la réponse
                if result.get("status") == "success":
                    response_message = result.get("message", "")
                    unified_logger.log("INFO", "webhook", f"Réponse du ConversationAgent: {response_message}",
                                     module="whatsapp", details={"response": response_message, "result": result})
                    return {"response": response_message}
                else:
                    # Gestion des erreurs
                    error_message = result.get("message", "Erreur inconnue")
                    unified_logger.error(f"Erreur du ConversationAgent: {error_message}", "webhook.whatsapp")
                    
                    # Réponse conviviale pour l'utilisateur
                    friendly_response = self.generate_friendly_error_response(error_message, message_content)
                    return {
                        "error": error_message,
                        "response": friendly_response
                    }
            
            except Exception as e:
                unified_logger.error(f"Erreur lors du traitement par ConversationAgent: {str(e)}", "webhook.whatsapp")
                import traceback
                stack_trace = traceback.format_exc()
                unified_logger.error(f"Stack trace: {stack_trace}", "webhook.whatsapp")
                
                # Générer une réponse d'erreur conviviale
                friendly_response = self.generate_friendly_error_response(str(e), message_content)
                
                return {
                    "error": f"Erreur de traitement: {str(e)}",
                    "debug": stack_trace,
                    "response": friendly_response
                }

        except Exception as e:
            unified_logger.error(f"Erreur lors du traitement du message: {str(e)}", "webhook.whatsapp")
            import traceback
            stack_trace = traceback.format_exc()
            unified_logger.error(stack_trace, "webhook.whatsapp")
            
            # Réponse d'erreur générique mais conviviale
            friendly_response = "Je suis désolé, je rencontre des difficultés techniques. Pourriez-vous réessayer dans quelques instants ?"
            
            return {
                "error": f"Erreur du webhook: {str(e)}",
                "debug": stack_trace,
                "response": friendly_response
            }
    
    def generate_friendly_error_response(self, error_message: str, original_message: str) -> str:
        """
        Génère une réponse d'erreur conviviale pour l'utilisateur
        """
        error_lower = error_message.lower()
        
        # Messages d'erreur spécifiques selon le type d'erreur
        if "no such table" in error_lower or "relation" in error_lower:
            return "Je ne trouve pas cette information dans ma base de données. Cette fonctionnalité n'est peut-être pas encore disponible."
            
        if "no access" in error_lower or "permission" in error_lower:
            return "Je n'ai pas l'autorisation d'accéder à cette information. Veuillez contacter un administrateur."
            
        if "timeout" in error_lower:
            return "La demande a pris trop de temps. Pourriez-vous réessayer ou simplifier votre question ?"
            
        if "agent" in error_lower and "non disponible" in error_lower:
            return "Une partie du système n'est pas disponible actuellement. Veuillez réessayer plus tard."
            
        # Message d'erreur générique mais convivial
        return "Je suis désolé, je n'ai pas pu traiter cette demande. Pourriez-vous reformuler votre question ou essayer une autre requête ?"

# Instance unique du webhook
webhook_handler = WhatsAppWebhook()

async def handle_whatsapp_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Point d'entrée pour le traitement des messages WhatsApp
    
    Args:
        data: Données du webhook
        
    Returns:
        Réponse à envoyer
    """
    unified_logger.log("INFO", "webhook", "Traitement d'une requête webhook WhatsApp avec ConversationAgent Révolutionnaire",
                      module="whatsapp", details={"data": data})
    return await webhook_handler.process_message(data)

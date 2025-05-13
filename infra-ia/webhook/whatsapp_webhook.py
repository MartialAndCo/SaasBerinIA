#!/usr/bin/env python3
"""
Module de webhook pour l'intégration WhatsApp.

Ce module gère la réception et le traitement des messages WhatsApp
via le webhook FastAPI.
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

# Import de la nouvelle configuration de logging
from utils.logging_config import get_logger

# Import des modules BerinIA
from webhook.webhook_config import get_webhook_agents
from utils.agent_definitions import WEBHOOK_REQUIRED_AGENTS

# Configuration du logger
logger = get_logger("webhook.whatsapp")

class WhatsAppWebhook:
    """
    Classe de gestion du webhook WhatsApp
    """
    def __init__(self):
        """
        Initialise le gestionnaire de webhook WhatsApp
        """
        logger.info("Initialisation du webhook WhatsApp")
        self.agents = {}
        self.initialized = False
        
    async def initialize(self):
        """
        Initialise les agents BerinIA pour le traitement des messages
        """
        if not self.initialized:
            logger.info("Initialisation des agents pour le webhook WhatsApp")
            try:
                # Récupération des agents depuis le registre
                self.agents = get_webhook_agents()
                
                if not self.agents:
                    logger.error("Aucun agent n'a pu être initialisé pour le webhook")
                    return False
                
                # Vérifier que tous les agents requis sont disponibles
                missing_agents = [name for name in WEBHOOK_REQUIRED_AGENTS if name not in self.agents]
                if missing_agents:
                    logger.error(f"Agents manquants: {', '.join(missing_agents)}")
                    return False
                
                self.initialized = True
                logger.info(f"Webhook WhatsApp initialisé avec {len(self.agents)} agents")
                return True
                
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du webhook WhatsApp: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return False
        return True
    
    async def format_response_with_meta_agent(self, raw_response: Union[str, Dict], context: Dict[str, Any], agent_used: str) -> str:
        """
        Utilise le MetaAgent pour formater la réponse de manière conversationnelle.
        
        Args:
            raw_response: Réponse brute de l'agent (string ou dict)
            context: Contexte original de la requête
            agent_used: Nom de l'agent qui a généré la réponse
            
        Returns:
            Réponse formatée de manière conversationnelle
        """
        if "MetaAgent" not in self.agents:
            logger.warning("MetaAgent non disponible pour formater la réponse")
            # Formater manuellement la réponse si possible
            if isinstance(raw_response, dict):
                if "result" in raw_response and "count" in raw_response["result"]:
                    count = raw_response["result"]["count"]
                    return f"Il y a actuellement {count} leads dans la base de données."
                elif "message" in raw_response:
                    return raw_response["message"]
                elif "response" in raw_response:
                    return raw_response["response"]
                elif "error" in raw_response:
                    return f"Désolé, une erreur est survenue : {raw_response['error']}"
                else:
                    return str(raw_response)
            return str(raw_response)
        
        # Préparer le message pour MetaAgent avec le contexte de formatage
        meta_agent = self.agents["MetaAgent"]
        original_message = context.get("message", "")
        
        # Convertir la réponse brute en string si c'est un dict
        raw_response_str = ""
        if isinstance(raw_response, dict):
            if "result" in raw_response:
                raw_response_str = str(raw_response["result"])
            elif "message" in raw_response:
                raw_response_str = raw_response["message"]
            elif "response" in raw_response:
                raw_response_str = raw_response["response"]
            elif "error" in raw_response:
                raw_response_str = f"Erreur: {raw_response['error']}"
            else:
                raw_response_str = json.dumps(raw_response)
        else:
            raw_response_str = str(raw_response)
        
        # Créer un contexte pour le formatage
        format_context = {
            "action": "format_response",
            "original_message": original_message,
            "raw_response": raw_response_str,
            "agent_used": agent_used,
            "message_type": "whatsapp",
            "format_context": context
        }
        
        try:
            # Appeler le MetaAgent pour formater la réponse
            format_result = meta_agent.run(format_context)
            
            if isinstance(format_result, dict):
                if "formatted_response" in format_result:
                    return format_result["formatted_response"]
                elif "message" in format_result:
                    return format_result["message"]
                elif "response" in format_result:
                    return format_result["response"]
                
            # Si on arrive ici, il n'y a pas de réponse formatée claire, utiliser une réponse par défaut
            logger.warning(f"Format de réponse non reconnu: {format_result}")
            return raw_response_str
            
        except Exception as e:
            logger.error(f"Erreur lors du formatage de la réponse: {str(e)}")
            return raw_response_str
    
    async def handle_error_intelligently(self, error: Exception, context: Dict[str, Any]) -> str:
        """
        Gère les erreurs de manière intelligente en générant une réponse utile.
        
        Args:
            error: L'exception qui s'est produite
            context: Le contexte de la requête
            
        Returns:
            Message d'erreur convivial
        """
        error_message = str(error)
        question = context.get("message", "")
        
        # Si MetaAgent est disponible, utiliser pour formater l'erreur
        if "MetaAgent" in self.agents:
            meta_agent = self.agents["MetaAgent"]
            error_context = {
                "action": "handle_error",
                "error_message": error_message,
                "original_question": question,
                "context": context
            }
            
            try:
                error_result = meta_agent.run(error_context)
                if isinstance(error_result, dict) and "response" in error_result:
                    return error_result["response"]
            except:
                pass
        
        # Messages d'erreur par défaut plus conviviaux selon le type d'erreur
        if "no such table" in error_message.lower() or "relation" in error_message.lower():
            return "Je ne trouve pas cette information dans ma base de données. Cette fonctionnalité n'est peut-être pas encore implémentée."
            
        if "no access" in error_message.lower() or "permission" in error_message.lower():
            return "Je n'ai pas l'autorisation d'accéder à cette information. Veuillez contacter un administrateur."
            
        if "timeout" in error_message.lower():
            return "La demande a pris trop de temps. Veuillez réessayer ou simplifier votre question."
            
        # Message d'erreur générique mais convivial
        return "Je suis désolé, je n'ai pas pu traiter cette demande. Pourriez-vous reformuler votre question ou essayer une autre requête?"
    
    async def process_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un message WhatsApp reçu

        Args:
            data: Message WhatsApp reçu

        Returns:
            Réponse à renvoyer
        """
        try:
            # S'assurer que les agents sont initialisés
            if not await self.initialize():
                logger.error("Impossible de traiter le message: webhook non initialisé")
                return {"error": "Webhook non initialisé", "debug": "Les agents n'ont pas pu être initialisés"}

            logger.info(f"Message WhatsApp reçu: {json.dumps(data)}")

            # Extraction des informations du message (support des deux formats)
            # Format 1: Structure utilisée par le test (sender, profile_name, message.text)
            # Format 2: Structure du bot WhatsApp (author, content)

            # Essayer d'extraire le contenu du message
            message_content = ""
            sender = ""
            profile_name = ""

            # Format test
            if "message" in data and isinstance(data["message"], dict):
                logger.info(f"Extraction du message au format test: {json.dumps(data['message'])}")
                message_content = data["message"].get("text", "")
                logger.info(f"Message extrait: '{message_content}'")
                sender = data.get("sender", "")
                profile_name = data.get("profile_name", "")

            # Format bot WhatsApp
            elif "content" in data:
                message_content = data.get("content", "")
                sender = data.get("author", "")
                profile_name = data.get("source", "WhatsApp")
                if "group" in data:
                    profile_name = f"{data.get('group', '')} (WhatsApp)"

            if not message_content or not sender:
                logger.warning("Message incomplet, impossible de traiter")
                logger.warning(f"Données reçues: {json.dumps(data)}")
                return {"error": "Message incomplet", "debug": f"Données reçues: {json.dumps(data)}"}

            logger.info(f"Message de '{profile_name}' ({sender}): {message_content}")

            # Vérifier que l'agent MetaAgent est disponible - C'est l'entrée principale pour tous les messages
            if "MetaAgent" not in self.agents:
                logger.error("Agent MetaAgent non disponible - impossible de traiter le message de manière intelligente")
                
                # Vérifier si on a au moins le MessagingAgent comme fallback
                if "MessagingAgent" not in self.agents:
                    logger.error("Agent MessagingAgent non disponible non plus")
                    return {
                        "error": "Agents requis non disponibles",
                        "debug": "Ni MetaAgent ni MessagingAgent ne sont disponibles"
                    }
                
                # Fallback vers MessagingAgent si MetaAgent n'est pas disponible
                logger.warning("Utilisation du MessagingAgent comme fallback")
                agent_key = "MessagingAgent"
            else:
                # Utiliser le MetaAgent comme entrée principale
                agent_key = "MetaAgent"

            # Récupération de l'agent
            agent = self.agents[agent_key]

            # Création d'un contexte pour l'agent
            context = {
                "sender": sender,
                "recipient": "BerinIA",
                "message": message_content,
                "content": message_content,  # Pour compatibilité avec tous les agents
                "profile_name": profile_name,
                "message_type": "whatsapp",
                "source": "whatsapp",
                "group": data.get("group", "Direct Message"),
                "author": sender
            }

            # Traitement du message par l'agent
            logger.info(f"Traitement du message par {agent_key}: '{message_content}'")

            try:
                # Traitement MetaAgent vers les autres agents
                if agent_key == "MetaAgent":
                    # MetaAgent doit recevoir le message au format compatible
                    meta_context = {
                        "message": message_content,
                        "content": message_content,
                        **context
                    }
                    
                    # Le MetaAgent va gérer la requête et déterminer quel agent utiliser
                    result = agent.run(meta_context)
                    
                    if not result:
                        raise ValueError(f"Aucun résultat reçu de {agent_key}")
                    
                    # Récupérer la réponse brute
                    raw_response = None
                    if "message" in result:
                        raw_response = result["message"]
                    elif "response" in result:
                        raw_response = result["response"]
                    elif "result" in result:
                        raw_response = result["result"]
                    else:
                        raw_response = str(result)
                    
                    logger.info(f"Réponse brute du MetaAgent: {raw_response}")
                    
                    # Formater la réponse pour qu'elle soit conversationnelle
                    response = await self.format_response_with_meta_agent(raw_response, meta_context, "MetaAgent")
                    logger.info(f"Réponse formatée: {response}")
                    
                    return {"response": response}
                
                # Cas spécial pour les requêtes de base de données
                elif (agent_key == "DatabaseQueryAgent" or 
                      agent.__class__.__name__ == "DatabaseQueryAgent" or
                      "database_query" in agent.__class__.__module__.lower() if hasattr(agent.__class__, "__module__") else False):
                    
                    # Créer un contexte explicite pour DatabaseQueryAgent
                    query_context = {
                        "message": message_content,
                        "question": message_content,
                        "direct_query": True,
                        **context
                    }
                    
                    # Déterminer si c'est une question spécifique
                    if "combien" in message_content.lower() and "leads" in message_content.lower():
                        if "contacté" in message_content.lower():
                            query_context["action"] = "count_contacted_leads"
                        else:
                            query_context["action"] = "count_leads"
                    
                    logger.info(f"Appel du DatabaseQueryAgent avec contexte: {json.dumps(query_context)}")
                    
                    # Exécuter la requête
                    result = agent.run(query_context)
                    logger.info(f"Résultat brut du DatabaseQueryAgent: {json.dumps(result) if isinstance(result, dict) else str(result)}")
                    
                    # Formater la réponse pour qu'elle soit conversationnelle
                    response = await self.format_response_with_meta_agent(result, query_context, "DatabaseQueryAgent")
                    logger.info(f"Réponse formatée: {response}")
                    
                    return {"response": response}
                
                # Pour les autres agents
                else:
                    # Utiliser la méthode appropriée si elle existe
                    if hasattr(agent, 'process_incoming'):
                        result = agent.process_incoming(message_content, context)
                    else:
                        result = agent.run(context)
                    
                    logger.info(f"Résultat brut de {agent_key}: {json.dumps(result) if isinstance(result, dict) else str(result)}")
                    
                    # Formater la réponse
                    response = await self.format_response_with_meta_agent(result, context, agent_key)
                    logger.info(f"Réponse formatée: {response}")
                    
                    return {"response": response}
            
            except Exception as e:
                logger.error(f"Erreur lors du traitement par l'agent {agent_key}: {str(e)}")
                import traceback
                stack_trace = traceback.format_exc()
                logger.error(f"Stack trace: {stack_trace}")
                
                # Générer une réponse d'erreur intelligente
                friendly_error = await self.handle_error_intelligently(e, context)
                logger.info(f"Réponse d'erreur conviviale: {friendly_error}")
                
                return {
                    "error": f"Erreur de traitement: {str(e)}",
                    "debug": stack_trace,
                    "response": friendly_error
                }

            logger.info(f"Réponse générée: {response}")
            return {"response": response}

        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {str(e)}")
            import traceback
            stack_trace = traceback.format_exc()
            logger.error(stack_trace)
            
            # Générer une réponse d'erreur intelligente
            friendly_error = await self.handle_error_intelligently(e, {"message": message_content})
            
            return {
                "error": f"Erreur du webhook: {str(e)}",
                "debug": stack_trace,
                "response": friendly_error
            }

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
    logger.info("Traitement d'une requête webhook WhatsApp")
    return await webhook_handler.process_message(data)

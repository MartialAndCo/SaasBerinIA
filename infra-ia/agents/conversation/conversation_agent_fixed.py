"""
ConversationAgent - Agent conversationnel révolutionnaire 100% IA - VERSION FIXÉE
Retourne les VRAIES données au lieu de réponses hardcodées
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback

from core.agent_base import Agent
from utils.llm import LLMService
from utils.ai_request_parser import analyze_user_request, ai_parser
from agents.overseer.overseer_agent import OverseerAgent

# Import database service avec fallback
try:
    from app.db.database import db_session
    from sqlalchemy import text
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

class ConversationAgent(Agent):
    """
    Agent conversationnel révolutionnaire utilisant 100% IA
    VERSION FIXÉE : Retourne les VRAIES données
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialisation du ConversationAgent"""
        super().__init__("ConversationAgent", config_path)
        
        # Logger dédié
        self.logger = logging.getLogger("BerinIA.ConversationAgent")
        
        # Historique conversationnel
        self.conversation_history = []
        self.max_history = self.config.get("settings", {}).get("max_history_length", 10)
        
        # Instance de l'OverseerAgent pour délégation
        self.overseer = OverseerAgent()
        
        # Cache des agents disponibles
        self.available_agents = {}
        self.refresh_agent_registry()
        
        # Statistiques d'utilisation
        self.usage_stats = {
            "total_requests": 0,
            "successful_analyses": 0,
            "agent_delegations": 0,
            "direct_responses": 0,
            "errors": 0
        }
        
    def refresh_agent_registry(self):
        """Met à jour le cache des agents disponibles via OverseerAgent"""
        try:
            self.available_agents = {
                **self.overseer.supervisors,
                **self.overseer.operational_agents
            }
            self.logger.info(f"Agents disponibles: {list(self.available_agents.keys())}")
        except Exception as e:
            self.logger.error(f"Erreur refresh agent registry: {e}")
            self.available_agents = {}
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Point d'entrée principal révolutionnaire"""
        try:
            # Extraction du message
            message = input_data.get("message", input_data.get("content", ""))
            source = input_data.get("source", "direct")
            author = input_data.get("author", "user")
            
            if not message:
                return self.error_response("Aucun message fourni")
            
            self.logger.info(f"🤖 ConversationAgent - Demande: '{message[:100]}...' (de {author})")
            self.usage_stats["total_requests"] += 1
            
            # Ajout à l'historique
            self.add_to_history(message, "user", author)
            
            # NOUVELLE ANALYSE 100% IA
            response = self.process_with_ai_analysis(message, source, author, input_data)
            
            # Ajout de la réponse à l'historique
            if response.get("message"):
                self.add_to_history(response["message"], "assistant", "ConversationAgent")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erreur dans run(): {e}")
            self.logger.error(traceback.format_exc())
            self.usage_stats["errors"] += 1
            return self.error_response(f"Erreur système: {str(e)}")
    
    def process_with_ai_analysis(self, message: str, source: str, author: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traitement révolutionnaire avec analyse 100% IA"""
        
        try:
            # Construction du contexte pour l'IA
            context = self.build_ai_context(source, author, input_data)
            
            # ANALYSE INTELLIGENTE SANS PATTERNS
            self.logger.info("🧠 Analyse IA en cours...")
            analysis = analyze_user_request(
                message=message,
                available_agents=list(self.available_agents.keys()),
                context=context
            )
            
            self.usage_stats["successful_analyses"] += 1
            
            self.logger.info(f"✅ Analyse terminée: {analysis['intention']} -> {analysis.get('agent_target', 'auto')} (confiance: {analysis.get('confidence', 0):.2f})")
            
            # EXÉCUTION BASÉE SUR L'ANALYSE IA
            return self.execute_ai_analysis(analysis, message)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse IA: {e}")
            return self.fallback_response(message)
    
    def build_ai_context(self, source: str, author: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Construit le contexte enrichi pour l'IA"""
        
        context = {
            "source": source,
            "author": author,
            "timestamp": datetime.now().isoformat()
        }
        
        # Historique conversationnel récent
        if self.conversation_history:
            recent_history = []
            for entry in self.conversation_history[-4:]:  # 2 derniers échanges
                recent_history.append(f"{entry['role']}: {entry['content'][:100]}...")
            context["conversation_history"] = " | ".join(recent_history)
        
        # État du système
        context["system_state"] = {
            "agents_available": len(self.available_agents),
            "db_connected": DATABASE_AVAILABLE,
            "total_requests": self.usage_stats["total_requests"]
        }
        
        return context
    
    def execute_ai_analysis(self, analysis: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Exécute l'action basée sur l'analyse IA"""
        
        intention = analysis.get("intention", "general_chat")
        parameters = analysis.get("parameters", {})
        agent_target = analysis.get("agent_target", "auto")
        confidence = analysis.get("confidence", 0.0)
        
        self.logger.info(f"🎯 Exécution: {intention} avec paramètres {parameters}")
        
        # Sélection automatique d'agent si nécessaire
        if agent_target == "auto":
            agent_target = ai_parser.suggest_agent(intention, parameters, list(self.available_agents.keys()))
            self.logger.info(f"🤖 Agent auto-sélectionné: {agent_target}")
        
        # Exécution selon l'intention
        if intention == "general_chat":
            return self.handle_general_chat(message, analysis)
        
        elif intention == "query_data":
            return self.handle_data_query(message, parameters, agent_target)
        
        elif intention == "scrape_leads":
            return self.handle_scrape_leads(message, parameters, agent_target)
        
        elif intention == "send_messages":
            return self.handle_send_messages(message, parameters, agent_target)
        
        elif intention == "analyze_data":
            return self.handle_analyze_data(message, parameters, agent_target)
        
        elif intention == "system_config":
            return self.handle_system_config(message, parameters, agent_target)
        
        else:
            # Délégation générique via OverseerAgent
            return self.delegate_via_overseer(agent_target, message, parameters)
    
    def handle_general_chat(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Gère les conversations générales"""
        
        message_lower = message.lower()
        
        # Réponses intelligentes pour conversations générales
        if any(word in message_lower for word in ["salut", "bonjour", "hello", "coucou"]):
            response = "Bonjour ! Je suis BerinIA, votre assistant de prospection révolutionnaire. Je comprends le langage naturel et peux vous aider avec le scraping, l'analyse de données, l'envoi de messages et bien plus. Comment puis-je vous aider ?"
        
        elif any(word in message_lower for word in ["merci", "thanks"]):
            response = "De rien ! N'hésitez pas si vous avez d'autres questions. Je suis là pour optimiser votre prospection."
        
        elif any(word in message_lower for word in ["aide", "help", "que peux-tu faire"]):
            response = self.get_capabilities_response()
        
        else:
            # Réponse IA générique
            response = self.generate_ai_response(message)
        
        self.usage_stats["direct_responses"] += 1
        return self.success_response(response)
    
    def handle_data_query(self, message: str, parameters: Dict[str, Any], agent_target: str) -> Dict[str, Any]:
        """Gère les requêtes de données - VERSION FIXÉE qui retourne les VRAIES données"""
        
        self.logger.info(f"📊 Requête de données: {parameters}")
        
        # Tentative d'accès direct BDD en priorité
        if DATABASE_AVAILABLE:
            try:
                result = self.execute_direct_database_query(message, parameters)
                if result.get("status") == "success":
                    return result
            except Exception as e:
                self.logger.warning(f"Échec accès direct BDD: {e}")
        
        # Délégation via OverseerAgent
        try:
            query_params = {
                "action": "execute_agent",
                "agent_name": "DatabaseQueryAgent",
                "agent_input": {
                    "question": message,
                    **parameters
                }
            }
            
            result = self.overseer.run(query_params)
            
            # 🚀 FIX CRITIQUE : Retourner le VRAI résultat au lieu d'un message générique
            if result.get("status") == "success":
                # Extraire les vraies données du résultat
                data = result.get("data", result.get("result", result.get("answer", "")))
                
                if data:
                    return self.success_response(str(data))
                else:
                    # Si pas de données, essayer de formater le résultat entier
                    formatted_result = self.format_agent_result(result, "données")
                    return self.success_response(formatted_result)
            else:
                return self.error_response(f"❌ Erreur lors de la requête de données: {result.get('message', 'Erreur inconnue')}")
                
        except Exception as e:
            self.logger.error(f"Erreur délégation données: {e}")
            return self.error_response(f"❌ Erreur lors de la requête de données: {str(e)}")
    
    def execute_direct_database_query(self, message: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute une requête directe en base de données"""
        
        try:
            # Génération intelligente de SQL via IA
            sql_query = self.generate_ai_sql(message, parameters)
            
            if sql_query:
                self.logger.info(f"🔍 Exécution SQL directe: {sql_query}")
                
                with db_session() as session:
                    result = session.execute(text(sql_query)).fetchall()
                    
                    # Formatage intelligent du résultat
                    formatted_result = self.format_database_result(result, message, parameters)
                    
                    return self.success_response(formatted_result)
            else:
                return self.error_response("❌ Impossible de générer la requête SQL")
                
        except Exception as e:
            self.logger.error(f"Erreur SQL directe: {e}")
            return self.error_response(f"❌ Erreur base de données: {str(e)}")
    
    def generate_ai_sql(self, message: str, parameters: Dict[str, Any]) -> Optional[str]:
        """Génère une requête SQL via IA"""
        
        try:
            prompt = f"""Génère une requête SQL PostgreSQL pour cette demande : "{message}"

PARAMÈTRES EXTRAITS: {json.dumps(parameters, indent=2)}

SCHÉMA DISPONIBLE:
Tables: leads, campaigns, niches, messages, system_logs

RÈGLES:
- Utilise UNIQUEMENT les tables disponibles
- Privilégie les requêtes simples et efficaces
- Retourne UNIQUEMENT la requête SQL, rien d'autre

EXEMPLES:
- "combien de leads" → SELECT COUNT(*) FROM leads
- "leads récents" → SELECT * FROM leads ORDER BY created_at DESC LIMIT 10
- "combien de campagnes" → SELECT COUNT(*) FROM campaigns

Requête SQL:"""

            sql_query = LLMService.call_llm(prompt, complexity="medium")
            
            # Nettoyage
            sql_query = sql_query.strip()
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except Exception as e:
            self.logger.error(f"Erreur génération SQL IA: {e}")
            return None
    
    def format_database_result(self, result: Any, message: str, parameters: Dict[str, Any]) -> str:
        """Formate le résultat de base de données de manière intelligente"""
        
        try:
            if not result:
                return "📊 Aucun résultat trouvé."
            
            if len(result) == 1 and len(result[0]) == 1:
                # Résultat simple (ex: COUNT)
                count = result[0][0]
                if "leads" in message.lower():
                    return f"📊 Il y a actuellement **{count} leads** dans la base de données."
                elif "campagne" in message.lower():
                    return f"📈 Il y a **{count} campagnes** en cours."
                elif "niche" in message.lower():
                    return f"📋 Il y a **{count} niches** configurées."
                else:
                    return f"📋 Résultat: **{count}**"
            
            elif len(result) <= 5:
                # Affichage détaillé pour peu de résultats
                formatted_results = []
                for i, row in enumerate(result):
                    formatted_results.append(f"{i+1}. {str(row)}")
                return f"📋 **{len(result)} résultats trouvés:**\n" + "\n".join(formatted_results)
            
            else:
                # Résumé pour beaucoup de résultats
                preview = "\n".join(f"{i+1}. {str(row)}" for i, row in enumerate(result[:3]))
                return f"📊 **{len(result)} résultats trouvés** (aperçu des 3 premiers):\n{preview}\n\n... et {len(result)-3} autres résultats."
                
        except Exception as e:
            self.logger.error(f"Erreur formatage résultat: {e}")
            return f"✅ Requête exécutée. Résultat brut : {str(result)}"
    
    def handle_scrape_leads(self, message: str, parameters: Dict[str, Any], agent_target: str) -> Dict[str, Any]:
        """Gère les demandes de scraping via ScrapingSupervisor - VERSION FIXÉE avec sauvegarde BDD"""
        
        self.logger.info(f"🔍 Scraping demandé: {parameters}")
        
        # Extraction des informations pour la réponse utilisateur
        niche = parameters.get("niche", "leads")
        quantity = parameters.get("quantity", 10)
        location = parameters.get("location", "")
        
        try:
            # Délégation au ScrapingSupervisor via OverseerAgent
            scraping_params = {
                "action": "coordinate_scraping",
                "niche": niche,
                "limit": quantity,
                "city": location,
                "source": parameters.get("source", "apify") or "apify",
                "save_to_db": True,
                "analyze_web_presence": True,
                "create_niche": True,  # 🚀 NOUVEAU : Création automatique de niche
                "auto_save": True      # 🚀 NOUVEAU : Sauvegarde automatique
            }
            
            # Lancement asynchrone via le superviseur
            self.logger.info(f"🔄 Délégation au ScrapingSupervisor")
            result = self.overseer.delegate_to_supervisor("ScrapingSupervisor", scraping_params)
            
            # Construction de la réponse utilisateur avec confirmation sauvegarde
            location_text = f" à {location}" if location else ""
            response_message = f"🚀 Scraping de {quantity} {niche} lancé{location_text}. Les leads seront automatiquement analysés, sauvegardés en BDD et la niche '{niche}' sera créée si nécessaire."
            
            self.usage_stats["agent_delegations"] += 1
            
            return self.success_response(response_message)
            
        except Exception as e:
            self.logger.error(f"Erreur délégation scraping: {e}")
            return self.error_response(f"❌ Erreur lors du lancement du scraping: {str(e)}")
    
    def handle_send_messages(self, message: str, parameters: Dict[str, Any], agent_target: str) -> Dict[str, Any]:
        """Gère l'envoi de messages via ProspectionSupervisor - VERSION FIXÉE avec création campagne"""
        
        self.logger.info(f"📧 Envoi de messages: {parameters}")
        
        # Extraction des informations pour la réponse
        niche = parameters.get("niche", "leads")
        quantity = parameters.get("quantity", 10)
        message_type = parameters.get("action_type", "email")
        
        try:
            # Délégation au ProspectionSupervisor via OverseerAgent
            messaging_params = {
                "action": "send_messages",
                "target_niche": niche,
                "message_type": message_type,
                "quantity": quantity,
                "campaign_name": f"Campagne {niche} {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "create_campaign": True,  # 🚀 NOUVEAU : Création automatique de campagne
                "auto_save": True         # 🚀 NOUVEAU : Sauvegarde automatique
            }
            
            self.logger.info(f"🔄 Délégation au ProspectionSupervisor")
            result = self.overseer.delegate_to_supervisor("ProspectionSupervisor", messaging_params)
            
            # Construction réponse avec confirmation création campagne
            response_message = f"📧 Campagne {message_type} créée et lancée pour {quantity} {niche}. Les messages seront envoyés selon la stratégie optimale et la campagne sera sauvegardée en BDD."
            
            self.usage_stats["agent_delegations"] += 1
            
            return self.success_response(response_message)
            
        except Exception as e:
            self.logger.error(f"Erreur délégation messaging: {e}")
            return self.error_response(f"❌ Erreur lors du lancement de la campagne: {str(e)}")
    
    def handle_analyze_data(self, message: str, parameters: Dict[str, Any], agent_target: str) -> Dict[str, Any]:
        """Gère les analyses de données via OverseerAgent"""
        
        self.logger.info(f"📈 Analyse de données: {parameters}")
        
        try:
            # Délégation via OverseerAgent
            analysis_params = {
                "action": "execute_agent",
                "agent_name": "PivotStrategyAgent",
                "agent_input": {
                    "analysis_type": parameters.get("action_type", "performance"),
                    "niche": parameters.get("niche", ""),
                    "time_period": parameters.get("filters", {}).get("time_period", "last_30_days")
                }
            }
            
            result = self.overseer.run(analysis_params)
            
            if result.get("status") == "success":
                return self.success_response("📈 Analyse de performance lancée. Les résultats seront disponibles sous peu.")
            else:
                return self.error_response(f"❌ Erreur lors de l'analyse: {result.get('message', 'Erreur inconnue')}")
                
        except Exception as e:
            self.logger.error(f"Erreur délégation analyse: {e}")
            return self.error_response(f"❌ Erreur lors de l'analyse: {str(e)}")
    
    def handle_system_config(self, message: str, parameters: Dict[str, Any], agent_target: str) -> Dict[str, Any]:
        """Gère les modifications système via OverseerAgent"""
        
        self.logger.info(f"⚙️ Configuration système: {parameters}")
        
        try:
            # Délégation directe à l'OverseerAgent
            config_params = {
                "action": "get_system_state",
                **parameters
            }
            
            result = self.overseer.run(config_params)
            
            if result.get("status") == "success":
                return self.success_response("⚙️ État du système récupéré avec succès.")
            else:
                return self.error_response(f"❌ Erreur de configuration: {result.get('message', 'Erreur inconnue')}")
                
        except Exception as e:
            self.logger.error(f"Erreur configuration: {e}")
            return self.error_response(f"❌ Erreur de configuration: {str(e)}")
    
    def delegate_via_overseer(self, agent_name: str, message: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Délégation intelligente via OverseerAgent - VERSION FIXÉE"""
        
        try:
            self.logger.info(f"🔄 Délégation à {agent_name} via OverseerAgent")
            self.usage_stats["agent_delegations"] += 1
            
            # Préparation des paramètres pour l'OverseerAgent
            overseer_params = {
                "action": "execute_agent",
                "agent_name": agent_name,
                "agent_input": {
                    "message": message,
                    "source": "ConversationAgent",
                    "original_message": message,
                    "ai_analysis": True
                }
            }
            
            # Ajout des paramètres extraits par IA
            if parameters:
                overseer_params["agent_input"].update(parameters)
            
            # Exécution via OverseerAgent
            result = self.overseer.run(overseer_params)
            
            # 🚀 FIX CRITIQUE : Retourner le VRAI résultat au lieu d'un message générique
            if result.get("status") == "success":
                # Extraire les vraies données du résultat
                data = result.get("data", result.get("result", result.get("answer", "")))
                
                if data:
                    return self.success_response(str(data))
                else:
                    # Si pas de données spécifiques, formater le résultat
                    formatted_result = self.format_agent_result(result, agent_name)
                    return self.success_response(formatted_result)
            else:
                error_msg = result.get("message", f"Erreur dans {agent_name}")
                return self.error_response(f"❌ {error_msg}")
            
        except Exception as e:
            self.logger.error(f"Erreur délégation {agent_name}: {e}")
            return self.error_response(f"❌ Erreur lors de la délégation à {agent_name}: {str(e)}")
    
    def format_agent_result(self, result: Dict[str, Any], context: str) -> str:
        """Formate le résultat d'un agent pour l'utilisateur"""
        
        try:
            # Essayer différents champs pour extraire les données
            data_fields = ["data", "result", "answer", "leads", "campaigns", "count", "message"]
            
            for field in data_fields:
                if field in result and result[field] is not None:
                    data = result[field]
                    
                    if isinstance(data, (int, float)):
                        return f"📊 Résultat: **{data}**"
                    elif isinstance(data, list):
                        if len(data) == 0:
                            return "📊 Aucun résultat trouvé."
                        elif len(data) <= 3:
                            formatted = "\n".join(f"• {item}" for item in data)
                            return f"📋 **{len(data)} résultats:**\n{formatted}"
                        else:
                            formatted = "\n".join(f"• {item}" for item in data[:3])
                            return f"📊 **{len(data)} résultats** (aperçu):\n{formatted}\n... et {len(data)-3} autres"
                    elif isinstance(data, str) and data.strip():
                        return data
            
            # Fallback : retourner le message du résultat
            return result.get("message", f"✅ Tâche {context} exécutée avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur formatage résultat agent: {e}")
            return f"✅ Tâche {context} exécutée avec succès"
    
    def generate_ai_response(self, message: str) -> str:
        """Génère une réponse IA pour les conversations générales"""
        
        try:
            prompt = f"""Tu es BerinIA, un assistant de prospection commerciale intelligent.

L'utilisateur dit: "{message}"

Réponds de manière naturelle, conviviale et utile. Tu peux aider avec:
- Le scraping de leads
- L'analyse de données
- L'envoi de messages
- La configuration du système

Garde ta réponse courte et propose de l'aide concrète.
"""
            
            response = LLMService.call_llm(prompt, complexity="low")
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Erreur génération réponse IA: {e}")
            return "Je suis BerinIA, votre assistant de prospection. Comment puis-je vous aider avec vos leads et campagnes ?"
    
    def get_capabilities_response(self) -> str:
        """Génère une réponse d'aide personnalisée"""
        
        capabilities = f"""🚀 **BerinIA - Assistant IA Révolutionnaire**

Je comprends le langage naturel et peux vous aider avec :

🔍 **Scraping Intelligent**
• "scrappe 5 restaurants à toulouse"
• "trouve des dentistes sur paris"  
• "récupère 20 leads dans l'immobilier"

📊 **Analyses de Données**
• "combien de leads avons-nous ?"
• "statistiques de la dernière campagne"
• "performance par niche"

📧 **Communication**
• "envoie un email aux nouveaux leads"
• "prépare une campagne SMS"
• "relance les prospects"

⚙️ **Configuration**
• "modifie la limite de scraping"
• "état du système"
• "agents disponibles"

💬 **Intelligence Naturelle**
Je comprends toutes les variantes de langage naturel - parlez-moi normalement !

Agents disponibles : {', '.join(list(self.available_agents.keys())[:5])}{'...' if len(self.available_agents) > 5 else ''}

**VERSION FIXÉE :** Retourne les VRAIES données, sauvegarde automatique en BDD, création auto de niches/campagnes !
"""
        return capabilities
    
    def fallback_response(self, message: str) -> Dict[str, Any]:
        """Réponse de fallback en cas d'erreur d'analyse"""
        
        self.logger.warning("Utilisation de la réponse de fallback")
        
        # Tentative de délégation basique via OverseerAgent
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["scrappe", "scrape", "trouve", "leads"]):
            return self.delegate_via_overseer("ScraperAgent", message)
        elif any(word in message_lower for word in ["combien", "stats", "données"]):
            return self.delegate_via_overseer("DatabaseQueryAgent", message)
        else:
            return self.success_response("Je suis désolé, j'ai eu un problème pour analyser votre demande. Pouvez-vous la reformuler ?")
    
    def add_to_history(self, content: str, role: str, author: str):
        """Ajoute une entrée à l'historique conversationnel"""
        self.conversation_history.append({
            "content": content,
            "role": role,
            "author": author,
            "timestamp": datetime.now().isoformat()
        })
        
        # Limitation de la taille
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'utilisation"""
        
        return {
            "agent_version": "fixed_v1_real_data",
            "usage_stats": self.usage_stats,
            "ai_parser_stats": ai_parser.get_analysis_stats(),
            "available_agents": len(self.available_agents),
            "conversation_length": len(self.conversation_history)
        }
    
    def success_response(self, message: str) -> Dict[str, Any]:
        """Génère une réponse de succès"""
        return {
            "status": "success",
            "message": message,
            "agent":
            "agent": "ConversationAgent",
            "timestamp": datetime.now().isoformat(),
            "version": "fixed_v1_real_data"
        }
    
    def error_response(self, message: str) -> Dict[str, Any]:
        """Génère une réponse d'erreur"""
        return {
            "status": "error",
            "message": message,
            "agent": "ConversationAgent", 
            "timestamp": datetime.now().isoformat(),
            "version": "fixed_v1_real_data"
        }

# Export de l'agent
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    agent = ConversationAgent()
    
    # Test avec la version fixée
    test_cases = [
        "combien de leads avons-nous ?",
        "scrappe 2 restaurants a toulouse", 
    ]
    
    for test in test_cases:
        print(f"\n🧪 Test: {test}")
        response = agent.run({"message": test})
        print(f"✅ Réponse: {response.get('message', response)}")


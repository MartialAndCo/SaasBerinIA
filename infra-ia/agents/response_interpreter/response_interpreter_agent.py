"""
Module du ResponseInterpreterAgent - Agent d'interprétation des réponses
"""
import os
import json
from typing import Dict, Any, Optional, List, Tuple
import datetime
import re
import urllib.parse

from core.agent_base import Agent
from utils.llm import LLMService
from core.db import DatabaseService
from agents.response_interpreter.lead_manager import LeadManager

class ResponseInterpreterAgent(Agent):
    """
    ResponseInterpreterAgent - Agent responsable de l'analyse des réponses reçues
    
    Cet agent est responsable de:
    - Lire les réponses aux emails ou SMS
    - Analyser leur ton et leur contenu
    - Déterminer le sentiment (positif, neutre, négatif)
    - Recommander les actions à entreprendre
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du ResponseInterpreterAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("ResponseInterpreterAgent", config_path)
        
        # État de l'agent
        self.analysis_stats = {
            "total_analyzed": 0,
            "positive_responses": 0,
            "neutral_responses": 0,
            "negative_responses": 0,
            "unclear_responses": 0
        }
        
        # Initialisation de la connexion à la base de données
        self.db = DatabaseService()
        
        # Initialisation du gestionnaire de leads
        self.lead_manager = LeadManager()
        
        # Chargement des règles d'analyse
        self.analysis_rules = self.config.get("analysis_rules", {})
        
        # Chargement des schémas de classification
        self.classification_schema = self.config.get("classification_schema", {})
        
        # Initialisation des modèles spécifiques
        self._init_models()
    
    def _init_models(self):
        """
        Initialise les modèles d'analyse des réponses
        """
        # Chargement des expressions régulières pré-définies si configurées
        self.regex_patterns = self.config.get("regex_patterns", {})
        
        # Chargement des listes de mots-clés
        self.keyword_lists = self.config.get("keyword_lists", {})
    
    def interpret(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interprète une réponse reçue d'un lead
        
        Args:
            input_data: Données d'entrée avec la réponse à analyser
            
        Returns:
            Résultat de l'interprétation
        """
        # Extraction des données nécessaires
        response_data = input_data.get("response_data", {})
        campaign_id = input_data.get("campaign_id", "")
        
        if not response_data:
            return {
                "status": "error",
                "message": "Données de réponse manquantes"
            }
        
        # Extraction du contenu et du contexte de la réponse
        content = response_data.get("content", "")
        sender = response_data.get("sender", "")
        response_type = response_data.get("type", "email")  # email ou sms
        lead_id = response_data.get("lead_id", "")
        conversation_history = input_data.get("conversation_history", [])
        
        if not content:
            return {
                "status": "error",
                "message": "Contenu de la réponse vide"
            }
        
        self.speak(f"Analyse d'une réponse {response_type} de '{sender}'", target="ProspectionSupervisor")
        
        # Détection des URLs contextuels qui pourraient être le site du client
        urls, is_client_website = self._extract_contextual_urls(content, conversation_history)
        
        # Analyse de la réponse selon la méthode configurée
        analysis_method = self.config.get("analysis_method", "llm")
        
        if analysis_method == "llm":
            interpretation = self._interpret_with_llm(content, response_type, campaign_id)
        elif analysis_method == "rules":
            interpretation = self._interpret_with_rules(content, response_type)
        elif analysis_method == "hybrid":
            # Si la méthode hybride est configurée, on commence par les règles
            # et on bascule sur le LLM si le résultat n'est pas clair
            interpretation = self._interpret_with_rules(content, response_type)
            
            if interpretation.get("confidence", 0) < self.config.get("min_confidence_threshold", 0.7):
                interpretation = self._interpret_with_llm(content, response_type, campaign_id)
        else:
            # Par défaut, on utilise le LLM
            interpretation = self._interpret_with_llm(content, response_type, campaign_id)
        
        # Si lead_id est fourni, récupérer les informations du lead pour enrichir l'analyse
        if lead_id:
            lead_data = self._get_lead_data(lead_id)
            
            if lead_data:
                interpretation["lead_data"] = lead_data
        
        # Mise à jour des statistiques
        self.analysis_stats["total_analyzed"] += 1
        
        sentiment = interpretation.get("sentiment", "neutral")
        if sentiment == "positive":
            self.analysis_stats["positive_responses"] += 1
        elif sentiment == "negative":
            self.analysis_stats["negative_responses"] += 1
        elif sentiment == "neutral":
            self.analysis_stats["neutral_responses"] += 1
        else:
            self.analysis_stats["unclear_responses"] += 1
        
        # Détermination de l'action à entreprendre
        recommended_action = self._determine_action(interpretation, response_data, campaign_id)
        interpretation["action"] = recommended_action
        
        # Enregistrement de l'analyse en base de données si nécessaire
        if not self.config.get("test_mode", True):
            self._save_interpretation(interpretation, response_data, campaign_id)
        
        # Log du résultat
        self.speak(
            f"Réponse interprétée: sentiment {sentiment}, action {recommended_action.get('type', 'none')}",
            target="ProspectionSupervisor"
        )
        
        # Si un URL a été détecté et qu'il semble être le site web du client,
        # l'ajouter à l'interprétation
        if urls and is_client_website:
            self.speak(f"Site web client détecté: {urls[0]}", target="ProspectionSupervisor")
            interpretation["client_website"] = {
                "urls": urls,
                "is_client_website": is_client_website
            }
        
        # Résultat global
        return {
            "status": "success",
            "interpretation": interpretation,
            "response_id": response_data.get("id", ""),
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "urls": urls if urls else [],
            "is_client_website": is_client_website
        }
    
    def _interpret_with_llm(self, content: str, response_type: str, campaign_id: str) -> Dict[str, Any]:
        """
        Interprète une réponse à l'aide d'un LLM
        
        Args:
            content: Contenu de la réponse
            response_type: Type de réponse (email, sms)
            campaign_id: ID de la campagne
            
        Returns:
            Résultat de l'interprétation
        """
        # Récupération du contexte de la campagne si nécessaire
        campaign_context = self._get_campaign_context(campaign_id) if campaign_id else ""
        
        # Construction du prompt
        prompt = f"""
        Analyse cette réponse {response_type} et détermine:
        1. Son SENTIMENT (positive, neutral, negative)
        2. Son INTÉRÊT (high, medium, low, none)
        3. Les OBJECTIONS ou QUESTIONS éventuelles
        4. Si la personne demande de ne plus la contacter (DO_NOT_CONTACT: true/false)
        
        RÉPONSE À ANALYSER:
        {content}
        
        {campaign_context}
        
        RÉPONDS AVEC UN JSON STRUCTURÉ DE CE FORMAT:
        {{
          "sentiment": "positive/neutral/negative",
          "interest_level": "high/medium/low/none",
          "objections": ["objection1", "objection2"],
          "questions": ["question1", "question2"],
          "do_not_contact": true/false,
          "confidence": 0.x,
          "key_points": ["point clé extrait 1", "point clé extrait 2"]
        }}
        """
        
        # Complexité adaptée selon la taille de la réponse
        complexity = "medium"
        if len(content) > 500:
            complexity = "high"
        elif len(content) < 100:
            complexity = "low"
        
        try:
            # Appel au LLM
            response = LLMService.call_llm(prompt, complexity=complexity)
            
            # Parsing de la réponse JSON
            try:
                interpretation = json.loads(response)
            except json.JSONDecodeError:
                # Si le parsing échoue, on essaie de trouver et extraire le JSON
                json_match = re.search(r'({[\s\S]*})', response)
                if json_match:
                    try:
                        interpretation = json.loads(json_match.group(1))
                    except:
                        # Fallback à une analyse minimale
                        interpretation = {
                            "sentiment": "neutral",
                            "interest_level": "medium",
                            "objections": [],
                            "questions": [],
                            "do_not_contact": False,
                            "confidence": 0.5,
                            "key_points": ["Impossible de parser la réponse"]
                        }
                else:
                    # Fallback à une analyse minimale
                    interpretation = {
                        "sentiment": "neutral",
                        "interest_level": "medium",
                        "objections": [],
                        "questions": [],
                        "do_not_contact": False,
                        "confidence": 0.5,
                        "key_points": ["Impossible de parser la réponse"]
                    }
            
            return interpretation
            
        except Exception as e:
            self.speak(f"Erreur lors de l'analyse avec LLM: {str(e)}", target="ProspectionSupervisor")
            
            # Analyse minimale par défaut
            return {
                "sentiment": "neutral",
                "interest_level": "medium",
                "objections": [],
                "questions": [],
                "do_not_contact": False,
                "confidence": 0.5,
                "key_points": [f"Erreur d'analyse: {str(e)}"]
            }
    
    def _interpret_with_rules(self, content: str, response_type: str) -> Dict[str, Any]:
        """
        Interprète une réponse à l'aide de règles prédéfinies
        
        Args:
            content: Contenu de la réponse
            response_type: Type de réponse (email, sms)
            
        Returns:
            Résultat de l'interprétation
        """
        # Normalisation du texte
        text = content.lower().strip()
        
        # Initialisation des compteurs
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        # Initialisation des listes d'objections et questions
        objections = []
        questions = []
        
        # Vérification des mots-clés positifs
        for keyword in self.keyword_lists.get("positive", []):
            if keyword.lower() in text:
                positive_count += 1
        
        # Vérification des mots-clés négatifs
        for keyword in self.keyword_lists.get("negative", []):
            if keyword.lower() in text:
                negative_count += 1
        
        # Vérification des objections
        for objection_pattern in self.keyword_lists.get("objections", []):
            if objection_pattern.lower() in text:
                # Extrait une phrase autour de l'objection
                start = max(0, text.find(objection_pattern.lower()) - 20)
                end = min(len(text), text.find(objection_pattern.lower()) + len(objection_pattern) + 30)
                context = text[start:end].strip()
                objections.append(context)
        
        # Vérification des questions
        for question_pattern in self.regex_patterns.get("questions", [r'\?']):
            matches = re.findall(question_pattern, text)
            for match in matches:
                # Extraction de la phrase complète
                sentences = re.split(r'[.!?]', text)
                for sentence in sentences:
                    if match in sentence:
                        questions.append(sentence.strip())
                        break
        
        # Détection de demande d'opt-out
        do_not_contact = any(
            pattern.lower() in text 
            for pattern in self.keyword_lists.get("opt_out", [])
        )
        
        # Détermination du sentiment
        if do_not_contact or negative_count > positive_count * 2:
            sentiment = "negative"
        elif positive_count > negative_count:
            sentiment = "positive"
        else:
            sentiment = "neutral"
        
        # Niveau d'intérêt
        if do_not_contact:
            interest_level = "none"
        elif sentiment == "positive" and positive_count > 3:
            interest_level = "high"
        elif sentiment == "positive":
            interest_level = "medium"
        elif sentiment == "neutral":
            interest_level = "medium" if "?" in text else "low"
        else:
            interest_level = "low"
        
        # Calcul du niveau de confiance
        # Plus il y a de mots-clés matchés, plus la confiance est élevée
        total_matches = positive_count + negative_count + len(objections) + len(questions)
        confidence = min(0.9, 0.5 + (total_matches * 0.05))
        
        # Extraction des points clés
        key_points = []
        if positive_count > 0:
            key_points.append(f"Contient {positive_count} expressions positives")
        if negative_count > 0:
            key_points.append(f"Contient {negative_count} expressions négatives")
        if objections:
            key_points.append(f"Contient {len(objections)} objections")
        if questions:
            key_points.append(f"Contient {len(questions)} questions")
        if do_not_contact:
            key_points.append("Demande explicite de ne plus être contacté")
        
        # Construction du résultat
        return {
            "sentiment": sentiment,
            "interest_level": interest_level,
            "objections": objections,
            "questions": questions,
            "do_not_contact": do_not_contact,
            "confidence": confidence,
            "key_points": key_points
        }
    
    def _determine_action(self, interpretation: Dict[str, Any], response_data: Dict[str, Any], campaign_id: str) -> Dict[str, Any]:
        """
        Détermine l'action à entreprendre suite à l'interprétation
        
        Args:
            interpretation: Résultat de l'interprétation
            response_data: Données de la réponse
            campaign_id: ID de la campagne
            
        Returns:
            Action recommandée
        """
        # Extraction des données clés
        sentiment = interpretation.get("sentiment", "neutral")
        interest_level = interpretation.get("interest_level", "medium")
        do_not_contact = interpretation.get("do_not_contact", False)
        
        # Action par défaut
        action = {
            "type": "none",
            "details": {}
        }
        
        # Règles de détermination de l'action
        if do_not_contact:
            # Si demande explicite de ne plus contacter, blacklister
            action = {
                "type": "blacklist",
                "details": {
                    "reason": "Opt-out explicite",
                    "blacklist_level": "permanent"
                }
            }
            
        elif sentiment == "negative":
            # Selon la gravité de la réponse négative
            if "confidence" in interpretation and interpretation["confidence"] > 0.8:
                action = {
                    "type": "blacklist",
                    "details": {
                        "reason": "Réponse fortement négative",
                        "blacklist_level": "campaign"
                    }
                }
            else:
                action = {
                    "type": "flag",
                    "details": {
                        "reason": "Réponse négative",
                        "flag_type": "review_needed"
                    }
                }
                
        elif sentiment == "positive":
            # Réponse positive, transfert au CRM selon niveau d'intérêt
            if interest_level in ["high", "medium"]:
                action = {
                    "type": "transfer_to_crm",
                    "details": {
                        "priority": "high" if interest_level == "high" else "medium",
                        "stage": "qualified_lead" if interest_level == "high" else "warm_lead"
                    }
                }
            else:
                # Intérêt positif mais faible
                action = {
                    "type": "send_follow_up",
                    "details": {
                        "template_id": "template_positive_response",
                        "delay_days": 1
                    }
                }
                
        elif sentiment == "neutral":
            # Si questions, envoyer une réponse adaptée
            if interpretation.get("questions", []):
                action = {
                    "type": "send_follow_up",
                    "details": {
                        "template_id": "template_neutral_response",
                        "delay_days": 1,
                        "include_answers": True
                    }
                }
            # Sinon, workflow standard selon l'intérêt
            elif interest_level == "medium":
                action = {
                    "type": "send_follow_up",
                    "details": {
                        "template_id": "template_neutral_response",
                        "delay_days": 3
                    }
                }
            else:
                action = {
                    "type": "continue_sequence",
                    "details": {
                        "note": "Continuer la séquence normale"
                    }
                }
        
        # On ajoute les données d'origine pour référence
        action["response_data"] = {
            "id": response_data.get("id", ""),
            "lead_id": response_data.get("lead_id", ""),
            "campaign_id": campaign_id
        }
        
        return action
    
    def _get_campaign_context(self, campaign_id: str) -> str:
        """
        Récupère le contexte de la campagne pour enrichir l'analyse
        
        Args:
            campaign_id: ID de la campagne
            
        Returns:
            Contexte de la campagne sous forme de texte
        """
        # En mode test, on ne récupère pas le contexte
        if self.config.get("test_mode", True):
            return """
            CONTEXTE DE LA CAMPAGNE:
            Cette campagne est une campagne de prospection B2B dans le secteur de la technologie.
            Produit/Service: Solution logicielle d'automatisation de marketing
            Cible: Directeurs Marketing et CMOs
            """
        
        # En mode production, récupération depuis la base de données
        try:
            query = """
            SELECT * FROM campaigns WHERE id = :campaign_id
            """
            
            result = self.db.fetch_one(query, {"campaign_id": campaign_id})
            
            if not result:
                return ""
            
            # Construction du contexte
            context = f"""
            CONTEXTE DE LA CAMPAGNE:
            Nom: {result.get('name', '')}
            Description: {result.get('description', '')}
            Produit/Service: {result.get('product', '')}
            Cible: {result.get('target_audience', '')}
            """
            
            return context
            
        except Exception as e:
            self.speak(f"Erreur lors de la récupération du contexte de campagne: {str(e)}", target="ProspectionSupervisor")
            return ""
    
    def _get_lead_data(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les données d'un lead
        
        Args:
            lead_id: ID du lead
            
        Returns:
            Données du lead ou None si non trouvé
        """
        # En mode test, on retourne des données fictives
        if self.config.get("test_mode", True):
            return {
                "lead_id": lead_id,
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "company": "Example Company",
                "position": "CEO",
                "industry": "Technology",
                "engagement_history": {
                    "emails_sent": 2,
                    "emails_opened": 1,
                    "links_clicked": 0
                }
            }
        
        # En mode production, récupération depuis la base de données
        try:
            query = """
            SELECT * FROM leads WHERE id = :lead_id
            """
            
            result = self.db.fetch_one(query, {"lead_id": lead_id})
            
            if not result:
                return None
            
            # Construction des données du lead
            lead_data = {
                "lead_id": result.get("id"),
                "first_name": result.get("first_name"),
                "last_name": result.get("last_name"),
                "email": result.get("email"),
                "company": result.get("company"),
                "position": result.get("position"),
                "industry": result.get("industry")
            }
            
            # Récupération de l'historique d'engagement si disponible
            engagement_query = """
            SELECT 
                COUNT(CASE WHEN type = 'sent' THEN 1 END) as emails_sent,
                COUNT(CASE WHEN type = 'open' THEN 1 END) as emails_opened,
                COUNT(CASE WHEN type = 'click' THEN 1 END) as links_clicked
            FROM lead_interactions
            WHERE lead_id = :lead_id
            """
            
            engagement = self.db.fetch_one(engagement_query, {"lead_id": lead_id})
            
            if engagement:
                lead_data["engagement_history"] = {
                    "emails_sent": engagement.get("emails_sent", 0),
                    "emails_opened": engagement.get("emails_opened", 0),
                    "links_clicked": engagement.get("links_clicked", 0)
                }
            
            return lead_data
            
        except Exception as e:
            self.speak(f"Erreur lors de la récupération du lead: {str(e)}", target="ProspectionSupervisor")
            return None
    
    def _save_interpretation(self, interpretation: Dict[str, Any], response_data: Dict[str, Any], campaign_id: str) -> bool:
        """
        Enregistre l'interprétation en base de données
        
        Args:
            interpretation: Résultat de l'interprétation
            response_data: Données de la réponse
            campaign_id: ID de la campagne
            
        Returns:
            Succès de l'enregistrement
        """
        try:
            # Construction de l'enregistrement
            record = {
                "id": response_data.get("id", ""),
                "lead_id": response_data.get("lead_id", ""),
                "campaign_id": campaign_id,
                "content": response_data.get("content", ""),
                "sentiment": interpretation.get("sentiment", "neutral"),
                "interest_level": interpretation.get("interest_level", "medium"),
                "do_not_contact": interpretation.get("do_not_contact", False),
                "action": json.dumps(interpretation.get("action", {})),
                "confidence": interpretation.get("confidence", 0.5),
                "analysis_date": datetime.datetime.now().isoformat()
            }
            
            # Insertion dans la base de données
            self.db.insert("response_interpretations", record)
            
            return True
            
        except Exception as e:
            self.speak(f"Erreur lors de l'enregistrement de l'interprétation: {str(e)}", target="ProspectionSupervisor")
            return False
    
    def get_interpretation_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques d'interprétation
        
        Returns:
            Statistiques d'interprétation
        """
        return {
            "status": "success",
            "stats": self.analysis_stats
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
        
        if action == "interpret" or action == "interpret_response":
            # Pour l'action "interpret_response", on reformate les données pour qu'elles correspondent
            # à ce qui est attendu par la méthode interpret()
            if action == "interpret_response":
                self.speak(f"Reçu une demande d'interprétation de réponse", target="OverseerAgent")
                # On adapte le format des données
                data = input_data.get("data", {})
                formatted_input = {
                    "response_data": data,
                    "campaign_id": data.get("campaign_id", "")
                }
                result = self.interpret(formatted_input)
                
                # On stocke le message original dans le résultat pour référence
                result["original_message"] = data.get("content", "")
                result["channel"] = data.get("source", "sms")  # 'email' ou 'sms'
                
                # S'assurer que les données du lead sont complètes pour le messaging
                if "lead_data" not in result:
                    result["lead_data"] = {}
                    
                # S'assurer que les informations cruciales sont présentes
                if data.get("source") == "sms":
                    phone_number = data.get("sender", "")
                    result["lead_data"]["phone"] = phone_number
                    
                    # Si le lead_id n'est pas spécifié, vérifier si le numéro existe déjà ou créer un nouveau lead externe
                    if not data.get("lead_id"):
                        lead_id, is_new = self.lead_manager.get_or_create_lead_from_sms(
                            phone_number=phone_number,
                            message_content=data.get("content", "")
                        )
                        if is_new:
                            self.speak(f"Nouveau lead externe créé pour le numéro {phone_number}: {lead_id}", target="OverseerAgent")
                        result["lead_data"]["lead_id"] = lead_id
                    else:
                        result["lead_data"]["lead_id"] = data.get("lead_id")
                        
                elif data.get("source") == "email":
                    email = data.get("sender", "")
                    result["lead_data"]["email"] = email
                    
                    # Si le lead_id n'est pas spécifié, vérifier si l'email existe déjà ou créer un nouveau lead externe
                    if not data.get("lead_id"):
                        lead_id, is_new = self.lead_manager.get_or_create_lead_from_email(
                            email=email,
                            message_content=data.get("content", "")
                        )
                        if is_new:
                            self.speak(f"Nouveau lead externe créé pour l'email {email}: {lead_id}", target="OverseerAgent")
                        result["lead_data"]["lead_id"] = lead_id
                    else:
                        result["lead_data"]["lead_id"] = data.get("lead_id")
                
                # Autres données du lead si disponibles
                if data.get("raw_data"):
                    result["lead_data"].update(data.get("raw_data", {}))
                
                # On transmet le résultat à l'OverseerAgent pour qu'il décide des actions à prendre
                self._notify_overseer(result)
                return result
            else:
                return self.interpret(input_data)
        
        elif action == "get_stats":
            return self.get_interpretation_stats()
        
        else:
            self.speak(f"Action non reconnue: {action}", target="OverseerAgent")
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }
            
    def _extract_contextual_urls(self, content: str, conversation_history: List[Dict[str, Any]] = None) -> Tuple[List[str], bool]:
        """
        Extrait les URLs du contenu de manière contextuelle.
        
        Analyse intelligemment le contenu pour déterminer si un URL est pertinent
        en fonction du contexte de la conversation (par exemple, si l'URL est
        probablement le site web du client après qu'on ait demandé son site web).
        
        Args:
            content: Le contenu du message
            conversation_history: Historique de la conversation (si disponible)
            
        Returns:
            Tuple contenant (liste des URLs pertinents, indication si l'URL est probablement le site du client)
        """
        # Expression régulière pour détecter les URLs
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?[/\w\.\-&=]*)?'
        urls = re.findall(url_pattern, content)
        
        # Si pas d'URLs trouvés, retourner une liste vide
        if not urls:
            return [], False
        
        # Normalisation des URLs (enlever les paramètres, etc.)
        normalized_urls = []
        for url in urls:
            try:
                # Extraction du domaine principal
                parsed = urllib.parse.urlparse(url)
                domain = parsed.netloc
                
                # Reconstruire l'URL sans les paramètres pour comparer
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                normalized_urls.append(clean_url)
            except:
                normalized_urls.append(url)
        
        # Analyse contextuelle pour déterminer si l'URL est probablement le site du client
        is_client_website = False
        
        # Recherche de contexte "site web" dans le message actuel ou précédent
        site_web_keywords = ["site web", "site internet", "page web", "page internet", "mon site", "notre site"]
        
        # Vérification du message actuel
        content_lower = content.lower()
        for keyword in site_web_keywords:
            if keyword in content_lower:
                is_client_website = True
                break
                
        # Vérification de l'historique de conversation si disponible
        if conversation_history and not is_client_website:
            # Recherche dans les derniers messages
            last_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
            
            for message in reversed(last_messages):
                if message.get("direction") == "outbound":  # Message envoyé par nous
                    msg_content = message.get("content", "").lower()
                    
                    # Chercher si on a demandé leur site web
                    site_web_questions = [
                        "site web", "site internet", "avez-vous un site", "votre site",
                        "pouvez-vous me partager", "quel est votre site"
                    ]
                    
                    for question in site_web_questions:
                        if question in msg_content and "?" in msg_content:
                            is_client_website = True
                            break
                    
                    if is_client_website:
                        break
        
        # Si on n'a qu'un seul URL et qu'il ressemble à un site professionnel, c'est probablement le site du client
        if len(urls) == 1 and not is_client_website:
            for url in normalized_urls:
                if any(business_domain in url for business_domain in [".com", ".fr", ".io", ".net", ".org", ".co.uk", ".info", ".eu"]):
                    # Éviter les sites connus qui ne sont pas des sites professionnels
                    known_platforms = ["facebook.com", "instagram.com", "twitter.com", "linkedin.com", "youtube.com", "google.com"]
                    if not any(platform in url for platform in known_platforms):
                        is_client_website = True
        
        return normalized_urls, is_client_website
    
    def _notify_overseer(self, interpretation_result: Dict[str, Any]) -> None:
        """
        Notifie l'OverseerAgent du résultat de l'interprétation
        
        Args:
            interpretation_result: Résultat de l'interprétation
        """
        try:
            # Import dynamique pour éviter les dépendances circulaires
            from agents.overseer.overseer_agent import OverseerAgent
            
            overseer = OverseerAgent()
            
            # Préparation des données pour l'Overseer
            notification = {
                "action": "handle_response_interpretation",
                "interpretation": interpretation_result,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Appel à l'OverseerAgent
            overseer_result = overseer.run(notification)
            
            self.speak(f"Notification envoyée à l'OverseerAgent: {overseer_result.get('status', 'unknown')}", 
                      target="OverseerAgent")
                
        except Exception as e:
            self.speak(f"Erreur lors de la notification à l'OverseerAgent: {str(e)}", 
                      target="OverseerAgent")

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du ResponseInterpreterAgent
    agent = ResponseInterpreterAgent()
    
    # Test de l'agent
    test_response = {
        "id": "resp_1",
        "lead_id": "lead_1",
        "sender": "test@example.com",
        "content": "Merci pour votre proposition, je suis intéressé. Pouvez-vous m'en dire plus sur les tarifs ?",
        "type": "email"
    }
    
    result = agent.run({
        "action": "interpret",
        "response_data": test_response,
        "campaign_id": "camp_test"
    })
    
    print(json.dumps(result, indent=2))

"""
Module du MessagingAgent - Agent d'envoi de messages aux leads
"""
import os
import json
import re
from typing import Dict, Any, Optional, List, Tuple
import datetime
import uuid
import time
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client  # Ajout de l'import du SDK Twilio
from pathlib import Path

from core.agent_base import Agent
from utils.llm import LLMService
from core.db import DatabaseService

class MessagingAgent(Agent):
    """
    MessagingAgent - Agent responsable de l'envoi des messages aux leads
    
    Cet agent est responsable de:
    - Rédiger des messages personnalisés pour chaque lead
    - Envoyer les messages via différents canaux (email, SMS)
    - Garder trace des communications envoyées
    - Gérer les limites d'envoi et les planifications
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du MessagingAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("MessagingAgent", config_path)
        
        # État de l'agent
        self.messaging_stats = {
            "total_sent": 0,
            "emails_sent": 0,
            "sms_sent": 0,
            "failed": 0,
            "last_sent_date": None
        }
        
        # Chargement des paramètres de messagerie
        self.daily_limit = self.config.get("daily_limit", 100)
        self.current_day_count = 0
        self.last_day_reset = datetime.datetime.now().date()
        
        # Initialisation de la connexion à la base de données
        self.db = DatabaseService()
        
        # Chargement des templates
        self.templates = self._load_templates()
        
        # Initialisation des clients de messagerie
        self._init_email_client()
        self._init_sms_client()
        
        # Chargement de la configuration de la personnalité
        self.persona_config = self._load_persona_config()
    
    def _load_templates(self) -> Dict[str, Any]:
        """
        Charge les templates de messages depuis la base de données ou les fichiers

        Returns:
            Dictionnaire de templates
        """
        templates = {}

        # D'abord, chargement des templates depuis la configuration
        templates = self.config.get("templates", {})

        # Si pas de templates dans la config, créer des templates par défaut
        if not templates:
            templates = {
                "default_intro": {
                    "name": "Introduction par défaut",
                    "content": "Bonjour {first_name},\n\nJ'espère que ce message vous trouve bien. Je suis {sender_name} de {company_name}.",
                    "type": "intro"
                },
                "default_followup": {
                    "name": "Relance par défaut",
                    "content": "Bonjour {first_name},\n\nJe me permets de revenir vers vous concernant mon précédent message.",
                    "type": "followup"
                },
                "default_closing": {
                    "name": "Conclusion par défaut",
                    "content": "Cordialement,\n{sender_name}\n{sender_title}\n{company_name}",
                    "type": "closing"
                }
            }
        
        try:
            # Tentative de chargement depuis la base de données
            query = "SELECT id, name, content, type FROM message_templates"
            
            # Utilisation d'un bloc try/except dédié pour la requête
            try:
                results = self.db.fetch_all(query)
                
                if results:
                    # Si des templates sont trouvés en base, ils remplacent ceux par défaut
                    templates = {}
                    for row in results:
                        template_id = row["id"]
                        templates[template_id] = {
                            "name": row["name"],
                            "content": row["content"],
                            "type": row["type"]
                        }
                    self.speak("Templates chargés depuis la base de données", target="ProspectionSupervisor")
            except Exception as db_error:
                # Erreur silencieuse pour les problèmes de base de données
                # Les templates de la configuration seront utilisés
                pass
                
        except Exception as e:
            # En cas d'erreur générale, utilisation des templates par défaut
            self.speak(f"Utilisation des templates par défaut", target="ProspectionSupervisor")

        return templates
    
    def _init_email_client(self):
        """
        Initialise le client d'envoi d'emails (SMTP ou API)
        """
        # Configuration email depuis config ou variables d'environnement
        email_config = self.config.get("email", {})
        
        self.email_service = email_config.get("service", "smtp")
        
        if self.email_service == "smtp":
            self.smtp_config = {
                "server": email_config.get("smtp_server") or os.getenv("SMTP_SERVER", ""),
                "port": email_config.get("smtp_port") or int(os.getenv("SMTP_PORT", "587")),
                "user": email_config.get("smtp_user") or os.getenv("SMTP_USER", ""),
                "password": email_config.get("smtp_password") or os.getenv("SMTP_PASSWORD", ""),
                "from_email": email_config.get("from_email") or os.getenv("FROM_EMAIL", "")
            }
        elif self.email_service == "mailgun":
            self.mailgun_config = {
                "api_key": email_config.get("mailgun_api_key") or os.getenv("MAILGUN_API_KEY", ""),
                "domain": email_config.get("mailgun_domain") or os.getenv("MAILGUN_DOMAIN", ""),
                "from_email": email_config.get("from_email") or os.getenv("FROM_EMAIL", "")
            }
        else:
            self.speak(f"Service email non supporté: {self.email_service}", target="ProspectionSupervisor")
    
    def _init_sms_client(self):
        """
        Initialise le client d'envoi de SMS (Twilio ou autre)
        """
        # Configuration SMS depuis config ou variables d'environnement
        sms_config = self.config.get("sms", {})
        
        self.sms_service = sms_config.get("service", "twilio")
        
        if self.sms_service == "twilio":
            self.twilio_config = {
                "account_sid": sms_config.get("twilio_account_sid") or os.getenv("TWILIO_SID") or os.getenv("TWILIO_ACCOUNT_SID", ""),
                "auth_token": sms_config.get("twilio_auth_token") or os.getenv("TWILIO_TOKEN") or os.getenv("TWILIO_AUTH_TOKEN", ""),
                "from_number": sms_config.get("from_number") or os.getenv("TWILIO_PHONE") or os.getenv("TWILIO_FROM_NUMBER", "")
            }
            # Log pour déboguer
            self.speak(f"Configuration Twilio: SID={self.twilio_config['account_sid'][:6]}..., Token={self.twilio_config['auth_token'][:6]}..., From={self.twilio_config['from_number']}", target="ProspectionSupervisor")
        else:
            self.speak(f"Service SMS non supporté: {self.sms_service}", target="ProspectionSupervisor")
    
    def send_messages(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie des messages à une liste de leads
        
        Args:
            input_data: Données d'entrée avec les leads et les paramètres d'envoi
            
        Returns:
            Résultat de l'envoi des messages
        """
        leads = input_data.get("leads", [])
        campaign_id = input_data.get("campaign_id", "")
        template_id = input_data.get("template_id", "")
        channel = input_data.get("channel", "email")
        batch_size = input_data.get("batch_size", self.config.get("batch_size", 20))
        
        if not leads:
            return {
                "status": "error",
                "message": "Aucun lead à contacter",
                "leads": []
            }
        
        if not template_id or template_id not in self.templates:
            return {
                "status": "error",
                "message": f"Template non trouvé: {template_id}",
                "leads": []
            }
        
        # Vérification de la limite quotidienne
        today = datetime.datetime.now().date()
        if today != self.last_day_reset:
            self.current_day_count = 0
            self.last_day_reset = today
        
        if self.current_day_count >= self.daily_limit:
            return {
                "status": "error",
                "message": f"Limite quotidienne atteinte ({self.daily_limit} messages)",
                "leads": []
            }
        
        # Limitation par batch
        available_quota = min(self.daily_limit - self.current_day_count, len(leads))
        leads_to_process = leads[:available_quota]
        
        self.speak(f"Envoi de {len(leads_to_process)} messages pour la campagne '{campaign_id}'", target="ProspectionSupervisor")
        
        sent_messages = []
        failed_messages = []
        
        # Traitement par batch
        for i in range(0, len(leads_to_process), batch_size):
            batch = leads_to_process[i:i+batch_size]
            
            self.speak(f"Traitement du batch {i//batch_size + 1}/{(len(leads_to_process) + batch_size - 1)//batch_size}", target="ProspectionSupervisor")
            
            for lead in batch:
                # Génération du message personnalisé
                message_data = self._generate_message(lead, template_id, campaign_id)
                
                if not message_data:
                    failed_messages.append({
                        "lead": lead,
                        "reason": "Échec de génération du message"
                    })
                    continue
                
                # Envoi du message selon le canal
                if channel == "email":
                    success, error = self._send_email(lead, message_data, campaign_id)
                elif channel == "sms":
                    success, error = self._send_sms(lead, message_data, campaign_id)
                else:
                    success, error = False, f"Canal non supporté: {channel}"
                
                if success:
                    # Enregistrement du message envoyé
                    message_id = self._save_message_to_db(lead, message_data, campaign_id, channel)
                    
                    sent_messages.append({
                        "lead_id": lead.get("lead_id", ""),
                        "message_id": message_id,
                        "channel": channel,
                        "sent_at": datetime.datetime.now().isoformat()
                    })
                    
                    # Mise à jour des stats
                    self.current_day_count += 1
                    self.messaging_stats["total_sent"] += 1
                    
                    if channel == "email":
                        self.messaging_stats["emails_sent"] += 1
                    elif channel == "sms":
                        self.messaging_stats["sms_sent"] += 1
                else:
                    failed_messages.append({
                        "lead": lead,
                        "reason": error
                    })
                    
                    # Mise à jour des stats
                    self.messaging_stats["failed"] += 1
            
            # Pause entre les batches
            if i + batch_size < len(leads_to_process):
                time_between_batches = self.config.get("time_between_batches", 60)  # Secondes
                time.sleep(time_between_batches)
        
        # Mise à jour de la date du dernier envoi
        self.messaging_stats["last_sent_date"] = datetime.datetime.now().isoformat()
        
        # Log des résultats
        self.speak(
            f"Envoi terminé: {len(sent_messages)} messages envoyés, {len(failed_messages)} échecs",
            target="ProspectionSupervisor"
        )
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "template_id": template_id,
            "channel": channel,
            "sent_messages": sent_messages,
            "failed_messages": failed_messages,
            "stats": {
                "total": len(leads_to_process),
                "sent": len(sent_messages),
                "failed": len(failed_messages),
                "remaining_daily_quota": self.daily_limit - self.current_day_count
            }
        }
    
    def _generate_message(self, lead: Dict[str, Any], template_id: str, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Génère un message personnalisé pour un lead
        
        Args:
            lead: Le lead à contacter
            template_id: L'ID du template à utiliser
            campaign_id: L'ID de la campagne
            
        Returns:
            Message personnalisé ou None en cas d'erreur
        """
        try:
            template = self.templates.get(template_id, {})
            
            if not template:
                self.speak(f"Template {template_id} non trouvé", target="ProspectionSupervisor")
                return None
            
            template_content = template.get("content", "")
            
            # Si le template contient des variables (à remplacer)
            if "{" in template_content and "}" in template_content:
                # Essayer de remplacer les variables directement
                personalized_content = template_content.format(**lead)
            else:
                # Si le template ne contient pas de variables
                # ou si le remplacement direct échoue, utiliser le LLM
                personalized_content = self._personalize_with_llm(lead, template_content, campaign_id)
            
            subject = template.get("subject", "")
            
            # Personnalisation du sujet si nécessaire
            if subject and "{" in subject and "}" in subject:
                try:
                    personalized_subject = subject.format(**lead)
                except KeyError:
                    personalized_subject = self._personalize_subject_with_llm(subject, lead)
            else:
                personalized_subject = subject
            
            return {
                "subject": personalized_subject,
                "content": personalized_content,
                "template_id": template_id
            }
            
        except Exception as e:
            self.speak(f"Erreur lors de la génération du message: {str(e)}", target="ProspectionSupervisor")
            return None
    
    def _personalize_with_llm(self, lead: Dict[str, Any], template_content: str, campaign_id: str) -> str:
        """
        Personnalise un template avec l'aide d'un LLM
        
        Args:
            lead: Le lead à contacter
            template_content: Le contenu du template
            campaign_id: L'ID de la campagne
            
        Returns:
            Contenu personnalisé
        """
        prompt = f"""
        Personnalise ce template d'email pour le lead suivant:
        
        LEAD:
        {json.dumps(lead, indent=2)}
        
        TEMPLATE:
        {template_content}
        
        INSTRUCTIONS DE PERSONNALISATION:
        1. Conserve la structure globale du template
        2. Insère des informations spécifiques du lead (nom, entreprise, etc.)
        3. Ajoute des éléments pertinents par rapport à l'industrie du lead
        4. Garde un ton professionnel et adapté au contexte
        5. Ne mentionne PAS que c'est un email automatisé ou généré par IA
        
        RÉPONDS UNIQUEMENT AVEC LE TEXTE PERSONNALISÉ, SANS COMMENTAIRES NI EXPLICATIONS.
        """
        
        try:
            response = LLMService.call_llm(prompt, complexity="medium")
            return response.strip()
        except Exception as e:
            self.speak(f"Erreur LLM lors de la personnalisation: {str(e)}", target="ProspectionSupervisor")
            
            # Fallback: remplacement basique
            content = template_content
            for key, value in lead.items():
                placeholder = f"{{{key}}}"
                if placeholder in content and value:
                    content = content.replace(placeholder, str(value))
            
            return content
    
    def _personalize_subject_with_llm(self, subject_template: str, lead: Dict[str, Any]) -> str:
        """
        Personnalise un sujet d'email avec l'aide d'un LLM
        
        Args:
            subject_template: Le template du sujet
            lead: Le lead à contacter
            
        Returns:
            Sujet personnalisé
        """
        prompt = f"""
        Personnalise ce sujet d'email pour le lead suivant:
        
        LEAD:
        {json.dumps(lead, indent=2)}
        
        SUJET À PERSONNALISER:
        {subject_template}
        
        RÉPONDS UNIQUEMENT AVEC LE SUJET PERSONNALISÉ, SANS AUTRE TEXTE.
        """
        
        try:
            response = LLMService.call_llm(prompt, complexity="low")
            return response.strip()
        except Exception as e:
            self.speak(f"Erreur LLM lors de la personnalisation du sujet: {str(e)}", target="ProspectionSupervisor")
            
            # Fallback: remplacement basique
            subject = subject_template
            for key, value in lead.items():
                placeholder = f"{{{key}}}"
                if placeholder in subject and value:
                    subject = subject.replace(placeholder, str(value))
            
            return subject
    
    def _send_email(self, lead: Dict[str, Any], message_data: Dict[str, Any], campaign_id: str) -> tuple[bool, str]:
        """
        Envoie un email à un lead
        
        Args:
            lead: Le lead à contacter
            message_data: Les données du message
            campaign_id: L'ID de la campagne
            
        Returns:
            Tuple (succès, erreur)
        """
        recipient_email = lead.get("email", "")
        
        if not recipient_email:
            return False, "Email du destinataire manquant"
        
        subject = message_data.get("subject", "")
        content = message_data.get("content", "")
        
        if not content:
            return False, "Contenu du message vide"
        
        # Envoi selon le service configuré
        if self.email_service == "smtp":
            return self._send_email_smtp(recipient_email, subject, content, campaign_id)
        elif self.email_service == "mailgun":
            return self._send_email_mailgun(recipient_email, subject, content, campaign_id)
        else:
            return False, f"Service email non supporté: {self.email_service}"
    
    def _send_email_smtp(self, recipient: str, subject: str, body: str, campaign_id: str) -> tuple[bool, str]:
        """
        Envoie un email via SMTP
        
        Args:
            recipient: L'email du destinataire
            subject: Le sujet du message
            body: Le corps du message
            campaign_id: L'ID de la campagne
            
        Returns:
            Tuple (succès, erreur)
        """
        # Simulation de l'envoi si en mode test
        if self.config.get("test_mode", True):
            self.speak(f"[MODE TEST] Email envoyé à {recipient} (SMTP)", target="ProspectionSupervisor")
            time.sleep(0.1)  # Légère pause pour simuler l'envoi
            return True, ""
        
        # Vérification de la configuration SMTP
        if not all([
            self.smtp_config.get("server"),
            self.smtp_config.get("port"),
            self.smtp_config.get("user"),
            self.smtp_config.get("password"),
            self.smtp_config.get("from_email")
        ]):
            return False, "Configuration SMTP incomplète"
        
        try:
            # Création du message
            msg = MIMEMultipart()
            msg["From"] = self.smtp_config["from_email"]
            msg["To"] = recipient
            msg["Subject"] = subject
            
            # Ajout d'un ID de tracking pour le suivi des réponses
            tracking_id = str(uuid.uuid4())
            msg["X-Campaign-ID"] = campaign_id
            msg["X-Tracking-ID"] = tracking_id
            
            # Ajout du corps du message
            msg.attach(MIMEText(body, "html"))
            
            # Connexion au serveur SMTP
            with smtplib.SMTP(self.smtp_config["server"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(self.smtp_config["user"], self.smtp_config["password"])
                server.send_message(msg)
            
            return True, ""
            
        except Exception as e:
            error_msg = f"Erreur SMTP: {str(e)}"
            self.speak(error_msg, target="ProspectionSupervisor")
            return False, error_msg
    
    def _send_email_mailgun(self, recipient: str, subject: str, body: str, campaign_id: str) -> tuple[bool, str]:
        """
        Envoie un email via l'API Mailgun
        
        Args:
            recipient: L'email du destinataire
            subject: Le sujet du message
            body: Le corps du message
            campaign_id: L'ID de la campagne
            
        Returns:
            Tuple (succès, erreur)
        """
        # Simulation de l'envoi si en mode test
        if self.config.get("test_mode", True):
            self.speak(f"[MODE TEST] Email envoyé à {recipient} (Mailgun)", target="ProspectionSupervisor")
            time.sleep(0.1)  # Légère pause pour simuler l'envoi
            return True, ""
        
        # Vérification de la configuration Mailgun
        if not all([
            self.mailgun_config.get("api_key"),
            self.mailgun_config.get("domain"),
            self.mailgun_config.get("from_email")
        ]):
            return False, "Configuration Mailgun incomplète"
        
        try:
            # Construction de l'URL de l'API
            api_url = f"https://api.mailgun.net/v3/{self.mailgun_config['domain']}/messages"
            
            # Génération d'un ID de tracking
            tracking_id = str(uuid.uuid4())
            
            # Construction du payload
            data = {
                "from": self.mailgun_config["from_email"],
                "to": recipient,
                "subject": subject,
                "html": body,
                "h:X-Campaign-ID": campaign_id,
                "h:X-Tracking-ID": tracking_id
            }
            
            # Envoi de la requête
            auth = ("api", self.mailgun_config["api_key"])
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(api_url, data=data, auth=auth)
                
                if response.status_code != 200:
                    return False, f"Erreur Mailgun: {response.status_code} - {response.text}"
            
            return True, ""
            
        except Exception as e:
            error_msg = f"Erreur Mailgun: {str(e)}"
            self.speak(error_msg, target="ProspectionSupervisor")
            return False, error_msg
    
    def _send_sms(self, lead: Dict[str, Any], message_data: Dict[str, Any], campaign_id: str) -> tuple[bool, str]:
        """
        Envoie un SMS à un lead
        
        Args:
            lead: Le lead à contacter
            message_data: Les données du message
            campaign_id: L'ID de la campagne
            
        Returns:
            Tuple (succès, erreur)
        """
        phone_number = lead.get("phone", "")
        
        if not phone_number:
            return False, "Numéro de téléphone manquant"
        
        content = message_data.get("content", "")
        
        if not content:
            return False, "Contenu du message vide"
        
        # Vérification explicite du mode test
        test_mode = self.config.get("test_mode")
        if test_mode is None:  # Si la configuration n'est pas trouvée
            test_mode = False  # Force mode réel par défaut
        
        # Log de débogage pour voir la valeur utilisée
        self.speak(f"Mode test: {test_mode}", target="ProspectionSupervisor")
            
        # Simulation de l'envoi si en mode test
        if test_mode:
            self.speak(f"[MODE TEST] SMS envoyé à {phone_number}", target="ProspectionSupervisor")
            time.sleep(0.1)  # Légère pause pour simuler l'envoi
            return True, ""
        
        # Envoi via Twilio
        if self.sms_service == "twilio":
            return self._send_sms_twilio(phone_number, content, campaign_id)
        else:
            return False, f"Service SMS non supporté: {self.sms_service}"
    
    def _send_sms_twilio(self, recipient: str, body: str, campaign_id: str) -> tuple[bool, str]:
        """
        Envoie un SMS via le SDK officiel Twilio
        
        Args:
            recipient: Le numéro de téléphone du destinataire
            body: Le corps du message
            campaign_id: L'ID de la campagne
            
        Returns:
            Tuple (succès, erreur)
        """
        # Vérification de la configuration Twilio
        if not all([
            self.twilio_config.get("account_sid"),
            self.twilio_config.get("auth_token"),
            self.twilio_config.get("from_number")
        ]):
            return False, "Configuration Twilio incomplète"
        
        # Vérification du format du numéro (doit commencer par +)
        if not recipient.startswith('+'):
            recipient = '+' + recipient
            
        try:
            # Création du client Twilio avec le SDK officiel
            client = Client(
                self.twilio_config["account_sid"],
                self.twilio_config["auth_token"]
            )
            
            # Envoi du message via le SDK
            message = client.messages.create(
                body=body,
                from_=self.twilio_config["from_number"],
                to=recipient
            )
            
            # Log du SID du message pour suivi
            self.speak(
                f"SMS envoyé avec succès via Twilio SDK, SID: {message.sid}",
                target="ProspectionSupervisor"
            )
            
            return True, ""
            
        except Exception as e:
            error_msg = f"Erreur Twilio SDK: {str(e)}"
            self.speak(error_msg, target="ProspectionSupervisor")
            return False, error_msg
    
    def _save_message_to_db(self, lead: Dict[str, Any], message_data: Dict[str, Any], campaign_id: str, channel: str) -> str:
        """
        Enregistre un message envoyé dans la base de données
        
        Args:
            lead: Le lead contacté
            message_data: Les données du message
            campaign_id: L'ID de la campagne
            channel: Le canal utilisé (email, sms, etc.)
            
        Returns:
            ID du message enregistré
        """
        message_id = str(uuid.uuid4())
        
        try:
            # Insertion dans la base de données
            message_record = {
                "id": message_id,
                "lead_id": lead.get("lead_id", ""),
                "campaign_id": campaign_id,
                "template_id": message_data.get("template_id", ""),
                "channel": channel,
                "subject": message_data.get("subject", ""),
                "content": message_data.get("content", ""),
                "sent_at": datetime.datetime.now().isoformat(),
                "status": "sent"
            }
            
            # Selon le mode de fonctionnement (test ou production)
            if not self.config.get("test_mode", True):
                self.db.insert("messages", message_record)
            
            return message_id
            
        except Exception as e:
            self.speak(f"Erreur lors de l'enregistrement du message: {str(e)}", target="ProspectionSupervisor")
            return message_id  # On retourne quand même l'ID généré
    
    def get_templates(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les templates disponibles
        
        Args:
            input_data: Données d'entrée (filtres optionnels)
            
        Returns:
            Liste des templates
        """
        template_type = input_data.get("type", None)
        
        if template_type:
            filtered_templates = {
                k: v for k, v in self.templates.items() 
                if v.get("type", "") == template_type
            }
            return {
                "status": "success",
                "templates": filtered_templates
            }
        else:
            return {
                "status": "success",
                "templates": self.templates
            }
    
    def get_messaging_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques d'envoi de messages
        
        Returns:
            Statistiques d'envoi
        """
        return {
            "status": "success",
            "stats": self.messaging_stats,
            "daily_limit": self.daily_limit,
            "current_day_count": self.current_day_count,
            "remaining_quota": self.daily_limit - self.current_day_count
        }
    
    def _load_persona_config(self) -> Dict[str, Any]:
        """
        Charge la configuration de la personnalité depuis le fichier persona_config.json
        
        Returns:
            Configuration de la personnalité
        """
        # Chemin par défaut vers le fichier de configuration
        config_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "config" / "persona_config.json"
        
        # Valeurs par défaut
        default_config = {
            "identity": {
                "name": "Louise",
                "entity": "BerinIA",
                "role": "Assistante commerciale"
            },
            "voice_tone": {
                "formal": True,
                "friendly": True,
                "brief": True
            },
            "communication_limits": {
                "allowed_topics": ["commercial", "client_business", "services_offered"],
                "forbidden_topics": ["technical_details", "internal_processes", "ai_functionality"],
                "refusal_replies": [
                    "Je n'ai pas accès à ces informations techniques, mais je serais ravie de vous aider sur les aspects commerciaux de notre collaboration.",
                    "Cette information est réservée à notre équipe technique. Je peux cependant vous mettre en contact avec eux si vous avez des questions spécifiques à ce sujet."
                ]
            },
            "default_prompt_template": "Tu es {name}, assistante commerciale pour {entity}. Tu réponds à un message d'un lead potentiel. Reste professionnelle, cordiale et concise."
        }
        
        try:
            # Vérification de l'existence du fichier
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.speak(f"Configuration de personnalité chargée depuis {config_path}", target="ProspectionSupervisor")
                return config
            else:
                self.speak(f"Fichier de configuration de personnalité non trouvé: {config_path}. Utilisation des valeurs par défaut.", target="ProspectionSupervisor")
                return default_config
        except Exception as e:
            self.speak(f"Erreur lors du chargement de la configuration de personnalité: {str(e)}. Utilisation des valeurs par défaut.", target="ProspectionSupervisor")
            return default_config
    
    def get_conversation_history(self, lead_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère l'historique de conversation avec un lead
        
        Args:
            lead_id: ID du lead
            limit: Nombre maximal de messages à récupérer
            
        Returns:
            Liste des messages échangés avec le lead
        """
        try:
            # Vérifier si le lead_id est un entier ou peut être converti en entier
            try:
                lead_id_int = int(lead_id)
            except (ValueError, TypeError):
                # Si lead_id n'est pas un entier valide, on retourne une liste vide
                self.speak(f"lead_id non valide pour conversion en entier: {lead_id}", target="ProspectionSupervisor")
                return []
            
            # Requête simplifiée qui n'utilise que les colonnes confirmées existantes
            query = """
                SELECT 
                    id, 
                    lead_id, 
                    content, 
                    sent_date as sent_at,
                    type,
                    status,
                    CASE 
                        WHEN type = 'reply' THEN 'inbound'
                        ELSE 'outbound'
                    END as direction
                FROM messages
                WHERE lead_id = :lead_id
                ORDER BY sent_date DESC
                LIMIT :limit
            """
            
            results = self.db.fetch_all(query, {"lead_id": lead_id_int, "limit": limit})
            
            # Inversion pour avoir l'ordre chronologique
            history = list(reversed(results)) if results else []
            
            return history
        except Exception as e:
            self.speak(f"Erreur lors de la récupération de l'historique de conversation: {str(e)}", target="ProspectionSupervisor")
            
            # En cas d'erreur, tenter une approche encore plus simple
            try:
                simplified_query = """
                    SELECT 
                        id, 
                        lead_id,
                        content,
                        sent_date as sent_at,
                        'outbound' as direction
                    FROM messages
                    WHERE lead_id = :lead_id
                    ORDER BY sent_date DESC
                    LIMIT :limit
                """
                
                self.speak("Tentative avec requête simplifiée de secours", target="ProspectionSupervisor")
                results = self.db.fetch_all(simplified_query, {"lead_id": lead_id_int, "limit": limit})
                
                # Inversion pour avoir l'ordre chronologique
                return list(reversed(results)) if results else []
                
            except Exception as e2:
                self.speak(f"Échec de la requête de secours: {str(e2)}", target="ProspectionSupervisor")
                return []
    
    def generate_contextual_response(self, input_data: Dict[str, Any]) -> str:
        """
        Génère une réponse contextuelle pour un message reçu d'un lead
        
        Args:
            input_data: Données d'entrée avec les informations sur le lead et le message
            
        Returns:
            Réponse générée
        """
        # Importation des templates de prompts optimisés
        from agents.messaging.prompts import SMS_RESPONSE_PROMPT, EMAIL_RESPONSE_PROMPT
        
        # Extraction des données nécessaires
        lead = input_data.get("lead_data", {})
        message = input_data.get("message", "")
        campaign_id = input_data.get("campaign_id", "")
        site_analysis = input_data.get("site_analysis", {})
        channel = input_data.get("channel", "sms")  # Par défaut, supposons que c'est un SMS
        
        # Récupération de l'historique de conversation
        lead_id = lead.get("lead_id", "")
        conversation_history = []
        
        if lead_id:
            conversation_history = self.get_conversation_history(lead_id)
        
        # Préparation des métadonnées conversationnelles
        current_time = datetime.datetime.now()
        messages_count = len(conversation_history) + 1  # +1 pour le message actuel
        is_first_message = messages_count <= 1
        
        # Déterminer le temps écoulé depuis le dernier message
        time_since_last_message = None
        time_description = "Premier message"
        
        if not is_first_message and conversation_history:
            try:
                last_msg_time_str = conversation_history[-1].get("sent_at", "")
                if last_msg_time_str:
                    # Essayer différents formats de date
                    try:
                        last_msg_time = datetime.datetime.fromisoformat(last_msg_time_str)
                    except ValueError:
                        try:
                            last_msg_time = datetime.datetime.strptime(last_msg_time_str, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            last_msg_time = current_time - datetime.timedelta(minutes=5)  # Fallback
                    
                    time_since_last_message = current_time - last_msg_time
                    
                    # Formuler une description du temps écoulé
                    if time_since_last_message.days > 0:
                        time_description = f"Il y a {time_since_last_message.days} jour(s)"
                    elif time_since_last_message.seconds // 3600 > 0:
                        time_description = f"Il y a {time_since_last_message.seconds // 3600} heure(s)"
                    elif time_since_last_message.seconds // 60 > 0:
                        time_description = f"Il y a {time_since_last_message.seconds // 60} minute(s)"
                    else:
                        time_description = "À l'instant"
            except Exception as e:
                self.speak(f"Erreur lors du calcul du temps écoulé: {str(e)}", target="ProspectionSupervisor")
                time_description = "Temps indéterminé"
        
        # Création d'un historique de conversation structuré et enrichi
        history_text = ""
        if conversation_history:
            history_text += f"=== CONVERSATION ({messages_count - 1} message(s) précédent(s)) ===\n\n"
            
            for i, msg in enumerate(conversation_history):
                # Extraire les informations du message
                direction = "BerinIA → Lead" if msg.get("direction") == "outbound" else "Lead → BerinIA"
                content = msg.get("content", "")
                date = msg.get("sent_at", "")
                msg_type = msg.get("type", "")
                
                # Formatter l'horodatage
                try:
                    date_obj = None
                    if date:
                        try:
                            date_obj = datetime.datetime.fromisoformat(date)
                        except ValueError:
                            try:
                                date_obj = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                pass
                    
                    if date_obj:
                        formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M:%S")
                    else:
                        formatted_date = date
                except:
                    formatted_date = date
                
                # Construire l'entrée de l'historique avec numéro de message et horodatage détaillé
                history_text += f"MESSAGE #{i+1} - {formatted_date}\n"
                history_text += f"[{direction}] {content}\n\n"
            
            # Ajouter une séparation claire pour le nouveau message
            history_text += f"=== NOUVEAU MESSAGE (#{messages_count}) - {current_time.strftime('%d/%m/%Y à %H:%M:%S')} ===\n"
            history_text += f"[Lead → BerinIA] {message}\n\n"
        else:
            # S'il n'y a pas d'historique, indiquer clairement qu'il s'agit du premier message
            history_text += "=== PREMIER MESSAGE DE LA CONVERSATION ===\n"
            history_text += f"Date et heure: {current_time.strftime('%d/%m/%Y à %H:%M:%S')}\n"
            history_text += f"[Lead → BerinIA] {message}\n\n"
        
        # Préparation des informations sur le lead pour le prompt
        lead_info_text = json.dumps(lead, indent=2, ensure_ascii=False)
        
        # Préparation des données d'analyse du site si disponibles
        site_analysis_text = ""
        if site_analysis:
            self.speak("Intégration des résultats d'analyse de site dans la réponse", target="ProspectionSupervisor")
            
            try:
                # Si c'est déjà une chaîne, l'utiliser directement
                if isinstance(site_analysis, str):
                    site_analysis_text = site_analysis
                # Sinon, formater les données d'analyse
                else:
                    site_analysis_dict = site_analysis.get("interpretation", {}) if "interpretation" in site_analysis else site_analysis
                    
                    # Extraire les informations clés
                    site_url = site_analysis_dict.get("url", "")
                    sector = site_analysis_dict.get("sector", "")
                    strengths = site_analysis_dict.get("strengths", [])
                    weaknesses = site_analysis_dict.get("weaknesses", [])
                    opportunities = site_analysis_dict.get("opportunities", [])
                    
                    # Formater le texte d'analyse
                    site_analysis_text = f"ANALYSE DU SITE:\n"
                    if site_url:
                        site_analysis_text += f"- Site: {site_url}\n"
                    if sector:
                        site_analysis_text += f"- Secteur: {sector}\n"
                    
                    if strengths:
                        site_analysis_text += "- Points forts: " + ", ".join(strengths[:3]) + "\n"
                    if weaknesses:
                        site_analysis_text += "- Points faibles: " + ", ".join(weaknesses[:3]) + "\n"
                    if opportunities:
                        site_analysis_text += "- Opportunités: " + ", ".join(opportunities[:3]) + "\n"
            except Exception as e:
                self.speak(f"Erreur lors de la préparation des données d'analyse du site: {str(e)}", 
                          target="ProspectionSupervisor")
        
        # Sélection du prompt selon le canal de communication
        if channel.lower() == "sms":
            self.speak("Utilisation du prompt optimisé pour SMS (concis)", target="ProspectionSupervisor")
            prompt_template = SMS_RESPONSE_PROMPT
        else:  # "email" ou autre
            self.speak("Utilisation du prompt optimisé pour email", target="ProspectionSupervisor")
            prompt_template = EMAIL_RESPONSE_PROMPT
        
        # Extraction de l'identité depuis la configuration
        identity = self.persona_config.get("identity", {})
        name = identity.get("name", "Louise")
        entity = identity.get("entity", "BerinIA")
        role = identity.get("role", "Assistante commerciale")
        
        # Construction du prompt avec les variables remplacées
        prompt = prompt_template.format(
            name=name,
            entity=entity,
            role=role,
            lead_info=lead_info_text,
            conversation_history=history_text,
            message_count=messages_count,
            time_description=time_description,
            is_first_message=is_first_message,
            last_message=message,
            subject=input_data.get("subject", "Votre message")
        )
        
        # Ajout des limites de communication
        comm_limits = self.persona_config.get("communication_limits", {})
        allowed_topics = comm_limits.get("allowed_topics", [])
        forbidden_topics = comm_limits.get("forbidden_topics", [])
        
        if allowed_topics:
            prompt += "\n\nSUJETS AUTORISÉS: " + ", ".join(allowed_topics)
        
        if forbidden_topics:
            prompt += "\nSUJETS INTERDITS: " + ", ".join(forbidden_topics)
        
        # Log du prompt pour debugging si nécessaire
        if self.config.get("debug_mode", False):
            self.speak(f"PROMPT: {prompt}", target="ProspectionSupervisor")
        
        # Appel au LLM avec complexité adaptée au canal
        try:
            complexity = "low" if channel.lower() == "sms" else "medium"
            response = LLMService.call_llm(prompt, complexity=complexity)
            response_text = response.strip()
            
            # Pour les SMS, vérification de longueur et avertissement si nécessaire
            if channel.lower() == "sms" and len(response_text) > 120:
                self.speak(f"Attention: Réponse SMS de {len(response_text)} caractères (>120)", target="ProspectionSupervisor")
            
            # Post-traitement pour supprimer les salutations superflues si ce n'est pas le premier message
            if not is_first_message and channel.lower() != "sms":  # Pour les emails uniquement
                # Modèles de salutations à détecter et supprimer
                greeting_patterns = [
                    r'^Bonjour.*?,\s*',
                    r'^Salut.*?,\s*',
                    r'^Cher.*?,\s*',
                    r'^Bien\s+le\s+bonjour.*?,\s*',
                    r'^Bonsoir.*?,\s*',
                    r'^Bien\s+le\s+bonsoir.*?,\s*',
                    r'^Hello.*?,\s*',
                    r'^Coucou.*?,\s*',
                ]
                
                # Appliquer les patterns pour supprimer les salutations
                for pattern in greeting_patterns:
                    response_text = re.sub(pattern, '', response_text, flags=re.IGNORECASE)
                
                # Capitaliser la première lettre si nécessaire
                if response_text and not response_text[0].isupper() and len(response_text) > 1:
                    response_text = response_text[0].upper() + response_text[1:]
            
            return response_text
        except Exception as e:
            self.speak(f"Erreur lors de la génération de réponse contextuelle: {str(e)}", target="ProspectionSupervisor")
            
            # Fallback: réponse générique adaptée selon le contexte et le canal
            if channel.lower() == "sms":
                if is_first_message:
                    return f"Bonjour! Merci pour votre message. Comment puis-je vous aider?"
                else:
                    return f"Merci pour votre message. Je vous réponds dès que possible."
            else:  # email
                if is_first_message:
                    return f"Bonjour,\n\nMerci pour votre message. Je suis {name} de {entity}. Je vais traiter votre demande dans les plus brefs délais.\n\nCordialement,\n{name}"
                else:
                    return f"Merci pour votre message.\n\nJe prends note de vos informations et reviendrai vers vous rapidement.\n\nCordialement,\n{name}"
    
    def send_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère et envoie une réponse à un message reçu d'un lead
        
        Args:
            input_data: Données d'entrée avec les informations du lead et du message
            
        Returns:
            Résultat de l'envoi
        """
        # Extraction des données nécessaires
        lead = input_data.get("lead_data", {})
        message = input_data.get("message", "")
        campaign_id = input_data.get("campaign_id", "")
        channel = input_data.get("channel", "sms")  # Par défaut, on répond par SMS
        
        if not lead:
            return {
                "status": "error",
                "message": "Données du lead manquantes"
            }
        
        if not message:
            return {
                "status": "error",
                "message": "Message du lead manquant"
            }
        
        # Génération d'une réponse contextuelle
        self.speak(f"Génération d'une réponse pour le lead {lead.get('lead_id', '')}", target="ProspectionSupervisor")
        response_content = self.generate_contextual_response(input_data)
        
        # Préparation des données du message
        message_data = {
            "content": response_content,
            "template_id": "contextual_response"
        }
        
        # Envoi de la réponse selon le canal approprié
        if channel == "email":
            # Ajout d'un sujet pour les emails
            message_data["subject"] = f"Re: {input_data.get('subject', 'Votre message')}"
            success, error = self._send_email(lead, message_data, campaign_id)
        else:  # Par défaut, on utilise le SMS
            success, error = self._send_sms(lead, message_data, campaign_id)
        
        if success:
            # Enregistrement du message envoyé
            message_id = self._save_message_to_db(lead, message_data, campaign_id, channel)
            
            self.speak(f"Réponse envoyée avec succès au lead {lead.get('lead_id', '')}", target="ProspectionSupervisor")
            
            return {
                "status": "success",
                "message": "Réponse envoyée avec succès",
                "message_id": message_id,
                "content": response_content
            }
        else:
            self.speak(f"Échec de l'envoi de la réponse: {error}", target="ProspectionSupervisor")
            
            return {
                "status": "error",
                "message": f"Échec de l'envoi de la réponse: {error}"
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
        
        if action == "send_messages":
            return self.send_messages(input_data)
        
        elif action == "send_email":
            # Récupération des paramètres
            to = input_data.get("parameters", {}).get("to")
            subject = input_data.get("parameters", {}).get("subject", "")
            body = input_data.get("parameters", {}).get("body", "")
            
            if not to:
                return {"status": "error", "message": "Destinataire (to) manquant"}
            
            # Création d'un lead temporaire
            temp_lead = {
                "lead_id": str(uuid.uuid4()),
                "email": to,
                "first_name": "Destinataire",
                "last_name": "Test",
                "company": "Test Company"
            }
            
            # Création d'un message temporaire
            temp_message_data = {
                "subject": subject,
                "content": body,
                "template_id": "direct_email"
            }
            
            # Envoi de l'email
            success, error = self._send_email(temp_lead, temp_message_data, "direct_email_campaign")
            
            if success:
                return {"status": "success", "message": f"Email envoyé à {to}"}
            else:
                return {"status": "error", "message": f"Échec de l'envoi: {error}"}
        
        elif action == "send_sms":
            # Récupération des paramètres
            phone_number = input_data.get("parameters", {}).get("phone_number")
            message = input_data.get("parameters", {}).get("message", "")
            
            if not phone_number:
                return {"status": "error", "message": "Numéro de téléphone manquant"}
            
            # Vérification du format du numéro (doit commencer par +)
            if not phone_number.startswith('+'):
                phone_number = '+' + phone_number
            
            # Création d'un lead temporaire
            temp_lead = {
                "lead_id": str(uuid.uuid4()),
                "phone": phone_number,
                "first_name": "Destinataire",
                "last_name": "Test",
                "company": "Test Company"
            }
            
            # Création d'un message temporaire
            temp_message_data = {
                "content": message,
                "template_id": "direct_sms"
            }
            
            # Envoi du SMS
            success, error = self._send_sms(temp_lead, temp_message_data, "direct_sms_campaign")
            
            if success:
                return {"status": "success", "message": f"SMS envoyé à {phone_number}"}
            else:
                return {"status": "error", "message": f"Échec de l'envoi: {error}"}
        
        elif action == "get_templates":
            return self.get_templates(input_data)
        
        elif action == "get_stats":
            return self.get_messaging_stats()
            
        elif action == "send_response":
            # Envoi d'une réponse à un message reçu
            return self.send_response(input_data)
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du MessagingAgent
    agent = MessagingAgent()
    
    # Test de l'agent en mode test
    test_lead = {
        "lead_id": "1",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@company.com",
        "position": "CEO",
        "company": "Test Company",
        "industry": "Technology"
    }
    
    result = agent.run({
        "action": "send_messages",
        "leads": [test_lead],
        "campaign_id": "test_campaign",
        "template_id": "template_initial"
    })
    
    print(json.dumps(result, indent=2))

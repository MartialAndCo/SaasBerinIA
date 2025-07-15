"""
Module du MessagingAgent - Agent d'envoi de messages aux leads
"""
import os
import json
import re
from typing import Dict, Any, Optional, List, Tuple
import datetime
import uuid
import hashlib
import time
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client  # SDK Twilio pour SMS
from pathlib import Path

from core.agent_base import Agent
from utils.llm import LLMService
from core.db import DatabaseService
from utils.smtp_rotation_manager import SMTPRotationManager  # Gestionnaire de rotation SMTP

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
        Charge les directives depuis l'API au lieu des templates locaux
        
        Returns:
            Dictionnaire vide (les directives sont chargées dynamiquement)
        """
        self.speak("Système de directives API activé - templates chargés dynamiquement", target="ProspectionSupervisor")
        return {}  # Templates locaux désactivés, utilisation des directives API
    
    def _get_directives(self) -> Dict[str, str]:
        """
        Récupère les directives depuis l'API messenger
        
        Returns:
            Dictionnaire avec sms_instructions et email_instructions
        """
        self.speak("DÉBUT _get_directives() - TEST FORCÉ", target="ProspectionSupervisor")
        try:
            import requests
            self.speak("Appel HTTP vers API directives...", target="ProspectionSupervisor")
            response = requests.get("http://localhost:8000/api/messenger/directives", timeout=10)
            
            if response.status_code == 200:
                directives = response.json()
                self.speak(f"SUCCESS: Directives API récupérées - SMS: {len(directives.get('sms_instructions', ''))} chars, Email: {len(directives.get('email_instructions', ''))} chars", target="ProspectionSupervisor")
                return directives
            else:
                self.speak(f"ERREUR: API directives status {response.status_code}", target="ProspectionSupervisor")
                return self._get_fallback_directives()
                
        except Exception as e:
            self.speak(f"EXCEPTION: Erreur connexion API directives: {str(e)}", target="ProspectionSupervisor")
            return self._get_fallback_directives()
    
    def _get_fallback_directives(self) -> Dict[str, str]:
        """
        Directives de fallback si l'API n'est pas disponible
        """
        return {
            "sms_instructions": "Tu es Louise de BerinIA. Réponds de manière concise et professionnelle.",
            "email_instructions": "Tu es Louise de BerinIA. Répondez de manière professionnelle avec signature.",
            "email_subject_instructions": "Génère un objet d'email professionnel et personnalisé (max 60 caractères)."
        }
    
    def _init_email_client(self):
        """
        Initialise le client d'envoi d'emails (SMTP Mailcheap)
        """
        # Configuration email depuis config ou variables d'environnement
        email_config = self.config.get("email", {})
        
        self.email_service = email_config.get("service", "mailcheap_smtp")
        
        if self.email_service == "mailcheap_smtp":
            # Récupérer les configurations SMTP
            smtp_accounts = email_config.get("smtp_accounts", [])
            
            if not smtp_accounts:
                self.speak("Aucun compte SMTP configuré. L'envoi d'emails échouera.", target="ProspectionSupervisor")
                return
            
            # Initialisation du gestionnaire de rotation SMTP
            test_mode = self.config.get("test_mode", False)
            self.smtp_rotation_manager = SMTPRotationManager(smtp_accounts, test_mode=test_mode)
            
            # Vérifier qu'au moins un compte est disponible
            available_accounts = self.smtp_rotation_manager.get_available_accounts()
            if available_accounts:
                self.speak(f"Gestionnaire SMTP initialisé avec {len(available_accounts)} compte(s) (test_mode: {test_mode})", target="ProspectionSupervisor")
            else:
                self.speak("Aucun compte SMTP disponible. Vérifiez les variables d'environnement.", target="ProspectionSupervisor")
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
        
        # Vérification que les directives API sont disponibles
        directives = self._get_directives()
        if not directives:
            return {
                "status": "error",
                "message": "Directives API non disponibles",
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
                # Génération du message personnalisé avec les directives API
                message_data = self._generate_message(lead, template_id, campaign_id, channel)
                
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
                        "lead_id": lead.get("id", lead.get("lead_id", "")),
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
            "campaign_id": 1,
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
    
    def _generate_message(self, lead: Dict[str, Any], template_id: str, campaign_id: str, channel: str = "email") -> Optional[Dict[str, Any]]:
        """
        Génère un message personnalisé pour un lead en utilisant les directives API
        
        Args:
            lead: Le lead à contacter
            template_id: Ignoré (legacy) - utilise maintenant les directives API
            campaign_id: L'ID de la campagne
            channel: Canal de communication (email ou sms)
            
        Returns:
            Message personnalisé ou None en cas d'erreur
        """
        try:
            # Récupération des directives depuis l'API
            directives = self._get_directives()
            
            if channel == "sms":
                instructions = directives.get("sms_instructions", "")
            else:  # email par défaut
                instructions = directives.get("email_instructions", "")
            
            if not instructions:
                self.speak(f"Directives {channel} non trouvées", target="ProspectionSupervisor")
                return None
            
            # Génération du message avec LLM basé sur les directives
            personalized_content = self._personalize_with_directives(lead, instructions, campaign_id, channel)
            
            # Sujet pour les emails (généré dynamiquement)
            if channel == "email":
                subject = self._generate_subject_with_llm(lead, campaign_id)
            else:
                subject = ""  # Pas de sujet pour SMS
            
            return {
                "subject": subject,
                "content": personalized_content
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
    
    def _personalize_with_directives(self, lead: Dict[str, Any], instructions: str, campaign_id: str, channel: str) -> str:
        """
        Génère un message personnalisé basé sur les directives API
        
        Args:
            lead: Le lead à contacter
            instructions: Les directives depuis l'API
            campaign_id: L'ID de la campagne
            channel: Canal de communication (email ou sms)
            
        Returns:
            Contenu du message personnalisé
        """
        prompt = f"""
        DIRECTIVES DE MESSAGERIE:
        {instructions}
        
        INFORMATIONS DU LEAD:
        {json.dumps(lead, indent=2)}
        
        CAMPAGNE ID: {campaign_id}
        CANAL: {channel}
        
        INSTRUCTIONS SPÉCIALES:
        1. Suis EXACTEMENT les directives ci-dessus
        2. Personnalise le message pour ce lead spécifique
        3. Utilise les informations du lead (nom, entreprise, secteur)
        4. Assure-toi que le message respecte les règles de continuité conversationnelle si mentionnées
        5. Pour les SMS: reste sous 160 caractères
        6. Pour les emails: structure professionnelle complète
        
        RÉPONDS UNIQUEMENT AVEC LE MESSAGE PERSONNALISÉ, SANS COMMENTAIRES.
        """
        
        try:
            response = LLMService.call_llm(prompt, complexity="medium")
            self.speak(f"Message {channel} généré via directives API", target="ProspectionSupervisor")
            return response.strip()
        except Exception as e:
            self.speak(f"Erreur LLM directives: {str(e)}", target="ProspectionSupervisor")
            
            # Fallback simple
            lead_name = lead.get("first_name", lead.get("name", ""))
            if channel == "sms":
                return f"Bonjour {lead_name}, Louise de BerinIA. Nous automatisons les processus pour TPE/PME. Intéressé ?"
            else:
                return f"Bonjour {lead_name},\n\nJe suis Louise de BerinIA.\n\nCordialement,\nLouise"
    
    def _generate_subject_with_llm(self, lead: Dict[str, Any], campaign_id: str) -> str:
        """
        Génère un sujet d'email personnalisé en utilisant les directives API
        
        Args:
            lead: Le lead à contacter
            campaign_id: L'ID de la campagne
            
        Returns:
            Sujet personnalisé
        """
        # Récupérer les directives d'objet depuis l'API
        directives = self._get_directives()
        subject_instructions = directives.get("email_subject_instructions", "")
        
        if not subject_instructions:
            # Fallback si pas de directives d'objet
            subject_instructions = """Génère un objet d'email professionnel et personnalisé.
            Maximum 60 caractères, engageant mais pas trop commercial."""
        
        prompt = f"""
        {subject_instructions}
        
        INFORMATIONS DU LEAD:
        {json.dumps(lead, indent=2)}
        
        CAMPAGNE: {campaign_id}
        
        RÉPONDS UNIQUEMENT AVEC L'OBJET, SANS GUILLEMETS NI EXPLICATIONS.
        """
        
        try:
            response = LLMService.call_llm(prompt, complexity="low")
            # Nettoyer la réponse des guillemets et limiter à 60 caractères
            subject = response.strip().replace('"', '').replace("'", "")
            if len(subject) > 60:
                subject = subject[:57] + "..."
            return subject
        except Exception as e:
            self.speak(f"Erreur génération sujet avec directives: {str(e)}", target="ProspectionSupervisor")
            
            # Fallback
            first_name = lead.get("first_name", lead.get("prenom", ""))
            company = lead.get("company", lead.get("entreprise", ""))
            
            if company:
                return f"Un petit mot pour {company}"
            elif first_name:
                return f"Solution automatisation pour {first_name}"
            else:
                return "Optimisez vos processus avec BerinIA"
    
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
        
        # Debug : vérifier le campaign_id reçu
        self.speak(f"DEBUG: Envoi email à {recipient_email} avec campaign_id: '{campaign_id}' (type: {type(campaign_id)})", target="ProspectionSupervisor")
        
        # Envoi selon le service configuré
        if self.email_service == "mailcheap_smtp":
            return self._send_email_smtp(recipient_email, subject, content, campaign_id, lead)
        else:
            return False, f"Service email non supporté: {self.email_service}"
    
    def _send_email_smtp(self, recipient: str, subject: str, html_content: str, campaign_id: str, lead: Dict[str, Any] = None) -> tuple[bool, str]:
        """
        Envoie un email via SMTP Mailcheap avec rotation des comptes
        
        Args:
            recipient: L'email du destinataire
            subject: Le sujet du message
            html_content: Le corps du message HTML
            campaign_id: L'ID de la campagne BerinIA
            lead: Données du lead (optionnel) pour les variables personnalisées
            
        Returns:
            Tuple (succès, erreur)
        """
        # Vérification du mode test
        test_mode = self.config.get("test_mode", False)
        if test_mode:
            self.speak(f"[MODE TEST] Email simulé envoyé à {recipient}", target="ProspectionSupervisor")
            time.sleep(0.1)  # Légère pause pour simuler l'envoi
            return True, ""
        
        # Sélectionner le compte SMTP avec rotation
        lead_id = lead.get("id", lead.get("lead_id", "")) if lead else ""
        smtp_config = self.smtp_rotation_manager.select_smtp_config_for_campaign(str(lead_id))
        
        if not smtp_config:
            return False, "Aucun compte SMTP disponible"
        
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_config['from_email']
            msg['To'] = recipient
            
            # Partie HTML
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Partie texte (optionnel)
            text_content = re.sub(r'<[^>]+>', '', html_content)  # Supprime les balises HTML
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)
            
            # Connexion SMTP sécurisée
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                server.starttls(context=context)
                server.login(smtp_config['user'], smtp_config['password'])
                server.send_message(msg)
            
            self.speak(f"Email envoyé via SMTP à {recipient} depuis {smtp_config['from_email']}", target="ProspectionSupervisor")
            return True, ""
            
        except Exception as e:
            error_msg = f"Erreur SMTP: {str(e)}"
            self.speak(error_msg, target="ProspectionSupervisor")
            return False, error_msg
    
    def _send_reply_smtp(self, lead: Dict[str, Any], message_data: Dict[str, Any], campaign_id: str) -> tuple[bool, str]:
        """
        Envoie une réponse via SMTP en utilisant le même email que l'envoi initial
        
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
        
        # Récupérer la configuration SMTP utilisée pour l'envoi initial
        lead_id = lead.get("id", lead.get("lead_id", ""))
        smtp_config = self.smtp_rotation_manager.get_smtp_config_for_reply(str(lead_id))
        
        if not smtp_config:
            self.speak(f"Aucune config SMTP trouvée pour réponse, utilisation d'un nouveau compte", target="ProspectionSupervisor")
            # Fallback : utiliser la méthode standard qui sélectionne un compte
            return self._send_email_smtp(recipient_email, subject, content, campaign_id, lead)
        
        try:
            # Créer le message de réponse
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_config['from_email']
            msg['To'] = recipient_email
            
            # Partie HTML
            html_part = MIMEText(content, 'html')
            msg.attach(html_part)
            
            # Partie texte
            text_content = re.sub(r'<[^>]+>', '', content)
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)
            
            # Connexion SMTP sécurisée
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                server.starttls(context=context)
                server.login(smtp_config['user'], smtp_config['password'])
                server.send_message(msg)
            
            self.speak(f"Réponse envoyée via SMTP à {recipient_email} depuis {smtp_config['from_email']}", target="ProspectionSupervisor")
            return True, ""
            
        except Exception as e:
            error_msg = f"Erreur SMTP réponse: {str(e)}"
            self.speak(error_msg, target="ProspectionSupervisor")
            return False, error_msg
    
    def _send_email_instantly(self, recipient: str, subject: str, body: str, campaign_id: str, lead: Dict[str, Any] = None) -> tuple[bool, str]:
        """
        DEPRECATED: Méthode obsolète pour Instantly.ai
        Redirige vers _send_email_smtp pour compatibilité
        """
        self.speak(f"DEPRECATED: _send_email_instantly redirigé vers SMTP pour {recipient}", target="ProspectionSupervisor")
        return self._send_email_smtp(recipient, subject, body, campaign_id, lead)
    
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
    

    def _get_or_create_thread_id(self, lead: Dict[str, Any]) -> str:
        """
        Récupère ou crée un thread_id pour un lead
        
        Args:
            lead: Le lead à contacter
            
        Returns:
            thread_id unique pour ce lead
        """
        lead_email = lead.get("email", "")
        lead_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
        
        # Vérifier s'il existe déjà des messages pour ce lead
        if lead.get("lead_id"):
            try:
                # Chercher un thread_id existant pour ce lead
                existing_thread = self.db.fetch_one(
                    "SELECT DISTINCT thread_id FROM messages WHERE lead_id = %s AND thread_id IS NOT NULL LIMIT 1",
                    (lead["lead_id"],)
                )
                
                if existing_thread and existing_thread.get("thread_id"):
                    return existing_thread["thread_id"]
            except Exception as e:
                self.speak(f"Erreur lors de la recherche de thread_id existant: {str(e)}", target="ProspectionSupervisor")
        
        # Générer un nouveau thread_id basé sur l'email ou le nom
        base = (lead_email or lead_name or "unknown").lower()
        thread_id = "thread_" + hashlib.md5(base.encode()).hexdigest()[:8]
        
        self.speak(f"Nouveau thread_id généré: {thread_id} pour {lead_name} ({lead_email})", target="ProspectionSupervisor")
        return thread_id

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
        
        # Log très visible pour identifier la version utilisée
        self.speak("NOUVELLE VERSION _save_message_to_db UTILISÉE - STRUCTURE CORRIGÉE", target="ProspectionSupervisor")
        
        try:
            # Récupérer les informations de la campagne si campaign_id est fourni
            campaign_name = ""
            if campaign_id:
                try:
                    campaign_query = "SELECT name FROM campaigns WHERE id = :campaign_id"
                    campaign_result = self.db.fetch_one(campaign_query, {"campaign_id": int(campaign_id)})
                    if campaign_result:
                        campaign_name = campaign_result.get("name", "")
                except:
                    pass
            
            # Insertion dans la base de données avec la structure correcte
            message_record = {
                "lead_id": lead.get("id", lead.get("lead_id", "")),
                "lead_name": lead.get("first_name", "") + " " + lead.get("last_name", ""),
                "lead_email": lead.get("email", ""),
                "campaign_id": int(campaign_id) if campaign_id and str(campaign_id).isdigit() else None,
                "campaign_name": campaign_name,
                "subject": message_data.get("subject", ""),
                "content": message_data.get("content", ""),
                "status": "sent",
                "type": "outbound",
                "sent_date": datetime.datetime.now(),
                "direction": "outbound",
                "sender_type": "agent",
                "message_type": channel,
                "sender_name": "BerinIA Bot",
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now()
            }
            
            # Selon le mode de fonctionnement (test ou production)
            test_mode = self.config.get("test_mode", False)  # Défaut False pour mode production
            if not test_mode:
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
        lead_id = lead.get("id", lead.get("lead_id", ""))
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
        message_id = input_data.get("message_id")  # ID du message original pour les réponses par email
        
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
            "content": response_content
        }
        
        # Envoi de la réponse selon le canal approprié
        if channel == "email":
            # Ajout d'un sujet pour les emails
            message_data["subject"] = f"Re: {input_data.get('subject', 'Votre message')}"
            
            # Debug des conditions pour reply_to_email
            test_mode = self.config.get("test_mode", False)  # Défaut False pour mode production
            self.speak(f"DEBUG send_response: message_id={message_id}, email_service={self.email_service}, test_mode={test_mode}", target="ProspectionSupervisor")
            
            # Utiliser le même email que l'envoi initial pour les réponses
            if self.email_service == "mailcheap_smtp" and not test_mode:
                # Utiliser la méthode de réponse SMTP pour maintenir la cohérence
                success, error = self._send_reply_smtp(lead, message_data, campaign_id)
            else:
                # Méthode standard d'envoi
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
                "content": body
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
                "content": message
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

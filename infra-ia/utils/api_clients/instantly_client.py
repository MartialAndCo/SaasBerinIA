"""
Module client pour l'API Instantly.ai
"""
import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import requests
from datetime import datetime

# Configuration du logging
logger = logging.getLogger("BerinIA-InstantlyClient")

class InstantlyClient:
    """
    Client pour l'API Instantly.ai
    
    Cette classe fournit des méthodes pour :
    - Authentification à l'API Instantly
    - Envoi d'emails
    - Vérification des emails
    - Récupération des statistiques
    - Gestion des réponses via webhook
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.instantly.ai/api/v2/"):
        """
        Initialisation du client Instantly
        
        Args:
            api_key: Clé API Instantly.ai (si None, recherche dans les variables d'environnement)
            base_url: URL de base de l'API Instantly
        """
        self.api_key = api_key or os.getenv("INSTANTLY_API_KEY", "")
        if not self.api_key:
            logger.warning("Aucune clé API Instantly.ai trouvée. L'authentification échouera.")
            
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Statistiques d'utilisation
        self.rate_limit_remaining = 600  # Limite par défaut (600 requêtes par minute)
        self.last_reset_time = datetime.now()
        self.retry_count = 0
        self.max_retries = 5
        
        logger.info("Initialisation du client Instantly.ai")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Gère la réponse de l'API, y compris les erreurs et le rate limiting.
        
        Args:
            response: Objet réponse de requests
            
        Returns:
            Données de la réponse
            
        Raises:
            Exception: En cas d'erreur de l'API après les tentatives de retry
        """
        if response.status_code == 200:
            # Réinitialisation du compteur de retry en cas de succès
            self.retry_count = 0
            return response.json()
            
        elif response.status_code == 429:
            # Rate limit atteint
            self.retry_count += 1
            if self.retry_count > self.max_retries:
                logger.error(f"Rate limit dépassé après {self.max_retries} tentatives")
                raise Exception(f"Rate limit dépassé: {response.text}")
                
            # Backoff exponentiel (1s, 2s, 4s, 8s, 16s)
            wait_time = 2 ** (self.retry_count - 1)
            logger.warning(f"Rate limit atteint, attente de {wait_time}s avant nouvel essai")
            time.sleep(wait_time)
            
            # Récursion pour réessayer
            return self._make_request(
                response.request.method, 
                response.request.url.replace(self.base_url, ""), 
                json.loads(response.request.body) if response.request.body else None
            )
            
        elif response.status_code == 401:
            logger.error("Authentification échouée: clé API invalide ou expirée")
            raise Exception(f"Erreur d'authentification: {response.text}")
            
        else:
            # Autres erreurs
            logger.error(f"Erreur API ({response.status_code}): {response.text}")
            raise Exception(f"Erreur API ({response.status_code}): {response.text}")

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une requête à l'API Instantly avec gestion d'erreurs et retry.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Point de terminaison de l'API (sans le base_url)
            data: Données à envoyer (pour POST, PATCH, etc.)
            
        Returns:
            Données de la réponse
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            logger.error(f"Erreur de connexion: {str(e)}")
            raise Exception(f"Erreur de connexion: {str(e)}")

    def send_email(self, recipient: str, subject: str, html_content: str, 
                  from_email: Optional[str] = None, campaign_id: Optional[str] = None,
                  tracking_id: Optional[str] = None, custom_variables: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Envoie un email via l'API Instantly
        
        Args:
            recipient: Adresse email du destinataire
            subject: Sujet de l'email
            html_content: Contenu HTML de l'email
            from_email: Adresse email de l'expéditeur (optionnel, utilisera le compte Instantly par défaut)
            campaign_id: ID de la campagne (optionnel)
            tracking_id: ID de suivi personnalisé (optionnel)
            custom_variables: Variables personnalisées pour le suivi (optionnel)
            
        Returns:
            Réponse de l'API avec les détails de l'envoi
        """
        # Si from_email est fourni, vérifie que c'est un compte valide dans Instantly
        account_email = None
        if from_email:
            account_email = self._validate_account(from_email)
        
        # Si aucun compte n'est trouvé ou disponible, utiliser un compte par défaut
        if not account_email:
            accounts = self.list_accounts(limit=1, status=1)  # status=1 = Active
            if accounts and accounts.get("items", []):
                account_email = accounts["items"][0].get("email")
            else:
                raise Exception("Aucun compte email actif disponible dans Instantly")
        
        # Construction de la requête pour envoyer l'email
        # Utilise l'API emails/reply car elle permet l'envoi d'emails directs
        # Même si ce n'est pas une réponse à proprement parler
        email_data = {
            "eaccount": account_email,
            "to": recipient,
            "subject": subject,
            "body": {
                "html": html_content,
                "text": self._html_to_text(html_content)
            }
        }
        
        # Ajout des données de tracking si fournies
        if campaign_id:
            email_data["campaign_id"] = campaign_id
        
        if tracking_id:
            email_data["metadata"] = {"tracking_id": tracking_id}
        
        if custom_variables:
            if "metadata" not in email_data:
                email_data["metadata"] = {}
            email_data["metadata"].update(custom_variables)
        
        # Envoi de l'email
        return self._make_request("POST", "emails/send", email_data)

    def reply_to_email(self, reply_to_uuid: str, subject: str, html_content: str, 
                      from_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Répond à un email reçu via l'API Instantly
        
        Args:
            reply_to_uuid: UUID de l'email auquel répondre
            subject: Sujet de la réponse
            html_content: Contenu HTML de la réponse
            from_email: Adresse email de l'expéditeur (optionnel)
            
        Returns:
            Réponse de l'API avec les détails de l'envoi
        """
        # Si from_email est fourni, vérifie que c'est un compte valide dans Instantly
        account_email = None
        if from_email:
            account_email = self._validate_account(from_email)
        
        # Si aucun compte n'est trouvé, récupérer l'email associé à l'email d'origine
        if not account_email:
            try:
                email_info = self._make_request("GET", f"emails/{reply_to_uuid}")
                account_email = email_info.get("eaccount")
            except Exception:
                # Si impossible de récupérer l'email, utiliser un compte par défaut
                accounts = self.list_accounts(limit=1, status=1)
                if accounts and accounts.get("items", []):
                    account_email = accounts["items"][0].get("email")
                else:
                    raise Exception("Aucun compte email pour répondre")
        
        # Construction de la requête pour envoyer la réponse
        reply_data = {
            "reply_to_uuid": reply_to_uuid,
            "eaccount": account_email,
            "subject": subject,
            "body": {
                "html": html_content,
                "text": self._html_to_text(html_content)
            }
        }
        
        # Envoi de la réponse
        return self._make_request("POST", "emails/reply", reply_data)

    def list_accounts(self, limit: int = 100, search: Optional[str] = None, 
                     status: Optional[int] = None) -> Dict[str, Any]:
        """
        Liste les comptes email disponibles dans Instantly
        
        Args:
            limit: Nombre maximum de comptes à retourner (max 100)
            search: Filtre de recherche par texte
            status: Filtre par statut (1=Active, 2=Paused)
            
        Returns:
            Liste des comptes correspondants aux critères
        """
        params = {"limit": limit}
        
        if search:
            params["search"] = search
        
        if status is not None:
            params["status"] = status
        
        # Construction de l'URL avec paramètres de requête
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"accounts?{query_string}"
        
        return self._make_request("GET", endpoint)

    def _validate_account(self, email: str) -> Optional[str]:
        """
        Vérifie si un compte email existe dans Instantly et est actif
        
        Args:
            email: Adresse email à vérifier
            
        Returns:
            L'adresse email si elle est valide, None sinon
        """
        try:
            account = self._make_request("GET", f"accounts/{email}")
            if account and account.get("status") == 1:  # Active
                return email
            else:
                logger.warning(f"Le compte {email} existe mais n'est pas actif")
                return None
        except Exception:
            logger.warning(f"Le compte {email} n'existe pas dans Instantly")
            return None

    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Vérifie la validité d'une adresse email
        
        Args:
            email: Adresse email à vérifier
            
        Returns:
            Résultat de la vérification
        """
        return self._make_request("POST", "email-verification", {"email": email})

    def get_email_status(self, email: str) -> Dict[str, Any]:
        """
        Récupère le statut de vérification d'une adresse email
        
        Args:
            email: Adresse email dont on veut le statut
            
        Returns:
            Statut de vérification de l'email
        """
        return self._make_request("GET", f"email-verification/{email}")

    def list_emails(self, campaign_id: Optional[str] = None, 
                   is_unread: bool = False, limit: int = 10) -> Dict[str, Any]:
        """
        Liste les emails reçus
        
        Args:
            campaign_id: Filtre par ID de campagne
            is_unread: Filtre pour n'afficher que les emails non lus
            limit: Nombre maximum d'emails à retourner
            
        Returns:
            Liste des emails correspondants aux critères
        """
        params = {"limit": limit}
        
        if campaign_id:
            params["campaign_id"] = campaign_id
        
        if is_unread:
            params["is_unread"] = "true"
        
        # Construction de l'URL avec paramètres de requête
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"emails?{query_string}"
        
        return self._make_request("GET", endpoint)

    def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une campagne
        
        Args:
            campaign_id: ID de la campagne
            
        Returns:
            Statistiques de la campagne
        """
        return self._make_request("GET", f"campaigns/analytics?id={campaign_id}")

    def get_daily_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Récupère les statistiques journalières d'une campagne
        
        Args:
            campaign_id: ID de la campagne
            
        Returns:
            Statistiques journalières de la campagne
        """
        return self._make_request("GET", f"campaigns/analytics/daily?campaign_id={campaign_id}")

    def mark_as_read(self, thread_id: str) -> Dict[str, Any]:
        """
        Marque un thread de messages comme lu
        
        Args:
            thread_id: ID du thread
            
        Returns:
            Résultat de l'opération
        """
        return self._make_request("POST", f"emails/threads/{thread_id}/mark-as-read")

    def _html_to_text(self, html: str) -> str:
        """
        Convertit un contenu HTML en texte brut (version simplifiée)
        
        Args:
            html: Contenu HTML à convertir
            
        Returns:
            Version texte du contenu HTML
        """
        # Version basique pour extraire le texte du HTML
        # Pour une version plus avancée, on pourrait utiliser BeautifulSoup ou html2text
        import re
        
        # Supprimer les balises HTML
        text = re.sub(r'<[^>]*>', ' ', html)
        
        # Remplacer les entités HTML courantes
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Nettoyer les espaces en double et les sauts de ligne
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse un payload webhook d'Instantly pour en extraire les informations clés
        
        Args:
            payload: Payload webhook reçu d'Instantly
            
        Returns:
            Données structurées extraites du webhook
        """
        event_type = payload.get("event_type", "unknown")
        
        # Structure de base des données extraites
        webhook_data = {
            "event_type": event_type,
            "timestamp": payload.get("timestamp"),
            "campaign_id": payload.get("campaign_id"),
            "campaign_name": payload.get("campaign_name"),
            "lead_email": payload.get("lead_email"),
            "email_account": payload.get("email_account"),
            "raw_data": payload
        }
        
        # Extraction des données spécifiques selon le type d'événement
        if event_type == "reply_received":
            # Pour les réponses, on extrait le contenu si disponible
            if "reply_content" in payload:
                webhook_data["content"] = payload["reply_content"]
            
            # ID du message pour permettre de répondre
            if "message_id" in payload:
                webhook_data["message_id"] = payload["message_id"]
        
        return webhook_data

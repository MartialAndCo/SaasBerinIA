"""
Module du FollowUpAgent - Agent qui gère les relances automatiques
"""
import os
import json
from typing import Dict, Any, Optional, List
import datetime
import time
import uuid

from core.agent_base import Agent
from utils.llm import LLMService
from core.db import DatabaseService

class FollowUpAgent(Agent):
    """
    FollowUpAgent - Agent responsable des relances automatiques
    
    Cet agent est responsable de:
    - Gérer les relances selon un scénario dynamique
    - Adapter le rythme selon le niveau de réponse
    - Déterminer le moment optimal pour relancer chaque lead
    - Créer des séquences de relance personnalisées
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du FollowUpAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("FollowUpAgent", config_path)
        
        # État de l'agent
        self.follow_up_stats = {
            "total_follow_ups_sent": 0,
            "campaigns_active": 0,
            "leads_in_sequences": 0,
            "conversion_after_follow_up": 0
        }
        
        # Initialisation de la connexion à la base de données
        self.db = DatabaseService()
        
        # Chargement des séquences de relance
        self.sequences = self.config.get("sequences", {})
        
        # Chargement des règles de timing
        self.timing_rules = self.config.get("timing_rules", {})
    
    def send_follow_ups(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie des relances aux leads qui n'ont pas répondu
        
        Args:
            input_data: Données d'entrée avec les paramètres des relances
            
        Returns:
            Résultat de l'envoi des relances
        """
        campaign_id = input_data.get("campaign_id", "")
        template_id = input_data.get("template_id", "")
        days_since_last = input_data.get("days_since_last", 7)
        max_follow_ups = input_data.get("max_follow_ups", 3)
        
        if not campaign_id:
            return {
                "status": "error",
                "message": "ID de campagne requis"
            }
        
        if not template_id:
            return {
                "status": "error",
                "message": "ID de template requis"
            }
        
        self.speak(f"Préparation des relances pour la campagne '{campaign_id}'", target="ProspectionSupervisor")
        
        # Récupération des leads à relancer
        try:
            leads_to_follow_up = self._get_leads_to_follow_up(campaign_id, days_since_last, max_follow_ups)
            
            if not leads_to_follow_up:
                self.speak(f"Aucun lead à relancer pour la campagne '{campaign_id}'", target="ProspectionSupervisor")
                
                return {
                    "status": "success",
                    "campaign_id": campaign_id,
                    "message": "Aucun lead à relancer",
                    "sent_follow_ups": [],
                    "skipped_follow_ups": []
                }
            
            self.speak(f"Préparation de {len(leads_to_follow_up)} relances", target="ProspectionSupervisor")
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des leads à relancer: {str(e)}"
            self.speak(error_msg, target="ProspectionSupervisor")
            
            return {
                "status": "error",
                "message": error_msg
            }
        
        # Envoi des relances via le MessagingAgent
        from agents.overseer.overseer_agent import OverseerAgent
        overseer = OverseerAgent()
        
        # Construction de la liste de leads à relancer
        leads = [lead["lead_data"] for lead in leads_to_follow_up]
        
        # Appel au MessagingAgent
        messaging_result = overseer.execute_agent("MessagingAgent", {
            "action": "send_messages",
            "leads": leads,
            "campaign_id": campaign_id,
            "template_id": template_id
        })
        
        if messaging_result.get("status") != "success":
            self.speak(f"Erreur lors de l'envoi des relances: {messaging_result.get('message')}", target="ProspectionSupervisor")
            return messaging_result
        
        # Récupération des résultats d'envoi
        sent_messages = messaging_result.get("sent_messages", [])
        failed_messages = messaging_result.get("failed_messages", [])
        
        # Mise à jour des statistiques
        self.follow_up_stats["total_follow_ups_sent"] += len(sent_messages)
        
        # Mise à jour des données de suivi pour les relances envoyées
        for message in sent_messages:
            lead_id = message.get("lead_id", "")
            if lead_id:
                # Trouver le lead correspondant dans la liste
                lead_sequence = next((item for item in leads_to_follow_up if item["lead_data"].get("lead_id") == lead_id), None)
                
                if lead_sequence:
                    # Mise à jour du compteur de relances
                    follow_up_count = lead_sequence.get("follow_up_count", 0) + 1
                    
                    # Enregistrement de la relance
                    self._update_follow_up_status(
                        lead_id=lead_id,
                        campaign_id=campaign_id,
                        follow_up_count=follow_up_count,
                        template_id=template_id,
                        message_id=message.get("message_id", "")
                    )
        
        # Log des résultats
        self.speak(
            f"Relances envoyées: {len(sent_messages)} succès, {len(failed_messages)} échecs",
            target="ProspectionSupervisor"
        )
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "template_id": template_id,
            "sent_follow_ups": sent_messages,
            "failed_follow_ups": failed_messages,
            "stats": {
                "sent": len(sent_messages),
                "failed": len(failed_messages)
            }
        }
    
    def send_custom_follow_up(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie une relance personnalisée à un lead spécifique
        
        Args:
            input_data: Données d'entrée avec le lead et le template
            
        Returns:
            Résultat de l'envoi de la relance
        """
        lead_id = input_data.get("lead_id", "")
        campaign_id = input_data.get("campaign_id", "")
        template_id = input_data.get("template_id", "")
        
        if not lead_id:
            return {
                "status": "error",
                "message": "ID de lead requis"
            }
        
        if not campaign_id:
            return {
                "status": "error",
                "message": "ID de campagne requis"
            }
        
        if not template_id:
            return {
                "status": "error",
                "message": "ID de template requis"
            }
        
        self.speak(f"Préparation d'une relance personnalisée pour le lead '{lead_id}'", target="ProspectionSupervisor")
        
        # Récupération des données du lead
        try:
            lead_data = self._get_lead_data(lead_id)
            
            if not lead_data:
                return {
                    "status": "error",
                    "message": f"Lead non trouvé: {lead_id}"
                }
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération du lead: {str(e)}"
            self.speak(error_msg, target="ProspectionSupervisor")
            
            return {
                "status": "error",
                "message": error_msg
            }
        
        # Envoi de la relance via le MessagingAgent
        from agents.overseer.overseer_agent import OverseerAgent
        overseer = OverseerAgent()
        
        messaging_result = overseer.execute_agent("MessagingAgent", {
            "action": "send_messages",
            "leads": [lead_data],
            "campaign_id": campaign_id,
            "template_id": template_id
        })
        
        if messaging_result.get("status") != "success":
            self.speak(f"Erreur lors de l'envoi de la relance: {messaging_result.get('message')}", target="ProspectionSupervisor")
            return messaging_result
        
        # Récupération des résultats d'envoi
        sent_messages = messaging_result.get("sent_messages", [])
        
        if not sent_messages:
            return {
                "status": "error",
                "message": "Échec de l'envoi de la relance personnalisée"
            }
        
        # Mise à jour des statistiques
        self.follow_up_stats["total_follow_ups_sent"] += 1
        
        # Récupération du compteur de relances actuel
        follow_up_count = self._get_follow_up_count(lead_id, campaign_id) + 1
        
        # Enregistrement de la relance
        self._update_follow_up_status(
            lead_id=lead_id,
            campaign_id=campaign_id,
            follow_up_count=follow_up_count,
            template_id=template_id,
            message_id=sent_messages[0].get("message_id", "")
        )
        
        # Log des résultats
        self.speak(
            f"Relance personnalisée envoyée au lead '{lead_id}'",
            target="ProspectionSupervisor"
        )
        
        return {
            "status": "success",
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "template_id": template_id,
            "message_id": sent_messages[0].get("message_id", ""),
            "follow_up_count": follow_up_count
        }
    
    def _get_leads_to_follow_up(self, campaign_id: str, days_since_last: int, max_follow_ups: int) -> List[Dict[str, Any]]:
        """
        Récupère les leads à relancer pour une campagne
        
        Args:
            campaign_id: ID de la campagne
            days_since_last: Nombre de jours depuis le dernier message
            max_follow_ups: Nombre maximal de relances
            
        Returns:
            Liste des leads à relancer
        """
        # Dans un environnement réel, cette fonction interrogerait la base de données
        # pour trouver les leads qui ont besoin d'une relance.
        
        # Pour les besoins de simulation, nous allons créer des données fictives
        # si le mode test est activé
        if self.config.get("test_mode", True):
            mock_leads = []
            
            for i in range(1, 6):
                mock_leads.append({
                    "lead_data": {
                        "lead_id": f"test_lead_{i}",
                        "first_name": f"Test{i}",
                        "last_name": f"User{i}",
                        "email": f"test{i}@example.com",
                        "company": f"Company {i}",
                        "position": "CEO",
                        "industry": "Technology"
                    },
                    "campaign_id": campaign_id,
                    "last_message_date": (datetime.datetime.now() - datetime.timedelta(days=days_since_last + 1)).isoformat(),
                    "follow_up_count": i % 3,  # 0, 1, 2, 0, 1
                    "status": "sent"
                })
            
            # Filtrer les leads qui ont atteint le nombre maximal de relances
            return [lead for lead in mock_leads if lead["follow_up_count"] < max_follow_ups]
        
        # Si nous sommes en mode production, nous interrogeons la base de données
        try:
            # Date limite pour considérer qu'un lead doit être relancé
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_since_last)
            cutoff_date_str = cutoff_date.isoformat()
            
            # Requête pour obtenir les leads à relancer
            query = """
            SELECT l.*, m.sent_at, f.follow_up_count
            FROM leads l
            JOIN messages m ON l.id = m.lead_id
            LEFT JOIN follow_ups f ON l.id = f.lead_id AND m.campaign_id = f.campaign_id
            WHERE m.campaign_id = :campaign_id
            AND m.sent_at < :cutoff_date
            AND (f.follow_up_count IS NULL OR f.follow_up_count < :max_follow_ups)
            AND NOT EXISTS (
                SELECT 1 FROM messages m2
                WHERE m2.lead_id = l.id
                AND m2.sent_at > m.sent_at
            )
            AND NOT EXISTS (
                SELECT 1 FROM responses r
                WHERE r.lead_id = l.id
                AND r.campaign_id = :campaign_id
            )
            """
            
            params = {
                "campaign_id": campaign_id,
                "cutoff_date": cutoff_date_str,
                "max_follow_ups": max_follow_ups
            }
            
            results = self.db.fetch_all(query, params)
            
            # Transformation des résultats
            leads_to_follow_up = []
            
            for row in results:
                # Conversion du résultat de la requête en dictionnaire
                lead_data = {
                    "lead_id": row.get("id"),
                    "first_name": row.get("first_name"),
                    "last_name": row.get("last_name"),
                    "email": row.get("email"),
                    "company": row.get("company"),
                    "position": row.get("position"),
                    "industry": row.get("industry")
                }
                
                leads_to_follow_up.append({
                    "lead_data": lead_data,
                    "campaign_id": campaign_id,
                    "last_message_date": row.get("sent_at"),
                    "follow_up_count": row.get("follow_up_count", 0),
                    "status": "pending"
                })
            
            return leads_to_follow_up
            
        except Exception as e:
            self.speak(f"Erreur lors de la récupération des leads à relancer: {str(e)}", target="ProspectionSupervisor")
            return []
    
    def _get_lead_data(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les données d'un lead
        
        Args:
            lead_id: ID du lead
            
        Returns:
            Données du lead ou None si non trouvé
        """
        # En mode test, nous retournons des données de test
        if self.config.get("test_mode", True):
            return {
                "lead_id": lead_id,
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "company": "Example Company",
                "position": "CEO",
                "industry": "Technology"
            }
        
        # En mode production, nous interrogeons la base de données
        try:
            query = "SELECT * FROM leads WHERE id = :lead_id"
            result = self.db.fetch_one(query, {"lead_id": lead_id})
            
            if not result:
                return None
            
            return {
                "lead_id": result.get("id"),
                "first_name": result.get("first_name"),
                "last_name": result.get("last_name"),
                "email": result.get("email"),
                "company": result.get("company"),
                "position": result.get("position"),
                "industry": result.get("industry")
            }
            
        except Exception as e:
            self.speak(f"Erreur lors de la récupération du lead: {str(e)}", target="ProspectionSupervisor")
            return None
    
    def _get_follow_up_count(self, lead_id: str, campaign_id: str) -> int:
        """
        Récupère le nombre de relances déjà effectuées pour un lead
        
        Args:
            lead_id: ID du lead
            campaign_id: ID de la campagne
            
        Returns:
            Nombre de relances
        """
        # En mode test, nous retournons une valeur aléatoire
        if self.config.get("test_mode", True):
            return 1
        
        # En mode production, nous interrogeons la base de données
        try:
            query = """
            SELECT follow_up_count
            FROM follow_ups
            WHERE lead_id = :lead_id
            AND campaign_id = :campaign_id
            """
            
            result = self.db.fetch_one(query, {
                "lead_id": lead_id,
                "campaign_id": campaign_id
            })
            
            if not result:
                return 0
            
            return result.get("follow_up_count", 0)
            
        except Exception as e:
            self.speak(f"Erreur lors de la récupération du compteur de relances: {str(e)}", target="ProspectionSupervisor")
            return 0
    
    def _update_follow_up_status(self, lead_id: str, campaign_id: str, follow_up_count: int, template_id: str, message_id: str) -> bool:
        """
        Met à jour le statut de relance d'un lead
        
        Args:
            lead_id: ID du lead
            campaign_id: ID de la campagne
            follow_up_count: Nombre de relances
            template_id: ID du template utilisé
            message_id: ID du message envoyé
            
        Returns:
            Succès de la mise à jour
        """
        # En mode test, nous simulons le succès de l'opération
        if self.config.get("test_mode", True):
            return True
        
        # En mode production, nous mettons à jour la base de données
        try:
            # Vérification si une entrée existe déjà
            query = """
            SELECT id FROM follow_ups
            WHERE lead_id = :lead_id
            AND campaign_id = :campaign_id
            """
            
            result = self.db.fetch_one(query, {
                "lead_id": lead_id,
                "campaign_id": campaign_id
            })
            
            if result:
                # Mise à jour de l'entrée existante
                update_query = """
                UPDATE follow_ups
                SET follow_up_count = :follow_up_count,
                    last_template_id = :template_id,
                    last_message_id = :message_id,
                    updated_at = :updated_at
                WHERE lead_id = :lead_id
                AND campaign_id = :campaign_id
                """
                
                self.db.execute(update_query, {
                    "lead_id": lead_id,
                    "campaign_id": campaign_id,
                    "follow_up_count": follow_up_count,
                    "template_id": template_id,
                    "message_id": message_id,
                    "updated_at": datetime.datetime.now().isoformat()
                })
            else:
                # Création d'une nouvelle entrée
                insert_query = """
                INSERT INTO follow_ups (
                    id, lead_id, campaign_id, follow_up_count,
                    last_template_id, last_message_id, created_at, updated_at
                ) VALUES (
                    :id, :lead_id, :campaign_id, :follow_up_count,
                    :template_id, :message_id, :created_at, :updated_at
                )
                """
                
                now = datetime.datetime.now().isoformat()
                
                self.db.execute(insert_query, {
                    "id": str(uuid.uuid4()),
                    "lead_id": lead_id,
                    "campaign_id": campaign_id,
                    "follow_up_count": follow_up_count,
                    "template_id": template_id,
                    "message_id": message_id,
                    "created_at": now,
                    "updated_at": now
                })
            
            return True
            
        except Exception as e:
            self.speak(f"Erreur lors de la mise à jour du statut de relance: {str(e)}", target="ProspectionSupervisor")
            return False
    
    def get_follow_up_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de relance
        
        Returns:
            Statistiques de relance
        """
        return {
            "status": "success",
            "stats": self.follow_up_stats
        }
    
    def get_sequence_for_lead(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Détermine la séquence de relance optimale pour un lead
        
        Args:
            input_data: Données d'entrée avec le lead et la campagne
            
        Returns:
            Séquence de relance recommandée
        """
        lead_id = input_data.get("lead_id", "")
        campaign_id = input_data.get("campaign_id", "")
        
        if not lead_id or not campaign_id:
            return {
                "status": "error",
                "message": "ID de lead et ID de campagne requis"
            }
        
        # Récupération de l'historique du lead
        lead_history = self._get_lead_history(lead_id, campaign_id)
        
        # Récupération du profil du lead
        lead_profile = self._get_lead_data(lead_id)
        
        if not lead_profile:
            return {
                "status": "error",
                "message": f"Lead non trouvé: {lead_id}"
            }
        
        # Détermination de la meilleure séquence (simple ou adaptative)
        sequence_id = self._recommend_sequence(lead_profile, lead_history, campaign_id)
        
        if not sequence_id:
            return {
                "status": "error",
                "message": "Aucune séquence appropriée trouvée"
            }
        
        sequence = self.sequences.get(sequence_id, {})
        
        # Calcul du timing optimal
        timing = self._calculate_optimal_timing(lead_profile, lead_history, sequence)
        
        return {
            "status": "success",
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "recommended_sequence": sequence_id,
            "sequence_details": sequence,
            "next_follow_up": timing
        }
    
    def _get_lead_history(self, lead_id: str, campaign_id: str) -> Dict[str, Any]:
        """
        Récupère l'historique d'un lead pour une campagne
        
        Args:
            lead_id: ID du lead
            campaign_id: ID de la campagne
            
        Returns:
            Historique du lead
        """
        # En mode test, nous simulons un historique
        if self.config.get("test_mode", True):
            return {
                "messages_sent": 2,
                "follow_ups_sent": 1,
                "last_message_date": (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(),
                "responses": 0,
                "opened": True,
                "clicked": False
            }
        
        # En mode production, interrogation de la base de données
        try:
            # Requête pour obtenir l'historique des messages
            messages_query = """
            SELECT COUNT(*) as count, MAX(sent_at) as last_date
            FROM messages
            WHERE lead_id = :lead_id
            AND campaign_id = :campaign_id
            """
            
            messages_result = self.db.fetch_one(messages_query, {
                "lead_id": lead_id,
                "campaign_id": campaign_id
            })
            
            # Requête pour obtenir le nombre de relances
            follow_ups_query = """
            SELECT follow_up_count
            FROM follow_ups
            WHERE lead_id = :lead_id
            AND campaign_id = :campaign_id
            """
            
            follow_ups_result = self.db.fetch_one(follow_ups_query, {
                "lead_id": lead_id,
                "campaign_id": campaign_id
            })
            
            # Requête pour obtenir l'historique des réponses
            responses_query = """
            SELECT COUNT(*) as count
            FROM responses
            WHERE lead_id = :lead_id
            AND campaign_id = :campaign_id
            """
            
            responses_result = self.db.fetch_one(responses_query, {
                "lead_id": lead_id,
                "campaign_id": campaign_id
            })
            
            # Requête pour obtenir les interactions (ouvertures, clics)
            interactions_query = """
            SELECT opened, clicked
            FROM message_interactions
            WHERE lead_id = :lead_id
            AND campaign_id = :campaign_id
            ORDER BY timestamp DESC
            LIMIT 1
            """
            
            interactions_result = self.db.fetch_one(interactions_query, {
                "lead_id": lead_id,
                "campaign_id": campaign_id
            })
            
            # Assemblage des résultats
            return {
                "messages_sent": messages_result.get("count", 0) if messages_result else 0,
                "follow_ups_sent": follow_ups_result.get("follow_up_count", 0) if follow_ups_result else 0,
                "last_message_date": messages_result.get("last_date") if messages_result else None,
                "responses": responses_result.get("count", 0) if responses_result else 0,
                "opened": interactions_result.get("opened", False) if interactions_result else False,
                "clicked": interactions_result.get("clicked", False) if interactions_result else False
            }
            
        except Exception as e:
            self.speak(f"Erreur lors de la récupération de l'historique du lead: {str(e)}", target="ProspectionSupervisor")
            
            # Valeurs par défaut en cas d'erreur
            return {
                "messages_sent": 0,
                "follow_ups_sent": 0,
                "last_message_date": None,
                "responses": 0,
                "opened": False,
                "clicked": False
            }
    
    def _recommend_sequence(self, lead_profile: Dict[str, Any], lead_history: Dict[str, Any], campaign_id: str) -> Optional[str]:
        """
        Recommande une séquence de relance pour un lead
        
        Args:
            lead_profile: Profil du lead
            lead_history: Historique du lead
            campaign_id: ID de la campagne
            
        Returns:
            ID de la séquence recommandée ou None
        """
        # Si le mode LLM est activé, nous utilisons un modèle pour recommander une séquence
        if self.config.get("use_llm_for_sequence", False):
            return self._recommend_sequence_with_llm(lead_profile, lead_history, campaign_id)
        
        # Sinon, logique simple basée sur l'historique
        
        # Si le lead a ouvert les emails mais pas cliqué, séquence éducative
        if lead_history.get("opened", False) and not lead_history.get("clicked", False):
            return "educational"
        
        # Si le lead a cliqué, séquence de conversion
        elif lead_history.get("clicked", False):
            return "conversion"
        
        # Si le lead est un décideur (position de haut niveau), séquence pour décideurs
        elif lead_profile.get("position", "").lower() in ["ceo", "cto", "cfo", "cmo", "coo", "founder", "co-founder", "owner", "director"]:
            return "decision_maker"
        
        # Séquence standard par défaut
        return "standard"
    
    def _recommend_sequence_with_llm(self, lead_profile: Dict[str, Any], lead_history: Dict[str, Any], campaign_id: str) -> Optional[str]:
        """
        Recommande une séquence de relance pour un lead en utilisant un LLM
        
        Args:
            lead_profile: Profil du lead
            lead_history: Historique du lead
            campaign_id: ID de la campagne
            
        Returns:
            ID de la séquence recommandée ou None
        """
        prompt = f"""
        Recommande la meilleure séquence de relance pour ce lead:
        
        PROFIL DU LEAD:
        {json.dumps(lead_profile, indent=2)}
        
        HISTORIQUE:
        {json.dumps(lead_history, indent=2)}
        
        SÉQUENCES DISPONIBLES:
        {json.dumps(list(self.sequences.keys()), indent=2)}
        
        RÉPONDS UNIQUEMENT AVEC LE NOM DE LA SÉQUENCE RECOMMANDÉE, SANS AUTRE TEXTE.
        """
        
        try:
            response = LLMService.call_llm(prompt, complexity="low")
            sequence_id = response.strip()
            
            # Vérification que la séquence existe
            if sequence_id in self.sequences:
                return sequence_id
            else:
                self.speak(f"Séquence recommandée par le LLM non trouvée: {sequence_id}", target="ProspectionSupervisor")
                return "standard"  # Fallback à la séquence standard
                
        except Exception as e:
            self.speak(f"Erreur lors de la recommandation de séquence avec LLM: {str(e)}", target="ProspectionSupervisor")
            return "standard"  # Fallback à la séquence standard
    
    def _calculate_optimal_timing(self, lead_profile: Dict[str, Any], lead_history: Dict[str, Any], sequence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule le timing optimal pour la prochaine relance
        
        Args:
            lead_profile: Profil du lead
            lead_history: Historique du lead
            sequence: Détails de la séquence sélectionnée
            
        Returns:
            Dictionnaire contenant le délai (en jours) avant la prochaine relance
        """
        try:
            base_delay = sequence.get("base_delay_days", 3)
            multiplier = 1.0

            # Ajustements en fonction du comportement
            if lead_history.get("opened"):
                multiplier *= 0.8
            if lead_history.get("clicked"):
                multiplier *= 0.5
            if lead_history.get("responses", 0) > 0:
                multiplier *= 0.3

            # Ajustement selon le poste
            position = lead_profile.get("position", "").lower()
            if position in ["ceo", "cto", "founder", "co-founder"]:
                multiplier *= 1.2

            delay_days = max(1, int(base_delay * multiplier))

            next_follow_up_date = datetime.datetime.now() + datetime.timedelta(days=delay_days)

            return {
                "delay_days": delay_days,
                "next_follow_up_date": next_follow_up_date.isoformat()
            }

        except Exception as e:
            self.speak(f"Erreur lors du calcul du timing de relance : {str(e)}", target="ProspectionSupervisor")
            return {
                "delay_days": 3,
                "next_follow_up_date": (datetime.datetime.now() + datetime.timedelta(days=3)).isoformat()
            }

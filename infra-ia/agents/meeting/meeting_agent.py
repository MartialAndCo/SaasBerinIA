"""
Module du MeetingAgent - Agent de gestion des rendez-vous
Gère l'interrogation des disponibilités, la création de RDV avec liens Jitsi, et les rappels différenciés
"""
import os
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from core.agent_base import Agent
from utils.llm import LLMService
from core.db import DatabaseService

# Import du module d'intégration Google Calendar
try:
    from .calendar_integration import GoogleCalendarIntegration
except ImportError:
    try:
        from calendar_integration import GoogleCalendarIntegration
    except ImportError:
        print("ERREUR: Module calendar_integration non trouvé")
        GoogleCalendarIntegration = None


class MeetingAgent(Agent):
    """
    MeetingAgent - Agent responsable de la gestion complète des rendez-vous
    
    Fonctionnalités:
    - Interrogation des disponibilités Google Calendar (freebusy.query)
    - Création de rendez-vous avec liens Jitsi automatiques
    - Gestion intelligente des rappels selon le canal (email vs SMS)
    - Interface avec MessagingAgent pour la prise de RDV
    - Programmation des follow-ups via AgentScheduler
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du MeetingAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("MeetingAgent", config_path)
        
        # Initialisation de la base de données
        self.db = DatabaseService()
        
        # Initialisation de l'intégration Google Calendar
        if GoogleCalendarIntegration:
            try:
                self.calendar = GoogleCalendarIntegration(self.config)
                self.speak("Intégration Google Calendar initialisée avec succès", target="ProspectionSupervisor")
            except Exception as e:
                self.calendar = None
                self.speak(f"Erreur initialisation Google Calendar: {str(e)}", target="ProspectionSupervisor")
        else:
            self.calendar = None
            self.speak("Intégration Google Calendar non disponible", target="ProspectionSupervisor")
        
        # Configuration des paramètres de meeting
        self.meeting_settings = self.config.get("meeting_settings", {})
        self.jitsi_settings = self.config.get("jitsi_settings", {})
        self.reminder_settings = self.config.get("reminders", {})
        
        # État de l'agent
        self.stats = {
            "meetings_created": 0,
            "slots_queries": 0,
            "reminders_scheduled": 0,
            "errors": 0,
            "last_activity": None
        }
        
        self.speak("MeetingAgent initialisé et prêt pour la gestion des rendez-vous", target="ProspectionSupervisor")
    
    def get_available_slots(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les créneaux disponibles dans l'agenda
        
        Args:
            input_data: Paramètres de recherche (durée, nombre de jours, etc.)
            
        Returns:
            Liste des créneaux disponibles
        """
        try:
            if not self.calendar:
                return {
                    "status": "error",
                    "message": "Intégration Google Calendar non disponible",
                    "available_slots": []
                }
            
            # Extraction des paramètres
            duration_minutes = input_data.get("duration_minutes", self.meeting_settings.get("default_duration_minutes", 30))
            days_ahead = input_data.get("days_ahead", 14)
            max_slots = input_data.get("max_slots", self.meeting_settings.get("max_slots_returned", 3))
            
            self.speak(f"Recherche de créneaux disponibles: {duration_minutes}min sur {days_ahead} jours", target="MessagingAgent")
            
            # Récupération des créneaux via Google Calendar
            available_slots = self.calendar.get_available_slots(
                duration_minutes=duration_minutes,
                days_ahead=days_ahead
            )
            
            # Limitation selon la configuration
            if len(available_slots) > max_slots:
                available_slots = available_slots[:max_slots]
            
            # Mise à jour des stats
            self.stats["slots_queries"] += 1
            self.stats["last_activity"] = datetime.now().isoformat()
            
            if available_slots:
                self.speak(f"{len(available_slots)} créneaux disponibles trouvés", target="MessagingAgent")
                return {
                    "status": "success",
                    "available_slots": available_slots,
                    "search_params": {
                        "duration_minutes": duration_minutes,
                        "days_ahead": days_ahead,
                        "max_slots": max_slots
                    },
                    "message": f"{len(available_slots)} créneaux disponibles"
                }
            else:
                self.speak("Aucun créneau disponible trouvé", target="MessagingAgent")
                return {
                    "status": "success",
                    "available_slots": [],
                    "message": "Aucun créneau disponible dans la période demandée"
                }
                
        except Exception as e:
            self.stats["errors"] += 1
            error_msg = f"Erreur lors de la recherche de créneaux: {str(e)}"
            self.speak(error_msg, target="MessagingAgent")
            return {
                "status": "error",
                "message": error_msg,
                "available_slots": []
            }
    
    def book_meeting(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un rendez-vous dans Google Calendar avec lien Jitsi
        
        Args:
            input_data: Données du client et paramètres du RDV
            
        Returns:
            Résultat de la création du rendez-vous
        """
        try:
            if not self.calendar:
                return {
                    "status": "error",
                    "message": "Intégration Google Calendar non disponible"
                }
            
            # Extraction des données client
            client_name = input_data.get("client_name", "")
            client_email = input_data.get("client_email", "")
            start_datetime = input_data.get("start_datetime", "")
            duration_minutes = input_data.get("duration_minutes", self.meeting_settings.get("default_duration_minutes", 30))
            description = input_data.get("description", "")
            lead_id = input_data.get("lead_id", "")
            channel = input_data.get("preferred_channel", "email")  # Canal préféré pour les rappels
            
            # Validations
            if not all([client_name, client_email, start_datetime]):
                return {
                    "status": "error",
                    "message": "Données client incomplètes (nom, email, datetime requis)"
                }
            
            # Récupération de l'entreprise du lead pour le titre
            company_name = ""
            if lead_id:
                try:
                    lead_id_int = int(lead_id) if lead_id else None
                    if lead_id_int:
                        lead_info = self.db.fetch_one(
                            "SELECT company, entreprise FROM leads WHERE id = :lead_id",
                            {"lead_id": lead_id_int}
                        )
                        if lead_info:
                            # Prioriser 'company' puis 'entreprise'
                            company_name = lead_info.get("company") or lead_info.get("entreprise") or ""
                except Exception as e:
                    self.speak(f"Erreur récupération entreprise: {str(e)}", target="ProspectionSupervisor")
            
            self.speak(f"Création RDV pour {client_name} ({client_email}) le {start_datetime}", target="MessagingAgent")
            
            # Génération de la description enrichie
            full_description = self._generate_meeting_description(client_name, description, lead_id)
            
            # Création du rendez-vous via Google Calendar
            meeting_result = self.calendar.create_meeting(
                client_name=client_name,
                client_email=client_email,
                start_datetime=start_datetime,
                duration_minutes=duration_minutes,
                description=full_description,
                company_name=company_name
            )
            
            if meeting_result["status"] == "success":
                # Enregistrement en base de données
                meeting_id = self._save_meeting_to_db(
                    meeting_result, client_name, client_email, lead_id
                )
                
                # Programmation des rappels selon le canal préféré
                self._schedule_reminders(
                    meeting_result, client_name, client_email, channel, lead_id
                )
                
                # Déclencher notification Telegram via webhook
                self._trigger_telegram_notification(
                    meeting_result, client_name, client_email, lead_id, meeting_id
                )
                
                # Mise à jour des stats
                self.stats["meetings_created"] += 1
                self.stats["last_activity"] = datetime.now().isoformat()
                
                self.speak(f"RDV créé avec succès: {meeting_result['meeting_link']}", target="MessagingAgent")
                
                return {
                    "status": "success",
                    "meeting_id": meeting_id,
                    "calendar_event_id": meeting_result["event_id"],
                    "meeting_link": meeting_result["meeting_link"],
                    "start_time": meeting_result["start_time"],
                    "end_time": meeting_result["end_time"],
                    "calendar_link": meeting_result["calendar_link"],
                    "attendees": meeting_result.get("attendees", []),
                    "reminders_scheduled": True,
                    "message": "Rendez-vous créé avec succès"
                }
            else:
                self.stats["errors"] += 1
                return meeting_result
                
        except Exception as e:
            self.stats["errors"] += 1
            error_msg = f"Erreur lors de la création du rendez-vous: {str(e)}"
            self.speak(error_msg, target="MessagingAgent")
            return {
                "status": "error",
                "message": error_msg
            }
    
    def _generate_meeting_description(self, client_name: str, base_description: str, lead_id: str) -> str:
        """
        Génère une description enrichie pour le rendez-vous
        
        Args:
            client_name: Nom du client
            base_description: Description de base
            lead_id: ID du lead
            
        Returns:
            Description enrichie
        """
        description_parts = []
        
        if base_description:
            description_parts.append(base_description)
        else:
            description_parts.append(f"Rendez-vous commercial avec {client_name}")
        
        # Ajouter les informations du lead si disponible
        if lead_id:
            try:
                # Conversion sécurisée de lead_id en entier si nécessaire
                try:
                    lead_id_int = int(lead_id)
                except (ValueError, TypeError):
                    # Si lead_id n'est pas convertible en entier, on le garde tel quel
                    lead_id_int = lead_id
                
                # Utiliser la nouvelle syntaxe avec des paramètres nommés pour éviter l'erreur
                lead_info = self.db.fetch_one(
                    "SELECT company, industry, position FROM leads WHERE id = :lead_id",
                    {"lead_id": lead_id_int}
                )
                if lead_info:
                    if lead_info.get("company"):
                        description_parts.append(f"Entreprise: {lead_info['company']}")
                    if lead_info.get("industry"):
                        description_parts.append(f"Secteur: {lead_info['industry']}")
                    if lead_info.get("position"):
                        description_parts.append(f"Poste: {lead_info['position']}")
            except Exception as e:
                self.speak(f"Erreur récupération infos lead: {str(e)}", target="ProspectionSupervisor")
        
        # Ajouter les infos BerinIA
        description_parts.append("---")
        description_parts.append("Rendez-vous généré automatiquement par BerinIA")
        description_parts.append("Solutions d'automatisation commerciale par IA")
        
        return "\n".join(description_parts)
    
    def _save_meeting_to_db(self, meeting_result: Dict[str, Any], client_name: str, 
                           client_email: str, lead_id: str) -> str:
        """
        Enregistre le rendez-vous en base de données
        
        Args:
            meeting_result: Résultat de la création Google Calendar
            client_name: Nom du client
            client_email: Email du client
            lead_id: ID du lead
            
        Returns:
            ID du meeting enregistré
        """
        try:
            meeting_id = str(uuid.uuid4())
            
            # Vérifier si la table meetings existe, sinon utiliser une table générique
            try:
                insert_query = """
                    INSERT INTO meetings (
                        id, lead_id, calendar_event_id, client_name, client_email,
                        meeting_link, start_time, end_time, status, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    meeting_id,
                    lead_id or None,
                    meeting_result["event_id"],
                    client_name,
                    client_email,
                    meeting_result["meeting_link"],
                    meeting_result["start_time"],
                    meeting_result["end_time"],
                    "scheduled",
                    datetime.now(),
                    datetime.now()
                )
                
                self.db.execute_query(insert_query, values)
                self.speak(f"Meeting enregistré en BDD avec ID: {meeting_id}", target="ProspectionSupervisor")
                
            except Exception as db_error:
                # Fallback: enregistrer dans les logs système si la table meetings n'existe pas
                self.speak(f"Table meetings non trouvée, enregistrement en logs: {str(db_error)}", target="ProspectionSupervisor")
                
                # Enregistrer les détails dans les messages pour traçabilité
                # Enregistrement simple en logs sans contrainte stricte sur lead_id
                message_content = f"RDV créé: {client_name} le {meeting_result['start_time']} - Lien: {meeting_result['meeting_link']}"
                self.speak(f"Meeting enregistré: {message_content}", target="ProspectionSupervisor")
                # Éviter l'enregistrement en base pour éviter les erreurs de contrainte
            
            return meeting_id
            
        except Exception as e:
            self.speak(f"Erreur enregistrement meeting: {str(e)}", target="ProspectionSupervisor")
            return str(uuid.uuid4())  # Retourner un ID quand même
    
    def _schedule_reminders(self, meeting_result: Dict[str, Any], client_name: str, 
                          client_email: str, channel: str, lead_id: str) -> None:
        """
        Programme les rappels selon le canal préféré
        
        Args:
            meeting_result: Résultat de la création du meeting
            client_name: Nom du client
            client_email: Email du client
            channel: Canal préféré (email ou sms)
            lead_id: ID du lead
        """
        try:
            # Pour les emails: les rappels Google Calendar natifs sont déjà configurés
            if channel == "email":
                self.speak(f"Rappels email programmés via Google Calendar pour {client_name}", target="MessagingAgent")
                return
            
            # Pour les SMS: programmer via AgentScheduler
            if channel == "sms":
                self._schedule_sms_reminders(meeting_result, client_name, lead_id)
            
        except Exception as e:
            self.speak(f"Erreur programmation rappels: {str(e)}", target="ProspectionSupervisor")
    
    def _schedule_sms_reminders(self, meeting_result: Dict[str, Any], client_name: str, lead_id: str) -> None:
        """
        Programme des rappels SMS via AgentScheduler
        
        Args:
            meeting_result: Résultat de la création du meeting
            client_name: Nom du client
            lead_id: ID du lead
        """
        try:
            # Récupération du numéro de téléphone du lead
            if not lead_id:
                self.speak("Impossible de programmer rappels SMS: lead_id manquant", target="ProspectionSupervisor")
                return
            
            lead_data = self.db.fetch_one("SELECT phone FROM leads WHERE id = %s", (lead_id,))
            if not lead_data or not lead_data.get("phone"):
                self.speak("Impossible de programmer rappels SMS: numéro manquant", target="ProspectionSupervisor")
                return
            
            phone_number = lead_data["phone"]
            meeting_start = datetime.fromisoformat(meeting_result["start_time"].replace('Z', '+00:00'))
            meeting_link = meeting_result["meeting_link"]
            
            # Configuration des rappels SMS
            sms_reminder_times = self.reminder_settings.get("sms", {}).get("times", [1440, 60, 10])
            
            for minutes_before in sms_reminder_times:
                reminder_time = meeting_start - timedelta(minutes=minutes_before)
                
                # Ne programmer que les rappels futurs
                if reminder_time > datetime.now(meeting_start.tzinfo):
                    # Création de la tâche pour AgentScheduler
                    reminder_task = {
                        "task_id": f"sms_reminder_{lead_id}_{minutes_before}_{int(datetime.now().timestamp())}",
                        "agent": "MessagingAgent",
                        "action": "send_sms",
                        "parameters": {
                            "phone_number": phone_number,
                            "message": self._generate_sms_reminder_text(client_name, meeting_start, meeting_link, minutes_before)
                        },
                        "scheduled_time": reminder_time.isoformat(),
                        "priority": 2,
                        "metadata": {
                            "type": "meeting_reminder",
                            "meeting_id": meeting_result.get("event_id"),
                            "lead_id": lead_id,
                            "reminder_type": f"{minutes_before}_minutes_before"
                        }
                    }
                    
                    # Communication avec AgentScheduler via le système
                    try:
                        from agents.overseer.overseer_agent import OverseerAgent
                        overseer = OverseerAgent()
                        
                        result = overseer.execute_agent(
                            agent_name="AgentSchedulerAgent",
                            agent_input={
                                "action": "schedule_task",
                                "task_data": reminder_task
                            },
                            sender="MeetingAgent"
                        )
                        
                        if result.get("status") == "success":
                            self.stats["reminders_scheduled"] += 1
                            self.speak(f"Rappel SMS programmé: {minutes_before}min avant pour {client_name}", target="MessagingAgent")
                        else:
                            self.speak(f"Échec programmation rappel SMS: {result.get('message', 'Erreur inconnue')}", target="ProspectionSupervisor")
                            
                    except Exception as scheduler_error:
                        self.speak(f"Erreur communication AgentScheduler: {str(scheduler_error)}", target="ProspectionSupervisor")
            
        except Exception as e:
            self.speak(f"Erreur programmation rappels SMS: {str(e)}", target="ProspectionSupervisor")
    
    def _trigger_telegram_notification(self, meeting_result: Dict[str, Any], 
                                      client_name: str, client_email: str, 
                                      lead_id: str, meeting_id: str) -> None:
        """
        Déclenche une notification Telegram via webhook pour le nouveau RDV
        
        Args:
            meeting_result: Résultat de la création Google Calendar
            client_name: Nom du client
            client_email: Email du client  
            lead_id: ID du lead
            meeting_id: ID du meeting en base
        """
        try:
            import requests
            
            # Préparer les données pour le webhook
            webhook_data = {
                'meeting_id': meeting_id,
                'client_name': client_name,
                'client_email': client_email,
                'start_time': meeting_result.get('start_time'),
                'end_time': meeting_result.get('end_time'),
                'meeting_link': meeting_result.get('meeting_link'),
                'calendar_event_id': meeting_result.get('event_id'),
                'lead_id': lead_id,
                'description': f"RDV créé automatiquement par BerinIA pour {client_name}"
            }
            
            # URL du webhook (API backend)
            webhook_url = "http://localhost:8000/api/webhooks/webhook/meeting-created"
            
            # Envoyer le webhook
            response = requests.post(
                webhook_url,
                json=webhook_data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.speak(f"Notification Telegram déclenchée pour RDV {client_name}", target="ProspectionSupervisor")
            else:
                self.speak(f"Échec notification Telegram: {response.status_code}", target="ProspectionSupervisor")
                
        except Exception as e:
            # Ne pas faire échouer la création du RDV si la notification échoue
            self.speak(f"Erreur notification Telegram: {str(e)}", target="ProspectionSupervisor")
    
    def _generate_sms_reminder_text(self, client_name: str, meeting_start: datetime, 
                                   meeting_link: str, minutes_before: int) -> str:
        """
        Génère le texte du rappel SMS
        
        Args:
            client_name: Nom du client
            meeting_start: Heure de début du meeting
            meeting_link: Lien Jitsi
            minutes_before: Nombre de minutes avant le RDV
            
        Returns:
            Texte du rappel SMS
        """
        # Formatage de l'heure
        meeting_time = meeting_start.strftime("%d/%m à %H:%M")
        
        if minutes_before >= 1440:  # J-1
            return f"Rappel: RDV demain {meeting_time}. Lien: {meeting_link} - BerinIA"
        elif minutes_before >= 60:  # H-1
            return f"Rappel: RDV dans 1h ({meeting_time}). Lien: {meeting_link}"
        else:  # M-10
            return f"RDV dans 10min! Cliquez: {meeting_link}"
    
    def get_meeting_status(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère le statut d'un rendez-vous
        
        Args:
            input_data: Données avec l'ID du meeting
            
        Returns:
            Statut du rendez-vous
        """
        try:
            meeting_id = input_data.get("meeting_id")
            calendar_event_id = input_data.get("calendar_event_id")
            
            if calendar_event_id and self.calendar:
                # Récupération via Google Calendar
                meeting_details = self.calendar.get_meeting_details(calendar_event_id)
                
                if meeting_details:
                    return {
                        "status": "success",
                        "meeting_details": meeting_details
                    }
                else:
                    return {
                        "status": "not_found",
                        "message": "Rendez-vous non trouvé dans Google Calendar"
                    }
            
            # Fallback: recherche en base de données
            if meeting_id:
                try:
                    db_meeting = self.db.fetch_one(
                        "SELECT * FROM meetings WHERE id = %s",
                        (meeting_id,)
                    )
                    
                    if db_meeting:
                        return {
                            "status": "success",
                            "meeting_details": dict(db_meeting)
                        }
                except Exception:
                    pass
            
            return {
                "status": "not_found",
                "message": "Rendez-vous non trouvé"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur récupération statut: {str(e)}"
            }
    
    def cancel_meeting(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Annule un rendez-vous
        
        Args:
            input_data: Données avec l'ID du meeting à annuler
            
        Returns:
            Résultat de l'annulation
        """
        try:
            calendar_event_id = input_data.get("calendar_event_id")
            
            if not calendar_event_id:
                return {
                    "status": "error",
                    "message": "ID de l'événement Calendar requis pour l'annulation"
                }
            
            if not self.calendar:
                return {
                    "status": "error",
                    "message": "Intégration Google Calendar non disponible"
                }
            
            # Annulation via Google Calendar
            success = self.calendar.cancel_meeting(calendar_event_id)
            
            if success:
                # Mise à jour en base de données si applicable
                try:
                    self.db.execute_query(
                        "UPDATE meetings SET status = %s, updated_at = %s WHERE calendar_event_id = %s",
                        ("cancelled", datetime.now(), calendar_event_id)
                    )
                except Exception:
                    pass  # Table peut ne pas exister
                
                self.speak(f"Rendez-vous annulé: {calendar_event_id}", target="MessagingAgent")
                return {
                    "status": "success",
                    "message": "Rendez-vous annulé avec succès"
                }
            else:
                return {
                    "status": "error",
                    "message": "Échec de l'annulation du rendez-vous"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de l'annulation: {str(e)}"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de l'agent
        
        Returns:
            Statistiques de l'agent
        """
        return {
            "status": "success",
            "stats": self.stats,
            "calendar_integration": self.calendar is not None,
            "config": {
                "default_duration": self.meeting_settings.get("default_duration_minutes", 30),
                "timezone": self.meeting_settings.get("timezone", "Europe/Paris"),
                "max_slots": self.meeting_settings.get("max_slots_returned", 3)
            }
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Méthode principale d'exécution de l'agent
        
        Args:
            input_data: Données d'entrée avec l'action à effectuer
            
        Returns:
            Résultat de l'action
        """
        action = input_data.get("action", "")
        
        if action == "get_available_slots":
            return self.get_available_slots(input_data)
        
        elif action == "book_meeting":
            return self.book_meeting(input_data)
        
        elif action == "get_meeting_status":
            return self.get_meeting_status(input_data)
        
        elif action == "cancel_meeting":
            return self.cancel_meeting(input_data)
        
        elif action == "get_stats":
            return self.get_stats()
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}",
                "available_actions": [
                    "get_available_slots",
                    "book_meeting", 
                    "get_meeting_status",
                    "cancel_meeting",
                    "get_stats"
                ]
            }


# Test direct de l'agent si exécuté comme script principal
if __name__ == "__main__":
    print("Test du MeetingAgent...")
    
    # Création d'une instance
    try:
        agent = MeetingAgent()
        
        # Test de récupération des créneaux
        test_slots = agent.run({
            "action": "get_available_slots",
            "duration_minutes": 30,
            "days_ahead": 7
        })
        
        print(f"Test créneaux: {test_slots}")
        
        # Test des stats
        test_stats = agent.run({"action": "get_stats"})
        print(f"Stats: {test_stats}")
        
    except Exception as e:
        print(f"Erreur test: {e}")

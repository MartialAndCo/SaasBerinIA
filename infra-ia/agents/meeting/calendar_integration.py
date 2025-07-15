"""
Module d'intégration Google Calendar pour MeetingAgent
Gère les authentifications OAuth2, les requêtes freebusy et la création d'événements
"""
import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pytz

# Imports Google Calendar API
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Erreur import Google Calendar API: {e}")
    print("Installez avec: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")


class GoogleCalendarIntegration:
    """
    Classe pour gérer l'intégration avec Google Calendar
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise l'intégration Google Calendar
        
        Args:
            config: Configuration contenant les identifiants Google
        """
        self.config = config
        self.google_config = config.get("google_calendar", {})
        self.meeting_settings = config.get("meeting_settings", {})
        
        # Configuration des scopes
        self.scopes = self.google_config.get("scopes", [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ])
        
        # Configuration du fuseau horaire
        self.timezone = pytz.timezone(self.meeting_settings.get("timezone", "Europe/Paris"))
        
        # Chemins pour les fichiers de tokens
        self.token_path = Path("agents/meeting/token.pickle")
        self.credentials_path = Path("agents/meeting/credentials.json")
        
        # Service Google Calendar (sera initialisé lors de la première utilisation)
        self._service = None
        
        # Créer le fichier credentials.json depuis la config
        self._create_credentials_file()
    
    def _create_credentials_file(self) -> None:
        """
        Crée le fichier credentials.json depuis la configuration
        """
        try:
            # Créer la structure complète pour le fichier credentials.json
            credentials_data = {
                "web": {
                    "client_id": self.google_config.get("client_id"),
                    "project_id": self.google_config.get("project_id"),
                    "auth_uri": self.google_config.get("auth_uri"),
                    "token_uri": self.google_config.get("token_uri"),
                    "auth_provider_x509_cert_url": self.google_config.get("auth_provider_x509_cert_url"),
                    "client_secret": self.google_config.get("client_secret"),
                    "redirect_uris": self.google_config.get("redirect_uris", ["http://localhost"])
                }
            }
            
            # Sauvegarder le fichier credentials.json
            with open(self.credentials_path, 'w') as f:
                json.dump(credentials_data, f, indent=2)
                
        except Exception as e:
            print(f"Erreur lors de la création du fichier credentials.json: {e}")
    
    def _get_service(self):
        """
        Obtient le service Google Calendar avec authentification
        
        Returns:
            Service Google Calendar authentifié
        """
        if self._service is not None:
            return self._service
        
        creds = None
        
        # Vérifier si le token existe déjà
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # Si les credentials n'existent pas ou ne sont pas valides
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Erreur lors du refresh du token: {e}")
                    creds = None
            
            if not creds:
                if not self.credentials_path.exists():
                    raise Exception("Fichier credentials.json manquant. Vérifiez la configuration Google Calendar.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), 
                    self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Sauvegarder les credentials pour la prochaine fois
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        # Construire le service
        self._service = build('calendar', 'v3', credentials=creds)
        return self._service
    
    def get_available_slots(self, duration_minutes: int = 30, days_ahead: int = 14) -> List[Dict[str, Any]]:
        """
        Récupère les créneaux disponibles dans l'agenda
        
        Args:
            duration_minutes: Durée du rendez-vous en minutes
            days_ahead: Nombre de jours à regarder dans le futur
            
        Returns:
            Liste des créneaux disponibles
        """
        try:
            service = self._get_service()
            
            # Configuration des heures de bureau
            business_start = self.meeting_settings.get("business_hours", {}).get("start", "09:00")
            business_end = self.meeting_settings.get("business_hours", {}).get("end", "18:00")
            working_days = self.meeting_settings.get("working_days", [1, 2, 3, 4, 5])  # Lun-Ven
            buffer_minutes = self.meeting_settings.get("buffer_minutes", 15)
            max_slots = self.meeting_settings.get("max_slots_returned", 3)
            
            # Calcul des dates de début et fin
            now = datetime.now(self.timezone)
            start_time = now.replace(second=0, microsecond=0)
            end_time = start_time + timedelta(days=days_ahead)
            
            # Requête freebusy pour connaître les créneaux occupés
            freebusy_request = {
                'timeMin': start_time.isoformat(),
                'timeMax': end_time.isoformat(),
                'timeZone': str(self.timezone),
                'items': [{'id': 'primary'}]  # Agenda principal
            }
            
            freebusy_result = service.freebusy().query(body=freebusy_request).execute()
            busy_periods = freebusy_result['calendars']['primary']['busy']
            
            # Convertir les périodes occupées en objets datetime
            busy_slots = []
            for period in busy_periods:
                start = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
                busy_slots.append((start.astimezone(self.timezone), end.astimezone(self.timezone)))
            
            # Générer les créneaux disponibles
            available_slots = []
            current_time = start_time
            
            while current_time < end_time and len(available_slots) < max_slots:
                # Vérifier si c'est un jour ouvrable
                if current_time.weekday() + 1 not in working_days:
                    current_time += timedelta(days=1)
                    current_time = current_time.replace(hour=int(business_start.split(':')[0]), 
                                                       minute=int(business_start.split(':')[1]))
                    continue
                
                # Vérifier si c'est dans les heures d'ouverture
                business_start_time = current_time.replace(hour=int(business_start.split(':')[0]), 
                                                          minute=int(business_start.split(':')[1]))
                business_end_time = current_time.replace(hour=int(business_end.split(':')[0]), 
                                                        minute=int(business_end.split(':')[1]))
                
                if current_time < business_start_time:
                    current_time = business_start_time
                    continue
                
                if current_time >= business_end_time:
                    current_time += timedelta(days=1)
                    current_time = current_time.replace(hour=int(business_start.split(':')[0]), 
                                                       minute=int(business_start.split(':')[1]))
                    continue
                
                # Vérifier si le créneau est libre
                slot_end = current_time + timedelta(minutes=duration_minutes)
                is_free = True
                
                for busy_start, busy_end in busy_slots:
                    if (current_time < busy_end and slot_end > busy_start):
                        is_free = False
                        break
                
                if is_free and slot_end <= business_end_time:
                    available_slots.append({
                        'start': current_time.isoformat(),
                        'end': slot_end.isoformat(),
                        'start_formatted': current_time.strftime('%d/%m/%Y à %H:%M'),
                        'end_formatted': slot_end.strftime('%H:%M'),
                        'duration_minutes': duration_minutes,
                        'timezone': str(self.timezone)
                    })
                
                # Passer au créneau suivant (avec buffer)
                current_time += timedelta(minutes=duration_minutes + buffer_minutes)
            
            return available_slots
            
        except Exception as e:
            print(f"Erreur lors de la récupération des créneaux disponibles: {e}")
            return []
    
    def check_existing_meeting(self, client_email: str, start_datetime: datetime, duration_minutes: int) -> bool:
        """
        Vérifie s'il existe déjà un meeting pour ce client à cette heure
        
        Args:
            client_email: Email du client
            start_datetime: Date/heure de début
            duration_minutes: Durée en minutes
            
        Returns:
            True si un meeting existe déjà, False sinon
        """
        try:
            service = self._get_service()
            
            # Fenêtre de recherche : 30 minutes avant et après
            time_min = (start_datetime - timedelta(minutes=30)).isoformat()
            time_max = (start_datetime + timedelta(minutes=30)).isoformat()
            
            # Rechercher les événements dans cette fenêtre
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Vérifier si un événement a le même client
            for event in events:
                attendees = event.get('attendees', [])
                for attendee in attendees:
                    if attendee.get('email') == client_email:
                        print(f"⚠️  Meeting existant trouvé pour {client_email} à {event.get('start', {}).get('dateTime')}")
                        return True
                        
            return False
            
        except Exception as e:
            print(f"Erreur lors de la vérification des meetings existants: {e}")
            return False
    
    def create_meeting(self, client_name: str, client_email: str, start_datetime: str, 
                      duration_minutes: int = 30, description: str = "", company_name: str = "") -> Dict[str, Any]:
        """
        Crée un rendez-vous dans Google Calendar
        
        Args:
            client_name: Nom du client
            client_email: Email du client
            start_datetime: Date/heure de début (ISO format)
            duration_minutes: Durée en minutes
            description: Description du rendez-vous
            company_name: Nom de l'entreprise (optionnel)
            
        Returns:
            Informations sur le rendez-vous créé
        """
        try:
            service = self._get_service()
            
            # 🔧 CORRECTION TIMEZONE CRITIQUE
            # 1. Parser la datetime d'entrée sans timezone (supposée être en heure locale)
            start_naive = datetime.fromisoformat(start_datetime.replace('Z', '').replace('+00:00', ''))
            print(f"🕐 Input datetime naive: {start_naive}")
            
            # 2. FORCER le timezone Europe/Paris (pas de localisation automatique)
            start = self.timezone.localize(start_naive)
            print(f"🕐 Localized to Europe/Paris: {start}")
            
            # Vérifier s'il existe déjà un meeting pour ce client à cette heure
            if self.check_existing_meeting(client_email, start, duration_minutes):
                return {
                    'status': 'error',
                    'message': f'Un rendez-vous existe déjà pour {client_email} autour de cette heure'
                }
            
            # 3. Calculer la fin
            end = start + timedelta(minutes=duration_minutes)
            print(f"🕐 End time: {end}")
            
            # Génération du lien Jitsi avec date
            jitsi_room_name = self._generate_jitsi_room_name(client_name, start)
            jitsi_link = f"{self.config.get('jitsi_settings', {}).get('base_url', 'https://meet.jit.si')}/{jitsi_room_name}"
            print(f"🔗 Jitsi room: {jitsi_room_name}")
            
            # Génération du titre selon la priorité entreprise > personne
            meeting_title = f"BerinIA & {company_name}" if company_name else f"BerinIA & {client_name}"
            
            # Configuration professionnelle de l'organisateur
            organizer_name = "Louise de BerinIA"  # Nom affiché pour l'organisateur
            
            # Préparation de la liste des invités
            attendees = [{'email': client_email, 'displayName': client_name}]
            
            # Ajouter l'invité par défaut si configuré et activé
            default_attendee = self.meeting_settings.get("default_attendee", {})
            
            if default_attendee.get("enabled", False) and default_attendee.get("email"):
                attendees.append({
                    'email': default_attendee.get("email"),
                    'displayName': default_attendee.get("name", "Admin BerinIA")
                })
            
            # Récupération des infos de l'organisateur
            organizer_info = self.meeting_settings.get("organizer_display", {})
            organizer_name = organizer_info.get("name", "Louise de BerinIA")
            organizer_title = organizer_info.get("title", "Assistante IA")
            organizer_company = organizer_info.get("company", "BerinIA")
            organizer_email = organizer_info.get("email_signature", "contact@berinia.com")
            
            # Création de la description professionnelle
            professional_description = self._create_professional_description(
                description, jitsi_link, organizer_name, organizer_title, 
                organizer_company, organizer_email
            )
            
            # Préparation de l'événement
            event = {
                'summary': meeting_title,
                'description': professional_description,
                'start': {
                    'dateTime': start.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'end': {
                    'dateTime': end.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'attendees': attendees,
                'reminders': self._get_email_reminders()
            }
            
            # Ajouter des propriétés pour améliorer l'apparence
            event['guestsCanModify'] = False  # Les invités ne peuvent pas modifier
            event['guestsCanSeeOtherGuests'] = True  # Les invités peuvent voir les autres
            event['transparency'] = 'opaque'  # Marque comme occupé
            
            # Création de l'événement
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all',  # Envoie l'invitation par email
                conferenceDataVersion=1  # Support des conférences
            ).execute()
            
            # Extraire tous les emails des invités
            all_attendees = [attendee['email'] for attendee in attendees]
            
            return {
                'status': 'success',
                'event_id': created_event['id'],
                'meeting_link': jitsi_link,
                'start_time': start.isoformat(),
                'end_time': end.isoformat(),
                'attendees': all_attendees,
                'calendar_link': created_event.get('htmlLink', ''),
                'created_event': created_event
            }
            
        except HttpError as e:
            print(f"Erreur HTTP lors de la création du rendez-vous: {e}")
            return {
                'status': 'error',
                'message': f'Erreur Google Calendar: {e}'
            }
        except Exception as e:
            print(f"Erreur lors de la création du rendez-vous: {e}")
            return {
                'status': 'error',
                'message': f'Erreur: {e}'
            }
    
    def _create_professional_description(self, base_description: str, jitsi_link: str,
                                        organizer_name: str, organizer_title: str,
                                        organizer_company: str, organizer_email: str) -> str:
        """
        Crée une description professionnelle pour le meeting
        
        Args:
            base_description: Description de base
            jitsi_link: Lien de visioconférence
            organizer_name: Nom de l'organisateur
            organizer_title: Titre de l'organisateur
            organizer_company: Entreprise
            organizer_email: Email de contact
            
        Returns:
            Description formatée professionnellement
        """
        description_parts = []
        
        # Description principale
        if base_description:
            description_parts.append(base_description)
        else:
            description_parts.append("Rendez-vous de découverte des solutions BerinIA")
        
        description_parts.append("")  # Ligne vide
        
        # Informations de connexion
        description_parts.append("📍 INFORMATIONS DE CONNEXION")
        description_parts.append(f"🔗 Lien de visioconférence : {jitsi_link}")
        description_parts.append("💡 Cliquez sur le lien ci-dessus pour rejoindre la réunion")
        description_parts.append("📱 Accessible depuis ordinateur, tablette ou smartphone")
        
        description_parts.append("")  # Ligne vide
        
        # Conseils
        description_parts.append("📋 CONSEILS POUR NOTRE RENDEZ-VOUS")
        description_parts.append("• Testez votre connexion quelques minutes avant")
        description_parts.append("• Préparez vos questions sur l'automatisation")
        description_parts.append("• Ayez sous la main vos défis commerciaux actuels")
        
        description_parts.append("")  # Ligne vide
        
        # Signature professionnelle
        description_parts.append("─────────────────────────────")
        description_parts.append(f"{organizer_name}")
        description_parts.append(f"{organizer_title}")
        description_parts.append(f"{organizer_company}")
        description_parts.append(f"✉️ {organizer_email}")
        description_parts.append("")
        description_parts.append("🤖 Ce rendez-vous a été organisé automatiquement par BerinIA")
        
        return "\n".join(description_parts)
    
    def _generate_jitsi_room_name(self, client_name: str, meeting_date: datetime = None) -> str:
        """
        Génère un nom de salle Jitsi unique et propre avec date
        
        Args:
            client_name: Nom du client
            meeting_date: Date du meeting (pour éviter les conflits)
            
        Returns:
            Nom de salle Jitsi avec format: berinia-nom-JJMM
        """
        # Nettoyer le nom du client
        clean_name = client_name.lower()
        clean_name = ''.join(c if c.isalnum() else '-' for c in clean_name)
        clean_name = '-'.join(filter(None, clean_name.split('-')))  # Supprimer les tirets multiples
        
        # Ajouter la date au format JJMM
        if meeting_date:
            date_suffix = meeting_date.strftime("%d%m")
        else:
            date_suffix = datetime.now().strftime("%d%m")
        
        prefix = self.config.get('jitsi_settings', {}).get('room_prefix', 'berinia')
        return f"{prefix}-{clean_name}-{date_suffix}"
    
    def _get_email_reminders(self) -> Dict[str, Any]:
        """
        Configure les rappels par email Google Calendar
        
        Returns:
            Configuration des rappels
        """
        reminder_settings = self.config.get('reminders', {}).get('email', {})
        
        if not reminder_settings.get('enabled', True):
            return {'useDefault': False, 'overrides': []}
        
        reminder_times = reminder_settings.get('times', [1440, 60, 10])  # J-1, H-1, M-10
        
        overrides = []
        for minutes in reminder_times:
            overrides.append({
                'method': 'email' if minutes >= 60 else 'popup',
                'minutes': minutes
            })
        
        return {
            'useDefault': False,
            'overrides': overrides
        }
    
    def get_meeting_details(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un rendez-vous existant
        
        Args:
            event_id: ID de l'événement Google Calendar
            
        Returns:
            Détails du rendez-vous ou None si non trouvé
        """
        try:
            service = self._get_service()
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            
            return {
                'event_id': event['id'],
                'summary': event.get('summary', ''),
                'description': event.get('description', ''),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'attendees': [att.get('email') for att in event.get('attendees', [])],
                'status': event.get('status', ''),
                'html_link': event.get('htmlLink', '')
            }
            
        except HttpError as e:
            if e.resp.status == 404:
                return None
            print(f"Erreur lors de la récupération du rendez-vous: {e}")
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération du rendez-vous: {e}")
            return None
    
    def cancel_meeting(self, event_id: str) -> bool:
        """
        Annule un rendez-vous
        
        Args:
            event_id: ID de l'événement à annuler
            
        Returns:
            True si l'annulation a réussi, False sinon
        """
        try:
            service = self._get_service()
            service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'  # Notifie les participants
            ).execute()
            return True
            
        except HttpError as e:
            print(f"Erreur lors de l'annulation du rendez-vous: {e}")
            return False
        except Exception as e:
            print(f"Erreur lors de l'annulation du rendez-vous: {e}")
            return False

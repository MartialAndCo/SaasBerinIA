from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class MeetingBase(BaseModel):
    client_name: str = Field(..., description="Nom du client")
    client_email: EmailStr = Field(..., description="Email du client")
    start_time: datetime = Field(..., description="Heure de début du RDV")
    end_time: datetime = Field(..., description="Heure de fin du RDV")
    duration_minutes: Optional[int] = Field(default=30, description="Durée en minutes")
    description: Optional[str] = Field(default=None, description="Description du RDV")
    lead_id: Optional[int] = Field(default=None, description="ID du lead associé")

class MeetingCreate(MeetingBase):
    calendar_event_id: Optional[str] = Field(default=None, description="ID de l'événement Google Calendar")
    meeting_link: Optional[str] = Field(default=None, description="Lien Jitsi du meeting")
    calendar_link: Optional[str] = Field(default=None, description="Lien Google Calendar")
    status: Optional[str] = Field(default="scheduled", description="Statut du RDV")

class MeetingUpdate(BaseModel):
    client_name: Optional[str] = None
    client_email: Optional[EmailStr] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None
    meeting_link: Optional[str] = None
    calendar_link: Optional[str] = None

class MeetingStatusUpdate(BaseModel):
    status: str = Field(..., description="Nouveau statut (scheduled, completed, cancelled, no_show)")
    notes: Optional[str] = Field(default=None, description="Notes optionnelles")

class MeetingFilter(BaseModel):
    lead_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None

class MeetingWithLead(BaseModel):
    id: int
    nom_client: str = Field(alias="client_name")
    email_client: EmailStr = Field(alias="client_email")
    heure_debut: datetime = Field(alias="start_time")
    heure_fin: datetime = Field(alias="end_time")
    duree: Optional[int] = Field(alias="duration_minutes")
    statut: str = Field(alias="status")
    lien_meeting: Optional[str] = Field(alias="meeting_link")
    description: Optional[str] = None
    date_creation: datetime = Field(alias="created_at")
    updated_at: Optional[datetime] = None
    
    # Informations du lead associé
    lead_id: Optional[int] = None
    lead_name: Optional[str] = None
    lead_company: Optional[str] = None
    lead_phone: Optional[str] = None
    
    # Résumé de la conversation (sera ajouté plus tard)
    conversation_summary: Optional[str] = None
    
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class Meeting(BaseModel):
    id: int
    nom_client: str = Field(alias="client_name")
    email_client: EmailStr = Field(alias="client_email")
    heure_debut: datetime = Field(alias="start_time")
    heure_fin: datetime = Field(alias="end_time")
    duree: Optional[int] = Field(alias="duration_minutes")
    statut: str = Field(alias="status")
    lien_meeting: Optional[str] = Field(alias="meeting_link")
    calendar_link: Optional[str] = None
    description: Optional[str] = None
    date_creation: datetime = Field(alias="created_at")
    updated_at: Optional[datetime] = None
    lead_id: Optional[int] = None
    calendar_event_id: Optional[str] = None
    
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class MeetingStats(BaseModel):
    total_meetings: int
    scheduled_meetings: int
    completed_meetings: int
    cancelled_meetings: int
    no_show_meetings: int
    upcoming_today: int
    upcoming_week: int
    
class MeetingActionRequest(BaseModel):
    action: str = Field(..., description="Action à effectuer (reschedule, cancel)")
    new_start_time: Optional[datetime] = Field(default=None, description="Nouvelle heure (pour reschedule)")
    new_duration: Optional[int] = Field(default=None, description="Nouvelle durée (pour reschedule)")
    reason: Optional[str] = Field(default=None, description="Raison de l'action")
    notify_client: Optional[bool] = Field(default=True, description="Notifier le client")
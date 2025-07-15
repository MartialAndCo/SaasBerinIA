from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    calendar_event_id = Column(String, nullable=True, index=True)
    client_name = Column(String(255), nullable=False)
    client_email = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    meeting_link = Column(String(500), nullable=True)
    calendar_link = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="scheduled", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations
    lead = relationship("Lead", back_populates="meetings")
    outcome = relationship("MeetingOutcome", back_populates="meeting", uselist=False)

    # Propriétés calculées pour compatibilité frontend
    @property
    def nom_client(self):
        return self.client_name
    
    @property
    def email_client(self):
        return self.client_email
    
    @property
    def statut(self):
        return self.status
    
    @property
    def heure_debut(self):
        return self.start_time
    
    @property
    def heure_fin(self):
        return self.end_time
    
    @property
    def lien_meeting(self):
        return self.meeting_link
    
    @property
    def duree(self):
        return self.duration_minutes
    
    @property
    def date_creation(self):
        return self.created_at
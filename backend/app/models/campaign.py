from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ville = Column(String, nullable=True)  # NOUVELLE COLONNE
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")
    target_leads = Column(Integer, default=0)
    agent = Column(String, nullable=True)
    niche_id = Column(Integer, nullable=True)
    instantly_campaign_id = Column(String, nullable=True)  # ID de la campagne dans Instantly.ai
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Attributs calculés assignables
        self.progress = 0
        self.conversion = 0.0
    
    # Propriétés calculées pour compatibilité frontend
    @property
    def nom(self):
        return self.name
    
    @property
    def statut(self):
        return self.status
        
    @property
    def date_creation(self):
        return self.created_at

    # Relations temporairement supprimées pour éviter les erreurs
    # niche_id = Column(Integer, ForeignKey("niches.id"))
    # niche = relationship("Niche", back_populates="campaigns")
    # leads = relationship("Lead", back_populates="campaign")
    # messages = relationship("Message", back_populates="campaign")

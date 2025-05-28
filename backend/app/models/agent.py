from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    type = Column(String)
    status = Column(String, default="inactive")
    config = Column(JSON, nullable=True)
    last_run = Column(DateTime, nullable=True)
    leads_generes = Column(Integer, default=0)
    campagnes_actives = Column(Integer, default=0)
    derniere_execution = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations temporairement supprimées pour éviter les erreurs
    # logs = relationship("AgentLog", back_populates="agent", cascade="all, delete-orphan")

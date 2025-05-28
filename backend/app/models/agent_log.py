from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    action = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Propriétés calculées pour compatibilité
    @property
    def operation(self):
        return self.action
        
    @property
    def input_data(self):
        return self.details.get('input_data') if self.details else None
        
    @property
    def output_data(self):
        return self.details.get('output_data') if self.details else None
        
    @property
    def execution_time(self):
        return self.details.get('execution_time', 0.0) if self.details else 0.0
    
    # Relations - temporairement supprimées pour éviter les erreurs
    # agent = relationship("Agent", back_populates="logs")

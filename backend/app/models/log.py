from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.database.base_class import Base

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)
    module = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)
    timestamp = Column(DateTime, default=func.now())
    
    # Propriété calculée pour compatibilité si nécessaire
    @property
    def source(self):
        return self.module

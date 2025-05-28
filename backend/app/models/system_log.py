from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.database.base_class import Base

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20), nullable=False)
    source = Column(String(100), nullable=False)
    agent_name = Column(String(100), nullable=True)
    module = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)
    context_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

"""
Modèles SQLAlchemy pour le système BerinIA.
Ce fichier contient les modèles de données utilisés par le système.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, 
    ForeignKey, Table, Float, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """Modèle pour les utilisateurs du système"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relations
    campaigns = relationship("Campaign", back_populates="created_by_user")
    niches = relationship("Niche", back_populates="created_by_user")


class Agent(Base):
    """Modèle pour les agents du système"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    type = Column(String(50), index=True)
    status = Column(String(50), default="inactive", index=True)
    config = Column(JSONB)
    last_run = Column(DateTime)
    leads_generes = Column(Integer, default=0)
    campagnes_actives = Column(Integer, default=0)
    derniere_execution = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    logs = relationship("AgentLog", back_populates="agent")
    tasks = relationship("Task", back_populates="agent")
    sent_interactions = relationship("AgentInteraction", foreign_keys="AgentInteraction.from_agent_id", back_populates="from_agent")
    received_interactions = relationship("AgentInteraction", foreign_keys="AgentInteraction.to_agent_id", back_populates="to_agent")


class AgentLog(Base):
    """Modèle pour les logs des agents"""
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    action = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(Text)
    details = Column(JSONB)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relations
    agent = relationship("Agent", back_populates="logs")


class Niche(Base):
    """Modèle pour les niches de marché"""
    __tablename__ = "niches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    keywords = Column(ARRAY(String))
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50), default="active", index=True)
    exploration_depth = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    created_by_user = relationship("User", back_populates="niches")
    leads = relationship("Lead", back_populates="niche")
    campaigns = relationship("Campaign", back_populates="niche")


class Lead(Base):
    """Modèle pour les leads (prospects)"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), index=True)
    phone = Column(String(50))
    company = Column(String(255), index=True)
    position = Column(String(100))
    linkedin_url = Column(String(255))
    website = Column(String(255))
    entreprise = Column(String(255))
    industry = Column(String(100))
    niche_id = Column(Integer, ForeignKey("niches.id"), index=True)
    source = Column(String(100))
    status = Column(String(50), default="new", index=True)
    score = Column(Integer, index=True)
    score_details = Column(JSONB)
    validation_status = Column(String(50), default="unvalidated")
    last_contact = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    niche = relationship("Niche", back_populates="leads")
    messages = relationship("Message", back_populates="lead")


class Campaign(Base):
    """Modèle pour les campagnes de prospection"""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    niche_id = Column(Integer, ForeignKey("niches.id"), index=True)
    target_leads = Column(Integer, default=0)
    agent = Column(String(100))
    status = Column(String(50), default="draft", index=True)
    message_template = Column(Text)
    subject_template = Column(String(255))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    niche = relationship("Niche", back_populates="campaigns")
    created_by_user = relationship("User", back_populates="campaigns")
    messages = relationship("Message", back_populates="campaign")


class Message(Base):
    """Modèle pour les messages envoyés aux leads"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), index=True)
    lead_name = Column(String(255))
    lead_email = Column(String(255))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), index=True)
    campaign_name = Column(String(255))
    subject = Column(String(255))
    content = Column(Text)
    status = Column(String(50), default="draft", index=True)
    type = Column(String(50), default="email")
    sent_date = Column(DateTime, index=True)
    open_date = Column(DateTime)
    reply_date = Column(DateTime)
    reply_content = Column(Text)
    sentiment = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    lead = relationship("Lead", back_populates="messages")
    campaign = relationship("Campaign", back_populates="messages")


class AgentInteraction(Base):
    """Modèle pour les interactions entre agents"""
    __tablename__ = "agent_interactions"

    id = Column(Integer, primary_key=True, index=True)
    from_agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    to_agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    message = Column(Text, nullable=False)
    context_id = Column(String(100))
    status = Column(String(50), default="sent")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relations
    from_agent = relationship("Agent", foreign_keys=[from_agent_id], back_populates="sent_interactions")
    to_agent = relationship("Agent", foreign_keys=[to_agent_id], back_populates="received_interactions")


class Task(Base):
    """Modèle pour les tâches planifiées"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    action = Column(String(100), nullable=False)
    parameters = Column(JSONB)
    status = Column(String(50), default="pending", index=True)
    priority = Column(Integer, default=3)
    scheduled_time = Column(DateTime, nullable=False, index=True)
    execution_time = Column(DateTime)
    is_recurring = Column(Boolean, default=False, index=True)
    recurrence_interval = Column(Integer)  # en secondes
    last_run = Column(DateTime)
    result = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    agent = relationship("Agent", back_populates="tasks")


class SystemSetting(Base):
    """Modèle pour les paramètres système"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    data_type = Column(String(50), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    is_editable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Log(Base):
    """Modèle pour les logs système"""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)
    module = Column(String(100))
    message = Column(Text, nullable=False)
    details = Column(JSONB)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from app.database.base_class import Base
import enum

class FrequencyEnum(enum.Enum):
    MANUAL = 'MANUAL'
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'
    CUSTOM_HOURS = 'CUSTOM_HOURS'

class RegionEnum(enum.Enum):
    US = 'US'
    EU = 'EU'

class SystemIntegrations(Base):
    __tablename__ = 'system_integrations'
    
    id = Column(Integer, primary_key=True, index=True)
    twilio_api_key = Column(String, nullable=True)
    twilio_account_sid = Column(String, nullable=True)
    twilio_auth_token = Column(String, nullable=True)
    twilio_integration_active = Column(Boolean, default=False)
    
    mailgun_api_key = Column(String, nullable=True)
    mailgun_domain = Column(String, nullable=True)
    mailgun_region = Column(Enum(RegionEnum), nullable=True)
    mailgun_integration_active = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SystemScheduling(Base):
    __tablename__ = 'system_scheduling'
    
    id = Column(Integer, primary_key=True, index=True)
    agent_group_frequency = Column(Enum(FrequencyEnum), nullable=True)
    agent_group_time = Column(String, nullable=True)
    custom_hours_interval = Column(Integer, nullable=True)
    agent_group_active = Column(Boolean, default=False)
    
    campaign_launch_time = Column(String, nullable=True)
    max_execution_duration = Column(Integer, nullable=True)
    leads_per_campaign = Column(Integer, default=50)
    max_simultaneous_campaigns = Column(Integer, default=5)
    
    daily_report_active = Column(Boolean, default=False)
    daily_report_time = Column(String, nullable=True)
    report_channel_slack = Column(Boolean, default=False)
    report_channel_email = Column(Boolean, default=False)
    report_channel_dashboard = Column(Boolean, default=False)
    
    knowledge_trigger_frequency = Column(Enum(FrequencyEnum), nullable=True)
    max_learning_delay = Column(Integer, default=7)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    email = Column(String)
    telephone = Column(String, nullable=True)
    entreprise = Column(String, nullable=True)
    date_creation = Column(DateTime, default=datetime.utcnow)
    statut = Column(String, default="new")
    
    # Champs d'analyse visuelle
    visual_score = Column(Integer, nullable=True)
    visual_analysis_data = Column(JSONB, nullable=True)
    has_popup = Column(Boolean, nullable=True)
    popup_removed = Column(Boolean, nullable=True)
    screenshot_path = Column(String, nullable=True)
    enhanced_screenshot_path = Column(String, nullable=True)
    visual_analysis_date = Column(DateTime, nullable=True)
    site_type = Column(String, nullable=True)
    visual_quality = Column(Integer, nullable=True)
    website_maturity = Column(String, nullable=True)
    design_strengths = Column(ARRAY(String), nullable=True)
    design_weaknesses = Column(ARRAY(String), nullable=True)

    campagne_id = Column(Integer, ForeignKey("campaigns.id"))
    campaign = relationship("Campaign", back_populates="leads")
    messages = relationship("Message", back_populates="lead")

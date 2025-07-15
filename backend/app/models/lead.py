from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, nullable=True)
    email = Column(String)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    position = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    website = Column(String, nullable=True)
    entreprise = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    niche_id = Column(Integer, nullable=True)
    source = Column(String, nullable=True)
    status = Column(String, default="new")
    score = Column(Integer, nullable=True)
    score_details = Column(JSONB, nullable=True)
    validation_status = Column(String, default="unvalidated")
    last_contact = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
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
    
    # Champs de facturation
    billing_address = Column(Text, nullable=True)
    billing_city = Column(String(255), nullable=True)
    billing_postal_code = Column(String(20), nullable=True)
    billing_country = Column(String(100), nullable=True)
    vat_number = Column(String(50), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_contact_name = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)

    # Propriétés calculées pour compatibilité frontend
    @property
    def nom(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.first_name
    
    @property
    def telephone(self):
        return self.phone
        
    @property
    def statut(self):
        return self.status
        
    @property
    def date_creation(self):
        return self.created_at

    # Relations - ✅ ACTIVÉ: colonne campagne_id (cohérent avec le système)
    campagne_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    # campaign = relationship("Campaign", back_populates="leads")
    # messages = relationship("Message", back_populates="lead")
    meetings = relationship("Meeting", back_populates="lead")

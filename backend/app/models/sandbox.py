from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from app.database.base_class import Base

class SandboxLead(Base):
    """
    Modèle pour les leads de test du sandbox
    Basé sur le modèle Lead avec des champs supplémentaires pour les tests
    """
    __tablename__ = "sandbox_leads"

    id = Column(Integer, primary_key=True, index=True)
    
    # Champs de base (identiques au modèle Lead)
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
    
    # Champs spécifiques au sandbox
    is_test = Column(Boolean, default=True)
    test_platform = Column(String)  # 'sms' ou 'email'
    template_used = Column(String, nullable=True)
    created_by_user = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    campagne_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)

    # Propriétés calculées pour compatibilité
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


class SandboxConversation(Base):
    """
    Modèle pour stocker les conversations du sandbox avec système de sessions
    """
    __tablename__ = "sandbox_conversations"

    id = Column(Integer, primary_key=True, index=True)
    sandbox_lead_id = Column(Integer, ForeignKey("sandbox_leads.id"))
    
    # 🆕 NOUVEAU SYSTÈME DE SESSIONS
    conversation_session_id = Column(String(100), index=True)  # ex: "conv_20250606_1234567"
    message_order = Column(Integer, default=0)  # Ordre dans la session: 1, 2, 3...
    message_type = Column(String(20), default="exchange")  # 'start', 'user', 'ai', 'exchange'
    
    # Structure de messages améliorée
    messages = Column(JSONB)  # {"user": "...", "ai": "...", "timestamp": "...", "platform": "sms"}
    platform = Column(String)  # 'sms' ou 'email'
    status = Column(String, default="active")  # active, completed, archived
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Méthodes utilitaires pour les sessions
    @property
    def session_display_name(self):
        """Nom d'affichage de la session pour l'interface"""
        if self.messages and isinstance(self.messages, dict):
            timestamp = self.created_at.strftime("%d/%m %H:%M")
            return f"Session {timestamp}"
        return f"Session {self.conversation_session_id}"
    
    @classmethod
    def generate_session_id(cls):
        """Génère un ID unique pour une nouvelle session"""
        from datetime import datetime
        import random
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = random.randint(1000, 9999)
        return f"conv_{timestamp}_{random_suffix}"


class SandboxTemplate(Base):
    """
    Modèle pour les templates de profils prédéfinis
    """
    __tablename__ = "sandbox_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # "Restaurant traditionnel", "E-commerce moderne"
    description = Column(Text)
    template_data = Column(JSONB)  # Données du template
    category = Column(String)  # "restaurant", "artisan", "commerce"
    created_at = Column(DateTime, default=datetime.utcnow)

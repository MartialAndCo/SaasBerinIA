from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class SandboxLeadBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    entreprise: Optional[str] = None
    industry: Optional[str] = None
    niche_id: Optional[int] = None
    source: Optional[str] = None
    status: str = "new"
    score: Optional[int] = None
    score_details: Optional[Dict[str, Any]] = None
    validation_status: str = "unvalidated"
    notes: Optional[str] = None
    
    # Champs d'analyse visuelle
    visual_score: Optional[int] = None
    visual_analysis_data: Optional[Dict[str, Any]] = None
    has_popup: Optional[bool] = None
    popup_removed: Optional[bool] = None
    site_type: Optional[str] = None
    visual_quality: Optional[int] = None
    website_maturity: Optional[str] = None
    design_strengths: Optional[List[str]] = None
    design_weaknesses: Optional[List[str]] = None
    
    # Champs spécifiques au sandbox
    test_platform: str  # 'sms' ou 'email'
    template_used: Optional[str] = None
    campagne_id: Optional[int] = None

    @validator('test_platform')
    def validate_platform(cls, v):
        if v not in ['sms', 'email']:
            raise ValueError('Platform must be either "sms" or "email"')
        return v

class SandboxLeadCreate(SandboxLeadBase):
    pass

class SandboxLead(SandboxLeadBase):
    id: int
    is_test: bool
    created_by_user: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 🆕 NOUVEAUX SCHEMAS POUR LE SYSTÈME DE SESSIONS

class SandboxMessageRequest(BaseModel):
    sandbox_lead_id: int
    platform: str
    user_message: Optional[str] = None
    action: str  # "start_conversation", "send_response", "reset_conversation"
    conversation_session_id: Optional[str] = None  # Pour continuer une session existante

    @validator('platform')
    def validate_platform(cls, v):
        if v not in ['sms', 'email']:
            raise ValueError('Platform must be either "sms" or "email"')
        return v
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['start_conversation', 'send_response', 'reset_conversation']:
            raise ValueError('Action must be start_conversation, send_response or reset_conversation')
        return v

class SandboxMessageResponse(BaseModel):
    success: bool
    message: str
    ai_response: Optional[str] = None  # Garder pour compatibilité
    ai_subject: Optional[str] = None   # Nouveau : objet séparé
    ai_content: Optional[str] = None   # Nouveau : contenu séparé
    conversation_session_id: Optional[str] = None
    message_order: Optional[int] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class SandboxConversationBase(BaseModel):
    sandbox_lead_id: int
    conversation_session_id: str
    message_order: int
    message_type: str = "exchange"  # 'start', 'user', 'ai', 'exchange'
    messages: Dict[str, Any]  # {"user": "...", "ai": "...", "timestamp": "...", "platform": "sms"}
    platform: str
    status: str = "active"
    notes: Optional[str] = None

class SandboxConversationCreate(SandboxConversationBase):
    pass

class SandboxConversation(SandboxConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SandboxConversationHistoryResponse(BaseModel):
    """Réponse contenant l'historique complet d'une conversation"""
    conversation_session_id: str
    sandbox_lead_id: int
    platform: str
    total_messages: int
    conversation_start: datetime
    conversation_end: Optional[datetime] = None
    messages: List[SandboxConversation]
    lead_info: Optional[Dict[str, Any]] = None

class SandboxConversationListResponse(BaseModel):
    """Liste des conversations d'un lead avec résumés"""
    sandbox_lead_id: int
    conversations: List[Dict[str, Any]]  # [{"session_id": "...", "start_time": "...", "message_count": 3, "platform": "sms"}]
    total_conversations: int

class SandboxResetRequest(BaseModel):
    """Requête pour réinitialiser une conversation"""
    sandbox_lead_id: int
    platform: str
    keep_lead: bool = True  # Garder le lead, juste créer une nouvelle conversation

class SandboxResetResponse(BaseModel):
    """Réponse après réinitialisation"""
    success: bool
    message: str
    new_conversation_session_id: str
    previous_session_archived: bool = False

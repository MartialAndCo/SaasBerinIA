from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class LeadBase(BaseModel):
    nom: str
    email: EmailStr
    telephone: Optional[str] = None
    entreprise: Optional[str] = None
    campagne_id: Optional[int] = None

class LeadCreate(LeadBase):
    statut: Optional[str] = "new"

class LeadUpdate(BaseModel):
    nom: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    entreprise: Optional[str] = None
    statut: Optional[str] = None
    campagne_id: Optional[int] = None
    # Champs de facturation
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None
    vat_number: Optional[str] = None
    billing_email: Optional[EmailStr] = None
    billing_contact_name: Optional[str] = None

class LeadStatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None

class VisualAnalysisBase(BaseModel):
    visual_score: Optional[int] = None
    has_popup: Optional[bool] = None
    popup_removed: Optional[bool] = None
    screenshot_path: Optional[str] = None
    enhanced_screenshot_path: Optional[str] = None
    site_type: Optional[str] = None
    visual_quality: Optional[int] = None
    website_maturity: Optional[str] = None
    design_strengths: Optional[List[str]] = None
    design_weaknesses: Optional[List[str]] = None

class VisualAnalysisCreate(VisualAnalysisBase):
    lead_id: int
    visual_analysis_data: Optional[Dict[str, Any]] = None
    visual_analysis_date: Optional[datetime] = datetime.utcnow()

class VisualAnalysisUpdate(VisualAnalysisBase):
    visual_analysis_data: Optional[Dict[str, Any]] = None
    visual_analysis_date: Optional[datetime] = datetime.utcnow()

class Lead(BaseModel):
    id: int
    # Mapping direct des champs avec les alias pour compatibilité frontend
    nom: Optional[str] = Field(default=None, description="Nom complet du lead")
    email: EmailStr
    telephone: Optional[str] = Field(default=None, alias="phone")
    entreprise: Optional[str] = Field(default=None, alias="company")
    statut: str = Field(default="new", alias="status")
    date_creation: datetime = Field(alias="created_at")
    updated_at: Optional[datetime] = None
    campagne_id: Optional[int] = None
    
    # Champs pour construction du nom
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Champs d'analyse visuelle
    visual_score: Optional[int] = None
    has_popup: Optional[bool] = None
    popup_removed: Optional[bool] = None
    screenshot_path: Optional[str] = None
    enhanced_screenshot_path: Optional[str] = None
    visual_analysis_date: Optional[datetime] = None
    site_type: Optional[str] = None
    visual_quality: Optional[int] = None
    website_maturity: Optional[str] = None
    design_strengths: Optional[List[str]] = None
    design_weaknesses: Optional[List[str]] = None
    visual_analysis_data: Optional[Dict[str, Any]] = None
    
    # Champs de facturation
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None
    vat_number: Optional[str] = None
    billing_email: Optional[EmailStr] = None
    billing_contact_name: Optional[str] = None
    stripe_customer_id: Optional[str] = None

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
        
        # Permettre l'utilisation des alias dans les deux sens
        @staticmethod
        def alias_generator(field_name: str) -> str:
            # Mapping des noms de champs
            aliases = {
                'telephone': 'phone',
                'entreprise': 'company', 
                'statut': 'status',
                'date_creation': 'created_at'
            }
            return aliases.get(field_name, field_name)

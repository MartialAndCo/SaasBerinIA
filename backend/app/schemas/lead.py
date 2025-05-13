from pydantic import BaseModel, EmailStr
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

class Lead(LeadBase):
    id: int
    statut: str
    date_creation: datetime
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

    class Config:
        orm_mode = True

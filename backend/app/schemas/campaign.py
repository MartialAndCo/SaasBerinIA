from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CampaignBase(BaseModel):
    nom: str = Field(..., alias="name")  # ✅ Alias pour compatibilité
    description: Optional[str] = None
    niche_id: int
    target_leads: Optional[int] = 0
    agent: Optional[str] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, alias="name")
    description: Optional[str] = None
    statut: Optional[str] = Field(default=None, alias="status")
    niche_id: Optional[int] = None
    target_leads: Optional[int] = None
    agent: Optional[str] = None

class Campaign(CampaignBase):
    id: int
    statut: str = Field(..., alias="status")  # ✅ Alias pour compatibilité
    date_creation: datetime = Field(..., alias="created_at")  # ✅ Alias pour compatibilité
    leads: Optional[int] = 0
    conversion: Optional[float] = 0.0
    progress: Optional[int] = 0

    class Config:
        from_attributes = True
        populate_by_name = True  # ✅ Permet d'utiliser les alias

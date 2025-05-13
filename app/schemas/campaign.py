from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    niche: str
    agent: Optional[str] = None
    targetLeads: Optional[int] = 500


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    targetLeads: Optional[int] = None
    agent: Optional[str] = None


class CampaignInDB(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    date: datetime
    status: str
    niche_id: int
    
    class Config:
        orm_mode = True


class Campaign(BaseModel):
    id: int
    name: str
    niche: str
    status: str
    leads: int
    conversion: float
    date: str
    agent: str
    progress: int
    description: Optional[str] = None
    targetLeads: Optional[int] = None
    
    class Config:
        orm_mode = True 
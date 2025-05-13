from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class LeadBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company: str
    status: str


class LeadCreate(LeadBase):
    campaign_id: int


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None


class LeadInDB(LeadBase):
    id: int
    date: datetime
    campaign_id: int
    
    class Config:
        orm_mode = True


class Lead(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    company: str
    campaign: str
    status: str
    date: str
    
    class Config:
        orm_mode = True 
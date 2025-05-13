from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class MailgunConfigCreate(BaseModel):
    api_key: str
    domain: str

class TwilioConfigCreate(BaseModel):
    account_sid: str
    auth_token: str
    phone_number: str

class MessengerDirectivesCreate(BaseModel):
    niche: Optional[str] = None
    campaign_id: Optional[int] = None
    directives: Dict[str, Any] = Field(..., description="Flexible directives for messaging")

class MessengerDirectivesResponse(MessengerDirectivesCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

from pydantic import BaseModel
from typing import Optional, Dict, List, Any, Union
from datetime import datetime

class AgentBase(BaseModel):
    name: str
    type: str
    status: Optional[str] = "inactive"

class AgentCreate(AgentBase):
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class Agent(AgentBase):
    id: int
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    last_run: Optional[datetime] = None
    derniere_execution: Optional[datetime] = None
    leads_generes: int = 0
    campagnes_actives: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SystemLogBase(BaseModel):
    level: str
    source: str
    agent_name: Optional[str] = None
    module: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None
    context_id: Optional[str] = None

class SystemLogCreate(SystemLogBase):
    pass

class SystemLogUpdate(BaseModel):
    level: Optional[str] = None
    source: Optional[str] = None
    agent_name: Optional[str] = None
    module: Optional[str] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    context_id: Optional[str] = None

class SystemLog(SystemLogBase):
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class SystemLogResponse(BaseModel):
    logs: list[SystemLog]
    total: int
    page: int
    per_page: int
    total_pages: int

class SystemLogStats(BaseModel):
    total_logs: int
    by_level: Dict[str, int]
    by_source: Dict[str, int]
    by_agent: Dict[str, int]
    recent_hour: int

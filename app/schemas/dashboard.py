from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    campaigns: Dict[str, Any]
    leads: Dict[str, Any]
    niches: Dict[str, Any]
    agents: Dict[str, Any]


class RecentActivity(BaseModel):
    id: int
    type: str  # "campaign", "lead", "niche", "agent"
    action: str
    description: str
    timestamp: str 
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Trend(BaseModel):
    value: float
    change: float
    trend: str  # "up", "down", "neutral"


class OverviewStats(BaseModel):
    leadsCollected: Trend
    conversionRate: Trend
    openRate: Trend
    costPerLead: Trend


class ChartDataPoint(BaseModel):
    date: str
    value: float


class CampaignComparisonData(BaseModel):
    name: str
    leads: int
    conversion: float


class NicheComparisonData(BaseModel):
    name: str
    conversion: float
    cost: float
    leads: int 
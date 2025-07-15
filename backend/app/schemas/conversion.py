"""Schémas Pydantic pour le suivi des conversions"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal

# === SERVICES ===
class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    setup_price: Decimal
    monthly_price: Decimal
    is_bundle: bool = False
    bundle_services: Optional[Dict[str, Any]] = None

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === MEETING OUTCOMES ===
class MeetingOutcomeBase(BaseModel):
    meeting_id: int
    outcome_type: str = Field(..., pattern="^(accepted|refused|thinking|no_show)$")
    refusal_reason: Optional[str] = Field(None, pattern="^(price_too_high|no_budget|internal_solution|bad_timing|not_convinced|competitor|other)$")
    refusal_details: Optional[str] = None
    follow_up_date: Optional[date] = None
    notes: Optional[str] = None

class MeetingOutcomeCreate(MeetingOutcomeBase):
    pass

class MeetingOutcomeUpdate(BaseModel):
    outcome_type: Optional[str] = Field(None, pattern="^(accepted|refused|thinking|no_show)$")
    refusal_reason: Optional[str] = Field(None, pattern="^(price_too_high|no_budget|internal_solution|bad_timing|not_convinced|competitor|other)$")
    refusal_details: Optional[str] = None
    follow_up_date: Optional[date] = None
    notes: Optional[str] = None

class MeetingOutcome(MeetingOutcomeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === SALES ===
class SaleServiceItem(BaseModel):
    service_id: int
    setup_price: Decimal
    monthly_price: Decimal
    start_date: Optional[date] = None
    
class SaleBase(BaseModel):
    client_name: str
    client_email: Optional[str] = None
    client_company: Optional[str] = None
    sale_date: date
    payment_status: str = Field("pending", pattern="^(pending|partial|paid)$")
    payment_date: Optional[date] = None
    notes: Optional[str] = None

class SaleCreate(SaleBase):
    meeting_outcome_id: int
    services: List[SaleServiceItem]

class SaleUpdate(BaseModel):
    payment_status: Optional[str] = Field(None, pattern="^(pending|partial|paid)$")
    payment_date: Optional[date] = None
    notes: Optional[str] = None

class Sale(SaleBase):
    id: int
    meeting_outcome_id: int
    total_setup_price: Decimal
    total_monthly_price: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SaleWithServices(Sale):
    sale_services: List['SaleServiceDetail']

# === SALE SERVICES ===
class SaleServiceBase(BaseModel):
    setup_price: Decimal
    monthly_price: Decimal
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = Field("active", pattern="^(active|paused|cancelled)$")

class SaleServiceCreate(SaleServiceBase):
    sale_id: int
    service_id: int

class SaleServiceDetail(SaleServiceBase):
    id: int
    sale_id: int
    service_id: int
    service: Service
    created_at: datetime
    
    class Config:
        from_attributes = True

# === STATISTIQUES ===
class ConversionStats(BaseModel):
    month: datetime
    total_meetings: int
    conversions: int
    refusals: int
    thinking: int
    conversion_rate: Optional[Decimal]

class RefusalStats(BaseModel):
    refusal_reason: str
    count: int
    percentage: Optional[Decimal]

class RevenueStats(BaseModel):
    month: datetime
    sales_count: int
    total_setup_revenue: Optional[Decimal]
    monthly_recurring_revenue: Optional[Decimal]
    avg_annual_value: Optional[Decimal]

# === REQUÊTES COMPLEXES ===
class MeetingConversionRequest(BaseModel):
    """Requête pour enregistrer la conversion d'un rendez-vous"""
    outcome_type: str = Field(..., pattern="^(accepted|refused|thinking|no_show)$")
    
    # Si refusé
    refusal_reason: Optional[str] = Field(None, pattern="^(price_too_high|no_budget|internal_solution|bad_timing|not_convinced|competitor|other)$")
    refusal_details: Optional[str] = None
    
    # Si à réfléchir
    follow_up_date: Optional[date] = None
    
    # Si accepté
    services: Optional[List[SaleServiceItem]] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_company: Optional[str] = None
    sale_date: Optional[date] = None
    
    notes: Optional[str] = None

class ConversionSummary(BaseModel):
    """Résumé complet d'une conversion"""
    meeting_outcome: MeetingOutcome
    sale: Optional[SaleWithServices] = None
    total_annual_value: Optional[Decimal] = None

# Mise à jour des forward references
SaleWithServices.model_rebuild()
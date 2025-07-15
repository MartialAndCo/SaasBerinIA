from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class BillingInfoBase(BaseModel):
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None
    vat_number: Optional[str] = None
    billing_email: Optional[EmailStr] = None
    billing_contact_name: Optional[str] = None

class BillingInfoUpdate(BillingInfoBase):
    pass

class BillingInfo(BillingInfoBase):
    lead_id: int
    stripe_customer_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class ServiceSelection(BaseModel):
    service_id: int
    quantity: int = 1
    custom_price: Optional[float] = None
    description: Optional[str] = None

class InvoiceCreate(BaseModel):
    lead_id: int
    services: List[ServiceSelection]
    billing_info: Optional[BillingInfoBase] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    send_email: bool = True

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None

class InvoiceBase(BaseModel):
    lead_id: int
    sale_id: Optional[int] = None
    invoice_number: str
    amount: float
    tax_amount: Optional[float] = None
    total_amount: float
    currency: str = 'EUR'
    status: str = 'draft'
    invoice_date: datetime
    due_date: Optional[datetime] = None
    services_data: Optional[Dict[str, Any]] = None
    billing_data: Optional[Dict[str, Any]] = None

class Invoice(InvoiceBase):
    id: int
    stripe_invoice_id: Optional[str] = None
    paid_date: Optional[datetime] = None
    pdf_url: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceListItem(BaseModel):
    id: int
    invoice_number: str
    lead_name: str
    company: Optional[str] = None
    total_amount: float
    currency: str
    status: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CreateInvoiceResponse(BaseModel):
    invoice: Invoice
    stripe_invoice_url: Optional[str] = None
    message: str
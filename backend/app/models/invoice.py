from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True)
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    stripe_invoice_id = Column(String(255), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default='EUR')
    status = Column(String(20), nullable=False, default='draft', index=True)
    invoice_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    due_date = Column(DateTime, nullable=True)
    paid_date = Column(DateTime, nullable=True)
    pdf_url = Column(String(500), nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    services_data = Column(JSON, nullable=True)
    billing_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    lead = relationship("Lead", backref="invoices")
    sale = relationship("Sale", backref="invoices")
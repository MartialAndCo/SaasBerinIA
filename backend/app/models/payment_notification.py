from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base


class PaymentNotification(Base):
    __tablename__ = "payment_notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relations
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    
    # Stripe information
    stripe_event_id = Column(String, unique=True, index=True)
    stripe_event_type = Column(String)  # invoice.payment_succeeded, invoice.payment_failed, etc.
    
    # Notification details
    notification_type = Column(String)  # payment_success, payment_failed, etc.
    amount = Column(Integer)  # Amount in cents
    currency = Column(String, default="eur")
    
    # Client information (dénormalisé pour éviter les jointures)
    client_name = Column(String)
    client_email = Column(String)
    
    # Additional data from Stripe
    stripe_data = Column(JSON)
    
    # Notification status
    sent_to_telegram = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(String)  # If notification failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    invoice = relationship("Invoice", backref="payment_notifications")
    lead = relationship("Lead", backref="payment_notifications")
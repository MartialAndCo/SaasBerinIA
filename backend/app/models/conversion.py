"""Modèles pour le suivi des conversions de rendez-vous"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    setup_price = Column(Numeric(10, 2), nullable=False, default=0)
    monthly_price = Column(Numeric(10, 2), nullable=False, default=0)
    is_bundle = Column(Boolean, default=False)
    bundle_services = Column(JSON)  # Pour les forfaits combinés
    # Intégration Stripe
    stripe_product_id = Column(String(255), nullable=True, index=True)
    stripe_price_id = Column(String(255), nullable=True, index=True)  # Prix par défaut
    product_type = Column(String(20), default='one_time')  # one_time, recurring, bundle
    sync_with_stripe = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    sale_services = relationship("SaleService", back_populates="service")
    
    @property
    def price(self):
        """Propriété calculée pour compatibilité avec le système de facturation.
        Retourne setup_price + monthly_price comme prix total."""
        return float(self.setup_price or 0) + float(self.monthly_price or 0)
    
    @property
    def default_price(self):
        """Prix par défaut à utiliser pour facturation (setup_price si existe, sinon monthly_price)."""
        if self.setup_price and self.setup_price > 0:
            return float(self.setup_price)
        return float(self.monthly_price or 0)

class MeetingOutcome(Base):
    __tablename__ = "meeting_outcomes"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    outcome_type = Column(String(20), nullable=False)  # accepted, refused, thinking, no_show
    refusal_reason = Column(String(50))  # price_too_high, no_budget, etc.
    refusal_details = Column(Text)  # Pour "autre" ou précisions
    follow_up_date = Column(Date)  # Pour les "thinking"
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    meeting = relationship("Meeting", back_populates="outcome")
    sales = relationship("Sale", back_populates="meeting_outcome")

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_outcome_id = Column(Integer, ForeignKey("meeting_outcomes.id", ondelete="CASCADE"))
    client_name = Column(String(255), nullable=False)
    client_email = Column(String(255))
    client_company = Column(String(255))
    total_setup_price = Column(Numeric(10, 2), nullable=False, default=0)
    total_monthly_price = Column(Numeric(10, 2), nullable=False, default=0)
    sale_date = Column(Date, nullable=False)
    payment_status = Column(String(20), default='pending')  # pending, partial, paid
    payment_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    meeting_outcome = relationship("MeetingOutcome", back_populates="sales")
    sale_services = relationship("SaleService", back_populates="sale")

class SaleService(Base):
    __tablename__ = "sale_services"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"))
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"))
    setup_price = Column(Numeric(10, 2), nullable=False)
    monthly_price = Column(Numeric(10, 2), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)  # NULL pour abonnements actifs
    status = Column(String(20), default='active')  # active, paused, cancelled
    created_at = Column(DateTime, default=func.now())
    
    # Relations
    sale = relationship("Sale", back_populates="sale_services")
    service = relationship("Service", back_populates="sale_services")

class StripeProductSync(Base):
    __tablename__ = "stripe_product_sync"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_timestamp = Column(DateTime, nullable=False, index=True)
    products_count = Column(Integer, nullable=False)
    one_time_products = Column(Integer, nullable=False, default=0)
    recurring_products = Column(Integer, nullable=False, default=0)
    sync_status = Column(String(20), nullable=False, default='success', index=True)
    error_message = Column(Text, nullable=True)
    sync_data = Column(JSON, nullable=True)  # Stockage des données de sync pour debug
    created_at = Column(DateTime, nullable=False, default=func.now())
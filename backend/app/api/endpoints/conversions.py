"""Endpoints API pour le suivi des conversions de rendez-vous"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.api import deps
from app.schemas.conversion import (
    Service, ServiceCreate,
    MeetingOutcome, MeetingOutcomeCreate, MeetingOutcomeUpdate,
    Sale, SaleCreate, SaleUpdate, SaleWithServices,
    ConversionStats, RefusalStats, RevenueStats,
    MeetingConversionRequest, ConversionSummary
)
from app.models.conversion import (
    Service as ServiceModel,
    MeetingOutcome as MeetingOutcomeModel,
    Sale as SaleModel,
    SaleService as SaleServiceModel
)
from app.models.meeting import Meeting as MeetingModel

router = APIRouter()

# === SERVICES ===
@router.get("/services/", response_model=List[Service])
def get_services(db: Session = Depends(deps.get_db)):
    """Récupère la liste des services disponibles"""
    return db.query(ServiceModel).all()

@router.post("/services/", response_model=Service)
def create_service(service: ServiceCreate, db: Session = Depends(deps.get_db)):
    """Crée un nouveau service"""
    db_service = ServiceModel(**service.dict())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

# === CONVERSION DE RENDEZ-VOUS ===
@router.post("/meetings/{meeting_id}/convert")
def convert_meeting(
    meeting_id: int,
    conversion: MeetingConversionRequest,
    db: Session = Depends(deps.get_db)
):
    """Enregistre le résultat d'un rendez-vous (conversion, refus, etc.)"""
    
    # Vérifier que le meeting existe
    meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Rendez-vous non trouvé")
    
    # Vérifier qu'il n'y a pas déjà un outcome pour ce meeting
    existing_outcome = db.query(MeetingOutcomeModel).filter(
        MeetingOutcomeModel.meeting_id == meeting_id
    ).first()
    if existing_outcome:
        raise HTTPException(
            status_code=400, 
            detail="Ce rendez-vous a déjà un résultat enregistré"
        )
    
    # Créer le meeting outcome
    outcome_data = {
        "meeting_id": meeting_id,
        "outcome_type": conversion.outcome_type,
        "refusal_reason": conversion.refusal_reason,
        "refusal_details": conversion.refusal_details,
        "follow_up_date": conversion.follow_up_date,
        "notes": conversion.notes
    }
    
    db_outcome = MeetingOutcomeModel(**outcome_data)
    db.add(db_outcome)
    db.flush()  # Pour obtenir l'ID
    
    # Si accepté, créer la vente
    sale = None
    if conversion.outcome_type == "accepted" and conversion.services:
        # Calculer les totaux
        total_setup = sum(service.setup_price for service in conversion.services)
        total_monthly = sum(service.monthly_price for service in conversion.services)
        
        # Créer la vente
        sale_data = {
            "meeting_outcome_id": db_outcome.id,
            "client_name": conversion.client_name or meeting.client_name,
            "client_email": conversion.client_email or meeting.client_email,
            "client_company": conversion.client_company or "Non renseignée",
            "total_setup_price": total_setup,
            "total_monthly_price": total_monthly,
            "sale_date": conversion.sale_date or date.today(),
            "payment_status": "pending"
        }
        
        db_sale = SaleModel(**sale_data)
        db.add(db_sale)
        db.flush()
        
        # Créer les services vendus
        for service_item in conversion.services:
            # Vérifier que le service existe
            service = db.query(ServiceModel).filter(
                ServiceModel.id == service_item.service_id
            ).first()
            if not service:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Service {service_item.service_id} non trouvé"
                )
            
            sale_service = SaleServiceModel(
                sale_id=db_sale.id,
                service_id=service_item.service_id,
                setup_price=service_item.setup_price,
                monthly_price=service_item.monthly_price,
                start_date=service_item.start_date or date.today()
            )
            db.add(sale_service)
        
        sale = db_sale
    
    db.commit()
    
    # Retourner le résumé
    return {
        "meeting_outcome_id": db_outcome.id,
        "sale_id": sale.id if sale else None,
        "message": f"Rendez-vous marqué comme '{conversion.outcome_type}'"
    }

@router.get("/meetings/{meeting_id}/outcome", response_model=Optional[ConversionSummary])
def get_meeting_outcome(meeting_id: int, db: Session = Depends(deps.get_db)):
    """Récupère le résultat d'un rendez-vous"""
    
    outcome = db.query(MeetingOutcomeModel).filter(
        MeetingOutcomeModel.meeting_id == meeting_id
    ).first()
    
    if not outcome:
        return None
    
    result = {"meeting_outcome": outcome}
    
    # Si il y a une vente, l'inclure avec les services
    if outcome.sales:
        sale = outcome.sales[0]  # Une conversion = une vente
        
        # Calculer la valeur annuelle
        annual_value = sale.total_setup_price + (sale.total_monthly_price * 12)
        
        result.update({
            "sale": sale,
            "total_annual_value": annual_value
        })
    
    return result

# === STATISTIQUES ===
@router.get("/stats/conversions", response_model=List[ConversionStats])
def get_conversion_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(deps.get_db)
):
    """Récupère les statistiques de conversion par mois"""
    
    query = db.query(
        func.date_trunc('month', MeetingOutcomeModel.created_at).label('month'),
        func.count().label('total_meetings'),
        func.count().filter(MeetingOutcomeModel.outcome_type == 'accepted').label('conversions'),
        func.count().filter(MeetingOutcomeModel.outcome_type == 'refused').label('refusals'),
        func.count().filter(MeetingOutcomeModel.outcome_type == 'thinking').label('thinking'),
        (func.count().filter(MeetingOutcomeModel.outcome_type == 'accepted') * 100.0 / 
         func.nullif(func.count(), 0)).label('conversion_rate')
    ).group_by(func.date_trunc('month', MeetingOutcomeModel.created_at))
    
    if start_date:
        query = query.filter(MeetingOutcomeModel.created_at >= start_date)
    if end_date:
        query = query.filter(MeetingOutcomeModel.created_at <= end_date)
    
    return query.order_by(desc('month')).all()

@router.get("/stats/refusals", response_model=List[RefusalStats])
def get_refusal_stats(db: Session = Depends(deps.get_db)):
    """Récupère les statistiques des raisons de refus"""
    
    total_refusals = db.query(func.count(MeetingOutcomeModel.id)).filter(
        MeetingOutcomeModel.outcome_type == 'refused'
    ).scalar()
    
    if total_refusals == 0:
        return []
    
    query = db.query(
        MeetingOutcomeModel.refusal_reason,
        func.count().label('count'),
        (func.count() * 100.0 / total_refusals).label('percentage')
    ).filter(
        and_(
            MeetingOutcomeModel.outcome_type == 'refused',
            MeetingOutcomeModel.refusal_reason.isnot(None)
        )
    ).group_by(MeetingOutcomeModel.refusal_reason)
    
    return query.order_by(desc('count')).all()

@router.get("/stats/revenue", response_model=List[RevenueStats])
def get_revenue_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(deps.get_db)
):
    """Récupère les statistiques de revenus par mois"""
    
    query = db.query(
        func.date_trunc('month', SaleModel.sale_date).label('month'),
        func.count().label('sales_count'),
        func.sum(SaleModel.total_setup_price).label('total_setup_revenue'),
        func.sum(SaleModel.total_monthly_price).label('monthly_recurring_revenue'),
        func.avg(SaleModel.total_setup_price + SaleModel.total_monthly_price * 12).label('avg_annual_value')
    ).filter(
        SaleModel.payment_status.in_(['paid', 'partial'])
    ).group_by(func.date_trunc('month', SaleModel.sale_date))
    
    if start_date:
        query = query.filter(SaleModel.sale_date >= start_date)
    if end_date:
        query = query.filter(SaleModel.sale_date <= end_date)
    
    return query.order_by(desc('month')).all()

# === GESTION DES VENTES ===
@router.get("/sales/", response_model=List[SaleWithServices])
def get_sales(
    limit: int = 20,
    offset: int = 0,
    payment_status: Optional[str] = None,
    db: Session = Depends(deps.get_db)
):
    """Récupère la liste des ventes"""
    
    query = db.query(SaleModel).options(
        joinedload(SaleModel.sale_services).joinedload(SaleServiceModel.service)
    )
    
    if payment_status:
        query = query.filter(SaleModel.payment_status == payment_status)
    
    return query.order_by(desc(SaleModel.created_at)).offset(offset).limit(limit).all()

@router.put("/sales/{sale_id}/payment", response_model=Sale)
def update_sale_payment(
    sale_id: int,
    payment_update: SaleUpdate,
    db: Session = Depends(deps.get_db)
):
    """Met à jour le statut de paiement d'une vente"""
    
    sale = db.query(SaleModel).filter(SaleModel.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Vente non trouvée")
    
    for field, value in payment_update.dict(exclude_unset=True).items():
        setattr(sale, field, value)
    
    sale.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sale)
    
    return sale

# === SUIVI ET RELANCES ===
@router.get("/follow-ups/")
def get_follow_ups(db: Session = Depends(deps.get_db)):
    """Récupère les prospects à relancer (thinking + date de suivi passée)"""
    
    today = date.today()
    
    follow_ups = db.query(MeetingOutcomeModel).filter(
        and_(
            MeetingOutcomeModel.outcome_type == 'thinking',
            MeetingOutcomeModel.follow_up_date <= today
        )
    ).all()
    
    return [
        {
            "meeting_outcome_id": outcome.id,
            "meeting_id": outcome.meeting_id,
            "follow_up_date": outcome.follow_up_date,
            "notes": outcome.notes,
            "days_overdue": (today - outcome.follow_up_date).days
        }
        for outcome in follow_ups
    ]
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

from app.database.connection import get_db
from app.models import Lead, Invoice, Service, Sale, Meeting
from app.schemas.billing import (
    BillingInfo, BillingInfoUpdate, 
    Invoice as InvoiceSchema, InvoiceCreate, InvoiceUpdate,
    InvoiceListItem, CreateInvoiceResponse
)
from app.services.stripe_service import StripeService
from app.services.stripe_products_mapping import (
    validate_and_complete_invoice_items,
    get_subscription_for_product,
    is_subscription_product
)

router = APIRouter()
logger = logging.getLogger(__name__)
stripe_service = StripeService()

@router.get("/lead/{lead_id}", response_model=BillingInfo)
def get_lead_billing_info(lead_id: int, db: Session = Depends(get_db)):
    """Récupérer les informations de facturation d'un lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    
    return BillingInfo(
        lead_id=lead.id,
        billing_address=lead.billing_address,
        billing_city=lead.billing_city,
        billing_postal_code=lead.billing_postal_code,
        billing_country=lead.billing_country,
        vat_number=lead.vat_number,
        billing_email=lead.billing_email or lead.email,
        billing_contact_name=lead.billing_contact_name or f"{lead.first_name} {lead.last_name}".strip(),
        stripe_customer_id=lead.stripe_customer_id
    )

@router.put("/lead/{lead_id}", response_model=BillingInfo)
def update_lead_billing_info(
    lead_id: int, 
    billing_info: BillingInfoUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour les informations de facturation d'un lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    
    # Mettre à jour les champs de facturation
    update_data = billing_info.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
    
    # Créer ou mettre à jour le customer Stripe si nécessaire
    if not lead.stripe_customer_id:
        try:
            customer = stripe_service.create_or_update_customer(
                email=billing_info.billing_email or lead.email,
                name=billing_info.billing_contact_name or f"{lead.first_name} {lead.last_name}".strip(),
                address={
                    'line1': billing_info.billing_address,
                    'city': billing_info.billing_city,
                    'postal_code': billing_info.billing_postal_code,
                    'country': billing_info.billing_country
                } if billing_info.billing_address else None,
                metadata={
                    'lead_id': str(lead.id),
                    'company': lead.company
                }
            )
            lead.stripe_customer_id = customer.id
        except Exception as e:
            logger.error(f"Erreur création customer Stripe: {e}")
    
    db.commit()
    db.refresh(lead)
    
    return BillingInfo(
        lead_id=lead.id,
        billing_address=lead.billing_address,
        billing_city=lead.billing_city,
        billing_postal_code=lead.billing_postal_code,
        billing_country=lead.billing_country,
        vat_number=lead.vat_number,
        billing_email=lead.billing_email,
        billing_contact_name=lead.billing_contact_name,
        stripe_customer_id=lead.stripe_customer_id
    )

@router.post("/create-invoice", response_model=CreateInvoiceResponse)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    """Créer une facture et l'envoyer via Stripe."""
    # Vérifier que le lead existe
    lead = db.query(Lead).filter(Lead.id == invoice_data.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    
    # Mettre à jour les infos de facturation si fournies
    if invoice_data.billing_info:
        for field, value in invoice_data.billing_info.dict(exclude_unset=True).items():
            setattr(lead, field, value)
        db.commit()
    
    # Vérifier que les infos de facturation sont complètes
    if not all([lead.billing_email or lead.email, 
                lead.billing_contact_name or f"{lead.first_name} {lead.last_name}".strip()]):
        raise HTTPException(
            status_code=400, 
            detail="Informations de facturation incomplètes"
        )
    
    # Récupérer les services sélectionnés
    service_ids = [s.service_id for s in invoice_data.services]
    services = db.query(Service).filter(Service.id.in_(service_ids)).all()
    if len(services) != len(service_ids):
        raise HTTPException(status_code=400, detail="Services invalides")
    
    # Calculer les montants
    amount = 0.0
    services_data = []
    for selection in invoice_data.services:
        service = next(s for s in services if s.id == selection.service_id)
        service_amount = (selection.custom_price or service.price) * selection.quantity
        amount += service_amount
        services_data.append({
            'service_id': service.id,
            'name': service.name,
            'description': selection.description or service.description,
            'quantity': selection.quantity,
            'unit_price': selection.custom_price or service.price,
            'amount': service_amount
        })
    
    # Calculer la TVA (20% par défaut)
    tax_rate = 0.20 if lead.billing_country == 'FR' else 0.0
    tax_amount = amount * tax_rate
    total_amount = amount + tax_amount
    
    # Générer le numéro de facture
    current_year = datetime.now().year
    last_invoice = db.query(Invoice).filter(
        Invoice.invoice_number.like(f"INV-{current_year}-%")
    ).order_by(Invoice.id.desc()).first()
    
    if last_invoice:
        last_number = int(last_invoice.invoice_number.split('-')[-1])
        invoice_number = f"INV-{current_year}-{last_number + 1:04d}"
    else:
        invoice_number = f"INV-{current_year}-0001"
    
    # Créer la facture dans la base de données
    invoice = Invoice(
        lead_id=lead.id,
        invoice_number=invoice_number,
        amount=amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        currency='EUR',
        status='draft',
        invoice_date=datetime.utcnow(),
        due_date=invoice_data.due_date or (datetime.utcnow() + timedelta(days=30)),
        services_data=services_data,
        billing_data={
            'address': lead.billing_address,
            'city': lead.billing_city,
            'postal_code': lead.billing_postal_code,
            'country': lead.billing_country,
            'vat_number': lead.vat_number,
            'email': lead.billing_email or lead.email,
            'contact_name': lead.billing_contact_name or f"{lead.first_name} {lead.last_name}".strip()
        }
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    # Créer la facture dans Stripe
    try:
        stripe_invoice = stripe_service.create_invoice(
            customer_id=lead.stripe_customer_id,
            amount=total_amount,
            currency='EUR',
            description=f"Facture {invoice_number}",
            metadata={
                'invoice_id': str(invoice.id),
                'lead_id': str(lead.id)
            },
            line_items=services_data,
            tax_rate=tax_rate,
            send_email=invoice_data.send_email
        )
        
        invoice.stripe_invoice_id = stripe_invoice.id
        invoice.pdf_url = stripe_invoice.invoice_pdf
        invoice.status = 'sent' if invoice_data.send_email else 'draft'
        db.commit()
        
        return CreateInvoiceResponse(
            invoice=invoice,
            stripe_invoice_url=stripe_invoice.hosted_invoice_url,
            message="Facture créée et envoyée avec succès" if invoice_data.send_email else "Facture créée avec succès"
        )
        
    except Exception as e:
        logger.error(f"Erreur création facture Stripe: {e}")
        invoice.status = 'error'
        db.commit()
        raise HTTPException(status_code=500, detail=f"Erreur création facture: {str(e)}")

@router.get("/invoices/{lead_id}", response_model=List[InvoiceListItem])
def get_lead_invoices(
    lead_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Récupérer toutes les factures d'un lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    
    query = db.query(Invoice).filter(Invoice.lead_id == lead_id)
    if status:
        query = query.filter(Invoice.status == status)
    
    invoices = query.order_by(Invoice.invoice_date.desc()).all()
    
    return [
        InvoiceListItem(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            lead_name=f"{lead.first_name} {lead.last_name}".strip(),
            company=lead.company,
            total_amount=invoice.total_amount,
            currency=invoice.currency,
            status=invoice.status,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            paid_date=invoice.paid_date
        )
        for invoice in invoices
    ]

@router.get("/invoice/{invoice_id}", response_model=InvoiceSchema)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Récupérer une facture spécifique."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return invoice

@router.put("/invoice/{invoice_id}", response_model=InvoiceSchema)
def update_invoice(
    invoice_id: int,
    update_data: InvoiceUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour une facture."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    # Ne pas permettre la modification si la facture est payée
    if invoice.status == 'paid':
        raise HTTPException(status_code=400, detail="Impossible de modifier une facture payée")
    
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(invoice, field, value)
    
    invoice.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(invoice)
    
    return invoice

@router.post("/invoice/{invoice_id}/send")
def send_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Envoyer une facture par email."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if not invoice.stripe_invoice_id:
        raise HTTPException(status_code=400, detail="Facture non liée à Stripe")
    
    try:
        stripe_service.send_invoice(invoice.stripe_invoice_id)
        invoice.status = 'sent'
        db.commit()
        return {"message": "Facture envoyée avec succès"}
    except Exception as e:
        logger.error(f"Erreur envoi facture: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur envoi facture: {str(e)}")

# =====================================
# NOUVEAUX ENDPOINTS - INTÉGRATION STRIPE PRODUCTS
# =====================================

@router.get("/stripe-products")
def get_stripe_products(
    active: bool = Query(True, description="Produits actifs seulement"),
    limit: int = Query(100, description="Limite de résultats")
):
    """Récupérer tous les produits Stripe avec leurs prix."""
    try:
        products = stripe_service.list_products_with_prices(active=active, limit=limit)
        return {
            "products": products,
            "count": len(products),
            "message": "Produits Stripe récupérés avec succès"
        }
    except Exception as e:
        logger.error(f"Erreur récupération produits Stripe: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération produits: {str(e)}")

@router.get("/stripe-products/{product_id}")
def get_stripe_product(product_id: str):
    """Récupérer un produit Stripe spécifique avec ses prix."""
    try:
        product = stripe_service.get_product_by_id(product_id)
        return {
            "product": product,
            "message": "Produit Stripe récupéré avec succès"
        }
    except Exception as e:
        logger.error(f"Erreur récupération produit {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération produit: {str(e)}")

@router.post("/sync-stripe-products")
def sync_stripe_products():
    """Synchroniser les produits Stripe avec la base locale."""
    try:
        sync_result = stripe_service.sync_stripe_products()
        return {
            "sync_result": sync_result,
            "message": f"Synchronisation terminée: {sync_result['products_count']} produits"
        }
    except Exception as e:
        logger.error(f"Erreur synchronisation produits Stripe: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur synchronisation: {str(e)}")

@router.post("/create-invoice-with-stripe-products", response_model=CreateInvoiceResponse)
def create_invoice_with_stripe_products(
    invoice_data: dict,  # Structure similaire à InvoiceCreate mais avec price_ids
    db: Session = Depends(get_db)
):
    """Créer une facture avec des produits Stripe (utilise price_id)."""
    lead_id = invoice_data.get('lead_id')
    price_items = invoice_data.get('price_items', [])
    send_email = invoice_data.get('send_email', True)
    
    # Vérifier que le lead existe
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    
    # Vérifier que le customer Stripe existe
    if not lead.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Client non configuré dans Stripe")
    
    try:
        # Créer la facture Stripe avec produits
        stripe_invoice = stripe_service.create_invoice_with_stripe_products(
            customer_id=lead.stripe_customer_id,
            price_items=price_items,
            currency='eur',
            description=f"Facture pour {lead.first_name} {lead.last_name}",
            metadata={
                'lead_id': str(lead.id),
                'billing_type': 'stripe_products'
            },
            send_email=send_email
        )
        
        # Générer le numéro de facture
        current_year = datetime.now().year
        last_invoice = db.query(Invoice).filter(
            Invoice.invoice_number.like(f"INV-{current_year}-%")
        ).order_by(Invoice.id.desc()).first()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            invoice_number = f"INV-{current_year}-{last_number + 1:04d}"
        else:
            invoice_number = f"INV-{current_year}-0001"
        
        # Créer la facture locale
        invoice = Invoice(
            lead_id=lead.id,
            invoice_number=invoice_number,
            stripe_invoice_id=stripe_invoice.id,
            amount=stripe_invoice.subtotal / 100,  # Stripe utilise les centimes
            tax_amount=(stripe_invoice.tax or 0) / 100,
            total_amount=stripe_invoice.total / 100,
            currency=stripe_invoice.currency.upper(),
            status='sent' if send_email else 'draft',
            invoice_date=datetime.utcnow(),
            due_date=datetime.fromtimestamp(stripe_invoice.due_date) if stripe_invoice.due_date else None,
            pdf_url=stripe_invoice.invoice_pdf,
            services_data=price_items,  # Stockage des price_items pour référence
            billing_data={
                'stripe_customer_id': lead.stripe_customer_id,
                'billing_type': 'stripe_products'
            }
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        return CreateInvoiceResponse(
            invoice=invoice,
            stripe_invoice_url=stripe_invoice.hosted_invoice_url,
            message="Facture créée avec produits Stripe" + (" et envoyée" if send_email else "")
        )
        
    except Exception as e:
        logger.error(f"Erreur création facture avec produits Stripe: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur création facture: {str(e)}")

# =====================================
# ENDPOINTS MANQUANTS - LISTER TOUTES LES FACTURES
# =====================================

@router.get("/invoices", response_model=List[InvoiceListItem])
def get_all_invoices(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    limit: int = Query(50, description="Limite de résultats"),
    offset: int = Query(0, description="Décalage pour pagination"),
    db: Session = Depends(get_db)
):
    """Récupérer toutes les factures avec pagination."""
    query = db.query(Invoice).join(Lead)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    # Compter le total pour pagination
    total = query.count()
    
    # Appliquer pagination et ordre
    invoices = query.order_by(Invoice.invoice_date.desc()).offset(offset).limit(limit).all()
    
    invoice_list = []
    for invoice in invoices:
        lead = invoice.lead
        invoice_list.append(InvoiceListItem(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            lead_name=f"{lead.first_name} {lead.last_name}".strip(),
            company=lead.company,
            total_amount=invoice.total_amount,
            currency=invoice.currency,
            status=invoice.status,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            paid_date=invoice.paid_date
        ))
    
    return invoice_list

# =====================================
# ENDPOINTS STATISTIQUES DE FACTURATION
# =====================================

@router.get("/stats")
def get_billing_stats(
    period: str = Query("month", description="Période: day, week, month, year"),
    db: Session = Depends(get_db)
):
    """Récupérer les statistiques de facturation."""
    try:
        from sqlalchemy import func, extract
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        
        # Définir les périodes
        if period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "year":
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Statistiques générales
        total_invoices = db.query(Invoice).count()
        total_revenue = db.query(func.sum(Invoice.total_amount)).filter(
            Invoice.status.in_(['sent', 'paid'])
        ).scalar() or 0
        
        # Statistiques de la période
        period_invoices = db.query(Invoice).filter(
            Invoice.invoice_date >= start_date
        ).count()
        
        period_revenue = db.query(func.sum(Invoice.total_amount)).filter(
            Invoice.invoice_date >= start_date,
            Invoice.status.in_(['sent', 'paid'])
        ).scalar() or 0
        
        # Statistiques par statut
        status_stats = db.query(
            Invoice.status,
            func.count(Invoice.id).label('count'),
            func.sum(Invoice.total_amount).label('total')
        ).group_by(Invoice.status).all()
        
        # Factures en attente de paiement
        pending_invoices = db.query(Invoice).filter(
            Invoice.status == 'sent',
            Invoice.due_date < now
        ).count()
        
        pending_amount = db.query(func.sum(Invoice.total_amount)).filter(
            Invoice.status == 'sent',
            Invoice.due_date < now
        ).scalar() or 0
        
        return {
            "total_invoices": total_invoices,
            "total_revenue": float(total_revenue),
            "period": period,
            "period_invoices": period_invoices,
            "period_revenue": float(period_revenue),
            "status_breakdown": [
                {
                    "status": stat.status,
                    "count": stat.count,
                    "total_amount": float(stat.total or 0)
                }
                for stat in status_stats
            ],
            "overdue_invoices": pending_invoices,
            "overdue_amount": float(pending_amount),
            "currency": "EUR"
        }
        
    except Exception as e:
        logger.error(f"Erreur calcul statistiques: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur calcul statistiques: {str(e)}")

@router.get("/invoice/{invoice_id}/details")
def get_invoice_details(invoice_id: int, db: Session = Depends(get_db)):
    """Récupérer les détails complets d'une facture avec infos lead."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    lead = invoice.lead
    
    # Récupérer les détails Stripe si disponible
    stripe_details = None
    if invoice.stripe_invoice_id:
        try:
            stripe_invoice = stripe_service.get_invoice(invoice.stripe_invoice_id)
            stripe_details = {
                "stripe_id": stripe_invoice.id,
                "hosted_invoice_url": stripe_invoice.hosted_invoice_url,
                "invoice_pdf": stripe_invoice.invoice_pdf,
                "payment_intent": stripe_invoice.payment_intent,
                "status": stripe_invoice.status
            }
        except Exception as e:
            logger.warning(f"Erreur récupération détails Stripe: {e}")
    
    return {
        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "amount": invoice.amount,
            "tax_amount": invoice.tax_amount,
            "total_amount": invoice.total_amount,
            "currency": invoice.currency,
            "status": invoice.status,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "paid_date": invoice.paid_date,
            "services_data": invoice.services_data,
            "billing_data": invoice.billing_data,
            "pdf_url": invoice.pdf_url
        },
        "lead": {
            "id": lead.id,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "email": lead.email,
            "company": lead.company,
            "phone": lead.phone,
            "billing_address": lead.billing_address,
            "billing_city": lead.billing_city,
            "billing_postal_code": lead.billing_postal_code,
            "billing_country": lead.billing_country,
            "vat_number": lead.vat_number
        },
        "stripe_details": stripe_details
    }

# =====================================
# ENDPOINT RENDEZ-VOUS DU JOUR POUR FACTURATION
# =====================================

@router.get("/today-meetings")
def get_today_meetings_for_billing(db: Session = Depends(get_db)):
    """Récupérer les rendez-vous du jour avec les infos clients pour facturation."""
    try:
        from datetime import datetime
        
        # Définir la période d'aujourd'hui
        now = datetime.utcnow()
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Récupérer les meetings d'aujourd'hui avec leurs leads
        meetings = db.query(Meeting).filter(
            Meeting.start_time >= start_date,
            Meeting.start_time <= end_date,
            Meeting.status.in_(['scheduled', 'confirmed', 'completed'])
        ).order_by(Meeting.start_time).all()
        
        meetings_for_billing = []
        for meeting in meetings:
            # Récupérer le lead associé
            lead = None
            if meeting.lead_id:
                lead = db.query(Lead).filter(Lead.id == meeting.lead_id).first()
            
            # Si pas de lead associé, chercher par email
            if not lead and meeting.client_email:
                lead = db.query(Lead).filter(Lead.email == meeting.client_email).first()
            
            # Construire les infos du meeting pour facturation
            meeting_info = {
                "meeting": {
                    "id": meeting.id,
                    "client_name": meeting.client_name,
                    "client_email": meeting.client_email,
                    "start_time": meeting.start_time,
                    "end_time": meeting.end_time,
                    "duration_minutes": meeting.duration_minutes,
                    "status": meeting.status,
                    "description": meeting.description,
                    "meeting_link": meeting.meeting_link
                },
                "lead": None,
                "can_invoice": False,
                "existing_invoices": 0
            }
            
            if lead:
                # Ajouter les infos du lead
                meeting_info["lead"] = {
                    "id": lead.id,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "email": lead.email,
                    "company": lead.company,
                    "phone": lead.phone,
                    "billing_address": lead.billing_address,
                    "billing_city": lead.billing_city,
                    "billing_postal_code": lead.billing_postal_code,
                    "billing_country": lead.billing_country,
                    "vat_number": lead.vat_number,
                    "billing_email": lead.billing_email,
                    "billing_contact_name": lead.billing_contact_name,
                    "stripe_customer_id": lead.stripe_customer_id
                }
                
                # Vérifier si on peut facturer (infos minimales présentes)
                meeting_info["can_invoice"] = bool(
                    lead.billing_email or lead.email
                )
                
                # Compter les factures existantes
                meeting_info["existing_invoices"] = db.query(Invoice).filter(
                    Invoice.lead_id == lead.id
                ).count()
            
            meetings_for_billing.append(meeting_info)
        
        return {
            "meetings": meetings_for_billing,
            "count": len(meetings_for_billing),
            "date": start_date.date().isoformat(),
            "message": f"{len(meetings_for_billing)} rendez-vous trouvés pour aujourd'hui"
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération meetings du jour: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération meetings: {str(e)}")

# =====================================
# VALIDATION ET AUTO-AJOUT D'ABONNEMENTS
# =====================================

@router.post("/validate-invoice-items")
def validate_invoice_items(
    items: List[Dict[str, Any]]
):
    """
    Valide une sélection de produits et ajoute automatiquement les abonnements obligatoires.
    
    Args:
        items: Liste des produits sélectionnés avec format:
               [{"product_id": "prod_xxx", "price_id": "price_xxx", "quantity": 1}]
    
    Returns:
        - valid: bool indiquant si la sélection est valide
        - items: liste complète incluant les abonnements ajoutés
        - warnings: avertissements (abonnements ajoutés, options disponibles)
        - errors: erreurs de validation
    """
    try:
        result = validate_and_complete_invoice_items(items)
        
        # Enrichir avec les détails des produits
        enriched_items = []
        for item in result["items"]:
            try:
                product = stripe_service.get_product_by_id(item["product_id"])
                price = stripe_service.get_price_details(item["price_id"])
                
                enriched_item = {
                    **item,
                    "product_name": product["name"],
                    "product_description": product["description"],
                    "unit_amount": price["unit_amount"],
                    "currency": price["currency"],
                    "price_type": price["type"],
                    "recurring": price.get("recurring")
                }
                enriched_items.append(enriched_item)
            except Exception as e:
                logger.error(f"Erreur enrichissement item {item['product_id']}: {e}")
                enriched_items.append(item)
        
        result["items"] = enriched_items
        return result
        
    except Exception as e:
        logger.error(f"Erreur validation items facture: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur validation: {str(e)}")

# @router.post("/create-invoice-with-validation", response_model=CreateInvoiceResponse)
def create_invoice_with_validation_OLD(
    invoice_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Créer une facture avec validation automatique et ajout des abonnements obligatoires.
    
    Structure attendue:
    {
        "lead_id": 123,
        "items": [
            {"product_id": "prod_xxx", "price_id": "price_xxx", "quantity": 1}
        ],
        "send_email": true,
        "due_date": "2025-02-28T00:00:00"
    }
    """
    lead_id = invoice_data.get('lead_id')
    items = invoice_data.get('items', [])
    send_email = invoice_data.get('send_email', True)
    due_date = invoice_data.get('due_date')
    
    # Vérifier que le lead existe
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead non trouvé")
    
    # Vérifier le customer Stripe
    if not lead.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Client non configuré dans Stripe")
    
    # Valider et compléter les items
    validation_result = validate_and_complete_invoice_items(items)
    
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=400, 
            detail={
                "message": "Validation échouée",
                "errors": validation_result["errors"]
            }
        )
    
    # Préparer les items pour Stripe
    price_items = []
    for item in validation_result["items"]:
        price_items.append({
            "price_id": item["price_id"],
            "quantity": item.get("quantity", 1),
            "product_id": item["product_id"]
        })
    
    try:
        # Créer la facture Stripe
        stripe_invoice = stripe_service.create_invoice_with_stripe_products(
            customer_id=lead.stripe_customer_id,
            price_items=price_items,
            currency='eur',
            description=f"Facture pour {lead.first_name} {lead.last_name}",
            metadata={
                'lead_id': str(lead.id),
                'billing_type': 'stripe_products_validated',
                'auto_added_subscriptions': str(any(item.get('auto_added') for item in validation_result['items']))
            },
            send_email=send_email,
            due_date=datetime.fromisoformat(due_date) if due_date else None
        )
        
        # Générer le numéro de facture
        current_year = datetime.now().year
        last_invoice = db.query(Invoice).filter(
            Invoice.invoice_number.like(f"INV-{current_year}-%")
        ).order_by(Invoice.id.desc()).first()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            invoice_number = f"INV-{current_year}-{last_number + 1:04d}"
        else:
            invoice_number = f"INV-{current_year}-0001"
        
        # Créer la facture locale avec les détails de validation
        invoice = Invoice(
            lead_id=lead.id,
            invoice_number=invoice_number,
            stripe_invoice_id=stripe_invoice.id,
            amount=stripe_invoice.subtotal / 100,
            tax_amount=(stripe_invoice.tax or 0) / 100,
            total_amount=stripe_invoice.total / 100,
            currency=stripe_invoice.currency.upper(),
            status='sent' if send_email else 'draft',
            invoice_date=datetime.utcnow(),
            due_date=datetime.fromtimestamp(stripe_invoice.due_date) if stripe_invoice.due_date else None,
            pdf_url=stripe_invoice.invoice_pdf,
            services_data={
                "items": validation_result["items"],
                "warnings": validation_result["warnings"],
                "auto_added": any(item.get('auto_added') for item in validation_result['items'])
            },
            billing_data={
                'stripe_customer_id': lead.stripe_customer_id,
                'billing_type': 'stripe_products_validated'
            }
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        return CreateInvoiceResponse(
            invoice=invoice,
            stripe_invoice_url=stripe_invoice.hosted_invoice_url,
            message="Facture créée avec validation" + 
                    (" et envoyée" if send_email else "") +
                    (f". {len(validation_result['warnings'])} abonnement(s) ajouté(s) automatiquement." 
                     if validation_result['warnings'] else "")
        )
        
    except Exception as e:
        logger.error(f"Erreur création facture avec validation: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur création facture: {str(e)}")

@router.get("/product-subscription-mapping/{product_id}")
def get_product_subscription_mapping(product_id: str):
    """
    Récupérer les informations d'abonnement associées à un produit.
    """
    subscription_info = get_subscription_for_product(product_id)
    
    if not subscription_info:
        return {
            "product_id": product_id,
            "has_subscription": False,
            "message": "Aucun abonnement associé à ce produit"
        }
    
    # Enrichir avec les détails Stripe
    try:
        subscription_product = stripe_service.get_product_by_id(subscription_info["subscription_product_id"])
        subscription_price = stripe_service.get_price_details(subscription_info["subscription_price_id"])
        
        return {
            "product_id": product_id,
            "has_subscription": True,
            "subscription": {
                "product_id": subscription_info["subscription_product_id"],
                "product_name": subscription_product["name"],
                "price_id": subscription_info["subscription_price_id"],
                "unit_amount": subscription_price["unit_amount"],
                "currency": subscription_price["currency"],
                "recurring": subscription_price["recurring"],
                "required": subscription_info["required"],
                "description": subscription_info["description"]
            }
        }
    except Exception as e:
        logger.error(f"Erreur récupération détails abonnement: {e}")
        return {
            "product_id": product_id,
            "has_subscription": True,
            "subscription": subscription_info,
            "error": "Impossible de récupérer les détails depuis Stripe"
        }

# =====================================
# ENDPOINTS POUR VALIDATION AUTOMATIQUE DES ABONNEMENTS
# =====================================

@router.post("/validate-invoice-items")
def validate_invoice_items(invoice_items: List[Dict]):
    """Valide et complète les items d'une facture avec les abonnements nécessaires."""
    try:
        result = validate_and_complete_invoice_items(invoice_items)
        return result
    except Exception as e:
        logger.error(f"Erreur validation items facture: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur validation: {str(e)}")

class InvoiceValidationRequest(BaseModel):
    lead_id: int
    selected_items: List[Dict]
    send_email: bool = False

@router.post("/create-invoice-with-validation", response_model=CreateInvoiceResponse)
def create_invoice_with_validation(
    request: InvoiceValidationRequest,
    db: Session = Depends(get_db)
):
    """Crée une facture en validant automatiquement les abonnements nécessaires."""
    try:
        # Extraire les paramètres de la requête
        lead_id = request.lead_id
        selected_items = request.selected_items
        send_email = request.send_email
        
        # Valider et compléter les items
        validation_result = validate_and_complete_invoice_items(selected_items)
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Validation échouée: {', '.join(validation_result['errors'])}"
            )
        
        # Utiliser les items validés pour créer la facture
        validated_items = validation_result["items"]
        
        # Convertir en format price_items pour l'API Stripe
        price_items = []
        for item in validated_items:
            price_items.append({
                "price_id": item["price_id"],
                "quantity": item.get("quantity", 1)
            })
        
        # Récupérer les infos du lead
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead non trouvé")
        
        if not lead.stripe_customer_id:
            raise HTTPException(status_code=400, detail="Client non configuré dans Stripe")
        
        # Créer la facture avec les items validés
        from datetime import datetime, timedelta
        due_date = datetime.utcnow() + timedelta(days=30)  # 30 jours par défaut
        
        stripe_invoice = stripe_service.create_invoice_with_stripe_products(
            customer_id=lead.stripe_customer_id,
            price_items=price_items,
            currency='eur',
            description=f"Facture pour {lead.first_name} {lead.last_name}",
            metadata={
                'lead_id': str(lead.id),
                'billing_type': 'stripe_products_validated',
                'auto_added_subscriptions': str(any(item.get('auto_added') for item in validated_items))
            },
            send_email=send_email,
            due_date=due_date
        )
        
        # Générer le numéro de facture
        current_year = datetime.now().year
        last_invoice = db.query(Invoice).filter(
            Invoice.invoice_number.like(f"INV-{current_year}-%")
        ).order_by(Invoice.id.desc()).first()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            invoice_number = f"INV-{current_year}-{last_number + 1:04d}"
        else:
            invoice_number = f"INV-{current_year}-0001"
        
        # Sauvegarder dans la base de données
        invoice = Invoice(
            lead_id=lead.id,
            invoice_number=invoice_number,
            stripe_invoice_id=stripe_invoice.id,
            amount=stripe_invoice.amount_due / 100,  # Stripe utilise des centimes
            currency=stripe_invoice.currency.upper(),
            tax_amount=getattr(stripe_invoice, 'tax', 0) / 100 if getattr(stripe_invoice, 'tax', 0) else 0,
            total_amount=stripe_invoice.total / 100,
            status='draft' if not send_email else 'sent',
            invoice_date=datetime.utcnow(),
            due_date=datetime.fromtimestamp(stripe_invoice.due_date) if stripe_invoice.due_date else None
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        # Créer la réponse
        result = CreateInvoiceResponse(
            invoice=invoice.__dict__,
            stripe_invoice_url=stripe_invoice.hosted_invoice_url,
            message=f"Facture {invoice_number} créée avec succès",
            validation_warnings=validation_result.get('warnings', [])
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur création facture avec validation: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur création facture: {str(e)}")
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
import stripe
import logging
from typing import Optional

from app.database.connection import get_db
from app.services.stripe_service import StripeService
from app.services.notification_service import NotificationService
from app.models import Invoice, Lead
from app.core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# Configurer Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Endpoint pour recevoir les webhooks Stripe"""
    
    # Récupérer le payload
    payload = await request.body()
    
    # Vérifier la signature si webhook secret est configuré
    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid payload from Stripe webhook")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature from Stripe webhook")
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        # En mode dev sans webhook secret
        import json
        event = json.loads(payload)
        logger.warning("Webhook signature verification skipped (no webhook secret)")
    
    # Traiter l'événement
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})
    
    logger.info(f"Received Stripe webhook: {event_type} - ID: {event.get('id')}")
    
    try:
        # Événements de paiement de facture
        if event_type in ["invoice.payment_succeeded", "invoice.payment_failed"]:
            invoice_id = event_data.get("id")
            
            # Trouver la facture dans notre base
            invoice = db.query(Invoice).filter(
                Invoice.stripe_invoice_id == invoice_id
            ).first()
            
            if invoice:
                # Mettre à jour le statut de la facture
                if event_type == "invoice.payment_succeeded":
                    invoice.status = "paid"
                    invoice.paid_at = event_data.get("status_transitions", {}).get("paid_at")
                else:
                    invoice.status = "failed"
                
                db.commit()
                
                # Créer une notification
                amount = event_data.get("amount_paid", 0) or event_data.get("amount_due", 0)
                customer_email = event_data.get("customer_email")
                customer_name = event_data.get("customer_name")
                
                # Si pas de nom, essayer de le récupérer du lead
                if not customer_name and invoice.lead:
                    customer_name = invoice.lead.name
                
                NotificationService.create_payment_notification(
                    db=db,
                    stripe_event_id=event.get("id"),
                    stripe_event_type=event_type,
                    invoice_id=invoice.id,
                    lead_id=invoice.lead_id,
                    amount=amount,
                    currency=event_data.get("currency", "eur"),
                    client_name=customer_name,
                    client_email=customer_email,
                    stripe_data=event_data
                )
                
                logger.info(f"Payment notification created for invoice {invoice.id}")
            else:
                logger.warning(f"Invoice not found for Stripe ID: {invoice_id}")
        
        # Événements de charge (paiement direct)
        elif event_type in ["charge.succeeded", "charge.failed"]:
            # Pour les charges, on essaie de trouver via le payment intent
            payment_intent_id = event_data.get("payment_intent")
            
            if payment_intent_id:
                invoice = db.query(Invoice).filter(
                    Invoice.stripe_payment_intent_id == payment_intent_id
                ).first()
                
                if invoice:
                    # Créer une notification
                    amount = event_data.get("amount", 0)
                    
                    # Récupérer les infos du client depuis les metadata ou billing_details
                    billing_details = event_data.get("billing_details", {})
                    customer_email = billing_details.get("email")
                    customer_name = billing_details.get("name")
                    
                    if not customer_name and invoice.lead:
                        customer_name = invoice.lead.name
                    
                    NotificationService.create_payment_notification(
                        db=db,
                        stripe_event_id=event.get("id"),
                        stripe_event_type=event_type,
                        invoice_id=invoice.id,
                        lead_id=invoice.lead_id,
                        amount=amount,
                        currency=event_data.get("currency", "eur"),
                        client_name=customer_name,
                        client_email=customer_email,
                        stripe_data=event_data
                    )
                    
                    logger.info(f"Payment notification created for charge {event_data.get('id')}")
        
        # Événement de paiement d'abonnement
        elif event_type == "invoice.payment_succeeded":
            # Gérer spécifiquement les paiements d'abonnement récurrents
            subscription_id = event_data.get("subscription")
            if subscription_id:
                logger.info(f"Subscription payment received: {subscription_id}")
                # Logique spécifique pour les abonnements si nécessaire
        
        return {"status": "success", "event_type": event_type}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        # On retourne quand même un succès pour éviter que Stripe retry
        return {"status": "error", "message": str(e)}


@router.get("/notifications/payments/unsent")
async def get_unsent_payment_notifications(
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Récupérer les notifications de paiement non envoyées"""
    notifications = NotificationService.get_unsent_notifications(db, limit=limit)
    
    return {
        "notifications": [
            {
                "id": n.id,
                "type": n.notification_type,
                "amount": n.amount / 100,
                "currency": n.currency,
                "client_name": n.client_name,
                "client_email": n.client_email,
                "created_at": n.created_at.isoformat(),
                "message": NotificationService.format_telegram_message(n)
            }
            for n in notifications
        ]
    }


@router.post("/notifications/payments/{notification_id}/mark-sent")
async def mark_notification_as_sent(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Marquer une notification comme envoyée"""
    success = NotificationService.mark_as_sent(db, notification_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"status": "success", "notification_id": notification_id}


@router.post("/notifications/payments/{notification_id}/mark-failed")
async def mark_notification_as_failed(
    notification_id: int,
    error_message: str,
    db: Session = Depends(get_db)
):
    """Marquer une notification comme échouée"""
    success = NotificationService.mark_as_failed(db, notification_id, error_message)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"status": "success", "notification_id": notification_id}


@router.get("/notifications/payments/daily-summary")
async def get_daily_payment_summary(db: Session = Depends(get_db)):
    """Obtenir le résumé quotidien des paiements"""
    summary = NotificationService.get_daily_summary(db)
    summary["message"] = NotificationService.format_daily_summary_message(summary)
    
    return summary
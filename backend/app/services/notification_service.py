from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import PaymentNotification, Invoice, Lead
# from ..schemas.billing import InvoiceResponse  # Pas nécessaire pour ce service
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service pour gérer les notifications de paiement"""
    
    @staticmethod
    def create_payment_notification(
        db: Session,
        stripe_event_id: str,
        stripe_event_type: str,
        invoice_id: int,
        lead_id: int,
        amount: int,
        currency: str = "eur",
        client_name: Optional[str] = None,
        client_email: Optional[str] = None,
        stripe_data: Optional[Dict[str, Any]] = None
    ) -> PaymentNotification:
        """Créer une nouvelle notification de paiement"""
        
        # Déterminer le type de notification basé sur l'événement Stripe
        notification_type = "payment_unknown"
        if "payment_succeeded" in stripe_event_type:
            notification_type = "payment_success"
        elif "payment_failed" in stripe_event_type:
            notification_type = "payment_failed"
        elif "charge.succeeded" in stripe_event_type:
            notification_type = "payment_success"
        elif "charge.failed" in stripe_event_type:
            notification_type = "payment_failed"
        
        notification = PaymentNotification(
            stripe_event_id=stripe_event_id,
            stripe_event_type=stripe_event_type,
            notification_type=notification_type,
            invoice_id=invoice_id,
            lead_id=lead_id,
            amount=amount,
            currency=currency,
            client_name=client_name,
            client_email=client_email,
            stripe_data=stripe_data or {}
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        logger.info(f"Notification de paiement créée: {notification.id} - Type: {notification_type}")
        return notification
    
    @staticmethod
    def get_unsent_notifications(db: Session, limit: int = 10) -> List[PaymentNotification]:
        """Récupérer les notifications non envoyées"""
        return db.query(PaymentNotification).filter(
            PaymentNotification.sent_to_telegram == False
        ).order_by(PaymentNotification.created_at).limit(limit).all()
    
    @staticmethod
    def mark_as_sent(db: Session, notification_id: int) -> bool:
        """Marquer une notification comme envoyée"""
        notification = db.query(PaymentNotification).filter(
            PaymentNotification.id == notification_id
        ).first()
        
        if notification:
            notification.sent_to_telegram = True
            notification.sent_at = datetime.utcnow()
            db.commit()
            return True
        return False
    
    @staticmethod
    def mark_as_failed(db: Session, notification_id: int, error_message: str) -> bool:
        """Marquer une notification comme échouée"""
        notification = db.query(PaymentNotification).filter(
            PaymentNotification.id == notification_id
        ).first()
        
        if notification:
            notification.error_message = error_message
            db.commit()
            return True
        return False
    
    @staticmethod
    def format_telegram_message(notification: PaymentNotification) -> str:
        """Formater un message pour Telegram"""
        emoji = "💰" if notification.notification_type == "payment_success" else "❌"
        status = "reçu" if notification.notification_type == "payment_success" else "échoué"
        
        amount_euros = notification.amount / 100
        
        message = f"{emoji} <b>Paiement {status}</b>\n\n"
        message += f"📄 <b>Facture:</b> #{notification.invoice_id}\n"
        message += f"💳 <b>Montant:</b> {amount_euros:.2f} {notification.currency.upper()}\n"
        
        if notification.client_name:
            message += f"👤 <b>Client:</b> {notification.client_name}\n"
        if notification.client_email:
            message += f"📧 <b>Email:</b> {notification.client_email}\n"
        
        message += f"\n🕐 <b>Date:</b> {notification.created_at.strftime('%d/%m/%Y %H:%M')}"
        
        if notification.notification_type == "payment_failed" and notification.stripe_data:
            failure_message = notification.stripe_data.get("failure_message", "Raison inconnue")
            message += f"\n\n⚠️ <b>Raison de l'échec:</b> {failure_message}"
        
        return message
    
    @staticmethod
    def get_daily_summary(db: Session) -> Dict[str, Any]:
        """Obtenir un résumé quotidien des paiements"""
        from datetime import date, time
        from sqlalchemy import func
        
        today = datetime.combine(date.today(), time.min)
        
        # Requête pour les statistiques du jour
        daily_stats = db.query(
            func.count(PaymentNotification.id).label("total_count"),
            func.sum(PaymentNotification.amount).label("total_amount"),
            PaymentNotification.notification_type
        ).filter(
            PaymentNotification.created_at >= today
        ).group_by(PaymentNotification.notification_type).all()
        
        summary = {
            "date": date.today().strftime("%d/%m/%Y"),
            "success_count": 0,
            "success_amount": 0,
            "failed_count": 0,
            "failed_amount": 0,
            "total_amount": 0
        }
        
        for stat in daily_stats:
            if stat.notification_type == "payment_success":
                summary["success_count"] = stat.total_count
                summary["success_amount"] = (stat.total_amount or 0) / 100
                summary["total_amount"] += summary["success_amount"]
            elif stat.notification_type == "payment_failed":
                summary["failed_count"] = stat.total_count
                summary["failed_amount"] = (stat.total_amount or 0) / 100
        
        return summary
    
    @staticmethod
    def format_daily_summary_message(summary: Dict[str, Any]) -> str:
        """Formater le message de résumé quotidien"""
        message = f"📊 <b>Résumé des paiements du {summary['date']}</b>\n\n"
        
        if summary["success_count"] > 0:
            message += f"✅ <b>Paiements réussis:</b> {summary['success_count']}\n"
            message += f"💰 <b>Montant total:</b> {summary['success_amount']:.2f} EUR\n\n"
        
        if summary["failed_count"] > 0:
            message += f"❌ <b>Paiements échoués:</b> {summary['failed_count']}\n"
            message += f"💸 <b>Montant perdu:</b> {summary['failed_amount']:.2f} EUR\n\n"
        
        if summary["success_count"] == 0 and summary["failed_count"] == 0:
            message += "Aucun paiement aujourd'hui.\n"
        
        return message
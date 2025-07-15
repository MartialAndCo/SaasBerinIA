import stripe
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis le fichier .env de l'infra-ia
load_dotenv('/root/berinia/infra-ia/.env')

class StripeService:
    def __init__(self):
        self.api_key = os.getenv('STRIPE_API_KEY')
        if not self.api_key:
            logger.warning("STRIPE_API_KEY not found in environment variables")
            logger.info("Please configure STRIPE_API_KEY in /root/berinia/infra-ia/.env")
        else:
            logger.info("Stripe API key loaded successfully")
        stripe.api_key = self.api_key
        
    def create_or_update_customer(
        self,
        email: str,
        name: str,
        address: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, str]] = None,
        customer_id: Optional[str] = None
    ) -> stripe.Customer:
        """Créer ou mettre à jour un customer Stripe."""
        try:
            customer_data = {
                'email': email,
                'name': name,
                'metadata': metadata or {}
            }
            
            if address:
                customer_data['address'] = address
            
            if customer_id:
                # Mettre à jour un customer existant
                return stripe.Customer.modify(customer_id, **customer_data)
            else:
                # Créer un nouveau customer
                return stripe.Customer.create(**customer_data)
                
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe customer: {e}")
            raise
    
    def create_invoice(
        self,
        customer_id: str,
        amount: float,
        currency: str = 'eur',
        description: str = '',
        metadata: Optional[Dict[str, str]] = None,
        line_items: Optional[List[Dict[str, Any]]] = None,
        tax_rate: float = 0.0,
        send_email: bool = True,
        due_date: Optional[datetime] = None
    ) -> stripe.Invoice:
        """Créer une facture Stripe."""
        try:
            # Créer la facture
            invoice = stripe.Invoice.create(
                customer=customer_id,
                currency=currency.lower(),
                description=description,
                metadata=metadata or {},
                auto_advance=send_email,  # Finaliser automatiquement si on envoie par email
                collection_method='send_invoice',
                due_date=int(due_date.timestamp()) if due_date else None
            )
            
            # Ajouter les lignes de facture
            if line_items:
                for item in line_items:
                    stripe.InvoiceItem.create(
                        invoice=invoice.id,
                        customer=customer_id,
                        amount=int(item['amount'] * 100),  # Stripe utilise les centimes
                        currency=currency.lower(),
                        description=f"{item['name']} - {item.get('description', '')}",
                        quantity=item.get('quantity', 1),
                        metadata={
                            'service_id': str(item.get('service_id', ''))
                        }
                    )
            else:
                # Si pas de line_items, créer une ligne unique
                stripe.InvoiceItem.create(
                    invoice=invoice.id,
                    customer=customer_id,
                    amount=int(amount * 100),
                    currency=currency.lower(),
                    description=description
                )
            
            # Ajouter la TVA si applicable
            if tax_rate > 0:
                # Créer un taux de taxe
                tax_rate_obj = stripe.TaxRate.create(
                    display_name="TVA",
                    percentage=tax_rate * 100,
                    inclusive=False,
                    active=True
                )
                
                # Appliquer le taux de taxe à la facture
                invoice = stripe.Invoice.modify(
                    invoice.id,
                    default_tax_rates=[tax_rate_obj.id]
                )
            
            # Finaliser la facture
            invoice = stripe.Invoice.finalize_invoice(invoice.id)
            
            # Envoyer par email si demandé
            if send_email:
                stripe.Invoice.send_invoice(invoice.id)
            
            return invoice
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur création facture Stripe: {e}")
            raise
    
    def send_invoice(self, invoice_id: str) -> stripe.Invoice:
        """Envoyer une facture par email."""
        try:
            return stripe.Invoice.send_invoice(invoice_id)
        except stripe.error.StripeError as e:
            logger.error(f"Erreur envoi facture Stripe: {e}")
            raise
    
    def get_invoice(self, invoice_id: str) -> stripe.Invoice:
        """Récupérer une facture Stripe."""
        try:
            return stripe.Invoice.retrieve(invoice_id)
        except stripe.error.StripeError as e:
            logger.error(f"Erreur récupération facture Stripe: {e}")
            raise
    
    def void_invoice(self, invoice_id: str) -> stripe.Invoice:
        """Annuler une facture."""
        try:
            return stripe.Invoice.void_invoice(invoice_id)
        except stripe.error.StripeError as e:
            logger.error(f"Erreur annulation facture Stripe: {e}")
            raise
    
    def list_customer_invoices(
        self, 
        customer_id: str,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[stripe.Invoice]:
        """Lister les factures d'un customer."""
        try:
            params = {
                'customer': customer_id,
                'limit': limit
            }
            if status:
                params['status'] = status
                
            return stripe.Invoice.list(**params).data
        except stripe.error.StripeError as e:
            logger.error(f"Erreur listing factures Stripe: {e}")
            raise
    
    def handle_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """Gérer les webhooks Stripe."""
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        if not webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise
    
    # =====================================
    # PRODUCTS API METHODS
    # =====================================
    
    def list_products_with_prices(
        self, 
        active: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Lister tous les produits avec leurs prix."""
        try:
            # Récupérer tous les produits
            products = stripe.Product.list(
                active=active,
                limit=limit
            ).data
            
            # Récupérer les prix pour chaque produit
            products_with_prices = []
            for product in products:
                # Récupérer les prix du produit
                prices = stripe.Price.list(
                    product=product.id,
                    active=True,
                    limit=10
                ).data
                
                # Structurer les données
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'metadata': product.metadata,
                    'images': product.images,
                    'active': product.active,
                    'created': product.created,
                    'updated': product.updated,
                    'prices': []
                }
                
                # Ajouter les prix
                for price in prices:
                    price_data = {
                        'id': price.id,
                        'unit_amount': price.unit_amount,
                        'currency': price.currency,
                        'type': price.type,  # 'one_time' ou 'recurring'
                        'recurring': price.recurring,
                        'active': price.active,
                        'nickname': price.nickname,
                        'metadata': price.metadata
                    }
                    product_data['prices'].append(price_data)
                
                products_with_prices.append(product_data)
            
            logger.info(f"Récupéré {len(products_with_prices)} produits avec leurs prix")
            return products_with_prices
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur récupération produits Stripe: {e}")
            raise
    
    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """Récupérer un produit spécifique avec ses prix."""
        try:
            # Récupérer le produit
            product = stripe.Product.retrieve(product_id)
            
            # Récupérer les prix du produit
            prices = stripe.Price.list(
                product=product_id,
                active=True,
                limit=10
            ).data
            
            # Structurer les données
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'metadata': product.metadata,
                'images': product.images,
                'active': product.active,
                'created': product.created,
                'updated': product.updated,
                'prices': []
            }
            
            # Ajouter les prix
            for price in prices:
                price_data = {
                    'id': price.id,
                    'unit_amount': price.unit_amount,
                    'currency': price.currency,
                    'type': price.type,
                    'recurring': price.recurring,
                    'active': price.active,
                    'nickname': price.nickname,
                    'metadata': price.metadata
                }
                product_data['prices'].append(price_data)
            
            return product_data
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur récupération produit {product_id}: {e}")
            raise
    
    def list_prices_for_product(self, product_id: str) -> List[Dict[str, Any]]:
        """Lister tous les prix d'un produit."""
        try:
            prices = stripe.Price.list(
                product=product_id,
                active=True,
                limit=10
            ).data
            
            prices_data = []
            for price in prices:
                price_data = {
                    'id': price.id,
                    'unit_amount': price.unit_amount,
                    'currency': price.currency,
                    'type': price.type,
                    'recurring': price.recurring,
                    'active': price.active,
                    'nickname': price.nickname,
                    'metadata': price.metadata
                }
                prices_data.append(price_data)
            
            return prices_data
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur récupération prix produit {product_id}: {e}")
            raise
    
    def get_price_details(self, price_id: str) -> Dict[str, Any]:
        """Récupérer les détails d'un prix spécifique."""
        try:
            price = stripe.Price.retrieve(price_id)
            
            price_data = {
                'id': price.id,
                'product': price.product,
                'unit_amount': price.unit_amount,
                'currency': price.currency,
                'type': price.type,
                'recurring': price.recurring,
                'active': price.active,
                'nickname': price.nickname,
                'metadata': price.metadata,
                'created': price.created
            }
            
            return price_data
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur récupération prix {price_id}: {e}")
            raise
    
    def filter_prices_by_type(
        self, 
        prices: List[Dict[str, Any]], 
        price_type: str
    ) -> List[Dict[str, Any]]:
        """Filtrer les prix par type (one_time ou recurring)."""
        return [price for price in prices if price.get('type') == price_type]
    
    def create_invoice_with_stripe_products(
        self,
        customer_id: str,
        price_items: List[Dict[str, Any]],
        currency: str = 'eur',
        description: str = '',
        metadata: Optional[Dict[str, str]] = None,
        send_email: bool = True,
        due_date: Optional[datetime] = None
    ) -> stripe.Invoice:
        """Créer une facture avec des produits Stripe (utilise price_id)."""
        try:
            # Créer la facture
            invoice = stripe.Invoice.create(
                customer=customer_id,
                currency=currency.lower(),
                description=description,
                metadata=metadata or {},
                auto_advance=send_email,
                collection_method='send_invoice',
                due_date=int(due_date.timestamp()) if due_date else None
            )
            
            # Ajouter les lignes de facture - on récupère le prix depuis Stripe
            for item in price_items:
                # Récupérer les détails du prix avec le produit expansé
                price_obj = stripe.Price.retrieve(item['price_id'], expand=['product'])
                
                # Obtenir le nom du produit
                product_name = "Produit"
                if hasattr(price_obj, 'product') and hasattr(price_obj.product, 'name'):
                    product_name = price_obj.product.name
                
                description = f"{product_name}"
                if price_obj.nickname:
                    description += f" - {price_obj.nickname}"
                
                quantity = item.get('quantity', 1)
                total_amount = price_obj.unit_amount * quantity
                
                stripe.InvoiceItem.create(
                    invoice=invoice.id,
                    customer=customer_id,
                    amount=total_amount,  # Montant total en centimes
                    currency=price_obj.currency,
                    description=f"{description} (Qté: {quantity})" if quantity > 1 else description,
                    metadata={
                        'product_id': str(item.get('product_id', '')),
                        'price_id': str(item.get('price_id', '')),
                        'quantity': str(quantity)
                    }
                )
            
            # Finaliser la facture
            invoice = stripe.Invoice.finalize_invoice(invoice.id)
            
            # Envoyer par email si demandé
            if send_email:
                stripe.Invoice.send_invoice(invoice.id)
            
            return invoice
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur création facture avec produits Stripe: {e}")
            raise
    
    def sync_stripe_products(self) -> Dict[str, Any]:
        """Synchroniser les produits Stripe avec la base locale."""
        try:
            # Récupérer tous les produits avec leurs prix
            products = self.list_products_with_prices()
            
            sync_result = {
                'products_count': len(products),
                'one_time_products': 0,
                'recurring_products': 0,
                'sync_timestamp': datetime.now().isoformat(),
                'products': products
            }
            
            # Compter les types de produits
            for product in products:
                has_one_time = any(p.get('type') == 'one_time' for p in product['prices'])
                has_recurring = any(p.get('type') == 'recurring' for p in product['prices'])
                
                if has_one_time:
                    sync_result['one_time_products'] += 1
                if has_recurring:
                    sync_result['recurring_products'] += 1
            
            logger.info(f"Synchronisation terminée: {sync_result['products_count']} produits")
            return sync_result
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur synchronisation produits Stripe: {e}")
            raise
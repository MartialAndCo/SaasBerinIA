"""Handler pour la facturation des clients"""
import logging
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services.api_client import BeriniaAPIClient
from utils.keyboards import (
    get_billing_menu_keyboard, get_clients_selection_keyboard,
    get_client_billing_options_keyboard, get_billing_services_selection_keyboard,
    get_billing_info_edit_keyboard, get_invoice_confirmation_keyboard,
    get_invoices_list_keyboard, get_invoice_details_keyboard
)
from utils.formatters import truncate_text, format_clients_list, format_loading
from config.settings import EMOJIS

logger = logging.getLogger(__name__)

class BillingHandler:
    """Gestionnaire pour la facturation"""
    
    def __init__(self):
        self.api_client = BeriniaAPIClient()
        # Store temporary data for multi-step operations
        self.temp_data = {}
    
    async def handle_callback(self, query, callback_data: str):
        """Gère tous les callbacks de facturation"""
        
        try:
            if callback_data == "billing_main":
                await self._show_billing_menu(query)
            
            elif callback_data == "billing_clients" or callback_data == "billing_select_client":
                await self._show_client_selection(query)
            
            elif callback_data.startswith("billing_clients_page_"):
                page = int(callback_data.split("_")[-1])
                await self._show_client_selection(query, page)
            
            elif callback_data.startswith("billing_client_"):
                client_id = callback_data.split("_")[-1]
                await self._show_client_billing_options(query, client_id)
            
            elif callback_data.startswith("billing_edit_info_"):
                client_id = callback_data.split("_")[-1]
                await self._show_edit_billing_info(query, client_id)
            
            elif callback_data.startswith("billing_create_invoice_"):
                client_id = callback_data.split("_")[-1]
                await self._show_invoice_type_selection(query, client_id)
            
            elif callback_data.startswith("billing_toggle_service_"):
                await self._handle_service_toggle(query, callback_data)
            
            elif callback_data.startswith("billing_clear_selection_"):
                client_id = callback_data.split("_")[-1]
                await self._clear_service_selection(query, client_id)
            
            elif callback_data.startswith("billing_finalize_"):
                client_id = callback_data.split("_")[-1]
                await self._show_invoice_confirmation(query, client_id)
            
            elif callback_data.startswith("billing_send_invoice_"):
                client_id = callback_data.split("_")[-1]
                await self._create_and_send_invoice(query, client_id, send_email=True)
            
            elif callback_data.startswith("billing_draft_invoice_"):
                client_id = callback_data.split("_")[-1]
                await self._create_and_send_invoice(query, client_id, send_email=False)
            
            elif callback_data.startswith("billing_view_invoices_"):
                client_id = callback_data.split("_")[-1]
                await self._show_client_invoices(query, client_id)
            
            elif callback_data == "billing_view_all_invoices":
                await self._show_all_invoices(query)
            
            elif callback_data.startswith("billing_invoice_details_"):
                invoice_id = callback_data.split("_")[-1]
                await self._show_invoice_details(query, invoice_id)
            
            elif callback_data.startswith("billing_send_invoice_email_"):
                invoice_id = callback_data.split("_")[-1]
                await self._send_invoice_email(query, invoice_id)
            
            elif callback_data == "billing_stats":
                await self._show_billing_stats(query)
            
            elif callback_data.startswith("billing_stats_"):
                period = callback_data.split("_")[-1]
                await self._show_billing_stats_period(query, period)
            
            elif callback_data == "billing_invoices":
                await self._show_all_invoices(query)
            
            elif callback_data.startswith("send_invoice_"):
                invoice_id = callback_data.split("_")[-1]
                await self._send_invoice_email(query, invoice_id)
            
            elif callback_data == "billing_today_meetings":
                await self._show_today_meetings(query)
            
            elif callback_data.startswith("billing_meeting_client_"):
                lead_id = callback_data.split("_")[-1]
                await self._select_client_from_meeting(query, int(lead_id))
            
            elif callback_data == "billing_stripe_products":
                await self._show_stripe_products(query)
            
            elif callback_data == "billing_sync_stripe":
                await self._sync_stripe_products(query)
            
            elif callback_data.startswith("billing_stripe_products_"):
                client_id = callback_data.split("_")[-1]
                await self._show_stripe_product_selection(query, client_id)
            
            elif callback_data.startswith("billing_local_services_"):
                client_id = callback_data.split("_")[-1]
                await self._show_service_selection(query, client_id)
            
            elif callback_data.startswith("billing_toggle_stripe_"):
                await self._handle_stripe_product_toggle(query, callback_data)
            
            elif callback_data.startswith("billing_clear_stripe_"):
                client_id = callback_data.split("_")[-1]
                await self._clear_stripe_selection(query, client_id)
            
            elif callback_data.startswith("billing_create_stripe_invoice_"):
                client_id = callback_data.split("_")[-1]
                await self._create_stripe_invoice(query, client_id)
            
            else:
                await query.answer("Fonction en cours de développement")
                
        except Exception as e:
            logger.error(f"Erreur dans billing handler: {e}")
            await query.answer("❌ Erreur lors du traitement")
            await self._show_billing_menu(query)
    
    async def _show_billing_menu(self, query):
        """Affiche le menu principal de facturation"""
        keyboard = get_billing_menu_keyboard()
        
        text = "💳 **Menu Facturation**\n\n"
        text += "Gestion de la facturation clients :\n\n"
        text += "• 👥 Sélectionner un client pour facturation\n"
        text += "• 📋 Consulter toutes les factures\n"
        text += "• 📊 Voir les statistiques de facturation"
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_client_selection(self, query, page: int = 0):
        """Affiche la liste des clients pour sélection"""
        await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
        
        # Récupérer tous les clients pour la pagination
        all_clients = self.api_client.get_clients_for_billing(limit=100)
        
        if not all_clients:
            await query.edit_message_text(
                text="❌ Aucun client trouvé",
                reply_markup=get_billing_menu_keyboard()
            )
            return
        
        # Pagination : 6 clients par page
        clients_per_page = 6
        start_idx = page * clients_per_page
        end_idx = start_idx + clients_per_page
        page_clients = all_clients[start_idx:end_idx]
        
        # Construire le texte avec les vrais noms et informations
        text = f"👥 **Sélection du client à facturer**\n\n"
        text += f"📄 Page {page + 1}/{(len(all_clients) - 1) // clients_per_page + 1} "
        text += f"({start_idx + 1}-{min(end_idx, len(all_clients))} sur {len(all_clients)})\n\n"
        
        for i, client in enumerate(page_clients, 1):
            # Construire le nom complet
            first_name = client.get('first_name', '').strip()
            last_name = client.get('last_name', '').strip()
            
            if first_name and last_name:
                name = f"{first_name} {last_name}"
            elif first_name:
                name = first_name
            elif last_name:
                name = last_name
            else:
                name = "Nom non renseigné"
            
            # Priorité: entreprise > company
            company = client.get('entreprise', '').strip() or client.get('company', '').strip()
            email = client.get('email', 'Email non renseigné')
            phone = client.get('phone', '').strip()
            position = client.get('position', '').strip()
            industry = client.get('industry', '').strip()
            source = client.get('source', '').strip()
            
            text += f"**{start_idx + i}. {name}**\n"
            if company:
                text += f"🏢 {company}\n"
            if position:
                text += f"💼 {position}\n"
            if industry:
                text += f"🏭 {industry}\n"
            text += f"📧 {email}\n"
            if phone:
                text += f"📞 {phone}\n"
            if source:
                text += f"📍 Source: {source}\n"
            
            # Status facturation
            if client.get('billing_address') or client.get('billing_city'):
                text += "✅ Prêt pour facturation\n"
            else:
                text += "⚠️ Infos facturation à compléter\n"
            text += "\n"
        
        # Créer le clavier avec pagination
        keyboard = get_clients_selection_keyboard(page_clients, page, len(all_clients), clients_per_page)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_client_billing_options(self, query, client_id: str):
        """Affiche les options de facturation pour un client"""
        # Récupérer les infos du client
        client = self.api_client.get_lead_details(int(client_id))
        if not client:
            await query.answer("❌ Client non trouvé")
            return
        
        # Récupérer les infos de facturation
        billing_info = self.api_client.get_billing_info(int(client_id))
        
        name = f"{client.get('first_name', '')} {client.get('last_name', '')}".strip()
        if not name:
            name = client.get('email', f"Client {client_id}")
        
        company = client.get('company', '')
        
        text = f"💳 **Facturation - {name}**\n"
        if company:
            text += f"🏢 {company}\n"
        text += "\n"
        
        # Afficher l'état des infos de facturation
        if billing_info:
            missing_fields = []
            if not billing_info.get('billing_address'):
                missing_fields.append("Adresse")
            if not billing_info.get('billing_city'):
                missing_fields.append("Ville")
            if not billing_info.get('billing_country'):
                missing_fields.append("Pays")
            if not billing_info.get('billing_email'):
                missing_fields.append("Email facturation")
            
            if missing_fields:
                text += f"⚠️ **Informations manquantes :** {', '.join(missing_fields)}\n\n"
            else:
                text += "✅ **Informations de facturation complètes**\n\n"
        else:
            text += "❌ **Aucune information de facturation**\n\n"
        
        text += "Que souhaitez-vous faire ?"
        
        keyboard = get_client_billing_options_keyboard(client_id)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_edit_billing_info(self, query, client_id: str):
        """Affiche l'interface d'édition des infos de facturation"""
        billing_info = self.api_client.get_billing_info(int(client_id))
        
        text = "📝 **Informations de facturation**\n\n"
        
        if billing_info:
            text += f"📍 **Adresse :** {billing_info.get('billing_address', 'Non renseignée')}\n"
            text += f"🏙️ **Ville :** {billing_info.get('billing_city', 'Non renseignée')}\n"
            text += f"📮 **Code postal :** {billing_info.get('billing_postal_code', 'Non renseigné')}\n"
            text += f"🌍 **Pays :** {billing_info.get('billing_country', 'Non renseigné')}\n"
            text += f"🏢 **Numéro TVA :** {billing_info.get('vat_number', 'Non renseigné')}\n"
            text += f"📧 **Email facturation :** {billing_info.get('billing_email', 'Non renseigné')}\n"
            text += f"👤 **Contact facturation :** {billing_info.get('billing_contact_name', 'Non renseigné')}\n"
        else:
            text += "❌ Aucune information de facturation enregistrée\n"
        
        text += "\nSélectionnez le champ à modifier :"
        
        keyboard = get_billing_info_edit_keyboard(client_id)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_service_selection(self, query, client_id: str):
        """Affiche la sélection des services à facturer"""
        services = self.api_client.get_available_services()
        
        if not services:
            await query.edit_message_text(
                text="❌ Aucun service disponible",
                reply_markup=get_client_billing_options_keyboard(client_id)
            )
            return
        
        # Récupérer les services sélectionnés temporairement
        session_key = f"billing_services_{client_id}"
        selected_services = self.temp_data.get(session_key, [])
        
        text = "🧾 **Création de facture**\n\n"
        text += "Sélectionnez les services à inclure dans la facture :\n\n"
        
        # Calcul du total si des services sont sélectionnés
        if selected_services:
            total = 0
            for service in services:
                if service.get('id') in selected_services:
                    if service.get('setup_price') and service.get('monthly_price'):
                        total += service['setup_price']  # Pour le moment, on ne compte que le setup
                    else:
                        total += service.get('price', 0)
            
            text += f"💰 **Total actuel :** {total}€\n\n"
        
        keyboard = get_billing_services_selection_keyboard(services, client_id, selected_services)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_service_toggle(self, query, callback_data: str):
        """Gère la sélection/désélection d'un service"""
        parts = callback_data.split("_")
        client_id = parts[3]
        service_id = int(parts[4])
        
        session_key = f"billing_services_{client_id}"
        selected_services = self.temp_data.get(session_key, [])
        
        if service_id in selected_services:
            selected_services.remove(service_id)
        else:
            selected_services.append(service_id)
        
        self.temp_data[session_key] = selected_services
        
        # Rafraîchir l'affichage
        await self._show_service_selection(query, client_id)
    
    async def _clear_service_selection(self, query, client_id: str):
        """Vide la sélection de services"""
        session_key = f"billing_services_{client_id}"
        self.temp_data[session_key] = []
        await self._show_service_selection(query, client_id)
    
    async def _show_invoice_confirmation(self, query, client_id: str):
        """Affiche la confirmation de création de facture"""
        session_key = f"billing_services_{client_id}"
        selected_services = self.temp_data.get(session_key, [])
        
        if not selected_services:
            await query.answer("❌ Aucun service sélectionné")
            return
        
        # Récupérer les détails des services
        services = self.api_client.get_available_services()
        selected_service_details = [s for s in services if s.get('id') in selected_services]
        
        # Récupérer les infos client et facturation
        client = self.api_client.get_lead_details(int(client_id))
        billing_info = self.api_client.get_billing_info(int(client_id))
        
        name = f"{client.get('first_name', '')} {client.get('last_name', '')}".strip()
        
        text = f"✅ **Confirmation de facture**\n\n"
        text += f"👤 **Client :** {name}\n"
        if client.get('company'):
            text += f"🏢 **Entreprise :** {client['company']}\n"
        text += "\n**Services sélectionnés :**\n"
        
        total = 0
        for service in selected_service_details:
            if service.get('setup_price') and service.get('monthly_price'):
                price = service['setup_price']
                text += f"• {service['name']} - {price}€ (setup)\n"
            else:
                price = service.get('price', 0)
                text += f"• {service['name']} - {price}€\n"
            total += price
        
        # Calcul TVA (20% pour la France)
        tax_rate = 0.20 if billing_info and billing_info.get('billing_country') == 'FR' else 0.0
        tax_amount = total * tax_rate
        total_with_tax = total + tax_amount
        
        text += f"\n💰 **Sous-total :** {total}€\n"
        if tax_amount > 0:
            text += f"📊 **TVA (20%) :** {tax_amount:.2f}€\n"
        text += f"💳 **Total TTC :** {total_with_tax:.2f}€\n\n"
        
        # Vérifier les infos de facturation
        if not billing_info or not all([
            billing_info.get('billing_email') or client.get('email'),
            billing_info.get('billing_contact_name') or name
        ]):
            text += "⚠️ **Attention :** Informations de facturation incomplètes\n\n"
        
        text += "Souhaitez-vous créer et envoyer cette facture ?"
        
        keyboard = get_invoice_confirmation_keyboard(client_id)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _create_and_send_invoice(self, query, client_id: str, send_email: bool = True):
        """Crée et envoie (optionnellement) une facture"""
        try:
            session_key = f"billing_services_{client_id}"
            selected_services = self.temp_data.get(session_key, [])
            
            if not selected_services:
                await query.answer("❌ Aucun service sélectionné")
                return
            
            # Préparer les données pour l'API
            services_data = []
            for service_id in selected_services:
                services_data.append({
                    "service_id": service_id,
                    "quantity": 1
                })
            
            invoice_data = {
                "lead_id": int(client_id),
                "services": services_data,
                "send_email": send_email
            }
            
            # Créer la facture via l'API
            result = self.api_client.create_invoice(invoice_data)
            
            if result:
                # Nettoyer les données temporaires
                if session_key in self.temp_data:
                    del self.temp_data[session_key]
                
                invoice = result.get('invoice', {})
                message = result.get('message', '')
                
                text = "✅ **Facture créée avec succès !**\n\n"
                text += f"📄 **Numéro :** {invoice.get('invoice_number')}\n"
                text += f"💰 **Montant :** {invoice.get('total_amount')}€\n"
                text += f"📅 **Date :** {invoice.get('invoice_date', '').split('T')[0]}\n"
                
                if send_email:
                    text += f"📤 **Statut :** Envoyée par email\n"
                else:
                    text += f"📝 **Statut :** Brouillon\n"
                
                if result.get('stripe_invoice_url'):
                    text += f"\n🔗 [Voir la facture Stripe]({result['stripe_invoice_url']})\n"
                
                text += f"\n{message}"
                
                keyboard = get_client_billing_options_keyboard(client_id)
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.answer("❌ Erreur lors de la création de la facture")
                
        except Exception as e:
            logger.error(f"Erreur création facture: {e}")
            await query.answer("❌ Erreur lors de la création de la facture")
    
    async def _show_client_invoices(self, query, client_id: str):
        """Affiche les factures d'un client"""
        invoices = self.api_client.get_lead_invoices(int(client_id))
        
        if not invoices:
            await query.edit_message_text(
                text="📋 Aucune facture trouvée pour ce client",
                reply_markup=get_client_billing_options_keyboard(client_id)
            )
            return
        
        text = f"📋 **Factures du client**\n\n"
        text += f"Total : {len(invoices)} facture(s)\n\n"
        
        keyboard = get_invoices_list_keyboard(invoices, client_id)
        
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_all_invoices(self, query):
        """Affiche toutes les factures"""
        try:
            # Récupérer toutes les factures via l'API
            invoices = self.api_client.get_all_invoices()
            
            if not invoices:
                await query.edit_message_text(
                    text="📋 **Toutes les factures**\n\n🔍 Aucune facture trouvée",
                    reply_markup=get_billing_menu_keyboard()
                )
                return
            
            # Créer le message avec pagination si nécessaire
            text = "📋 **Toutes les factures**\n\n"
            
            # Limiter à 10 factures par page
            display_invoices = invoices[:10]
            
            for invoice in display_invoices:
                status_emoji = {
                    'draft': '📝',
                    'sent': '📤',
                    'paid': '✅',
                    'overdue': '⚠️',
                    'cancelled': '❌'
                }.get(invoice.get('status', 'draft'), '📄')
                
                amount = invoice.get('total_amount', 0)
                invoice_date = invoice.get('invoice_date', '')[:10] if invoice.get('invoice_date') else 'N/A'
                
                text += f"{status_emoji} **{invoice.get('invoice_number', 'N/A')}**\n"
                text += f"   📅 {invoice_date} - {amount:.2f}€\n"
                text += f"   👤 {invoice.get('lead_name', 'Client inconnu')}\n"
                if invoice.get('company'):
                    text += f"   🏢 {invoice.get('company')}\n"
                text += "\n"
            
            if len(invoices) > 10:
                text += f"... et {len(invoices) - 10} factures supplémentaires\n\n"
            
            # Ajouter des boutons pour les actions
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Statistiques", callback_data="billing_stats")],
                [InlineKeyboardButton("↩️ Retour", callback_data="billing_main")]
            ])
            
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur affichage factures: {e}")
            await query.edit_message_text(
                text="📋 **Toutes les factures**\n\n❌ Erreur lors de la récupération des factures",
                reply_markup=get_billing_menu_keyboard()
            )
    
    async def _show_invoice_details(self, query, invoice_id: str):
        """Affiche les détails d'une facture"""
        try:
            # Récupérer les détails de la facture via l'API
            invoice_details = self.api_client.get_invoice_details(int(invoice_id))
            
            if not invoice_details:
                await query.edit_message_text(
                    text=f"📄 **Détails de la facture {invoice_id}**\n\n❌ Facture non trouvée",
                    reply_markup=get_billing_menu_keyboard()
                )
                return
            
            invoice = invoice_details.get('invoice', {})
            lead = invoice_details.get('lead', {})
            stripe_details = invoice_details.get('stripe_details')
            
            # Construire le message détaillé
            text = f"📄 **Détails de la facture {invoice.get('invoice_number', 'N/A')}**\n\n"
            
            # Informations de base
            status_emoji = {
                'draft': '📝',
                'sent': '📤',
                'paid': '✅',
                'overdue': '⚠️',
                'cancelled': '❌'
            }.get(invoice.get('status', 'draft'), '📄')
            
            text += f"**📊 Statut:** {status_emoji} {invoice.get('status', 'N/A').title()}\n"
            text += f"**💰 Montant HT:** {invoice.get('amount', 0):.2f}€\n"
            text += f"**🧾 TVA:** {invoice.get('tax_amount', 0):.2f}€\n"
            text += f"**💯 Total TTC:** {invoice.get('total_amount', 0):.2f}€\n"
            text += f"**💱 Devise:** {invoice.get('currency', 'EUR')}\n\n"
            
            # Informations client
            text += "👤 **Client:**\n"
            text += f"   📧 {lead.get('first_name', '')} {lead.get('last_name', '')}\n"
            text += f"   📨 {lead.get('email', 'N/A')}\n"
            if lead.get('company'):
                text += f"   🏢 {lead.get('company')}\n"
            if lead.get('phone'):
                text += f"   📞 {lead.get('phone')}\n"
            text += "\n"
            
            # Informations de facturation
            if lead.get('billing_address'):
                text += "🏠 **Adresse de facturation:**\n"
                text += f"   {lead.get('billing_address')}\n"
                if lead.get('billing_city'):
                    text += f"   {lead.get('billing_postal_code', '')} {lead.get('billing_city')}\n"
                if lead.get('billing_country'):
                    text += f"   {lead.get('billing_country')}\n"
                if lead.get('vat_number'):
                    text += f"   🆔 TVA: {lead.get('vat_number')}\n"
                text += "\n"
            
            # Dates
            invoice_date = invoice.get('invoice_date', '')[:10] if invoice.get('invoice_date') else 'N/A'
            due_date = invoice.get('due_date', '')[:10] if invoice.get('due_date') else 'N/A'
            paid_date = invoice.get('paid_date', '')[:10] if invoice.get('paid_date') else None
            
            text += f"📅 **Date facture:** {invoice_date}\n"
            text += f"📅 **Date échéance:** {due_date}\n"
            if paid_date:
                text += f"✅ **Date paiement:** {paid_date}\n"
            text += "\n"
            
            # Services facturés
            services_data = invoice.get('services_data', [])
            if services_data:
                text += "🛍️ **Services facturés:**\n"
                for service in services_data:
                    service_name = service.get('name', 'Service')
                    quantity = service.get('quantity', 1)
                    unit_price = service.get('unit_price', 0)
                    amount = service.get('amount', 0)
                    
                    text += f"   • {service_name}\n"
                    text += f"     Qté: {quantity} × {unit_price:.2f}€ = {amount:.2f}€\n"
                text += "\n"
            
            # Informations Stripe
            if stripe_details:
                text += "🔗 **Stripe:**\n"
                text += f"   📄 Facture: {stripe_details.get('stripe_id', 'N/A')}\n"
                if stripe_details.get('hosted_invoice_url'):
                    text += f"   🌐 URL publique disponible\n"
                if stripe_details.get('invoice_pdf'):
                    text += f"   📎 PDF disponible\n"
                text += "\n"
            
            # Créer le clavier avec les actions disponibles
            keyboard_buttons = []
            
            if invoice.get('status') == 'draft' and stripe_details:
                keyboard_buttons.append([InlineKeyboardButton("📤 Envoyer par email", callback_data=f"send_invoice_{invoice_id}")])
            
            if stripe_details and stripe_details.get('hosted_invoice_url'):
                keyboard_buttons.append([InlineKeyboardButton("🌐 Voir sur Stripe", url=stripe_details.get('hosted_invoice_url'))])
            
            keyboard_buttons.append([InlineKeyboardButton("↩️ Retour", callback_data="billing_invoices")])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur affichage détails facture: {e}")
            await query.edit_message_text(
                text=f"📄 **Détails de la facture {invoice_id}**\n\n❌ Erreur lors de la récupération des détails",
                reply_markup=get_billing_menu_keyboard()
            )
    
    async def _send_invoice_email(self, query, invoice_id: str):
        """Envoie une facture par email"""
        try:
            result = self.api_client.send_invoice(int(invoice_id))
            if result:
                await query.answer("✅ Facture envoyée par email")
            else:
                await query.answer("❌ Erreur lors de l'envoi")
        except Exception as e:
            logger.error(f"Erreur envoi facture: {e}")
            await query.answer("❌ Erreur lors de l'envoi")
    
    async def _show_billing_stats(self, query):
        """Affiche les statistiques de facturation"""
        try:
            # Récupérer les statistiques via l'API
            stats = self.api_client.get_billing_stats()
            
            if not stats:
                await query.edit_message_text(
                    text="📊 **Statistiques de facturation**\n\n❌ Erreur lors de la récupération des statistiques",
                    reply_markup=get_billing_menu_keyboard()
                )
                return
            
            # Construire le message avec les statistiques
            text = "📊 **Statistiques de facturation**\n\n"
            
            # Statistiques générales
            text += "📈 **Vue d'ensemble:**\n"
            text += f"   💰 Chiffre d'affaires total: {stats.get('total_revenue', 0):.2f}€\n"
            text += f"   📄 Nombre total de factures: {stats.get('total_invoices', 0)}\n"
            text += f"   💱 Devise: {stats.get('currency', 'EUR')}\n\n"
            
            # Statistiques de la période courante
            period = stats.get('period', 'month')
            period_name = {
                'day': "aujourd'hui",
                'week': 'cette semaine',
                'month': 'ce mois',
                'year': 'cette année'
            }.get(period, 'cette période')
            
            text += f"📅 **Performance {period_name}:**\n"
            text += f"   💰 Revenus: {stats.get('period_revenue', 0):.2f}€\n"
            text += f"   📄 Factures: {stats.get('period_invoices', 0)}\n\n"
            
            # Répartition par statut
            status_breakdown = stats.get('status_breakdown', [])
            if status_breakdown:
                text += "📊 **Répartition par statut:**\n"
                for status_stat in status_breakdown:
                    status = status_stat.get('status', 'unknown')
                    count = status_stat.get('count', 0)
                    amount = status_stat.get('total_amount', 0)
                    
                    status_emoji = {
                        'draft': '📝',
                        'sent': '📤',
                        'paid': '✅',
                        'overdue': '⚠️',
                        'cancelled': '❌'
                    }.get(status, '📄')
                    
                    text += f"   {status_emoji} {status.title()}: {count} factures ({amount:.2f}€)\n"
                text += "\n"
            
            # Factures en retard
            overdue_invoices = stats.get('overdue_invoices', 0)
            overdue_amount = stats.get('overdue_amount', 0)
            if overdue_invoices > 0:
                text += "⚠️ **Factures en retard:**\n"
                text += f"   📄 {overdue_invoices} factures\n"
                text += f"   💰 Montant: {overdue_amount:.2f}€\n\n"
            
            # Ajouter des boutons pour différentes périodes
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📅 Jour", callback_data="billing_stats_day"),
                    InlineKeyboardButton("📅 Semaine", callback_data="billing_stats_week")
                ],
                [
                    InlineKeyboardButton("📅 Mois", callback_data="billing_stats_month"),
                    InlineKeyboardButton("📅 Année", callback_data="billing_stats_year")
                ],
                [InlineKeyboardButton("📋 Toutes les factures", callback_data="billing_invoices")],
                [InlineKeyboardButton("↩️ Retour", callback_data="billing_main")]
            ])
            
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur affichage statistiques: {e}")
            await query.edit_message_text(
                text="📊 **Statistiques de facturation**\n\n❌ Erreur lors de la récupération des statistiques",
                reply_markup=get_billing_menu_keyboard()
            )

    async def _show_billing_stats_period(self, query, period: str):
        """Affiche les statistiques pour une période spécifique"""
        try:
            stats = self.api_client.get_billing_stats(period=period)
            if stats:
                # Réutiliser la logique d'affichage mais avec la période spécifiée
                await self._show_billing_stats(query)
            else:
                await query.answer("❌ Erreur lors de la récupération des statistiques")
        except Exception as e:
            logger.error(f"Erreur statistiques période {period}: {e}")
            await query.answer("❌ Erreur lors de la récupération des statistiques")

    async def _show_today_meetings(self, query):
        """Affiche les rendez-vous du jour pour facturation"""
        try:
            meetings_data = self.api_client.get_today_meetings_for_billing()
            
            if not meetings_data or not meetings_data.get('meetings'):
                await query.edit_message_text(
                    text="📅 **Rendez-vous du jour**\n\n🔍 Aucun rendez-vous aujourd'hui",
                    reply_markup=get_billing_menu_keyboard()
                )
                return
            
            meetings = meetings_data.get('meetings', [])
            default_date = "aujourd'hui"
            text = f"📅 **Rendez-vous du jour ({meetings_data.get('date', default_date)})**\n\n"
            text += f"🔢 {len(meetings)} rendez-vous trouvés\n\n"
            
            keyboard_buttons = []
            
            for meeting in meetings[:8]:  # Limiter à 8 pour éviter les messages trop longs
                meeting_info = meeting.get('meeting', {})
                lead_info = meeting.get('lead')
                
                client_name = meeting_info.get('client_name', 'Client')
                start_time = meeting_info.get('start_time', '')[:16] if meeting_info.get('start_time') else 'N/A'
                status = meeting_info.get('status', 'unknown')
                can_invoice = meeting.get('can_invoice', False)
                existing_invoices = meeting.get('existing_invoices', 0)
                
                status_emoji = {
                    'scheduled': '📅',
                    'confirmed': '✅',
                    'completed': '🎯',
                    'cancelled': '❌'
                }.get(status, '📅')
                
                text += f"{status_emoji} **{client_name}**\n"
                text += f"   🕒 {start_time.replace('T', ' ')}\n"
                text += f"   📊 Statut: {status.title()}\n"
                
                if lead_info:
                    company = lead_info.get('company')
                    if company:
                        text += f"   🏢 {company}\n"
                    
                    if can_invoice:
                        text += f"   ✅ Prêt pour facturation\n"
                        if existing_invoices > 0:
                            text += f"   📄 {existing_invoices} factures existantes\n"
                        
                        # Ajouter bouton pour facturer ce client
                        keyboard_buttons.append([
                            InlineKeyboardButton(
                                f"💳 Facturer {client_name[:15]}...",
                                callback_data=f"billing_meeting_client_{lead_info.get('id')}"
                            )
                        ])
                    else:
                        text += f"   ⚠️ Infos facturation incomplètes\n"
                else:
                    text += f"   ❓ Client non trouvé en base\n"
                
                text += "\n"
            
            if len(meetings) > 8:
                text += f"... et {len(meetings) - 8} autres rendez-vous\n\n"
            
            # Ajouter boutons de navigation
            keyboard_buttons.extend([
                [InlineKeyboardButton("👥 Tous les clients", callback_data="billing_clients")],
                [InlineKeyboardButton("↩️ Retour", callback_data="billing_main")]
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur affichage meetings du jour: {e}")
            await query.edit_message_text(
                text="📅 **Rendez-vous du jour**\n\n❌ Erreur lors de la récupération des rendez-vous",
                reply_markup=get_billing_menu_keyboard()
            )

    async def _select_client_from_meeting(self, query, lead_id: int):
        """Sélectionne un client depuis les meetings pour facturation"""
        try:
            # Récupérer les infos du lead
            lead_info = self.api_client.get_billing_info(lead_id)
            if not lead_info:
                await query.answer("❌ Client non trouvé")
                return
            
            # Stocker l'ID du client sélectionné et rediriger vers le processus normal
            self.temp_data[query.from_user.id] = {'selected_lead_id': lead_id}
            await self._show_client_billing_options(query, str(lead_id))
            
        except Exception as e:
            logger.error(f"Erreur sélection client meeting: {e}")
            await query.answer("❌ Erreur lors de la sélection du client")

    async def _show_stripe_products(self, query):
        """Affiche les produits Stripe disponibles"""
        try:
            products_data = self.api_client.get_stripe_products()
            
            if not products_data or not products_data.get('products'):
                await query.edit_message_text(
                    text="🛍️ **Produits Stripe**\n\n🔍 Aucun produit trouvé\n\nUtilisez 'Synchroniser' pour récupérer les produits depuis Stripe",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Synchroniser Stripe", callback_data="billing_sync_stripe")],
                        [InlineKeyboardButton("↩️ Retour", callback_data="billing_main")]
                    ])
                )
                return
            
            products = products_data.get('products', [])
            count = products_data.get('count', 0)
            
            text = f"🛍️ **Produits Stripe ({count} produits)**\n\n"
            
            # Afficher les produits (limiter à 8)
            for product in products[:8]:
                text += f"📦 **{product.get('name', 'Produit sans nom')}**\n"
                
                if product.get('description'):
                    text += f"   📝 {product.get('description')[:50]}...\n"
                
                # Afficher les prix
                prices = product.get('prices', [])
                if prices:
                    text += "   💰 Prix:\n"
                    for price in prices[:3]:  # Limiter à 3 prix par produit
                        amount = price.get('unit_amount', 0) / 100 if price.get('unit_amount') else 0
                        currency = price.get('currency', 'eur').upper()
                        price_type = price.get('type', 'one_time')
                        
                        type_emoji = '💳' if price_type == 'one_time' else '🔄'
                        type_name = 'Unique' if price_type == 'one_time' else 'Récurrent'
                        
                        text += f"     {type_emoji} {amount:.2f} {currency} ({type_name})\n"
                        
                        if price.get('recurring') and price_type == 'recurring':
                            interval = price.get('recurring', {}).get('interval', 'month')
                            text += f"       📅 Facturation: {interval}\n"
                else:
                    text += "   ⚠️ Aucun prix configuré\n"
                
                text += "\n"
            
            if len(products) > 8:
                text += f"... et {len(products) - 8} autres produits\n\n"
            
            text += "ℹ️ *Synchronisez pour mettre à jour la liste*"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Synchroniser", callback_data="billing_sync_stripe")],
                [InlineKeyboardButton("📋 Voir les factures", callback_data="billing_invoices")],
                [InlineKeyboardButton("↩️ Retour", callback_data="billing_main")]
            ])
            
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur affichage produits Stripe: {e}")
            await query.edit_message_text(
                text="🛍️ **Produits Stripe**\n\n❌ Erreur lors de la récupération des produits",
                reply_markup=get_billing_menu_keyboard()
            )

    async def _sync_stripe_products(self, query):
        """Synchronise les produits avec Stripe"""
        try:
            await query.answer("🔄 Synchronisation en cours...")
            
            sync_result = self.api_client.sync_stripe_products()
            
            if sync_result:
                products_count = sync_result.get('sync_result', {}).get('products_count', 0)
                one_time = sync_result.get('sync_result', {}).get('one_time_products', 0)
                recurring = sync_result.get('sync_result', {}).get('recurring_products', 0)
                
                text = "✅ **Synchronisation terminée**\n\n"
                text += f"📦 **{products_count} produits** synchronisés\n"
                text += f"💳 Produits uniques: {one_time}\n"
                text += f"🔄 Produits récurrents: {recurring}\n\n"
                text += "Les produits sont maintenant disponibles pour la facturation."
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛍️ Voir les produits", callback_data="billing_stripe_products")],
                    [InlineKeyboardButton("↩️ Retour", callback_data="billing_main")]
                ])
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    text="❌ **Erreur de synchronisation**\n\nImpossible de synchroniser avec Stripe",
                    reply_markup=get_billing_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Erreur synchronisation Stripe: {e}")
            await query.edit_message_text(
                text="❌ **Erreur de synchronisation**\n\nErreur lors de la synchronisation avec Stripe",
                reply_markup=get_billing_menu_keyboard()
            )

    async def _show_invoice_type_selection(self, query, client_id: str):
        """Affiche le choix du type de facture à créer"""
        try:
            # Récupérer les infos du client
            client = self.api_client.get_lead_details(int(client_id))
            if not client:
                await query.answer("❌ Client non trouvé")
                return
            
            name = f"{client.get('first_name', '')} {client.get('last_name', '')}".strip()
            if not name:
                name = client.get('email', f"Client {client_id}")
            
            text = f"🧾 **Création de facture - {name}**\n\n"
            text += "Quel type de facture souhaitez-vous créer ?\n\n"
            text += "💡 **Produits Stripe** - Catalogue complet avec abonnements automatiques\n"
            text += "⚙️ **Services locaux** - Services configurés localement"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🛍️ Produits Stripe", callback_data=f"billing_stripe_products_{client_id}")],
                [InlineKeyboardButton("⚙️ Services locaux", callback_data=f"billing_local_services_{client_id}")],
                [InlineKeyboardButton("↩️ Retour", callback_data=f"billing_client_{client_id}")]
            ])
            
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur sélection type facture: {e}")
            await query.answer("❌ Erreur lors de l'affichage des options")

    async def _show_stripe_product_selection(self, query, client_id: str):
        """Affiche la sélection des produits Stripe pour facture"""
        try:
            await query.edit_message_text(text=format_loading(), parse_mode=ParseMode.MARKDOWN)
            
            # Récupérer les produits Stripe
            products_data = self.api_client.get_stripe_products()
            
            if not products_data or not products_data.get('products'):
                await query.edit_message_text(
                    text="❌ **Produits Stripe non disponibles**\n\nVeuillez synchroniser les produits Stripe d'abord",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Synchroniser", callback_data="billing_sync_stripe")],
                        [InlineKeyboardButton("↩️ Retour", callback_data=f"billing_client_{client_id}")]
                    ])
                )
                return
            
            products = products_data.get('products', [])
            
            # Récupérer les infos du client
            client = self.api_client.get_lead_details(int(client_id))
            name = f"{client.get('first_name', '')} {client.get('last_name', '')}".strip()
            if not name:
                name = client.get('email', f"Client {client_id}")
            
            # Récupérer les sélections en cours
            session_key = f"stripe_products_{client_id}"
            selected_products = self.temp_data.get(session_key, [])
            
            text = f"🛍️ **Sélection produits Stripe - {name}**\n\n"
            
            if selected_products:
                text += f"✅ **{len(selected_products)} produits sélectionnés**\n\n"
            
            text += "📦 **Catalogue des produits :**\n\n"
            
            # Afficher les produits principaux (non-abonnements)
            main_products = []
            for product in products:
                if not self._is_subscription_product(product.get('name', '')):
                    main_products.append(product)
            
            for i, product in enumerate(main_products[:6], 1):  # Limiter à 6 produits
                name_prod = product.get('name', 'Produit')
                prices = product.get('prices', [])
                
                # Trouver le prix principal (one_time si disponible)
                main_price = None
                for price in prices:
                    if price.get('type') == 'one_time':
                        main_price = price
                        break
                
                if not main_price and prices:
                    main_price = prices[0]
                
                if main_price:
                    amount = main_price.get('unit_amount', 0) / 100
                    currency = main_price.get('currency', 'eur').upper()
                    
                    is_selected = any(p['product_id'] == product.get('id') for p in selected_products)
                    status_emoji = "✅" if is_selected else "⚪"
                    
                    text += f"{status_emoji} **{i}. {name_prod}**\n"
                    text += f"   💰 {amount:.0f} {currency}\n"
                    
                    # Indiquer s'il y a un abonnement associé
                    if self._has_required_subscription(product.get('id')):
                        text += f"   🔄 *Abonnement inclus automatiquement*\n"
                    
                    text += "\n"
            
            # Créer les boutons de sélection
            keyboard_buttons = []
            for i, product in enumerate(main_products[:6], 1):
                is_selected = any(p['product_id'] == product.get('id') for p in selected_products)
                status = "✅" if is_selected else "⚪"
                
                callback_data = f"billing_toggle_stripe_{client_id}_{product.get('id')}"
                keyboard_buttons.append([
                    InlineKeyboardButton(f"{status} {i}. {product.get('name', 'Produit')[:25]}...", 
                                       callback_data=callback_data)
                ])
            
            # Boutons d'action
            action_buttons = []
            if selected_products:
                action_buttons.append(InlineKeyboardButton("🧾 Créer la facture", 
                                                         callback_data=f"billing_create_stripe_invoice_{client_id}"))
                action_buttons.append(InlineKeyboardButton("🗑️ Vider sélection", 
                                                         callback_data=f"billing_clear_stripe_{client_id}"))
            
            if action_buttons:
                keyboard_buttons.append(action_buttons)
            
            keyboard_buttons.append([InlineKeyboardButton("↩️ Retour", callback_data=f"billing_client_{client_id}")])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erreur sélection produits Stripe: {e}")
            await query.edit_message_text(
                text="❌ **Erreur**\n\nImpossible de charger les produits Stripe",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Retour", callback_data=f"billing_client_{client_id}")]
                ])
            )

    def _is_subscription_product(self, product_name: str) -> bool:
        """Vérifie si un produit est un abonnement"""
        subscription_keywords = ['abonnement', 'maintenance', 'hébergement']
        return any(keyword in product_name.lower() for keyword in subscription_keywords)

    def _has_required_subscription(self, product_id: str) -> bool:
        """Vérifie si un produit a un abonnement obligatoire associé"""
        # Mapping simplifié (doit correspondre à celui du backend)
        required_subscriptions = {
            "prod_Sc1yH37xXqZkQu": True,  # Bot IA
            "prod_Sc20qI5hNsXqdd": True,  # Téléphone IA
            "prod_Sc21TjcwoabG1w": True,  # Pack Combiné
            "prod_Sc1xkiIBLkWXZt": False, # Site internet (optionnel)
        }
        return required_subscriptions.get(product_id, False)

    async def _handle_stripe_product_toggle(self, query, callback_data: str):
        """Gère la sélection/désélection d'un produit Stripe"""
        try:
            # Format: billing_toggle_stripe_{client_id}_{product_id}
            # Le product_id peut contenir des underscores, donc on prend tout après le 3ème underscore
            parts = callback_data.split("_", 4)  # Limiter à 5 parties max
            client_id = parts[3]
            product_id = parts[4] if len(parts) > 4 else ""
            
            session_key = f"stripe_products_{client_id}"
            selected_products = self.temp_data.get(session_key, [])
            
            # Récupérer les infos du produit depuis l'API
            products_data = self.api_client.get_stripe_products()
            products = products_data.get('products', []) if products_data else []
            
            product_info = None
            for product in products:
                if product.get('id') == product_id:
                    product_info = product
                    break
            
            if not product_info:
                await query.answer("❌ Produit introuvable")
                return
            
            # Trouver le prix principal
            prices = product_info.get('prices', [])
            main_price = None
            for price in prices:
                if price.get('type') == 'one_time':
                    main_price = price
                    break
            
            if not main_price and prices:
                main_price = prices[0]
            
            if not main_price:
                await query.answer("❌ Aucun prix trouvé pour ce produit")
                return
            
            # Vérifier si déjà sélectionné
            existing_index = -1
            for i, selected in enumerate(selected_products):
                if selected['product_id'] == product_id:
                    existing_index = i
                    break
            
            if existing_index >= 0:
                # Désélectionner
                selected_products.pop(existing_index)
                logger.info(f"DEBUG: Produit {product_id} désélectionné")
            else:
                # Sélectionner
                new_product = {
                    'product_id': product_id,
                    'price_id': main_price.get('id'),
                    'name': product_info.get('name'),
                    'unit_amount': main_price.get('unit_amount', 0),
                    'currency': main_price.get('currency', 'eur')
                }
                selected_products.append(new_product)
                logger.info(f"DEBUG: Produit {product_id} sélectionné: {new_product}")
            
            self.temp_data[session_key] = selected_products
            logger.info(f"DEBUG: temp_data mis à jour - session_key={session_key}, products={len(selected_products)}")
            
            # Rafraîchir l'affichage
            await self._show_stripe_product_selection(query, client_id)
            
        except Exception as e:
            logger.error(f"Erreur toggle produit Stripe: {e}")
            await query.answer("❌ Erreur lors de la sélection")

    async def _clear_stripe_selection(self, query, client_id: str):
        """Vide la sélection de produits Stripe"""
        session_key = f"stripe_products_{client_id}"
        self.temp_data[session_key] = []
        await self._show_stripe_product_selection(query, client_id)

    async def _create_stripe_invoice(self, query, client_id: str):
        """Crée une facture avec les produits Stripe sélectionnés"""
        try:
            logger.info(f"DEBUG: _create_stripe_invoice appelée avec client_id={client_id}")
            session_key = f"stripe_products_{client_id}"
            selected_products = self.temp_data.get(session_key, [])
            logger.info(f"DEBUG: session_key={session_key}, selected_products={selected_products}")
            logger.info(f"DEBUG: temp_data keys={list(self.temp_data.keys())}")
            
            if not selected_products:
                logger.warning(f"DEBUG: Aucun produit sélectionné pour client_id={client_id}")
                await query.answer("❌ Aucun produit sélectionné")
                return
            
            await query.edit_message_text(
                text="⏳ **Création de la facture...**\n\nValidation des abonnements et création en cours...",
                parse_mode='Markdown'
            )
            
            # Préparer les items pour validation
            invoice_items = []
            for product in selected_products:
                invoice_items.append({
                    'product_id': product['product_id'],
                    'price_id': product['price_id'],
                    'quantity': 1
                })
            
            # Créer la facture avec validation automatique
            result = self.api_client.create_invoice_with_validation(
                lead_id=int(client_id),
                selected_items=invoice_items,
                send_email=False  # Brouillon par défaut
            )
            
            if result:
                # Nettoyer les données temporaires
                if session_key in self.temp_data:
                    del self.temp_data[session_key]
                
                invoice = result.get('invoice', {})
                warnings = result.get('validation_warnings', [])
                
                text = "✅ **Facture créée avec succès !**\n\n"
                text += f"📄 **Numéro :** {invoice.get('invoice_number', 'N/A')}\n"
                text += f"💰 **Montant :** {invoice.get('total_amount', 0):.2f}€\n"
                text += f"📅 **Date :** {invoice.get('invoice_date', '').split('T')[0] if invoice.get('invoice_date') else 'N/A'}\n"
                text += f"📝 **Statut :** Brouillon\n"
                
                if warnings:
                    text += f"\n⚠️ **Abonnements ajoutés automatiquement :**\n"
                    for warning in warnings:
                        text += f"• {warning}\n"
                
                if result.get('stripe_invoice_url'):
                    text += f"\n🔗 [Voir la facture Stripe]({result['stripe_invoice_url']})\n"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Envoyer par email", callback_data=f"send_invoice_{invoice.get('id')}")],
                    [InlineKeyboardButton("📄 Détails facture", callback_data=f"billing_invoice_details_{invoice.get('id')}")],
                    [InlineKeyboardButton("↩️ Retour client", callback_data=f"billing_client_{client_id}")]
                ])
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    text="❌ **Erreur**\n\nImpossible de créer la facture",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("↩️ Retour", callback_data=f"billing_client_{client_id}")]
                    ])
                )
                
        except Exception as e:
            logger.error(f"Erreur création facture Stripe: {e}")
            await query.edit_message_text(
                text="❌ **Erreur**\n\nErreur lors de la création de la facture",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Retour", callback_data=f"billing_client_{client_id}")]
                ])
            )
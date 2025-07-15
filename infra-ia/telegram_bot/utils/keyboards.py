"""Claviers interactifs pour le bot Telegram"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.settings import EMOJIS

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Clavier du menu principal"""
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['stats']} Statistiques générales", callback_data="stats_main")],
        [InlineKeyboardButton(f"{EMOJIS['campaigns']} Campagnes", callback_data="campaigns_main")],
        [InlineKeyboardButton(f"{EMOJIS['leads']} Leads", callback_data="leads_main")],
        [InlineKeyboardButton(f"{EMOJIS['niches']} Niches", callback_data="niches_main")],
        [InlineKeyboardButton("📆 Tâches", callback_data="tasks_main")],
        [InlineKeyboardButton("💳 Facturer les clients", callback_data="billing_main")],
        [InlineKeyboardButton(f"{EMOJIS['system']} Système", callback_data="system_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# === CLAVIERS POUR FACTURATION ===

def get_billing_menu_keyboard() -> InlineKeyboardMarkup:
    """Clavier du menu facturation"""
    keyboard = [
        [InlineKeyboardButton("👥 Sélectionner un client", callback_data="billing_clients")],
        [InlineKeyboardButton("📅 Rendez-vous du jour", callback_data="billing_today_meetings")],
        [InlineKeyboardButton("📋 Voir toutes les factures", callback_data="billing_invoices")],
        [InlineKeyboardButton("📊 Statistiques facturation", callback_data="billing_stats")],
        [InlineKeyboardButton("🛍️ Produits Stripe", callback_data="billing_stripe_products")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_clients_selection_keyboard(page_clients: list, page: int = 0, total_clients: int = 0, clients_per_page: int = 6) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner un client à facturer"""
    keyboard = []
    
    # Boutons pour chaque client de la page
    for i, client in enumerate(page_clients, 1):
        # Construire le nom d'affichage
        first_name = client.get('first_name', '').strip()
        last_name = client.get('last_name', '').strip()
        
        if first_name and last_name:
            name = f"{first_name} {last_name}"
        elif first_name:
            name = first_name
        elif last_name:
            name = last_name
        else:
            name = client.get('email', 'Client')[:20]
        
        # Priorité: entreprise > company
        company = client.get('entreprise', '').strip() or client.get('company', '').strip()
        if company:
            display_name = f"{name} - {company}"
        else:
            display_name = name
        
        # Truncate if too long
        if len(display_name) > 30:
            display_name = display_name[:27] + "..."
        
        callback_data = f"billing_client_{client.get('id')}"
        keyboard.append([InlineKeyboardButton(f"{page * clients_per_page + i}. {display_name}", callback_data=callback_data)])
    
    # Navigation
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Précédent", callback_data=f"billing_clients_page_{page-1}"))
    
    total_pages = (total_clients - 1) // clients_per_page + 1
    if page + 1 < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ Suivant", callback_data=f"billing_clients_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Bouton retour
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="billing_main")])
    return InlineKeyboardMarkup(keyboard)

def get_client_billing_options_keyboard(client_id: str) -> InlineKeyboardMarkup:
    """Clavier pour les options de facturation d'un client"""
    keyboard = [
        [InlineKeyboardButton("📝 Modifier infos facturation", callback_data=f"billing_edit_info_{client_id}")],
        [InlineKeyboardButton("🧾 Créer une facture", callback_data=f"billing_create_invoice_{client_id}")],
        [InlineKeyboardButton("📋 Voir ses factures", callback_data=f"billing_view_invoices_{client_id}")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="billing_select_client")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_billing_services_selection_keyboard(services: list, client_id: str, selected_services: list = None) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner les services à facturer"""
    if selected_services is None:
        selected_services = []
    
    keyboard = []
    
    for service in services[:10]:  # Limite à 10 services
        service_id = service.get('id')
        is_selected = service_id in selected_services
        
        # Emoji selon sélection
        status_emoji = "✅" if is_selected else "⚪"
        
        # Prix
        if service.get('setup_price') and service.get('monthly_price'):
            price_text = f"{service['setup_price']}€ + {service['monthly_price']}€/mois"
        else:
            price_text = f"{service.get('price', 0)}€"
        
        service_name = service.get('name', f'Service {service_id}')
        
        callback_data = f"billing_toggle_service_{client_id}_{service_id}"
        keyboard.append([InlineKeyboardButton(
            f"{status_emoji} {service_name} ({price_text})", 
            callback_data=callback_data
        )])
    
    # Actions de finalisation
    action_buttons = []
    if selected_services:
        action_buttons.append(InlineKeyboardButton("✅ Créer la facture", callback_data=f"billing_finalize_{client_id}"))
    
    action_buttons.append(InlineKeyboardButton("🔄 Tout désélectionner", callback_data=f"billing_clear_selection_{client_id}"))
    
    if action_buttons:
        keyboard.append(action_buttons)
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"billing_client_{client_id}")])
    
    return InlineKeyboardMarkup(keyboard)

def get_billing_info_edit_keyboard(client_id: str) -> InlineKeyboardMarkup:
    """Clavier pour éditer les informations de facturation"""
    keyboard = [
        [InlineKeyboardButton("📍 Adresse", callback_data=f"billing_edit_address_{client_id}")],
        [InlineKeyboardButton("🏙️ Ville", callback_data=f"billing_edit_city_{client_id}")],
        [InlineKeyboardButton("📮 Code postal", callback_data=f"billing_edit_postal_{client_id}")],
        [InlineKeyboardButton("🌍 Pays", callback_data=f"billing_edit_country_{client_id}")],
        [InlineKeyboardButton("🏢 Numéro TVA", callback_data=f"billing_edit_vat_{client_id}")],
        [InlineKeyboardButton("📧 Email facturation", callback_data=f"billing_edit_email_{client_id}")],
        [InlineKeyboardButton("👤 Contact facturation", callback_data=f"billing_edit_contact_{client_id}")],
        [InlineKeyboardButton("✅ Valider les infos", callback_data=f"billing_validate_info_{client_id}")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"billing_client_{client_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_invoice_confirmation_keyboard(client_id: str) -> InlineKeyboardMarkup:
    """Clavier de confirmation pour créer une facture"""
    keyboard = [
        [InlineKeyboardButton("✅ Créer et envoyer", callback_data=f"billing_send_invoice_{client_id}")],
        [InlineKeyboardButton("📝 Créer sans envoyer", callback_data=f"billing_draft_invoice_{client_id}")],
        [InlineKeyboardButton("❌ Annuler", callback_data=f"billing_create_invoice_{client_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_invoices_list_keyboard(invoices: list, client_id: str = None) -> InlineKeyboardMarkup:
    """Clavier pour lister les factures"""
    keyboard = []
    
    for invoice in invoices[:8]:  # Limite à 8 factures
        invoice_number = invoice.get('invoice_number', f"Facture {invoice.get('id')}")
        status = invoice.get('status', 'unknown')
        amount = invoice.get('total_amount', 0)
        
        # Emoji selon le statut
        status_emojis = {
            'draft': '📝',
            'sent': '📤',
            'paid': '✅',
            'cancelled': '❌',
            'overdue': '⚠️'
        }
        status_emoji = status_emojis.get(status, '❓')
        
        callback_data = f"billing_invoice_details_{invoice.get('id')}"
        keyboard.append([InlineKeyboardButton(
            f"{status_emoji} {invoice_number} ({amount}€)", 
            callback_data=callback_data
        )])
    
    # Retour
    if client_id:
        keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"billing_client_{client_id}")])
    else:
        keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="billing_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_invoice_details_keyboard(invoice_id: str, client_id: str = None) -> InlineKeyboardMarkup:
    """Clavier pour les détails d'une facture"""
    keyboard = [
        [InlineKeyboardButton("📤 Envoyer par email", callback_data=f"billing_send_invoice_email_{invoice_id}")],
        [InlineKeyboardButton("📄 Voir PDF", callback_data=f"billing_view_pdf_{invoice_id}")],
        [InlineKeyboardButton("❌ Annuler facture", callback_data=f"billing_cancel_invoice_{invoice_id}")],
    ]
    
    if client_id:
        keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"billing_view_invoices_{client_id}")])
    else:
        keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="billing_view_all_invoices")])
    
    return InlineKeyboardMarkup(keyboard)

# === NOUVEAUX CLAVIERS POUR CRÉATION CAMPAGNES ===

def get_create_campaign_keyboard() -> InlineKeyboardMarkup:
    """Clavier pour créer une nouvelle campagne"""
    keyboard = [
        [InlineKeyboardButton("📂 Sélectionner une niche", callback_data="create_campaign_select_niche")],
        [InlineKeyboardButton("🆕 Créer nouvelle niche", callback_data="create_campaign_new_niche")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="campaigns_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_niches_selection_keyboard(niches: list) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner une niche"""
    keyboard = []
    
    for niche in niches[:10]:  # Limite à 10 niches
        name = niche.get('name', f'Niche {niche.get("id", "?")}')
        callback_data = f"select_niche_{niche.get('id')}"
        keyboard.append([InlineKeyboardButton(f"📂 {name}", callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="campaigns_start")])
    return InlineKeyboardMarkup(keyboard)

def get_cities_selection_keyboard(cities: list, niche_id: str) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner une ville"""
    keyboard = []
    
    for city in cities[:10]:  # Limite à 10 villes
        callback_data = f"select_city_{niche_id}_{city.replace(' ', '_')}"
        keyboard.append([InlineKeyboardButton(f"🏙️ {city}", callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="create_campaign_select_niche")])
    return InlineKeyboardMarkup(keyboard)

def get_confirm_creation_keyboard(niche_id: str, city: str) -> InlineKeyboardMarkup:
    """Clavier de confirmation pour création campagne"""
    city_clean = city.replace(' ', '_')
    keyboard = [
        [InlineKeyboardButton("✅ Confirmer création", callback_data=f"confirm_create_{niche_id}_{city_clean}")],
        [InlineKeyboardButton("❌ Annuler", callback_data="campaigns_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_stats_menu_keyboard() -> InlineKeyboardMarkup:
    """Clavier du menu statistiques"""
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['view']} Volume total de leads", callback_data="stats_leads_volume")],
        [InlineKeyboardButton(f"{EMOJIS['view']} Taux global de conversion", callback_data="stats_conversion")],
        [InlineKeyboardButton(f"{EMOJIS['view']} Répartition des réponses", callback_data="stats_responses")],
        [InlineKeyboardButton(f"{EMOJIS['view']} Historique performances", callback_data="stats_history")],
        [InlineKeyboardButton(f"{EMOJIS['view']} Compensation totale", callback_data="stats_compensation")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_campaigns_menu_keyboard() -> InlineKeyboardMarkup:
    """Clavier du menu campagnes"""
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['view']} Voir campagnes actives", callback_data="campaigns_active")],
        [InlineKeyboardButton(f"📈 Statistiques campagne", callback_data="campaigns_stats")],
        [InlineKeyboardButton(f"{EMOJIS['start']} Lancer une campagne", callback_data="campaigns_start")],
        [InlineKeyboardButton("🔄 Relancer une campagne", callback_data="campaigns_restart")],
        [InlineKeyboardButton(f"{EMOJIS['stop']} Stopper une campagne", callback_data="campaigns_stop")],
        [InlineKeyboardButton(f"{EMOJIS['export']} Exporter les données", callback_data="campaigns_export")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_leads_menu_keyboard() -> InlineKeyboardMarkup:
    """Clavier du menu leads"""
    keyboard = [
        [InlineKeyboardButton(f"🔢 Voir le nombre total", callback_data="leads_count")],
        [InlineKeyboardButton(f"✅ Voir le taux de qualification", callback_data="leads_qualification")],
        [InlineKeyboardButton(f"📄 Lister les leads", callback_data="leads_list")],
        [InlineKeyboardButton(f"📅 Rendez-vous", callback_data="leads_meetings")],
        [InlineKeyboardButton(f"{EMOJIS['view']} Rechercher un lead", callback_data="leads_search")],
        [InlineKeyboardButton(f"📊 Répartition par statut", callback_data="leads_status")],
        [InlineKeyboardButton(f"🧮 Compensation d'un lead", callback_data="leads_compensation")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_niches_menu_keyboard() -> InlineKeyboardMarkup:
    """Clavier du menu niches"""
    keyboard = [
        [InlineKeyboardButton(f"📄 Lister toutes les niches", callback_data="niches_list")],
        [InlineKeyboardButton(f"📊 Performances d'une niche", callback_data="niches_performance")],
        [InlineKeyboardButton(f"{EMOJIS['stop']} Stopper une niche", callback_data="niches_stop")],
        [InlineKeyboardButton(f"🆕 Proposer nouvelle niche", callback_data="niches_new")],
        [InlineKeyboardButton(f"🧠 Analyser viabilité", callback_data="niches_analyze")],
        [InlineKeyboardButton(f"📈 Voir campagnes associées", callback_data="niches_campaigns")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_system_menu_keyboard() -> InlineKeyboardMarkup:
    """Clavier du menu système"""
    keyboard = [
        [InlineKeyboardButton(f"🔁 État des agents", callback_data="system_agents")],
        [InlineKeyboardButton(f"📆 Tâches planifiées", callback_data="system_tasks")],
        [InlineKeyboardButton(f"🔒 Logs de sécurité", callback_data="system_security")],
        [InlineKeyboardButton(f"🧠 Logs de décisions", callback_data="system_logs")],
        [InlineKeyboardButton(f"{EMOJIS['restart']} Redémarrer système", callback_data="system_restart")],
        [InlineKeyboardButton(f"🔧 État des services", callback_data="system_services")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Clavier simple avec bouton retour"""
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=callback_data)]
    ]
    return InlineKeyboardMarkup(keyboard)

# === CLAVIERS POUR CONVERSION DES RENDEZ-VOUS ===

def get_meeting_conversion_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Clavier pour la conversion d'un rendez-vous"""
    keyboard = [
        [InlineKeyboardButton("✅ Oui, client accepté", callback_data=f"convert_{meeting_id}_accepted")],
        [InlineKeyboardButton("❌ Non, refusé", callback_data=f"convert_{meeting_id}_refused")],
        [InlineKeyboardButton("🤔 À réfléchir", callback_data=f"convert_{meeting_id}_thinking")],
        [InlineKeyboardButton("👻 Client absent", callback_data=f"convert_{meeting_id}_no_show")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"meeting_details_{meeting_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_services_selection_keyboard(meeting_id: int, services: list) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner les services achetés"""
    keyboard = []
    
    # Services individuels
    for service in services:
        if not service.get('is_bundle', False):
            callback_data = f"select_service_{meeting_id}_{service['id']}"
            setup = service['setup_price']
            monthly = service['monthly_price']
            text = f"{service['name']} ({setup}€ + {monthly}€/mois)"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # Forfaits
    keyboard.append([InlineKeyboardButton("📦 Forfaits", callback_data=f"show_bundles_{meeting_id}")])
    
    # Options de finalisation
    keyboard.extend([
        [InlineKeyboardButton("✅ Valider la sélection", callback_data=f"finalize_services_{meeting_id}")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"convert_{meeting_id}_accepted")]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_refusal_reasons_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Clavier pour les raisons de refus"""
    reasons = [
        ("price_too_high", "💰 Prix trop élevé"),
        ("no_budget", "💸 Pas de budget"),
        ("internal_solution", "🏠 Solution interne"),
        ("bad_timing", "⏰ Mauvais timing"),
        ("not_convinced", "🤷 Pas convaincu"),
        ("competitor", "🏆 Concurrent choisi"),
        ("other", "📝 Autre raison")
    ]
    
    keyboard = []
    for reason_code, reason_text in reasons:
        callback_data = f"refuse_{meeting_id}_{reason_code}"
        keyboard.append([InlineKeyboardButton(reason_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"convert_{meeting_id}_refused")])
    
    return InlineKeyboardMarkup(keyboard)

def get_thinking_options_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Clavier pour les options de suivi 'en réflexion'"""
    keyboard = [
        [InlineKeyboardButton("📅 Rappel dans 1 semaine", callback_data=f"thinking_{meeting_id}_7")],
        [InlineKeyboardButton("📅 Rappel dans 2 semaines", callback_data=f"thinking_{meeting_id}_14")],
        [InlineKeyboardButton("📅 Rappel dans 1 mois", callback_data=f"thinking_{meeting_id}_30")],
        [InlineKeyboardButton("📅 Rappel dans 3 mois", callback_data=f"thinking_{meeting_id}_90")],
        [InlineKeyboardButton("📝 Date personnalisée", callback_data=f"thinking_{meeting_id}_custom")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"convert_{meeting_id}_thinking")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_bundles_keyboard(meeting_id: int, services: list) -> InlineKeyboardMarkup:
    """Clavier pour les forfaits combinés"""
    keyboard = []
    
    # Forfaits
    for service in services:
        if service.get('is_bundle', False):
            callback_data = f"select_bundle_{meeting_id}_{service['id']}"
            setup = service['setup_price']
            monthly = service['monthly_price']
            text = f"{service['name']} ({setup}€ + {monthly}€/mois)"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.extend([
        [InlineKeyboardButton("🔙 Services individuels", callback_data=f"show_services_{meeting_id}")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"convert_{meeting_id}_accepted")]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_conversion_stats_keyboard() -> InlineKeyboardMarkup:
    """Clavier pour les statistiques de conversion"""
    keyboard = [
        [InlineKeyboardButton("📊 Taux de conversion", callback_data="conversion_stats_rates")],
        [InlineKeyboardButton("❌ Raisons de refus", callback_data="conversion_stats_refusals")],
        [InlineKeyboardButton("💰 Revenus générés", callback_data="conversion_stats_revenue")],
        [InlineKeyboardButton("🔄 Prospects à relancer", callback_data="conversion_follow_ups")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="stats_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action: str, item_id: str = "") -> InlineKeyboardMarkup:
    """Clavier de confirmation pour actions critiques"""
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJIS['success']} Confirmer", callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton(f"{EMOJIS['error']} Annuler", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_campaigns_list_keyboard(campaigns: list) -> InlineKeyboardMarkup:
    """Clavier pour lister les campagnes"""
    keyboard = []
    
    for i, campaign in enumerate(campaigns[:10]):  # Limite à 10 pour éviter les messages trop longs
        status_emoji = EMOJIS['active'] if campaign.get('status') == 'active' else EMOJIS['inactive']
        text = f"{status_emoji} {campaign.get('name', f'Campagne {i+1}')}"
        callback_data = f"campaign_details_{campaign.get('id', i)}"
        keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # Bouton retour
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour menu campagnes", callback_data="campaigns_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_leads_list_keyboard(leads: list, offset: int = 0) -> InlineKeyboardMarkup:
    """Clavier pour lister les leads avec pagination"""
    keyboard = []
    
    for i, lead in enumerate(leads[:5]):  # 5 par page
        name = lead.get('name', lead.get('email', f'Lead {offset + i + 1}'))
        callback_data = f"lead_details_{lead.get('id', offset + i)}"
        keyboard.append([InlineKeyboardButton(f"👤 {name}", callback_data=callback_data)])
    
    # Navigation
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Précédent", callback_data=f"leads_list_{offset-5}"))
    if len(leads) == 5:  # S'il y a potentiellement plus de leads
        nav_buttons.append(InlineKeyboardButton("➡️ Suivant", callback_data=f"leads_list_{offset+5}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Bouton retour
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour menu leads", callback_data="leads_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_niches_list_keyboard(niches: list) -> InlineKeyboardMarkup:
    """Clavier pour lister les niches"""
    keyboard = []
    
    for i, niche in enumerate(niches[:10]):
        name = niche.get('name', f'Niche {i+1}')
        callback_data = f"niche_details_{niche.get('id', i)}"
        keyboard.append([InlineKeyboardButton(f"📂 {name}", callback_data=callback_data)])
    
    # Bouton retour
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour menu niches", callback_data="niches_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_agents_list_keyboard(agents: list) -> InlineKeyboardMarkup:
    """Clavier pour lister les agents"""
    keyboard = []
    
    for agent in agents[:10]:
        status_emoji = EMOJIS['active'] if agent.get('status') == 'active' else EMOJIS['inactive']
        name = agent.get('name', 'Agent inconnu')
        callback_data = f"agent_details_{agent.get('name', 'unknown')}"
        keyboard.append([InlineKeyboardButton(f"{status_emoji} {name}", callback_data=callback_data)])
    
    # Bouton retour
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour menu système", callback_data="system_main")])
    
    return InlineKeyboardMarkup(keyboard)

# === CLAVIERS POUR GESTION DES TÂCHES ===

def get_tasks_menu_keyboard() -> InlineKeyboardMarkup:
    """Clavier du menu tâches planifiées"""
    keyboard = [
        [InlineKeyboardButton("📋 Voir toutes les tâches", callback_data="tasks_list")],
        [InlineKeyboardButton("➕ Créer une tâche", callback_data="tasks_create")],
        [InlineKeyboardButton("🗑️ Supprimer une tâche", callback_data="tasks_delete")],
        [InlineKeyboardButton("▶️ Exécuter une tâche", callback_data="tasks_execute")],
        [InlineKeyboardButton("🤖 Voir capacités agents", callback_data="tasks_capabilities")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour menu système", callback_data="system_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_tasks_list_keyboard(tasks: list) -> InlineKeyboardMarkup:
    """Clavier pour lister les tâches avec actions"""
    keyboard = []
    
    for task in tasks[:8]:  # Limite à 8 pour laisser place aux boutons d'action
        task_id = task.get('task_id', 'unknown')
        name = task.get('name', 'Tâche inconnue')
        status = task.get('status', 'unknown')
        
        # Emoji selon le statut
        if status == 'pending':
            status_emoji = '⏳'
        elif status == 'running':
            status_emoji = '🟡'
        elif status == 'completed':
            status_emoji = '✅'
        elif status == 'failed':
            status_emoji = '❌'
        else:
            status_emoji = '❓'
        
        callback_data = f"task_details_{task_id}"
        keyboard.append([InlineKeyboardButton(f"{status_emoji} {name}", callback_data=callback_data)])
    
    # Boutons d'action
    action_buttons = [
        [InlineKeyboardButton("➕ Nouvelle tâche", callback_data="tasks_create")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="system_tasks")]
    ]
    keyboard.extend(action_buttons)
    
    return InlineKeyboardMarkup(keyboard)

def get_task_details_keyboard(task_id: str) -> InlineKeyboardMarkup:
    """Clavier pour les détails d'une tâche avec actions"""
    keyboard = [
        [
            InlineKeyboardButton("▶️ Exécuter", callback_data=f"task_execute_{task_id}"),
            InlineKeyboardButton("🗑️ Supprimer", callback_data=f"task_delete_{task_id}")
        ],
        [
            InlineKeyboardButton("⏸️ Suspendre", callback_data=f"task_pause_{task_id}"),
            InlineKeyboardButton("✏️ Modifier", callback_data=f"task_edit_{task_id}")
        ],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour aux tâches", callback_data="tasks_list")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_task_confirmation_keyboard(action: str, task_id: str) -> InlineKeyboardMarkup:
    """Clavier de confirmation pour actions sur tâches"""
    action_text = {
        'delete': 'Supprimer',
        'execute': 'Exécuter', 
        'pause': 'Suspendre'
    }.get(action, 'Confirmer')
    
    keyboard = [
        [
            InlineKeyboardButton(f"✅ Confirmer {action_text.lower()}", callback_data=f"confirm_task_{action}_{task_id}"),
            InlineKeyboardButton("❌ Annuler", callback_data=f"task_details_{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_agents_selection_keyboard(agents: list) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner un agent lors de la création de tâche"""
    keyboard = []
    
    # Agents principaux pour les tâches
    main_agents = [
        ("MessagingAgent", "📧"),
        ("ProspectionSupervisor", "🎯"), 
        ("PivotStrategyAgent", "📊"),
        ("TaskWatchdogAgent", "🛡️"),
        ("ScrapingSupervisorAgent", "🔍"),
        ("ResponseInterpreterAgent", "💬")
    ]
    
    for agent_name, emoji in main_agents:
        # Vérifier si l'agent existe dans la liste
        agent_exists = any(agent.get('name') == agent_name for agent in agents)
        if agent_exists:
            callback_data = f"select_agent_{agent_name}"
            keyboard.append([InlineKeyboardButton(f"{emoji} {agent_name}", callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="tasks_create")])
    return InlineKeyboardMarkup(keyboard)

def get_agent_actions_keyboard(agent_name: str) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner l'action selon l'agent"""
    actions_map = {
        "MessagingAgent": [
            ("📨 Envoyer message", "send_message"),
            ("📬 Messages groupés", "send_bulk_messages"),
            ("📋 Créer template", "create_message_template"),
            ("📅 Planifier relance", "schedule_follow_up"),
            ("🔄 Contact automatique", "auto_contact")
        ],
        "ProspectionSupervisor": [
            ("🎯 Démarrer prospection", "start_prospection"),
            ("📊 Surveiller campagnes", "monitor_campaigns"),
            ("📈 Rapport quotidien", "daily_report"),
            ("🔍 Analyse performance", "performance_analysis"),
            ("✅ Qualification leads", "lead_qualification")
        ],
        "PivotStrategyAgent": [
            ("📊 Analyser stratégie", "analyze_strategy"),
            ("🔄 Suggérer pivot", "suggest_pivot"),
            ("📈 Analyse marché", "market_analysis"),
            ("⚡ Optimiser stratégie", "strategy_optimization"),
            ("👥 Analyse concurrence", "competitor_analysis")
        ],
        "TaskWatchdogAgent": [
            ("👀 Surveiller tâches", "monitor_tasks"),
            ("🛡️ Vérification sécurité", "security_check"),
            ("💚 Santé système", "system_health"),
            ("🚨 Gestion alertes", "alert_management"),
            ("📋 Analyse logs", "log_analysis")
        ],
        "ScrapingSupervisorAgent": [
            ("🔍 Démarrer scraping", "start_scraping"),
            ("👀 Surveiller scraping", "monitor_scraping"),
            ("✅ Contrôle qualité", "quality_check"),
            ("🔍 Validation données", "data_validation"),
            ("📚 Gestion sources", "source_management")
        ],
        "ResponseInterpreterAgent": [
            ("💬 Interpréter réponse", "interpret_response"),
            ("😊 Analyse sentiment", "sentiment_analysis"),
            ("📅 Décision relance", "follow_up_decision"),
            ("⭐ Noter lead", "lead_scoring"),
            ("📂 Catégoriser réponse", "response_categorization")
        ]
    }
    
    keyboard = []
    actions = actions_map.get(agent_name, [])
    
    for action_text, action_code in actions:
        callback_data = f"select_action_{agent_name}_{action_code}"
        keyboard.append([InlineKeyboardButton(action_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour agents", callback_data="tasks_select_agent")])
    return InlineKeyboardMarkup(keyboard)

def get_task_priority_keyboard(agent_name: str, action: str) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner la priorité de la tâche"""
    keyboard = [
        [InlineKeyboardButton("🔴 Haute priorité (1)", callback_data=f"set_priority_{agent_name}_{action}_1")],
        [InlineKeyboardButton("🟡 Priorité moyenne (2)", callback_data=f"set_priority_{agent_name}_{action}_2")],
        [InlineKeyboardButton("🟢 Priorité basse (3)", callback_data=f"set_priority_{agent_name}_{action}_3")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"select_agent_{agent_name}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_task_schedule_keyboard(agent_name: str, action: str, priority: int) -> InlineKeyboardMarkup:
    """Clavier pour planifier la tâche"""
    keyboard = [
        [InlineKeyboardButton("⚡ Exécuter maintenant", callback_data=f"schedule_now_{agent_name}_{action}_{priority}")],
        [InlineKeyboardButton("⏰ Dans 1 heure", callback_data=f"schedule_1h_{agent_name}_{action}_{priority}")],
        [InlineKeyboardButton("📅 Dans 24h", callback_data=f"schedule_24h_{agent_name}_{action}_{priority}")],
        [InlineKeyboardButton("🔄 Répétitive (1h)", callback_data=f"schedule_recurring_1h_{agent_name}_{action}_{priority}")],
        [InlineKeyboardButton("🔄 Répétitive (24h)", callback_data=f"schedule_recurring_24h_{agent_name}_{action}_{priority}")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"select_action_{agent_name}_{action}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_task_final_confirmation_keyboard(agent_name: str, action: str, priority: int, schedule_type: str) -> InlineKeyboardMarkup:
    """Clavier de confirmation finale pour créer la tâche"""
    keyboard = [
        [InlineKeyboardButton("✅ Créer la tâche", callback_data=f"create_task_{agent_name}_{action}_{priority}_{schedule_type}")],
        [InlineKeyboardButton("❌ Annuler", callback_data="tasks_create")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_tasks_to_delete_keyboard(tasks: list) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner une tâche à supprimer"""
    keyboard = []
    
    for task in tasks[:10]:
        task_id = task.get('task_id', 'unknown')
        name = task.get('name', 'Tâche inconnue')
        status = task.get('status', 'unknown')
        
        if status == 'pending':
            status_emoji = '⏳'
        elif status == 'running':
            status_emoji = '🟡'
        else:
            status_emoji = '❓'
        
        callback_data = f"confirm_delete_task_{task_id}"
        keyboard.append([InlineKeyboardButton(f"{status_emoji} {name}", callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="system_tasks")])
    return InlineKeyboardMarkup(keyboard)

def get_tasks_to_execute_keyboard(tasks: list) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner une tâche à exécuter"""
    keyboard = []
    
    for task in tasks[:10]:
        task_id = task.get('task_id', 'unknown')
        name = task.get('name', 'Tâche inconnue')
        status = task.get('status', 'unknown')
        
        # Seules les tâches en attente peuvent être exécutées
        if status == 'pending':
            callback_data = f"confirm_execute_task_{task_id}"
            keyboard.append([InlineKeyboardButton(f"⏳ {name}", callback_data=callback_data)])
    
    if not keyboard:
        keyboard.append([InlineKeyboardButton("ℹ️ Aucune tâche exécutable", callback_data="system_tasks")])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="system_tasks")])
    return InlineKeyboardMarkup(keyboard)

# === CLAVIERS POUR GESTION DES RENDEZ-VOUS ===

def get_meetings_menu_keyboard() -> InlineKeyboardMarkup:
    """Clavier du menu rendez-vous"""
    keyboard = [
        [InlineKeyboardButton("📊 Statistiques RDV", callback_data="meetings_stats")],
        [InlineKeyboardButton("📅 RDV à venir", callback_data="meetings_upcoming")],
        [InlineKeyboardButton("📋 Tous les RDV", callback_data="meetings_all")],
        [InlineKeyboardButton("🗓️ RDV aujourd'hui", callback_data="meetings_today")],
        [InlineKeyboardButton("📆 RDV cette semaine", callback_data="meetings_week")],
        [InlineKeyboardButton("📅 RDV ce mois", callback_data="meetings_month")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour aux leads", callback_data="leads_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meetings_filter_keyboard() -> InlineKeyboardMarkup:
    """Clavier pour filtrer les rendez-vous par statut"""
    keyboard = [
        [InlineKeyboardButton("📅 Programmés", callback_data="meetings_filter_scheduled")],
        [InlineKeyboardButton("✅ Terminés", callback_data="meetings_filter_completed")],
        [InlineKeyboardButton("❌ Annulés", callback_data="meetings_filter_cancelled")],
        [InlineKeyboardButton("👻 Absence", callback_data="meetings_filter_no_show")],
        [InlineKeyboardButton("🔄 Tous les statuts", callback_data="meetings_all")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="leads_meetings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meeting_details_keyboard(meeting_id: int, calendar_event_id: str = None) -> InlineKeyboardMarkup:
    """Clavier pour les détails d'un rendez-vous avec actions"""
    keyboard = []
    
    # Actions principales
    action_row = []
    if calendar_event_id:
        action_row.append(InlineKeyboardButton("📅 Voir calendrier", url=f"https://calendar.google.com/calendar/u/0/r/week"))
    action_row.append(InlineKeyboardButton("💬 Résumé échange", callback_data=f"meeting_conversation_{meeting_id}"))
    
    if action_row:
        keyboard.append(action_row)
    
    # Actions de gestion
    management_buttons = [
        [
            InlineKeyboardButton("🎯 Conversion client", callback_data=f"meeting_convert_{meeting_id}"),
            InlineKeyboardButton("⏰ Reporter", callback_data=f"meeting_reschedule_{meeting_id}")
        ],
        [
            InlineKeyboardButton("❌ Annuler RDV", callback_data=f"meeting_cancel_{meeting_id}"),
            InlineKeyboardButton("📊 Voir statistiques", callback_data="conversion_stats_main")
        ]
    ]
    keyboard.extend(management_buttons)
    
    # Navigation
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour aux RDV", callback_data="leads_meetings")])
    
    return InlineKeyboardMarkup(keyboard)

def get_meeting_action_confirmation_keyboard(action: str, meeting_id: int) -> InlineKeyboardMarkup:
    """Clavier de confirmation pour actions sur rendez-vous"""
    action_texts = {
        'cancel': 'Annuler le RDV',
        'complete': 'Marquer terminé',
        'no_show': 'Marquer absence',
        'reschedule': 'Reporter le RDV'
    }
    
    action_text = action_texts.get(action, 'Confirmer')
    
    keyboard = [
        [
            InlineKeyboardButton(f"✅ Confirmer", callback_data=f"confirm_meeting_{action}_{meeting_id}"),
            InlineKeyboardButton("❌ Annuler", callback_data=f"meeting_details_{meeting_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meeting_reschedule_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Clavier pour reporter un rendez-vous"""
    keyboard = [
        [InlineKeyboardButton("🕐 Dans 1 heure", callback_data=f"reschedule_1h_{meeting_id}")],
        [InlineKeyboardButton("📅 Demain même heure", callback_data=f"reschedule_tomorrow_{meeting_id}")],
        [InlineKeyboardButton("📅 Lundi prochain", callback_data=f"reschedule_next_monday_{meeting_id}")],
        [InlineKeyboardButton("🗓️ Choisir date/heure", callback_data=f"reschedule_custom_{meeting_id}")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=f"meeting_details_{meeting_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meetings_pagination_keyboard(current_page: int, total_pages: int, filter_type: str = "all") -> InlineKeyboardMarkup:
    """Clavier de pagination pour les listes de rendez-vous"""
    keyboard = []
    
    # Boutons de pagination
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Précédent", callback_data=f"meetings_page_{filter_type}_{current_page-1}"))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ Suivant", callback_data=f"meetings_page_{filter_type}_{current_page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Filtres rapides
    keyboard.append([
        InlineKeyboardButton("🔍 Filtrer", callback_data="meetings_filter"),
        InlineKeyboardButton("📊 Statistiques", callback_data="meetings_stats")
    ])
    
    # Retour
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="leads_meetings")])
    
    return InlineKeyboardMarkup(keyboard)

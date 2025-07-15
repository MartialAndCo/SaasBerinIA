"""Keyboards communs réutilisables dans tout le bot"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional, Dict

def get_back_button(target: str, label: str = None) -> InlineKeyboardMarkup:
    """Bouton retour générique avec label personnalisable"""
    if label is None:
        labels = {
            "main_menu": "🏠 Menu principal",
            "meetings": "📅 Meetings", 
            "stats": "📊 Stats",
            "campaigns": "🎯 Campagnes",
            "leads": "👥 Leads",
            "tasks": "📆 Tâches",
            "system": "🧠 Système",
            "niches": "📂 Niches"
        }
        label = labels.get(target, f"⬅️ Retour {target}")
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=target)]
    ])

def get_back_and_home_buttons(back_target: str, back_label: str = None) -> InlineKeyboardMarkup:
    """Boutons retour + accueil"""
    back_text = back_label or f"⬅️ Retour"
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(back_text, callback_data=back_target),
            InlineKeyboardButton("🏠 Accueil", callback_data="main_menu")
        ]
    ])

def get_confirmation_buttons(confirm_action: str, cancel_action: str = None) -> InlineKeyboardMarkup:
    """Boutons de confirmation standard"""
    cancel_target = cancel_action or "main_menu"
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirmer", callback_data=confirm_action),
            InlineKeyboardButton("❌ Annuler", callback_data=cancel_target)
        ]
    ])

def get_yes_no_buttons(yes_action: str, no_action: str) -> InlineKeyboardMarkup:
    """Boutons Oui/Non simples"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Oui", callback_data=yes_action),
            InlineKeyboardButton("❌ Non", callback_data=no_action)
        ]
    ])

def get_refresh_button(refresh_action: str, back_action: str = None) -> InlineKeyboardMarkup:
    """Bouton rafraîchir + retour"""
    buttons = [InlineKeyboardButton("🔄 Rafraîchir", callback_data=refresh_action)]
    
    if back_action:
        buttons.append(InlineKeyboardButton("⬅️ Retour", callback_data=back_action))
    
    return InlineKeyboardMarkup([buttons])

def get_navigation_buttons(current_section: str) -> InlineKeyboardMarkup:
    """Navigation rapide entre sections principales"""
    sections = {
        "stats": ("📊", "stats_main"),
        "campaigns": ("🎯", "campaigns_main"), 
        "leads": ("👥", "leads_main"),
        "meetings": ("📅", "meetings_main"),
        "tasks": ("📆", "tasks_main"),
        "system": ("🧠", "system_main")
    }
    
    keyboard = []
    row = []
    
    for section, (emoji, callback) in sections.items():
        if section != current_section:  # Ne pas inclure la section actuelle
            row.append(InlineKeyboardButton(emoji, callback_data=callback))
            
            if len(row) == 3:  # 3 boutons par ligne
                keyboard.append(row)
                row = []
    
    if row:  # Ajouter la dernière ligne si pas complète
        keyboard.append(row)
    
    # Ligne de retour
    keyboard.append([InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def build_list_keyboard(items: List[Dict], 
                       item_format_func,
                       callback_prefix: str,
                       items_per_page: int = 5,
                       current_page: int = 0,
                       back_action: str = "main_menu") -> InlineKeyboardMarkup:
    """Construit un clavier de liste avec pagination"""
    
    keyboard = []
    start_idx = current_page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]
    
    # Ajouter les éléments de la page
    for item in page_items:
        button_text = item_format_func(item)
        callback_data = f"{callback_prefix}_{item.get('id', item.get('name', ''))}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Pagination
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    if total_pages > 1:
        pagination_row = []
        
        if current_page > 0:
            pagination_row.append(
                InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}_page_{current_page-1}")
            )
        
        pagination_row.append(
            InlineKeyboardButton(f"{current_page+1}/{total_pages}", callback_data="page_info")
        )
        
        if current_page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}_page_{current_page+1}")
            )
        
        keyboard.append(pagination_row)
    
    # Bouton retour
    keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data=back_action)])
    
    return InlineKeyboardMarkup(keyboard)

def get_status_filter_keyboard(callback_prefix: str, 
                              statuses: Dict[str, str],
                              back_action: str = "main_menu") -> InlineKeyboardMarkup:
    """Clavier de filtres par statut générique"""
    keyboard = []
    
    # Ajouter tous les statuts
    for status_key, status_label in statuses.items():
        keyboard.append([
            InlineKeyboardButton(status_label, callback_data=f"{callback_prefix}_{status_key}")
        ])
    
    # Option "Tous"
    keyboard.append([
        InlineKeyboardButton("📋 Tous", callback_data=f"{callback_prefix}_all")
    ])
    
    # Retour
    keyboard.append([
        InlineKeyboardButton("⬅️ Retour", callback_data=back_action)
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_action_buttons(actions: List[Dict[str, str]], 
                      columns: int = 2,
                      back_action: str = None) -> InlineKeyboardMarkup:
    """Génère un clavier d'actions avec colonnes configurables"""
    keyboard = []
    row = []
    
    for action in actions:
        button = InlineKeyboardButton(action['text'], callback_data=action['callback'])
        row.append(button)
        
        if len(row) == columns:
            keyboard.append(row)
            row = []
    
    # Ajouter la dernière ligne si pas complète
    if row:
        keyboard.append(row)
    
    # Bouton retour si spécifié
    if back_action:
        keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data=back_action)])
    
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu principal du bot"""
    keyboard = [
        # Ligne 1: Statistiques et données
        [
            InlineKeyboardButton("📊 Statistiques", callback_data="stats_main"),
            InlineKeyboardButton("📈 Rapport quotidien", callback_data="daily_report_main")
        ],
        # Ligne 2: Gestion commerciale
        [
            InlineKeyboardButton("🎯 Campagnes", callback_data="campaigns_main"),
            InlineKeyboardButton("👥 Leads", callback_data="leads_main")
        ],
        # Ligne 3: Meetings et tâches
        [
            InlineKeyboardButton("📅 Meetings", callback_data="meetings_main"),
            InlineKeyboardButton("📆 Tâches", callback_data="tasks_main")
        ],
        # Ligne 4: Configuration
        [
            InlineKeyboardButton("📂 Niches", callback_data="niches_main"),
            InlineKeyboardButton("🧠 Système", callback_data="system_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quick_actions_keyboard() -> InlineKeyboardMarkup:
    """Actions rapides pour utilisateurs expérimentés"""
    keyboard = [
        [
            InlineKeyboardButton("⚡ Meetings du jour", callback_data="meetings_today"),
            InlineKeyboardButton("📊 Stats rapides", callback_data="stats_quick")
        ],
        [
            InlineKeyboardButton("🎯 Nouvelle campagne", callback_data="campaigns_create"),
            InlineKeyboardButton("📆 Nouvelle tâche", callback_data="tasks_create")
        ],
        [
            InlineKeyboardButton("🔄 Restart services", callback_data="system_restart_all"),
            InlineKeyboardButton("📋 Logs système", callback_data="system_logs")
        ],
        [InlineKeyboardButton("🏠 Menu complet", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contextual_help_keyboard(section: str) -> InlineKeyboardMarkup:
    """Aide contextuelle selon la section"""
    help_actions = {
        "meetings": [
            {"text": "❓ Comment convertir", "callback": "help_meeting_conversion"},
            {"text": "📖 Guide meetings", "callback": "help_meetings_guide"}
        ],
        "campaigns": [
            {"text": "❓ Créer campagne", "callback": "help_campaign_creation"},
            {"text": "📖 Guide campagnes", "callback": "help_campaigns_guide"}
        ],
        "tasks": [
            {"text": "❓ Types de tâches", "callback": "help_task_types"},
            {"text": "📖 Guide tâches", "callback": "help_tasks_guide"}
        ]
    }
    
    actions = help_actions.get(section, [
        {"text": "📖 Aide générale", "callback": "help_general"}
    ])
    
    keyboard = []
    for action in actions:
        keyboard.append([InlineKeyboardButton(action['text'], callback_data=action['callback'])])
    
    keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data=f"{section}_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Clavier de paramètres utilisateur"""
    keyboard = [
        [InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications")],
        [InlineKeyboardButton("⏰ Fuseaux horaires", callback_data="settings_timezone")],
        [InlineKeyboardButton("🎨 Interface", callback_data="settings_ui")],
        [InlineKeyboardButton("📊 Préférences stats", callback_data="settings_stats")],
        [InlineKeyboardButton("⬅️ Menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Helpers pour construire des keyboards dynamiques

def build_grid_keyboard(items: List[str], 
                       callback_prefix: str,
                       columns: int = 2,
                       back_action: str = None) -> InlineKeyboardMarkup:
    """Construit un clavier en grille"""
    keyboard = []
    row = []
    
    for item in items:
        callback_data = f"{callback_prefix}_{item.lower().replace(' ', '_')}"
        button = InlineKeyboardButton(item, callback_data=callback_data)
        row.append(button)
        
        if len(row) == columns:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    if back_action:
        keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data=back_action)])
    
    return InlineKeyboardMarkup(keyboard)

def combine_keyboards(*keyboards: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """Combine plusieurs keyboards en un seul"""
    combined_keyboard = []
    
    for keyboard in keyboards:
        combined_keyboard.extend(keyboard.inline_keyboard)
    
    return InlineKeyboardMarkup(combined_keyboard)

def add_help_button(keyboard: InlineKeyboardMarkup, 
                   section: str) -> InlineKeyboardMarkup:
    """Ajoute un bouton d'aide à un keyboard existant"""
    new_keyboard = keyboard.inline_keyboard.copy()
    help_button = [InlineKeyboardButton("❓ Aide", callback_data=f"help_{section}")]
    new_keyboard.append(help_button)
    
    return InlineKeyboardMarkup(new_keyboard)
"""Claviers simplifiés et orientés actions rapides"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_simple() -> InlineKeyboardMarkup:
    """Menu principal simplifié avec actions rapides"""
    keyboard = [
        # Ligne 1: Actions quotidiennes
        [
            InlineKeyboardButton("📅 Meetings", callback_data="meetings_quick"),
            InlineKeyboardButton("📊 Stats", callback_data="stats_quick")
        ],
        # Ligne 2: Gestion
        [
            InlineKeyboardButton("🎯 Campagnes", callback_data="campaigns_quick"),
            InlineKeyboardButton("👥 Leads", callback_data="leads_quick")
        ],
        # Ligne 3: Administration
        [
            InlineKeyboardButton("📆 Tâches", callback_data="tasks_quick"),
            InlineKeyboardButton("🧠 Système", callback_data="system_quick")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meetings_quick_keyboard() -> InlineKeyboardMarkup:
    """Actions rapides pour les meetings"""
    keyboard = [
        [InlineKeyboardButton("📅 Meetings du jour", callback_data="meetings_today")],
        [InlineKeyboardButton("📋 Tous les meetings", callback_data="meetings_all")],
        [InlineKeyboardButton("🎯 Conversions rapides", callback_data="meetings_convert")],
        [InlineKeyboardButton("📈 Stats conversions", callback_data="meetings_stats")],
        [InlineKeyboardButton("⬅️ Menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_conversion_quick_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Interface ultra-rapide pour conversion"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Accepté", callback_data=f"quick_accept_{meeting_id}"),
            InlineKeyboardButton("❌ Refusé", callback_data=f"quick_refuse_{meeting_id}")
        ],
        [
            InlineKeyboardButton("🤔 Réfléchit", callback_data=f"quick_thinking_{meeting_id}"),
            InlineKeyboardButton("👻 Absent", callback_data=f"quick_noshow_{meeting_id}")
        ],
        [InlineKeyboardButton("⬅️ Retour", callback_data="meetings_convert")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quick_refusal_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Raisons de refus simplifiées"""
    keyboard = [
        [InlineKeyboardButton("💰 Prix", callback_data=f"refuse_quick_{meeting_id}_price_too_high")],
        [InlineKeyboardButton("💸 Budget", callback_data=f"refuse_quick_{meeting_id}_no_budget")],
        [InlineKeyboardButton("⏰ Timing", callback_data=f"refuse_quick_{meeting_id}_bad_timing")],
        [InlineKeyboardButton("🏢 Interne", callback_data=f"refuse_quick_{meeting_id}_internal_solution")],
        [InlineKeyboardButton("⬅️ Retour", callback_data=f"quick_refuse_{meeting_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_stats_quick_keyboard() -> InlineKeyboardMarkup:
    """Stats essentielles"""
    keyboard = [
        [InlineKeyboardButton("📊 Vue d'ensemble", callback_data="stats_overview")],
        [InlineKeyboardButton("🎯 Conversions", callback_data="stats_conversions")],
        [InlineKeyboardButton("👥 Leads", callback_data="stats_leads")],
        [InlineKeyboardButton("💰 CA", callback_data="stats_revenue")],
        [InlineKeyboardButton("⬅️ Menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button(target: str) -> InlineKeyboardMarkup:
    """Bouton retour générique"""
    labels = {
        "main_menu": "🏠 Menu principal",
        "meetings": "📅 Meetings", 
        "stats": "📊 Stats",
        "campaigns": "🎯 Campagnes",
        "leads": "👥 Leads"
    }
    
    label = labels.get(target, f"⬅️ Retour {target}")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=target)]
    ])

def get_contextual_actions(item_type: str, item_id: int) -> InlineKeyboardMarkup:
    """Actions contextuelles selon le type d'élément"""
    if item_type == "meeting":
        keyboard = [
            [InlineKeyboardButton("🎯 Convertir", callback_data=f"meeting_convert_{item_id}")],
            [InlineKeyboardButton("📝 Détails", callback_data=f"meeting_details_{item_id}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="meetings_quick")]
        ]
    elif item_type == "lead":
        keyboard = [
            [InlineKeyboardButton("📞 Contacter", callback_data=f"lead_contact_{item_id}")],
            [InlineKeyboardButton("📝 Détails", callback_data=f"lead_details_{item_id}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="leads_quick")]
        ]
    elif item_type == "campaign":
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data=f"campaign_stats_{item_id}")],
            [InlineKeyboardButton("⏸️ Pause", callback_data=f"campaign_pause_{item_id}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data="campaigns_quick")]
        ]
    else:
        keyboard = [[InlineKeyboardButton("⬅️ Retour", callback_data="main_menu")]]
    
    return InlineKeyboardMarkup(keyboard)
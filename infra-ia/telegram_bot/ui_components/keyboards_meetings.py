"""Keyboards dédiés aux meetings - Extraits et consolidés"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_meetings_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu principal des meetings"""
    keyboard = [
        # Ligne 1: Actions quotidiennes
        [
            InlineKeyboardButton("📊 Statistiques", callback_data="meetings_stats"),
            InlineKeyboardButton("📅 À venir", callback_data="meetings_upcoming")
        ],
        # Ligne 2: Navigation temporelle  
        [
            InlineKeyboardButton("🗓️ Aujourd'hui", callback_data="meetings_today"),
            InlineKeyboardButton("📆 Cette semaine", callback_data="meetings_week")
        ],
        # Ligne 3: Gestion complète
        [
            InlineKeyboardButton("📋 Tous les meetings", callback_data="meetings_all"),
            InlineKeyboardButton("🔍 Filtrer", callback_data="meetings_filter")
        ],
        # Ligne 4: Retour
        [InlineKeyboardButton("⬅️ Menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meetings_quick_keyboard() -> InlineKeyboardMarkup:
    """Interface rapide pour conversions"""
    keyboard = [
        [InlineKeyboardButton("⚡ Conversions rapides", callback_data="meetings_convert_quick")],
        [InlineKeyboardButton("📅 Meetings du jour", callback_data="meetings_today")],
        [InlineKeyboardButton("📈 Stats conversions", callback_data="meetings_stats")],
        [InlineKeyboardButton("⬅️ Menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meeting_conversion_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Interface de conversion pour un meeting spécifique"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Accepté", callback_data=f"convert_{meeting_id}_accepted"),
            InlineKeyboardButton("❌ Refusé", callback_data=f"convert_{meeting_id}_refused")
        ],
        [
            InlineKeyboardButton("🤔 À réfléchir", callback_data=f"convert_{meeting_id}_thinking"),
            InlineKeyboardButton("👻 Absent", callback_data=f"convert_{meeting_id}_no_show")
        ],
        [InlineKeyboardButton("⬅️ Retour", callback_data="meetings_upcoming")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quick_conversion_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Interface ultra-rapide (2 clics max)"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Accepté", callback_data=f"quick_accept_{meeting_id}"),
            InlineKeyboardButton("❌ Refusé", callback_data=f"quick_refuse_{meeting_id}")
        ],
        [
            InlineKeyboardButton("🤔 Réfléchit", callback_data=f"quick_thinking_{meeting_id}"),
            InlineKeyboardButton("👻 Absent", callback_data=f"quick_noshow_{meeting_id}")
        ],
        [InlineKeyboardButton("⬅️ Meetings", callback_data="meetings_quick")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_services_selection_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Sélection de services pour client accepté"""
    keyboard = [
        [InlineKeyboardButton("🌐 Site web (1497€ + 29€/mois)", callback_data=f"select_service_{meeting_id}_website")],
        [InlineKeyboardButton("🤖 Bot IA (797€ + 249€/mois)", callback_data=f"select_service_{meeting_id}_bot_ia")],
        [InlineKeyboardButton("📱 App mobile (2497€ + 99€/mois)", callback_data=f"select_service_{meeting_id}_mobile_app")],
        [InlineKeyboardButton("💼 Pack complet (3997€ + 299€/mois)", callback_data=f"select_service_{meeting_id}_complete_pack")],
        [InlineKeyboardButton("🎯 Autre service", callback_data=f"select_service_{meeting_id}_other")],
        [InlineKeyboardButton("⬅️ Retour", callback_data=f"convert_{meeting_id}_accepted")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_refusal_reasons_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Raisons de refus détaillées"""
    keyboard = [
        [InlineKeyboardButton("💰 Prix trop élevé", callback_data=f"refuse_{meeting_id}_price_too_high")],
        [InlineKeyboardButton("💸 Pas de budget", callback_data=f"refuse_{meeting_id}_no_budget")],
        [InlineKeyboardButton("⏰ Mauvais timing", callback_data=f"refuse_{meeting_id}_bad_timing")],
        [InlineKeyboardButton("🏢 Solution interne", callback_data=f"refuse_{meeting_id}_internal_solution")],
        [InlineKeyboardButton("🤷 Peu d'intérêt", callback_data=f"refuse_{meeting_id}_low_interest")],
        [InlineKeyboardButton("🎯 Autre raison", callback_data=f"refuse_{meeting_id}_other")],
        [InlineKeyboardButton("⬅️ Retour", callback_data=f"convert_{meeting_id}_refused")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_thinking_options_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Options de suivi pour clients en réflexion"""
    keyboard = [
        [InlineKeyboardButton("📞 Relance dans 3 jours", callback_data=f"thinking_{meeting_id}_3_days")],
        [InlineKeyboardButton("📅 Relance dans 1 semaine", callback_data=f"thinking_{meeting_id}_1_week")],
        [InlineKeyboardButton("📆 Relance dans 2 semaines", callback_data=f"thinking_{meeting_id}_2_weeks")],
        [InlineKeyboardButton("📋 Suivi personnalisé", callback_data=f"thinking_{meeting_id}_custom")],
        [InlineKeyboardButton("⬅️ Retour", callback_data=f"convert_{meeting_id}_thinking")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meeting_details_keyboard(meeting_id: int, status: str = "scheduled") -> InlineKeyboardMarkup:
    """Actions disponibles pour un meeting selon son statut"""
    keyboard = []
    
    if status == "scheduled":
        # Meeting programmé - toutes les actions disponibles
        keyboard.extend([
            [InlineKeyboardButton("🎯 Convertir", callback_data=f"meeting_convert_{meeting_id}")],
            [InlineKeyboardButton("💬 Conversation", callback_data=f"meeting_conversation_{meeting_id}")],
            [
                InlineKeyboardButton("📅 Reprogrammer", callback_data=f"meeting_reschedule_{meeting_id}"),
                InlineKeyboardButton("❌ Annuler", callback_data=f"meeting_cancel_{meeting_id}")
            ]
        ])
    else:
        # Meeting terminé/annulé - actions limitées
        keyboard.append([
            InlineKeyboardButton("💬 Conversation", callback_data=f"meeting_conversation_{meeting_id}")
        ])
    
    # Retour
    keyboard.append([
        InlineKeyboardButton("⬅️ Retour", callback_data="meetings_upcoming")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_meeting_actions_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Actions rapides sur un meeting"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Terminé", callback_data=f"meeting_complete_{meeting_id}"),
            InlineKeyboardButton("👻 No-show", callback_data=f"meeting_no_show_{meeting_id}")
        ],
        [
            InlineKeyboardButton("📅 Reprogrammer", callback_data=f"meeting_reschedule_{meeting_id}"),
            InlineKeyboardButton("❌ Annuler", callback_data=f"meeting_cancel_{meeting_id}")
        ],
        [InlineKeyboardButton("⬅️ Retour", callback_data=f"meeting_details_{meeting_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meetings_filter_keyboard() -> InlineKeyboardMarkup:
    """Filtres pour la liste des meetings"""
    keyboard = [
        [InlineKeyboardButton("📅 Programmés", callback_data="meetings_filter_scheduled")],
        [InlineKeyboardButton("✅ Terminés", callback_data="meetings_filter_completed")],
        [InlineKeyboardButton("❌ Annulés", callback_data="meetings_filter_cancelled")],
        [InlineKeyboardButton("👻 No-show", callback_data="meetings_filter_no_show")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="meetings_all")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reschedule_options_keyboard(meeting_id: int) -> InlineKeyboardMarkup:
    """Options de reprogrammation"""
    keyboard = [
        [InlineKeyboardButton("📞 Contacter le client", callback_data=f"reschedule_contact_{meeting_id}")],
        [InlineKeyboardButton("📧 Envoyer proposition", callback_data=f"reschedule_email_{meeting_id}")],
        [InlineKeyboardButton("📅 Sélectionner créneaux", callback_data=f"reschedule_slots_{meeting_id}")],
        [InlineKeyboardButton("⬅️ Retour", callback_data=f"meeting_details_{meeting_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action: str, meeting_id: int) -> InlineKeyboardMarkup:
    """Clavier de confirmation générique"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmer", callback_data=f"confirm_meeting_{action}_{meeting_id}"),
            InlineKeyboardButton("❌ Annuler", callback_data=f"meeting_details_{meeting_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_meeting_list_keyboard(meetings: list, action_prefix: str = "meeting_details") -> InlineKeyboardMarkup:
    """Génère un clavier avec liste de meetings"""
    keyboard = []
    
    for meeting in meetings[:10]:  # Limite à 10 pour ne pas surcharger
        client_name = meeting.get('client_name', f"Meeting #{meeting['id']}")
        date_str = meeting.get('start_time', '')[:10] if meeting.get('start_time') else 'Date TBD'
        
        button_text = f"📅 {client_name} ({date_str})"
        callback_data = f"{action_prefix}_{meeting['id']}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Boutons de navigation
    keyboard.append([
        InlineKeyboardButton("🔄 Rafraîchir", callback_data="meetings_upcoming"),
        InlineKeyboardButton("⬅️ Menu meetings", callback_data="meetings_main")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_pagination_keyboard(current_page: int, total_pages: int, base_callback: str) -> InlineKeyboardMarkup:
    """Clavier de pagination pour les listes"""
    keyboard = []
    
    # Boutons de pagination
    pagination_row = []
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton("⬅️ Précédent", callback_data=f"{base_callback}_page_{current_page-1}")
        )
    
    pagination_row.append(
        InlineKeyboardButton(f"{current_page+1}/{total_pages}", callback_data="page_info")
    )
    
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton("Suivant ➡️", callback_data=f"{base_callback}_page_{current_page+1}")
        )
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    # Retour
    keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data="meetings_main")])
    
    return InlineKeyboardMarkup(keyboard)

# Helpers pour keyboard generation dynamique

def build_dynamic_meeting_keyboard(meeting_data: dict) -> InlineKeyboardMarkup:
    """Construit un clavier dynamique basé sur les données du meeting"""
    meeting_id = meeting_data['id']
    status = meeting_data.get('status', 'scheduled')
    
    # Récupérer le clavier approprié selon le statut
    if status == 'scheduled':
        return get_meeting_details_keyboard(meeting_id, status)
    else:
        return get_meeting_details_keyboard(meeting_id, status)

def build_conversion_flow_keyboard(meeting_id: int, step: str) -> InlineKeyboardMarkup:
    """Construit le clavier approprié selon l'étape de conversion"""
    if step == "main":
        return get_meeting_conversion_keyboard(meeting_id)
    elif step == "services":
        return get_services_selection_keyboard(meeting_id)
    elif step == "refusal":
        return get_refusal_reasons_keyboard(meeting_id)
    elif step == "thinking":
        return get_thinking_options_keyboard(meeting_id)
    else:
        # Fallback vers conversion principale
        return get_meeting_conversion_keyboard(meeting_id)
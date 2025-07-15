"""Claviers avancés pour la gestion complète des tâches"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.settings import EMOJIS

# Import des modules core avec fallback simple
try:
    from core.callback_manager import callback_manager
except ImportError:
    # Simple fallback callback manager
    class CallbackManager:
        def register(self, **kwargs):
            action = kwargs.get('action', 'unknown')
            if action == "select_agent_for_task":
                return f"select_agent_for_task_{kwargs.get('task_type', '')}_{kwargs.get('agent_name', '')}"
            elif action == "select_action_for_task":
                return f"select_action_for_task_{kwargs.get('task_type', '')}_{kwargs.get('agent_name', '')}_{kwargs.get('action_code', '')}"
            elif action == "param_action":
                return f"param_{kwargs.get('task_type', '')}_{kwargs.get('agent_name', '')}_{kwargs.get('action_code', '')}_{kwargs.get('param_type', '')}"
            elif action == "condition_selection":
                return f"condition_{kwargs.get('task_type', '')}_{kwargs.get('agent_name', '')}_{kwargs.get('action_code', '')}_{kwargs.get('condition', '')}"
            elif action == "task_config":
                return f"config_{kwargs.get('task_type', '')}_{kwargs.get('agent_name', '')}_{kwargs.get('action_code', '')}_{kwargs.get('config_value', '')}"
            else:
                return f"{action}_callback"
    callback_manager = CallbackManager()

try:
    from core.error_handler import error_handler
except ImportError:
    # Simple fallback error handler
    class ErrorHandler:
        def validate_callback_data(self, data):
            return len(data) < 64
    error_handler = ErrorHandler()

def get_task_type_selection_keyboard() -> InlineKeyboardMarkup:
    """Clavier pour sélectionner le type de tâche"""
    keyboard = [
        [InlineKeyboardButton("🔧 SYSTEM_RECURRING", callback_data="task_type_system_recurring")],
        [InlineKeyboardButton("💼 BUSINESS_RECURRING", callback_data="task_type_business_recurring")],
        [InlineKeyboardButton("⚡ ONE_TIME", callback_data="task_type_one_time")],
        [InlineKeyboardButton("❓ CONDITIONAL", callback_data="task_type_conditional")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="tasks_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_advanced_agents_selection_keyboard(agents: list, task_type: str) -> InlineKeyboardMarkup:
    """Clavier avancé pour sélectionner un agent pour création de tâche"""
    keyboard = []
    
    main_agents = [
        ("MessagingAgent", "📧"),
        ("ProspectionSupervisor", "🎯"), 
        ("PivotStrategyAgent", "📊"),
        ("TaskWatchdogAgent", "🛡️"),
        ("ScrapingSupervisorAgent", "🔍"),
        ("ResponseInterpreterAgent", "💬"),
        ("FollowUpAgent", "📅"),
        ("CleanerAgent", "🧹"),
        ("DatabaseQueryAgent", "💾"),
        ("NicheExplorerAgent", "🎯"),
        ("OverseerAgent", "🧠"),
        ("ScraperAgent", "🔍"),
        ("AgentSchedulerAgent", "⏰")
    ]
    
    for agent_name, emoji in main_agents:
        agent_exists = any(agent.get('name') == agent_name for agent in agents)
        if agent_exists:
            # Utiliser le callback_manager pour créer un callback_data court
            callback_data = callback_manager.register(
                action="select_agent_for_task",
                task_type=task_type,
                agent_name=agent_name
            )
            button_text = f"{emoji} {agent_name}"
            
            # Valider avant d'ajouter
            if error_handler.validate_callback_data(callback_data):
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data="tasks_create")])
    return InlineKeyboardMarkup(keyboard)

def get_advanced_agent_actions_keyboard(agent_name: str, task_type: str) -> InlineKeyboardMarkup:
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
            ("📊 Analyser performance", "analyze_performance"),
            ("🎯 Optimiser stratégie", "optimize_strategy"),
            ("📈 Recommandations pivot", "pivot_recommendations"),
            ("🔄 Ajuster campagne", "adjust_campaign"),
            ("📋 Rapport stratégique", "strategic_report"),
            ("🎯 Identifier opportunités", "identify_opportunities")
        ],
        "TaskWatchdogAgent": [
            ("🛡️ Analyser sécurité tâche", "analyze_task_security"),
            ("📊 Rapport sécurité", "security_report"),
            ("🚨 Alertes système", "system_alerts"),
            ("🔍 Audit activités", "audit_activities"),
            ("⚙️ Configurer règles", "configure_rules")
        ],
        "ScrapingSupervisorAgent": [
            ("🔍 Superviser scraping", "supervise_scraping"),
            ("📊 Rapport scraping", "scraping_report"),
            ("🎯 Optimiser sources", "optimize_sources"),
            ("📈 Statistiques collecte", "collection_stats"),
            ("⚙️ Configurer scraping", "configure_scraping")
        ],
        "ResponseInterpreterAgent": [
            ("💬 Interpréter réponse", "interpret_response"),
            ("📊 Analyser sentiment", "analyze_sentiment"),
            ("🎯 Classifier intention", "classify_intention"),
            ("📋 Rapport interprétation", "interpretation_report"),
            ("⚙️ Configurer modèles", "configure_models")
        ],
        "FollowUpAgent": [
            ("📅 Planifier relance", "schedule_follow_up"),
            ("📧 Envoyer rappel", "send_reminder"),
            ("🔍 Analyser réponses", "analyze_responses"),
            ("📊 Rapport suivi", "follow_up_report")
        ],
        "CleanerAgent": [
            ("🧹 Nettoyer leads", "clean_leads"),
            ("📊 Détecter doublons", "detect_duplicates"),
            ("🔍 Valider données", "validate_data"),
            ("📋 Rapport nettoyage", "cleaning_report"),
            ("⚙️ Configurer règles", "configure_cleaning_rules")
        ],
        "DatabaseQueryAgent": [
            ("💾 Requête SQL intelligente", "smart_query"),
            ("📊 Compter les leads", "count_leads"),
            ("💬 Conversations actives", "active_conversations"),
            ("📈 Taux de conversion", "conversion_rate"),
            ("🔍 Recherche globale", "global_search"),
            ("📋 Statistiques avancées", "advanced_stats"),
            ("🎯 Analyse leads qualifiés", "qualified_leads_analysis")
        ],
        "NicheExplorerAgent": [
            ("🎯 Explorer nouvelles niches", "explore_niches"),
            ("📊 Analyser potentiel niche", "analyze_niche_potential"),
            ("🚀 Recommandations stratégiques", "strategic_recommendations"),
            ("🔍 Découvrir niches TPE/PME", "discover_niches"),
            ("🚫 Gérer blacklist niches", "manage_blacklist"),
            ("📈 Analyse marché", "market_analysis")
        ],
        "OverseerAgent": [
            ("🧠 Orchestrer workflow", "orchestrate_workflow"),
            ("⚙️ Exécuter agent spécifique", "execute_agent"),
            ("🔧 Mettre à jour config", "update_config"),
            ("📊 État du système", "get_system_state"),
            ("🔄 Déléguer au superviseur", "delegate_to_supervisor"),
            ("🎯 Traiter instruction admin", "handle_admin_instruction")
        ],
        "ScraperAgent": [
            ("🔍 Scraper via Apify", "scrape_from_apify"),
            ("🌐 Scraper via Apollo", "scrape_from_apollo"),
            ("📊 Statistiques scraping", "get_scraping_stats"),
            ("🔗 Analyser présence web", "analyze_web_presence"),
            ("💾 Sauvegarder leads en BDD", "save_leads_to_db"),
            ("🎯 Scraper niche spécifique", "scrape_niche")
        ],
        "AgentSchedulerAgent": [
            ("⏰ Planifier tâche", "schedule_task"),
            ("❌ Annuler tâche", "cancel_task"),
            ("📋 Tâches en attente", "get_pending_tasks"),
            ("▶️ Démarrer scheduler", "start_scheduler"),
            ("⏸️ Arrêter scheduler", "stop_scheduler"),
            ("🧹 Nettoyer tâches expirées", "cleanup_expired_tasks"),
            ("📊 Statistiques scheduler", "get_stats")
        ]
    }
    
    keyboard = []
    actions = actions_map.get(agent_name, [])
    
    for action_text, action_code in actions:
        # Utiliser le callback_manager pour créer un callback_data court
        callback_data = callback_manager.register(
            action="select_action_for_task",
            task_type=task_type,
            agent_name=agent_name,
            action_code=action_code
        )
        
        # Valider avant d'ajouter
        if error_handler.validate_callback_data(callback_data):
            keyboard.append([InlineKeyboardButton(action_text, callback_data=callback_data)])
    
    # Bouton retour avec callback_manager aussi
    back_callback = callback_manager.register(
        action="select_agent_for_task",
        task_type=task_type
    )
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

def get_action_parameters_keyboard(agent_name: str, action: str, task_type: str) -> InlineKeyboardMarkup:
    """Clavier pour configurer les paramètres spécifiques à l'action"""
    keyboard = []
    
    # Paramètres génériques
    if action in ["send_message", "send_bulk_messages"]:
        parameters = [
            ("🎯 Tous les leads qualifiés", "qualified_leads"),
            ("👤 Lead spécifique", "specific_lead"),
            ("🎯 Leads d'une campagne", "campaign_leads"),
            ("📂 Leads d'une niche", "niche_leads")
        ]
    elif action in ["start_prospection", "scrape_niche"]:
        parameters = [
            ("📂 Sélectionner niche", "select_niche"),
            ("🏙️ Sélectionner ville", "select_city")
        ]
    elif action in ["send_reminder", "schedule_follow_up"]:
        parameters = [
            ("🎯 Campagne spécifique", "campaign_reminder"),
            ("⏰ Délai 24h", "24h_reminder"),
            ("⏰ Délai 48h", "48h_reminder")
        ]
    # Paramètres pour PivotStrategyAgent
    elif action in ["analyze_performance", "optimize_strategy", "pivot_recommendations"]:
        parameters = [
            ("📊 Campagne active", "active_campaign"),
            ("📈 Période spécifique", "specific_period"),
            ("🎯 Niche particulière", "specific_niche"),
            ("🔄 Toutes campagnes", "all_campaigns")
        ]
    # Paramètres pour TaskWatchdogAgent
    elif action in ["analyze_task_security", "audit_activities"]:
        parameters = [
            ("🔍 Tâche spécifique", "specific_task"),
            ("📊 Analyse globale", "global_analysis"),
            ("⚠️ Alertes récentes", "recent_alerts"),
            ("🛡️ Audit complet", "full_audit")
        ]
    # Nouveaux paramètres pour les agents ajoutés
    elif action in ["smart_query", "global_search"]:
        parameters = [
            ("🔍 Recherche par mots-clés", "keyword_search"),
            ("📊 Requête statistiques", "stats_query"),
            ("💬 Analyse conversations", "conversation_analysis"),
            ("🎯 Filtrer par niche", "niche_filter")
        ]
    elif action in ["explore_niches", "discover_niches"]:
        parameters = [
            ("🇫🇷 France métropolitaine", "france_metro"),
            ("🏙️ Zones urbaines", "urban_zones"),
            ("🌾 Zones rurales", "rural_zones"),
            ("💼 Secteur spécifique", "specific_sector")
        ]
    elif action in ["orchestrate_workflow", "execute_agent"]:
        parameters = [
            ("🔄 Workflow scraping complet", "full_scraping"),
            ("💬 Workflow messaging", "messaging_workflow"),
            ("📊 Workflow qualification", "qualification_workflow"),
            ("🎯 Workflow personnalisé", "custom_workflow")
        ]
    elif action in ["scrape_from_apify", "scrape_from_apollo"]:
        parameters = [
            ("🍽️ Restaurants", "restaurants"),
            ("⚖️ Cabinets d'avocats", "law_firms"),
            ("🏥 Cabinets médicaux", "medical_offices"),
            ("🔧 Artisans", "craftsmen"),
            ("🏪 Commerces de proximité", "local_shops")
        ]
    elif action in ["schedule_task", "schedule_advanced_task"]:
        parameters = [
            ("⚡ Exécution immédiate", "immediate"),
            ("⏰ Dans 1 heure", "1hour"),
            ("📅 Quotidien", "daily"),
            ("📆 Hebdomadaire", "weekly")
        ]
    else:
        # Paramètre par défaut
        parameters = [("✅ Continuer sans paramètres", "no_params")]
    
    for text, param_type in parameters:
        callback_data = callback_manager.register(
            action="param_action",
            task_type=task_type,
            agent_name=agent_name,
            action_code=action,
            param_type=param_type
        )
        if error_handler.validate_callback_data(callback_data):
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # Bouton retour
    back_callback = callback_manager.register(
        action="select_action_for_task",
        task_type=task_type,
        agent_name=agent_name,
        action_code=action
    )
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

def get_condition_selection_keyboard(task_type: str, agent_name: str, action: str) -> InlineKeyboardMarkup:
    """Clavier pour sélectionner une condition prédéfinie"""
    conditions = [
        ("📧 no_response_after_24h", "no_response_24h"),
        ("📧 no_response_after_48h", "no_response_48h"),
        ("📊 low_campaign_performance", "low_performance"),
        ("👥 no_new_leads_today", "no_leads_today"),
        ("🔄 system_idle_for_1h", "system_idle")
    ]
    
    keyboard = []
    for text, condition_code in conditions:
        callback_data = callback_manager.register(
            action="condition_selection",
            task_type=task_type,
            agent_name=agent_name,
            action_code=action,
            condition=condition_code
        )
        if error_handler.validate_callback_data(callback_data):
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # Bouton retour
    back_callback = callback_manager.register(
        action="param_action",
        task_type=task_type,
        agent_name=agent_name,
        action_code=action,
        param_type="configure"
    )
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

def get_task_type_configuration_keyboard(task_type: str, agent_name: str, action: str, params: str) -> InlineKeyboardMarkup:
    """Clavier pour configurer les paramètres spécifiques au type de tâche"""
    keyboard = []
    
    if task_type == "system_recurring":
        configs = [
            ("⏰ Toutes les heures", "3600"),
            ("📅 Quotidien", "86400"),
            ("📆 Hebdomadaire", "604800")
        ]
        for text, config_value in configs:
            callback_data = callback_manager.register(
                action="task_config",
                task_type=task_type,
                agent_name=agent_name,
                action_code=action,
                param_type=params,
                config_value=config_value
            )
            if error_handler.validate_callback_data(callback_data):
                keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
                
    elif task_type == "business_recurring":
        configs = [
            ("⏰ Toutes les heures", "3600"),
            ("📅 Quotidien", "86400"),
            ("📆 Hebdomadaire", "604800"),
            ("🗓️ Fin dans 30 jours", "end30")
        ]
        for text, config_value in configs:
            callback_data = callback_manager.register(
                action="task_config",
                task_type=task_type,
                agent_name=agent_name,
                action_code=action,
                param_type=params,
                config_value=config_value
            )
            if error_handler.validate_callback_data(callback_data):
                keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
                
    elif task_type == "one_time":
        configs = [
            ("⚡ Maintenant", "now"),
            ("⏰ Dans 1 heure", "1h"),
            ("📅 Dans 24h", "24h")
        ]
        for text, config_value in configs:
            callback_data = callback_manager.register(
                action="task_config",
                task_type=task_type,
                agent_name=agent_name,
                action_code=action,
                param_type=params,
                config_value=config_value
            )
            if error_handler.validate_callback_data(callback_data):
                keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
                
    elif task_type == "conditional":
        configs = [
            ("🔍 Vérifier toutes les heures", "check_3600"),
            ("🔍 Vérifier toutes les 6h", "check_21600")
        ]
        for text, config_value in configs:
            callback_data = callback_manager.register(
                action="task_config",
                task_type=task_type,
                agent_name=agent_name,
                action_code=action,
                param_type=params,
                config_value=config_value
            )
            if error_handler.validate_callback_data(callback_data):
                keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # Bouton retour
    back_callback = callback_manager.register(
        action="param_action",
        task_type=task_type,
        agent_name=agent_name,
        action_code=action,
        param_type=params
    )
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Retour", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

def get_final_task_confirmation_keyboard(task_data: dict) -> InlineKeyboardMarkup:
    """Clavier de confirmation finale pour créer la tâche"""
    keyboard = [
        [InlineKeyboardButton("✅ Créer la tâche", callback_data="create_final_task")],
        [InlineKeyboardButton("❌ Annuler", callback_data="tasks_create")]
    ]
    return InlineKeyboardMarkup(keyboard)

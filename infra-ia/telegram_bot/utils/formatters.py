"""Formatage des réponses pour le bot Telegram"""
from typing import Dict, List, Optional, Any
from config.settings import EMOJIS

def format_stats_summary(stats: Dict) -> str:
    """Formate un résumé des statistiques"""
    if not stats:
        return "❌ Aucune statistique disponible"
    
    text = f"""📊 **Statistiques générales BerinIA**

{EMOJIS['leads']} **Leads :** {stats.get('total_leads', 'N/A')}
🎯 **Campagnes actives :** {stats.get('active_campaigns', 'N/A')}
📈 **Taux de conversion :** {stats.get('conversion_rate', 'N/A')}%
💰 **Compensation totale :** {stats.get('total_compensation', 'N/A')}€
"""
    
    return text

def format_campaign_list(campaigns: List[Dict]) -> str:
    """Formate la liste des campagnes"""
    if not campaigns:
        return "ℹ️ Aucune campagne trouvée"
    
    text = f"🎯 **Campagnes ({len(campaigns)})**\n\n"
    
    for i, campaign in enumerate(campaigns[:10], 1):
        status = campaign.get('status', 'unknown')
        status_emoji = '✅' if status == 'active' else '❌'
        
        name = campaign.get('name', f'Campagne {i}')
        leads_count = campaign.get('leads_count', 0)
        qualified_leads = campaign.get('qualified_leads', 0)
        
        # Calculer le vrai taux de conversion
        conversion_rate = (qualified_leads / leads_count * 100) if leads_count > 0 else 0
        
        text += f"{i}️⃣ **{name}**\n"
        text += f"   {status_emoji} {status.title()}\n"
        text += f"   👥 {leads_count} leads | ✅ {qualified_leads} qualifiés\n"
        text += f"   📊 {conversion_rate:.1f}% conversion\n\n"
    
    if len(campaigns) > 10:
        text += f"... et {len(campaigns) - 10} autres campagnes\n"
    
    return text

def format_campaign_details(campaign: Dict) -> str:
    """Formate les détails d'une campagne"""
    if not campaign:
        return "❌ Campagne non trouvée"
    
    status = campaign.get('status', 'unknown')
    status_emoji = EMOJIS['active'] if status == 'active' else EMOJIS['inactive']
    
    text = f"""🎯 **Détails de la campagne**

📋 **Nom :** {campaign.get('name', 'N/A')}
{status_emoji} **Statut :** {status.title()}
📊 **Leads :** {campaign.get('leads_count', 0)}
📈 **Taux de conversion :** {campaign.get('conversion_rate', 0)}%
💰 **Revenus générés :** {campaign.get('revenue', 0)}€
📅 **Créée le :** {campaign.get('created_at', 'N/A')}
📂 **Niche :** {campaign.get('niche', 'N/A')}
"""
    
    return text

def format_leads_summary(leads_stats: Dict) -> str:
    """Formate le résumé des leads"""
    if not leads_stats:
        return "❌ Aucune statistique de leads disponible"
    
    text = f"""👥 **Résumé des leads**

🔢 **Total :** {leads_stats.get('total_count', 0)}
✅ **Qualifiés :** {leads_stats.get('qualified_count', 0)}
📈 **Taux de qualification :** {leads_stats.get('qualification_rate', 0)}%
💬 **Réponses positives :** {leads_stats.get('positive_responses', 0)}
😐 **Réponses neutres :** {leads_stats.get('neutral_responses', 0)}
❌ **Réponses négatives :** {leads_stats.get('negative_responses', 0)}
"""
    
    return text

def format_leads_list(leads: List[Dict], offset: int = 0) -> str:
    """Formate la liste des leads"""
    if not leads:
        return "ℹ️ Aucun lead trouvé"
    
    text = f"👥 **Leads (page {offset//5 + 1})**\n\n"
    
    for i, lead in enumerate(leads[:5], 1):
        name = lead.get('name', lead.get('email', f'Lead {offset + i}'))
        status = lead.get('status', 'unknown')
        company = lead.get('company', 'N/A')
        score = lead.get('score', 0)
        
        # Emoji selon le statut
        if status == 'qualified':
            status_emoji = '✅'
        elif status == 'contacted':
            status_emoji = '📧'
        elif status == 'responded':
            status_emoji = '💬'
        else:
            status_emoji = '⏳'
        
        text += f"{offset + i}. {status_emoji} **{name}**\n"
        text += f"   🏢 {company} | 📊 Score: {score}\n"
        text += f"   📧 {lead.get('email', 'N/A')}\n\n"
    
    return text

def format_lead_details(lead: Dict) -> str:
    """Formate les détails d'un lead"""
    if not lead:
        return "❌ Lead non trouvé"
    
    text = f"""👤 **Détails du lead**

📛 **Nom :** {lead.get('name', 'N/A')}
📧 **Email :** {lead.get('email', 'N/A')}
🏢 **Entreprise :** {lead.get('company', 'N/A')}
📊 **Score :** {lead.get('score', 0)}/100
📍 **Statut :** {lead.get('status', 'N/A')}
📞 **Téléphone :** {lead.get('phone', 'N/A')}
💰 **Compensation :** {lead.get('compensation', 0)}€
📅 **Ajouté le :** {lead.get('created_at', 'N/A')}
🎯 **Campagne :** {lead.get('campaign', 'N/A')}
"""
    
    return text

def format_niches_list(niches: List[Dict]) -> str:
    """Formate la liste des niches"""
    if not niches:
        return "ℹ️ Aucune niche trouvée"
    
    text = f"📂 **Niches ({len(niches)})**\n\n"
    
    for i, niche in enumerate(niches[:10], 1):
        name = niche.get('name', f'Niche {i}')
        status = niche.get('status', 'active')
        leads_count = niche.get('leads_count', 0)
        campaigns_count = niche.get('campaigns_count', 0)
        
        status_emoji = EMOJIS['active'] if status == 'active' else EMOJIS['inactive']
        
        text += f"{i}️⃣ **{name}**\n"
        text += f"   {status_emoji} {status.title()}\n"
        text += f"   🎯 {campaigns_count} campagnes | 👥 {leads_count} leads\n\n"
    
    return text

def format_niche_performance(niche: Dict, performance: Dict) -> str:
    """Formate les performances d'une niche"""
    if not niche or not performance:
        return "❌ Données de performance non disponibles"
    
    text = f"""📂 **Performance de la niche : {niche.get('name', 'N/A')}**

📊 **Métriques générales :**
• Total leads : {performance.get('total_leads', 0)}
• Taux de conversion : {performance.get('conversion_rate', 0)}%
• Revenus générés : {performance.get('revenue', 0)}€
• ROI : {performance.get('roi', 0)}%

🎯 **Campagnes associées :** {performance.get('campaigns_count', 0)}
📈 **Évolution :** {performance.get('trend', 'stable')}
⭐ **Score de viabilité :** {performance.get('viability_score', 0)}/100
"""
    
    return text

def format_agents_status(agents) -> str:
    """Formate l'état des agents"""
    # CORRECTION : Gérer le cas où agents peut être None, une liste ou un dict
    if not agents:
        return "ℹ️ Aucun agent trouvé"
    
    # Si agents est un dict avec une clé 'agents', l'extraire
    if isinstance(agents, dict):
        if 'agents' in agents:
            agents_list = agents['agents']
        else:
            # Sinon traiter le dict comme un seul agent
            agents_list = [agents]
    else:
        agents_list = agents if isinstance(agents, list) else []
    
    text = "🧠 **État des agents**\n\n"
    
    if not agents_list:
        return text + "ℹ️ Aucun agent configuré dans le système"
    
    active_count = sum(1 for agent in agents_list if agent.get('status') == 'active')
    
    text += f"📊 **Résumé :** {active_count}/{len(agents_list)} agents actifs\n\n"
    
    for agent in agents_list:
        name = agent.get('name', 'Agent inconnu')
        status = agent.get('status', 'unknown')
        created_at = agent.get('created_at')
        updated_at = agent.get('updated_at')
        
        # Afficher des informations plus pertinentes
        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_date = dt.strftime('%d/%m/%Y')
            except:
                created_date = 'N/A'
        else:
            created_date = 'N/A'
        
        # Déterminer l'activité basée sur le statut et le type
        agent_type = agent.get('type', 'unknown')
        if status == 'active':
            if agent_type in ['orchestrator', 'supervisor', 'system']:
                activity_info = 'Système principal - Actif'
            elif agent_type == 'worker':
                activity_info = 'Agent de travail - Prêt'
            elif agent_type == 'interface':
                activity_info = 'Interface - En écoute'
            elif agent_type == 'strategic':
                activity_info = 'Stratégie - Surveillant'
            else:
                activity_info = 'Agent opérationnel'
        else:
            activity_info = 'Inactif'
        
        if status == 'active':
            status_emoji = '✅'
        elif status == 'inactive':
            status_emoji = '❌'
        else:
            status_emoji = '⚠️'
        
        text += f"{status_emoji} **{name}**\n"
        text += f"   🔧 Type: {agent_type} | 📋 {activity_info}\n\n"
    
    return text

def format_system_logs(logs: List[Dict], limit: int = 10) -> str:
    """Formate les logs système"""
    if not logs:
        return "ℹ️ Aucun log disponible"
    
    text = f"📋 **Logs système (derniers {min(len(logs), limit)})**\n\n"
    
    for log in logs[:limit]:
        timestamp = log.get('timestamp', 'N/A')
        level = log.get('level', 'INFO')
        message = log.get('message', 'N/A')
        
        # Emoji selon le niveau
        if level == 'ERROR':
            level_emoji = '❌'
        elif level == 'WARNING':
            level_emoji = '⚠️'
        elif level == 'INFO':
            level_emoji = 'ℹ️'
        else:
            level_emoji = '📝'
        
        text += f"{level_emoji} **{timestamp}**\n"
        text += f"   {message}\n\n"
    
    return text

def format_scheduled_tasks(tasks: List[Dict]) -> str:
    """Formate les tâches planifiées"""
    if not tasks:
        return "ℹ️ Aucune tâche planifiée"
    
    text = f"📆 **Tâches planifiées ({len(tasks)})**\n\n"
    
    for task in tasks:
        task_id = task.get('task_id', 'unknown')
        name = task.get('name', 'Tâche inconnue')
        next_run = task.get('next_run', 'N/A')
        status = task.get('status', 'unknown')
        agent = task.get('agent', 'Agent inconnu')
        schedule = task.get('schedule', 'N/A')
        priority = task.get('priority', 3)
        
        # Formatage de la date
        if next_run and next_run != 'N/A':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%d/%m/%Y %H:%M')
            except:
                formatted_date = next_run
        else:
            formatted_date = 'N/A'
        
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
        
        # Emoji de priorité
        if priority == 1:
            priority_emoji = '🔴'
        elif priority == 2:
            priority_emoji = '🟡'
        else:
            priority_emoji = '🟢'
        
        text += f"{status_emoji} **{name}** (ID: {task_id})\n"
        text += f"   🤖 Agent: {agent}\n"
        text += f"   🔄 Récurrence: {schedule}\n"
        text += f"   ⏰ Prochaine: {formatted_date}\n"
        text += f"   {priority_emoji} Priorité: {priority}\n\n"
    
    return text

def format_task_details(task: Dict) -> str:
    """Formate les détails d'une tâche"""
    if not task:
        return "❌ Tâche non trouvée"
    
    task_id = task.get('task_id', task.get('id', 'unknown'))
    name = task.get('name', 'Tâche inconnue')
    agent = task.get('agent', 'Agent inconnu')
    status = task.get('status', 'unknown')
    schedule = task.get('schedule', 'N/A')
    next_run = task.get('next_run', 'N/A')
    last_run = task.get('last_run', 'N/A')
    priority = task.get('priority', 3)
    params = task.get('params', {})
    
    # Formatage des dates
    if next_run and next_run != 'N/A':
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
            formatted_next = dt.strftime('%d/%m/%Y %H:%M')
        except:
            formatted_next = next_run
    else:
        formatted_next = 'N/A'
    
    if last_run and last_run != 'N/A':
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
            formatted_last = dt.strftime('%d/%m/%Y %H:%M')
        except:
            formatted_last = last_run
    else:
        formatted_last = 'Jamais exécutée'
    
    text = f"""📋 **Détails de la tâche**

🆔 **ID :** {task_id}
📝 **Nom :** {name}
🤖 **Agent :** {agent}
📊 **Statut :** {status}
🔄 **Récurrence :** {schedule}
⏰ **Prochaine exécution :** {formatted_next}
📅 **Dernière exécution :** {formatted_last}
🎯 **Priorité :** {priority}

⚙️ **Paramètres :**
{format_task_parameters(params)}
"""
    
    return text

def format_task_parameters(params: Dict) -> str:
    """Formate les paramètres d'une tâche"""
    if not params:
        return "   • Aucun paramètre"
    
    text = ""
    for key, value in params.items():
        text += f"   • {key}: {value}\n"
    
    return text.strip()

def format_agent_capabilities() -> str:
    """Formate les capacités de chaque agent pour la création de tâches"""
    capabilities = {
        "MessagingAgent": [
            "send_message", "send_bulk_messages", "create_message_template",
            "schedule_follow_up", "auto_contact"
        ],
        "ProspectionSupervisor": [
            "start_prospection", "monitor_campaigns", "daily_report",
            "performance_analysis", "lead_qualification"
        ],
        "PivotStrategyAgent": [
            "analyze_strategy", "suggest_pivot", "market_analysis",
            "strategy_optimization", "competitor_analysis"
        ],
        "TaskWatchdogAgent": [
            "monitor_tasks", "security_check", "system_health",
            "alert_management", "log_analysis"
        ],
        "ScrapingSupervisorAgent": [
            "start_scraping", "monitor_scraping", "quality_check",
            "data_validation", "source_management"
        ],
        "ResponseInterpreterAgent": [
            "interpret_response", "sentiment_analysis", "follow_up_decision",
            "lead_scoring", "response_categorization"
        ]
    }
    
    text = "🤖 **Capacités des agents**\n\n"
    
    for agent_name, actions in capabilities.items():
        text += f"**{agent_name}:**\n"
        for action in actions:
            text += f"   • {action}\n"
        text += "\n"
    
    return text

def format_services_status(services: Dict) -> str:
    """Formate l'état des services"""
    if not services:
        return "ℹ️ Aucun service trouvé"
    
    text = "🔧 **État des services**\n\n"
    
    for service_name, service_info in services.items():
        status = service_info.get('status', 'unknown')
        uptime = service_info.get('uptime', 'N/A')
        raw_status = service_info.get('raw_status', '')
        
        # Emoji selon le statut réel
        if status == 'active':
            status_emoji = EMOJIS['active']
            status_text = "Actif"
        elif status == 'failing':
            status_emoji = '🔄'
            status_text = f"En redémarrage ({raw_status})"
        else:
            status_emoji = EMOJIS['inactive']
            status_text = "Inactif"
        
        text += f"{status_emoji} **{service_name}** - {status_text}\n"
        text += f"   ⏱️ Uptime : {uptime}\n\n"
    
    return text

def truncate_text(text: str, max_length: int = 4000) -> str:
    """Tronque le texte si trop long pour Telegram"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length-50] + "\n\n... (message tronqué)"

def format_error(error_msg: str) -> str:
    """Formate un message d'erreur - CORRECTION ANTI-PARSING"""
    # Échapper tous les caractères Markdown pour éviter les erreurs de parsing
    safe_msg = str(error_msg).replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace('`', '\\`').replace('(', '\\(').replace(')', '\\)')
    return f"❌ Erreur\n\n{safe_msg}"

def format_success(message: str) -> str:
    """Formate un message de succès - CORRECTION ANTI-PARSING"""
    # Échapper tous les caractères Markdown pour éviter les erreurs de parsing
    safe_msg = str(message).replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace('`', '\\`').replace('(', '\\(').replace(')', '\\)')
    return f"✅ Succès\n\n{safe_msg}"

def format_loading() -> str:
    """Message de chargement"""
    return f"{EMOJIS['loading']} Chargement en cours..."

def format_clients_list(clients: List[Dict]) -> str:
    """Formate la liste des clients pour facturation"""
    if not clients:
        return "ℹ️ Aucun client trouvé"
    
    text = f"👥 **Clients pour facturation ({len(clients)})**\n\n"
    
    for i, client in enumerate(clients[:10], 1):
        # Construire le nom du client
        name = f"{client.get('first_name', '')} {client.get('last_name', '')}".strip()
        if not name:
            name = client.get('email', f'Client {client.get("id")}')
        
        company = client.get('company', '')
        email = client.get('email', 'N/A')
        
        text += f"{i}️⃣ **{name}**\n"
        if company:
            text += f"   🏢 {company}\n"
        text += f"   📧 {email}\n"
        
        # Vérifier s'il a des infos de facturation
        if client.get('billing_address') or client.get('billing_city'):
            text += f"   ✅ Infos facturation\n"
        else:
            text += f"   ⚠️ Infos facturation manquantes\n"
        text += "\n"
    
    if len(clients) > 10:
        text += f"... et {len(clients) - 10} autres clients\n"
    
    return text

from fastapi import APIRouter
from app.api.endpoints import stats, dashboard, logs, logs_detailed, system_logs, niches, campaigns, leads, leads_stats, leads_management, campaigns_management, agents, agents_detailed, messages, system_settings, services, env_settings, tasks, sandbox, messenger, meetings, conversations, meeting_webhooks, conversions, billing, stripe_webhooks
from app.routes import health

api_router = APIRouter()

# Endpoint de santé (health check)
api_router.include_router(health.router, prefix="", tags=["health"])

# Les endpoints statiques et non dynamiques d'abord
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(logs_detailed.router, prefix="/logs-extended", tags=["logs"])
api_router.include_router(system_logs.router, prefix="/system-logs", tags=["system-logs"])

# Endpoints spécifiques pour les statistiques de leads (doivent être avant /leads)
api_router.include_router(leads_stats.router, prefix="/leads", tags=["leads"])

# Nouveaux endpoints de gestion
api_router.include_router(leads_management.router, prefix="/leads-management", tags=["leads-management"])
api_router.include_router(campaigns_management.router, prefix="/campaigns-management", tags=["campaigns-management"])

# Les endpoints principaux
api_router.include_router(niches.router, prefix="/niches", tags=["niches"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(conversions.router, prefix="/conversions", tags=["conversions"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(agents_detailed.router, prefix="/agents-extended", tags=["agents"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])

# Endpoint de gestion des tâches planifiées
api_router.include_router(tasks.router, prefix="", tags=["tasks"])

# Endpoints pour paramètres système et services
api_router.include_router(system_settings.router, prefix="/system", tags=["system"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(env_settings.router, prefix="/system", tags=["system"])

# Endpoint sandbox pour les tests de messagerie
api_router.include_router(sandbox.router, prefix="/sandbox", tags=["sandbox"])

# Endpoint messenger pour les directives
api_router.include_router(messenger.router, prefix="/messenger", tags=["messenger"])

# Endpoints pour webhooks meetings
api_router.include_router(meeting_webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Endpoints pour la facturation
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])

# Endpoints pour les webhooks Stripe et notifications
api_router.include_router(stripe_webhooks.router, prefix="", tags=["webhooks", "stripe"])

from fastapi import APIRouter
from app.api.endpoints import stats, dashboard, logs, logs_detailed, system_logs, niches, campaigns, leads, agents, agents_detailed, messages, system_settings, services, env_settings, tasks

api_router = APIRouter()

# Les endpoints statiques et non dynamiques d'abord
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(logs_detailed.router, prefix="/logs-extended", tags=["logs"])
api_router.include_router(system_logs.router, prefix="/system-logs", tags=["system-logs"])

# Les endpoints principaux
api_router.include_router(niches.router, prefix="/niches", tags=["niches"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(agents_detailed.router, prefix="/agents-extended", tags=["agents"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])

# Endpoint de gestion des tâches planifiées
api_router.include_router(tasks.router, prefix="", tags=["tasks"])

# Endpoints pour paramètres système et services
api_router.include_router(system_settings.router, prefix="/system", tags=["system"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(env_settings.router, prefix="/system", tags=["system"])

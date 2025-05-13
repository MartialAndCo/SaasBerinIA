from fastapi import APIRouter

from app.api.endpoints import stats, leads, campaigns, niches, logs

api_router = APIRouter()

api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(niches.router, prefix="/niches", tags=["niches"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"]) 
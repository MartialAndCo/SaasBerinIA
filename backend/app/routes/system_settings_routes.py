from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.services.system_settings_service import SystemSettingsService
from app.database.session import get_db

router = APIRouter(prefix="/system-settings", tags=["System Settings"])

@router.post("/integrations")
def update_integrations(
    data: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """
    Update system integration settings
    Accepts any key from SystemIntegrations model
    """
    try:
        service = SystemSettingsService(db)
        updated_settings = service.update_integrations(**data)
        return {"status": "success", "data": updated_settings}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/scheduling")
def update_scheduling(
    data: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """
    Update system scheduling settings
    Accepts any key from SystemScheduling model
    """
    try:
        service = SystemSettingsService(db)
        updated_settings = service.update_scheduling(**data)
        return {"status": "success", "data": updated_settings}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/integrations")
def get_integrations(
    db: Session = Depends(get_db)
):
    """
    Retrieve current integration settings
    """
    try:
        service = SystemSettingsService(db)
        settings = service.get_integrations()
        return {"status": "success", "data": settings}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/scheduling")
def get_scheduling(
    db: Session = Depends(get_db)
):
    """
    Retrieve current scheduling settings
    """
    try:
        service = SystemSettingsService(db)
        settings = service.get_scheduling()
        return {"status": "success", "data": settings}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

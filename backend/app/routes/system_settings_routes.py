from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import subprocess
import json

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

@router.get("/services")
def get_services_status():
    """
    Retrieve status of all BerinIA services
    """
    try:
        services = [
            "berinia-api.service",
            "berinia-next.service", 
            "berinia-webhook.service",
            "berinia-whatsapp.service",
            "berinia-qdrant.service",
            "berinia-agents.service",
            "berinia-scheduler.service"
        ]
        
        services_status = []
        
        for service_name in services:
            try:
                # Vérifier le statut du service avec systemctl
                result = subprocess.run(
                    ["systemctl", "is-active", service_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                status = "active" if result.stdout.strip() == "active" else "inactive"
                
                # Récupérer l'uptime si le service est actif
                uptime = None
                if status == "active":
                    try:
                        uptime_result = subprocess.run(
                            ["systemctl", "show", service_name, "--property=ActiveEnterTimestamp"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if uptime_result.returncode == 0:
                            timestamp_line = uptime_result.stdout.strip()
                            if "=" in timestamp_line:
                                uptime = timestamp_line.split("=", 1)[1]
                    except Exception:
                        uptime = "N/A"
                
                services_status.append({
                    "name": service_name,
                    "status": status,
                    "uptime": uptime
                })
                
            except Exception as e:
                # En cas d'erreur pour un service spécifique, le marquer comme erreur
                services_status.append({
                    "name": service_name,
                    "status": "error",
                    "uptime": None
                })
        
        return {"status": "success", "data": services_status}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du statut des services: {str(e)}")

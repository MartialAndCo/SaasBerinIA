from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import subprocess
import logging
import os
import traceback
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.services.system_settings_service import SystemSettingsService
from app.api import deps

logger = logging.getLogger(__name__)

# Modèles Pydantic pour les nouveaux endpoints
class ServiceStatus(BaseModel):
    name: str
    status: str
    uptime: Optional[str] = None

class ServicesList(BaseModel):
    status: str
    data: List[ServiceStatus]

class ServiceControlData(BaseModel):
    success: bool
    service: str
    action: str
    error: Optional[str] = None

class ServiceControlResponse(BaseModel):
    status: str
    data: ServiceControlData

router = APIRouter()

@router.post("/integrations")
def update_integrations(
    data: Dict[str, Any], 
    db: Session = Depends(deps.get_db)
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
    db: Session = Depends(deps.get_db)
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
    db: Session = Depends(deps.get_db)
):
    """
    Retrieve current integration settings
    """
    try:
        logger.info("Récupération des paramètres d'intégration")
        service = SystemSettingsService(db)
        settings = service.get_integrations()
        logger.info(f"Paramètres récupérés: {settings}")
        return {"status": "success", "data": settings}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des paramètres d'intégration: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/scheduling")
def get_scheduling(
    db: Session = Depends(deps.get_db)
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

# Endpoints spécifiques pour Instantly.ai
@router.get("/integrations/instantly")
def get_instantly_settings(
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les paramètres d'intégration Instantly.ai
    """
    try:
        service = SystemSettingsService(db)
        integrations = service.get_integrations()

        # Filtrer uniquement les paramètres Instantly
        instantly_settings = {
            "instantly_api_key": integrations.get("instantly_api_key", None),
            "instantly_integration_active": integrations.get("instantly_integration_active", False)
        }

        return {"status": "success", "data": instantly_settings}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des paramètres Instantly.ai: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/integrations/instantly")
def update_instantly_settings(
    data: Dict[str, Any],
    db: Session = Depends(deps.get_db)
):
    """
    Met à jour les paramètres d'intégration Instantly.ai
    """
    try:
        service = SystemSettingsService(db)
        updated_settings = service.update_integrations(**data)
        
        # Si succès et que le service webhook est actif, le redémarrer
        if data.get("instantly_integration_active", False):
            try:
                subprocess.run(["sudo", "systemctl", "restart", "berinia-webhook.service"], check=True)
                logger.info("Service webhook redémarré avec succès après mise à jour des paramètres Instantly.ai")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Impossible de redémarrer le service webhook: {str(e)}")
                return {
                    "status": "warning",
                    "data": updated_settings,
                    "message": "Paramètres mis à jour mais erreur lors du redémarrage du service webhook"
                }
        
        return {"status": "success", "data": updated_settings}
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des paramètres Instantly.ai: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Endpoints spécifiques pour WhatsApp
@router.get("/integrations/whatsapp")
def get_whatsapp_settings(
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les paramètres d'intégration WhatsApp
    """
    try:
        service = SystemSettingsService(db)
        integrations = service.get_integrations()
        
        # Filtrer uniquement les paramètres WhatsApp
        whatsapp_settings = {
            "whatsapp_integration_active": integrations.get("whatsapp_integration_active", False),
            "whatsapp_notification_group": integrations.get("whatsapp_notification_group", None)
        }
        
        # Vérifier si le service WhatsApp est actif
        try:
            status_cmd = subprocess.run(
                ['systemctl', 'is-active', 'berinia-whatsapp.service'],
                capture_output=True, text=True, check=False
            )
            whatsapp_settings["service_active"] = status_cmd.stdout.strip() == "active"
        except Exception:
            whatsapp_settings["service_active"] = False
        
        return {"status": "success", "data": whatsapp_settings}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des paramètres WhatsApp: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/integrations/whatsapp")
def update_whatsapp_settings(
    data: Dict[str, Any],
    db: Session = Depends(deps.get_db)
):
    """
    Met à jour les paramètres d'intégration WhatsApp
    """
    try:
        service = SystemSettingsService(db)
        updated_settings = service.update_integrations(**data)
        
        # Si succès et qu'on active/désactive l'intégration, redémarrer le service
        if "whatsapp_integration_active" in data:
            action = "restart" if data["whatsapp_integration_active"] else "stop"
            try:
                subprocess.run(["sudo", "systemctl", action, "berinia-whatsapp.service"], check=True)
                logger.info(f"Service WhatsApp {action} avec succès")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Impossible de {action} le service WhatsApp: {str(e)}")
                return {
                    "status": "warning",
                    "data": updated_settings,
                    "message": f"Paramètres mis à jour mais erreur lors du {action} du service WhatsApp"
                }
        
        return {"status": "success", "data": updated_settings}
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des paramètres WhatsApp: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint pour récupérer le statut des services système
@router.get("/services", response_model=ServicesList)
def get_services_status():
    """
    Récupère le statut des services système (qdrant, webhook, agents)
    """
    try:
        services = []
        monitored_services = [
            "berinia-api.service",
            "berinia-next.service", 
            "berinia-webhook.service",
            "berinia-whatsapp.service",
            "berinia-qdrant.service", 
            "berinia-agents.service",
            "berinia-scheduler.service"
        ]
        
        for service_name in monitored_services:
            # Vérifier si le service est actif
            status_cmd = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True, text=True, check=False
            )
            status = status_cmd.stdout.strip()
            
            # Par défaut
            service_info = {
                "name": service_name,
                "status": "active" if status == "active" else "inactive",
            }
            
            # Si le service est actif, récupérer son uptime
            if status == "active":
                try:
                    # Récupérer le timestamp d'activation
                    time_cmd = subprocess.run(
                        ['systemctl', 'show', service_name, '--property=ActiveEnterTimestamp'],
                        capture_output=True, text=True, check=False
                    )
                    
                    # Extraire la date de la sortie (format: ActiveEnterTimestamp=Thu 2025-05-15 10:05:33 UTC)
                    timestamp_str = time_cmd.stdout.strip().split('=')[1]
                    
                    # Convertir en datetime
                    formats_to_try = [
                        "%a %Y-%m-%d %H:%M:%S %Z",   # Format standard
                        "%Y-%m-%d %H:%M:%S %Z"       # Format alternatif
                    ]
                    
                    active_time = None
                    for fmt in formats_to_try:
                        try:
                            active_time = datetime.strptime(timestamp_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if active_time:
                        # Calculer l'uptime
                        now = datetime.now()
                        delta = now - active_time
                        
                        # Formater l'uptime
                        days = delta.days
                        hours, remainder = divmod(delta.seconds, 3600)
                        minutes = remainder // 60
                        
                        service_info["uptime"] = f"{days}j {hours}h {minutes}m"
                except Exception as e:
                    logger.warning(f"Erreur lors de la récupération de l'uptime pour {service_name}: {str(e)}")
                    service_info["uptime"] = "inconnu"
            
            services.append(service_info)
        
        return {"status": "success", "data": services}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut des services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint pour contrôler les services système
@router.post("/service-control", response_model=ServiceControlResponse)
def control_service(data: Dict[str, str]):
    """
    Contrôle un service système (démarrer/arrêter/redémarrer)
    
    Paramètres:
    - service: Nom du service (berinia-qdrant.service, berinia-webhook.service, berinia-agents.service)
    - action: Action à effectuer (start, stop, restart)
    """
    try:
        service_name = data.get("service")
        action = data.get("action")
        
        # Validation
        if not service_name:
            raise HTTPException(status_code=400, detail="Le nom du service est requis")
            
        if action not in ["start", "stop", "restart"]:
            raise HTTPException(status_code=400, detail="Action invalide. Utilisez start, stop ou restart")
            
        # Contrôle de sécurité pour empêcher l'exécution de commandes arbitraires
        allowed_services = [
            "berinia-api.service",
            "berinia-next.service", 
            "berinia-webhook.service",
            "berinia-whatsapp.service",
            "berinia-qdrant.service", 
            "berinia-agents.service",
            "berinia-scheduler.service"
        ]
        
        if service_name not in allowed_services:
            raise HTTPException(status_code=403, detail=f"Service non autorisé: {service_name}")
        
        # Exécuter la commande
        subprocess.run(["sudo", "systemctl", action, service_name], check=True)
        
        logger.info(f"Service {service_name} {action} avec succès")
        
        return {
            "status": "success", 
            "data": {
                "success": True,
                "service": service_name,
                "action": action
            }
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'action {action} sur {service_name}: {e}")
        return {
            "status": "error",
            "data": {
                "success": False,
                "service": service_name,
                "action": action,
                "error": str(e)
            }
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'action {action} sur {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

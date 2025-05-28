from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional

from app.api import deps
from app.services.services_service import ServicesService

router = APIRouter()

@router.get("/")
def get_all_services(
    db: Session = Depends(deps.get_db)
):
    """
    Liste tous les services systemd gérés par BerinIA
    """
    try:
        service = ServicesService(db)
        return {"status": "success", "data": service.get_all_services()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{service_name}")
def get_service_details(
    service_name: str = Path(..., description="Nom du service"),
    db: Session = Depends(deps.get_db)
):
    """
    Obtient les détails d'un service spécifique
    """
    try:
        service = ServicesService(db)
        return {"status": "success", "data": service.get_service_status(service_name)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{service_name}/action")
def service_action(
    service_name: str = Path(..., description="Nom du service"),
    action: str = Query(..., description="Action à effectuer (start, stop, restart, enable, disable)"),
    db: Session = Depends(deps.get_db)
):
    """
    Exécute une action sur un service (start, stop, restart, enable, disable)
    """
    try:
        if action not in ["start", "stop", "restart", "enable", "disable"]:
            raise HTTPException(status_code=400, detail=f"Action non valide: {action}")
            
        service = ServicesService(db)
        result = service.execute_action(service_name, action)
        
        if result["success"]:
            return {"status": "success", "data": result}
        else:
            return {"status": "error", "message": result["message"], "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{service_name}/logs")
def get_service_logs(
    service_name: str = Path(..., description="Nom du service"),
    lines: int = Query(50, description="Nombre de lignes à récupérer"),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les logs d'un service
    """
    try:
        service = ServicesService(db)
        result = service.get_service_logs(service_name, lines)
        
        if result["success"]:
            return {"status": "success", "data": result}
        else:
            return {"status": "error", "message": result["message"], "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/overview", response_model=schemas.OverviewStats)
def get_overview_stats(db: Session = Depends(deps.get_db)):
    """
    Récupère les statistiques générales pour le dashboard
    """
    # Récupérer les leads collectés
    total_leads = crud.lead.count(db)
    leads_last_month = crud.lead.count_by_period(
        db, 
        start_date=(datetime.now() - timedelta(days=60)),
        end_date=(datetime.now() - timedelta(days=30))
    )
    leads_this_month = crud.lead.count_by_period(
        db, 
        start_date=(datetime.now() - timedelta(days=30)),
        end_date=datetime.now()
    )
    
    leads_change = 0
    if leads_last_month > 0:
        leads_change = ((leads_this_month - leads_last_month) / leads_last_month) * 100
    
    # Récupérer le taux de conversion
    current_conversion = crud.campaign.get_average_conversion(db)
    last_month_conversion = crud.campaign.get_average_conversion(
        db, 
        start_date=(datetime.now() - timedelta(days=60)),
        end_date=(datetime.now() - timedelta(days=30))
    )
    
    conversion_change = 0
    if last_month_conversion > 0:
        conversion_change = ((current_conversion - last_month_conversion) / last_month_conversion) * 100
    
    # Récupérer le taux d'ouverture (simulé)
    current_open_rate = 24.5
    last_month_open_rate = 20.2
    
    open_rate_change = 0
    if last_month_open_rate > 0:
        open_rate_change = ((current_open_rate - last_month_open_rate) / last_month_open_rate) * 100
    
    # Récupérer le coût par lead
    current_cost = crud.niche.get_average_cost_per_lead(db)
    last_month_cost = crud.niche.get_average_cost_per_lead(
        db, 
        start_date=(datetime.now() - timedelta(days=60)),
        end_date=(datetime.now() - timedelta(days=30))
    )
    
    cost_change = 0
    if last_month_cost > 0:
        cost_change = ((current_cost - last_month_cost) / last_month_cost) * 100
    
    return {
        "leadsCollected": {
            "value": total_leads,
            "change": round(leads_change, 1),
            "trend": "up" if leads_change >= 0 else "down"
        },
        "conversionRate": {
            "value": round(current_conversion, 1),
            "change": round(conversion_change, 1),
            "trend": "up" if conversion_change >= 0 else "down"
        },
        "openRate": {
            "value": current_open_rate,
            "change": round(open_rate_change, 1),
            "trend": "up" if open_rate_change >= 0 else "down"
        },
        "costPerLead": {
            "value": round(current_cost, 2),
            "change": round(cost_change, 1),
            "trend": "down" if cost_change <= 0 else "up"
        }
    }


@router.get("/conversion", response_model=List[Dict[str, Any]])
def get_conversion_stats(
    period: str = Query("30d", description="Période (7d, 30d, 90d, 1y)"),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les données de conversion pour le graphique
    """
    days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }.get(period, 30)
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Récupérer les données de conversion par jour
    conversion_data = crud.campaign.get_conversion_by_day(db, start_date)
    
    # Formater les données pour le frontend
    result = []
    current_date = start_date
    while current_date <= datetime.now():
        date_str = current_date.strftime("%Y-%m-%d")
        value = next((item["value"] for item in conversion_data if item["date"] == date_str), 0)
        result.append({
            "date": date_str,
            "value": value
        })
        current_date += timedelta(days=1)
    
    return result


@router.get("/leads", response_model=List[Dict[str, Any]])
def get_leads_stats(
    period: str = Query("30d", description="Période (7d, 30d, 90d, 1y)"),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les données de leads pour le graphique
    """
    days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }.get(period, 30)
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Récupérer les données de leads par jour
    leads_data = crud.lead.get_leads_by_day(db, start_date)
    
    # Formater les données pour le frontend
    result = []
    current_date = start_date
    while current_date <= datetime.now():
        date_str = current_date.strftime("%Y-%m-%d")
        value = next((item["value"] for item in leads_data if item["date"] == date_str), 0)
        result.append({
            "date": date_str,
            "value": value
        })
        current_date += timedelta(days=1)
    
    return result


@router.get("/campaigns", response_model=List[Dict[str, Any]])
def get_campaigns_stats(
    period: str = Query("30d", description="Période (7d, 30d, 90d, 1y)"),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les données de comparaison des campagnes
    """
    days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }.get(period, 30)
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Récupérer les données des campagnes
    campaigns = crud.campaign.get_multi_with_stats(db, start_date=start_date)
    
    # Formater les données pour le frontend
    result = []
    for campaign in campaigns:
        result.append({
            "name": campaign.name,
            "leads": campaign.leads_count,
            "conversion": campaign.conversion_rate
        })
    
    return result


@router.get("/niches", response_model=List[Dict[str, Any]])
def get_niches_stats(
    period: str = Query("30d", description="Période (7d, 30d, 90d, 1y)"),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les données de comparaison des niches
    """
    days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }.get(period, 30)
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Récupérer les données des niches
    niches = crud.niche.get_multi_with_stats(db, start_date=start_date)
    
    # Formater les données pour le frontend
    result = []
    for niche in niches:
        result.append({
            "name": niche.nom,
            "conversion": niche.taux_conversion,
            "cost": niche.cout_par_lead,
            "leads": niche.leads_count
        })
    
    return result


@router.get("/period", response_model=Dict[str, Any])
def get_stats_by_period(
    from_date: str = Query(..., description="Date de début (YYYY-MM-DD)"),
    to_date: str = Query(..., description="Date de fin (YYYY-MM-DD)"),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les statistiques pour une période spécifique
    """
    try:
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD")
    
    # Récupérer les statistiques pour la période
    leads_count = crud.lead.count_by_period(db, start_date, end_date)
    conversion_rate = crud.campaign.get_average_conversion(db, start_date, end_date)
    cost_per_lead = crud.niche.get_average_cost_per_lead(db, start_date, end_date)
    
    return {
        "period": {
            "from": from_date,
            "to": to_date
        },
        "stats": {
            "leads": leads_count,
            "conversion": round(conversion_rate, 1),
            "costPerLead": round(cost_per_lead, 2)
        }
    } 
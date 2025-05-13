from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api import deps
from app.models.lead import Lead as LeadModel
from app.schemas.lead import Lead, LeadCreate, LeadUpdate, VisualAnalysisCreate, VisualAnalysisUpdate
from app.crud.lead import update_lead_visual_analysis, create_visual_analysis

# Remplacer
router = APIRouter(tags=["Leads"])

@router.get("/", response_model=List[Lead])
def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = Query(None),
    statut: Optional[str] = Query(None),
    campagne_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère la liste des leads avec filtres optionnels
    """
    # Construire la requête de base
    query = db.query(LeadModel)
    
    # Appliquer les filtres
    if search:
        query = query.filter(
            (LeadModel.nom.ilike(f"%{search}%")) | 
            (LeadModel.email.ilike(f"%{search}%")) |
            (LeadModel.telephone.ilike(f"%{search}%"))
        )
    
    if statut:
        query = query.filter(LeadModel.statut == statut)
    
    if campagne_id:
        query = query.filter(LeadModel.campagne_id == campagne_id)
    
    # Exécuter la requête avec pagination
    leads = query.offset(skip).limit(limit).all()
    return leads

@router.post("/", response_model=Lead, status_code=status.HTTP_201_CREATED)
def create_lead(lead: LeadCreate, db: Session = Depends(deps.get_db)):
    """
    Crée un nouveau lead
    """
    db_lead = LeadModel(
        nom=lead.nom,
        email=lead.email,
        telephone=lead.telephone,
        entreprise=lead.entreprise,
        statut=lead.statut,
        campagne_id=lead.campagne_id
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@router.get("/{lead_id}", response_model=Lead)
def get_lead(lead_id: int, db: Session = Depends(deps.get_db)):
    """
    Récupère un lead spécifique par son ID
    """
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.put("/{lead_id}", response_model=Lead)
def update_lead(lead_id: int, lead: LeadUpdate, db: Session = Depends(deps.get_db)):
    """
    Met à jour un lead existant
    """
    db_lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    update_data = lead.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_lead, key, value)
    
    db.commit()
    db.refresh(db_lead)
    return db_lead

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(deps.get_db)):
    """
    Supprime un lead
    """
    db_lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    db.delete(db_lead)
    db.commit()
    return None

@router.get("/export", status_code=status.HTTP_200_OK)
def export_leads(
    campagne_id: Optional[int] = Query(None),
    format: str = Query("csv", regex="^(csv|excel)$"),
    db: Session = Depends(deps.get_db)
):
    """
    Exporte les leads au format CSV ou Excel
    """
    # Construire la requête
    query = db.query(LeadModel)
    
    if campagne_id:
        query = query.filter(LeadModel.campagne_id == campagne_id)
    
    leads = query.all()
    
    # Ici, vous implémenteriez la logique d'export réelle
    # Pour l'instant, nous retournons juste un message de succès
    return {"message": f"{len(leads)} leads exportés au format {format}"}

# Endpoints pour l'analyse visuelle

@router.post("/{lead_id}/visual-analysis", response_model=Lead)
def add_visual_analysis(
    lead_id: int, 
    analysis: VisualAnalysisCreate, 
    db: Session = Depends(deps.get_db)
):
    """
    Ajoute une analyse visuelle à un lead existant
    """
    # Vérifier que le lead existe
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Définir l'ID du lead dans l'analyse
    analysis.lead_id = lead_id
    
    # Créer l'analyse visuelle
    updated_lead = create_visual_analysis(db, analysis)
    if not updated_lead:
        raise HTTPException(status_code=500, detail="Failed to create visual analysis")
    
    return updated_lead

@router.put("/{lead_id}/visual-analysis", response_model=Lead)
def update_visual_analysis(
    lead_id: int, 
    analysis: VisualAnalysisUpdate, 
    db: Session = Depends(deps.get_db)
):
    """
    Met à jour l'analyse visuelle d'un lead existant
    """
    # Vérifier que le lead existe
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Mettre à jour l'analyse visuelle
    updated_lead = update_lead_visual_analysis(db, lead_id, analysis)
    if not updated_lead:
        raise HTTPException(status_code=500, detail="Failed to update visual analysis")
    
    return updated_lead

@router.post("/{lead_id}/upload-screenshot", response_model=Lead)
async def upload_screenshot(
    lead_id: int,
    screenshot_type: str = Query(..., regex="^(original|enhanced)$"),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db)
):
    """
    Télécharge une capture d'écran pour un lead
    """
    # Vérifier que le lead existe
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Vérifier que le fichier est une image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Définir le chemin de sauvegarde
    import os
    from pathlib import Path
    
    # Créer les répertoires nécessaires
    screenshots_dir = Path("screenshots")
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    
    # Générer un nom de fichier unique
    file_extension = os.path.splitext(file.filename)[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{lead_id}_{screenshot_type}_{timestamp}{file_extension}"
    filepath = screenshots_dir / filename
    
    # Enregistrer le fichier
    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())
    
    # Mettre à jour le chemin dans la base de données
    if screenshot_type == "original":
        lead.screenshot_path = str(filepath)
    else:
        lead.enhanced_screenshot_path = str(filepath)
    
    db.commit()
    db.refresh(lead)
    
    return lead

@router.get("/visual-analysis", response_model=List[Lead])
def get_leads_with_visual_analysis(
    min_score: Optional[int] = Query(None, ge=0, le=100),
    has_popup: Optional[bool] = Query(None),
    site_type: Optional[str] = Query(None),
    min_quality: Optional[int] = Query(None, ge=0, le=10),
    maturity: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db)
):
    """
    Récupère les leads avec filtrage sur les critères d'analyse visuelle
    """
    # Construire la requête de base
    query = db.query(LeadModel).filter(LeadModel.visual_analysis_date.isnot(None))
    
    # Appliquer les filtres
    if min_score is not None:
        query = query.filter(LeadModel.visual_score >= min_score)
    
    if has_popup is not None:
        query = query.filter(LeadModel.has_popup == has_popup)
    
    if site_type:
        query = query.filter(LeadModel.site_type == site_type)
    
    if min_quality is not None:
        query = query.filter(LeadModel.visual_quality >= min_quality)
    
    if maturity:
        query = query.filter(LeadModel.website_maturity == maturity)
    
    # Exécuter la requête
    leads = query.all()
    return leads

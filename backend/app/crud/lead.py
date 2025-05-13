from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, VisualAnalysisCreate, VisualAnalysisUpdate
from datetime import datetime

def create_lead(db: Session, lead: LeadCreate) -> Lead:
    db_lead = Lead(
        nom=lead.nom,
        email=lead.email,
        telephone=lead.telephone,
        statut=lead.statut,
        campagne_id=lead.campagne_id
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

def get_leads(db: Session):
    return db.query(Lead).all()

def get_lead(db: Session, lead_id: int):
    return db.query(Lead).filter(Lead.id == lead_id).first()

def update_lead_visual_analysis(db: Session, lead_id: int, analysis: VisualAnalysisUpdate):
    db_lead = get_lead(db, lead_id)
    if db_lead:
        for key, value in analysis.dict(exclude_unset=True).items():
            setattr(db_lead, key, value)
        
        # Toujours mettre à jour la date d'analyse
        db_lead.visual_analysis_date = datetime.utcnow()
        
        db.commit()
        db.refresh(db_lead)
    return db_lead

def create_visual_analysis(db: Session, analysis: VisualAnalysisCreate):
    db_lead = get_lead(db, analysis.lead_id)
    if db_lead:
        for key, value in analysis.dict(exclude_unset=True, exclude={"lead_id"}).items():
            setattr(db_lead, key, value)
        
        db.commit()
        db.refresh(db_lead)
    return db_lead

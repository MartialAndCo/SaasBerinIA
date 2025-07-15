#!/usr/bin/env python3
"""
Script pour vérifier le nombre de leads dans la base de données
et confirmer la séparation entre leads normaux et sandbox
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Ajouter le répertoire backend au path Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d'environnement
load_dotenv()

from app.models.lead import Lead
from app.models.sandbox import SandboxLead
from app.database.base import Base

# Configuration de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://berinia_user:berinia_pass@localhost/berinia")

# Créer le moteur et la session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_leads():
    """Vérifier le nombre et la répartition des leads"""
    db = SessionLocal()
    
    try:
        # Compter les leads normaux
        normal_leads_count = db.query(func.count(Lead.id)).scalar()
        print(f"✅ Nombre de leads normaux (table 'leads'): {normal_leads_count}")
        
        # Compter les leads sandbox
        sandbox_leads_count = db.query(func.count(SandboxLead.id)).scalar()
        print(f"📦 Nombre de leads sandbox (table 'sandbox_leads'): {sandbox_leads_count}")
        
        # Afficher les 5 derniers leads normaux
        print("\n📋 Les 5 derniers leads normaux:")
        recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(5).all()
        for lead in recent_leads:
            print(f"  - {lead.id}: {lead.first_name} {lead.last_name or ''} ({lead.email}) - Créé le: {lead.created_at}")
        
        # Afficher les 5 derniers leads sandbox
        print("\n📦 Les 5 derniers leads sandbox:")
        recent_sandbox = db.query(SandboxLead).order_by(SandboxLead.created_at.desc()).limit(5).all()
        for lead in recent_sandbox:
            print(f"  - {lead.id}: {lead.first_name} {lead.last_name or ''} ({lead.email}) - Test: {lead.is_test}")
        
        # Vérifier les statuts des leads normaux
        print("\n📊 Répartition des statuts (leads normaux):")
        status_counts = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
        for status, count in status_counts:
            print(f"  - {status}: {count} leads")
        
        # Vérifier les leads avec analyse visuelle
        visual_leads = db.query(func.count(Lead.id)).filter(Lead.visual_score.isnot(None)).scalar()
        print(f"\n👁️ Leads avec analyse visuelle: {visual_leads}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 Vérification des leads dans la base de données...\n")
    verify_leads()
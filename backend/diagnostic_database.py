#!/usr/bin/env python3
"""
Script de diagnostic pour analyser la base de données BerinIA
PHASE 1 : Diagnostic complet
"""

import os
import sys
sys.path.append("/root/berinia/backend")

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.api.deps import get_db
from app.models.lead import Lead
from app.models.campaign import Campaign  
from app.models.agent import Agent
from app.models.niche import Niche
from app.models.message import Message

def diagnostic_leads(db: Session):
    """Diagnostic des leads"""
    print("=" * 50)
    print("📊 DIAGNOSTIC LEADS")
    print("=" * 50)
    
    total_leads = db.query(Lead).count()
    print(f"Total leads: {total_leads}")
    
    # Statuts réels utilisés
    statuts = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    print("\n📋 Statuts utilisés:")
    for statut, count in statuts:
        print(f"  - {statut}: {count} leads")
    
    # Leads par campagne  
    print("\n🎯 Leads par campagne:")
    leads_par_campagne = db.query(Lead.campagne_id, func.count(Lead.id)).group_by(Lead.campagne_id).all()
    for campagne_id, count in leads_par_campagne:
        print(f"  - Campagne {campagne_id}: {count} leads")
    
    # Leads récents
    leads_recents = db.query(Lead).filter(Lead.created_at.isnot(None)).order_by(Lead.created_at.desc()).limit(5).all()
    print(f"\n📅 Derniers leads créés:")
    for lead in leads_recents:
        print(f"  - {lead.first_name} {lead.last_name or ''} ({lead.status}) - {lead.created_at}")

def diagnostic_campaigns(db: Session):
    """Diagnostic des campagnes"""
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSTIC CAMPAGNES")
    print("=" * 50)
    
    total_campaigns = db.query(Campaign).count()
    print(f"Total campagnes: {total_campaigns}")
    
    # Statuts réels utilisés
    statuts = db.query(Campaign.status, func.count(Campaign.id)).group_by(Campaign.status).all()
    print("\n📋 Statuts utilisés:")
    for statut, count in statuts:
        print(f"  - {statut}: {count} campagnes")
    
    # Détail des campagnes
    campaigns = db.query(Campaign).all()
    print(f"\n📄 Détail des campagnes:")
    for campaign in campaigns:
        leads_count = db.query(Lead).filter(Lead.campagne_id == campaign.id).count()
        print(f"  - {campaign.name} (ID: {campaign.id}) - Status: {campaign.status} - {leads_count} leads")

def diagnostic_messages(db: Session):
    """Diagnostic des messages et réponses"""
    print("\n" + "=" * 50)
    print("💬 DIAGNOSTIC MESSAGES")
    print("=" * 50)
    
    total_messages = db.query(Message).count()
    print(f"Total messages: {total_messages}")
    
    # Statuts des messages
    statuts = db.query(Message.status, func.count(Message.id)).group_by(Message.status).all()
    print("\n📋 Statuts des messages:")
    for statut, count in statuts:
        print(f"  - {statut}: {count} messages")
    
    # Direction des messages
    directions = db.query(Message.direction, func.count(Message.id)).group_by(Message.direction).all()
    print("\n🔄 Direction des messages:")
    for direction, count in directions:
        print(f"  - {direction}: {count} messages")
    
    # Types de messages
    types = db.query(Message.message_type, func.count(Message.id)).group_by(Message.message_type).all()
    print("\n📱 Types de messages:")
    for msg_type, count in types:
        print(f"  - {msg_type}: {count} messages")
    
    # Réponses (messages inbound)
    reponses = db.query(Message).filter(Message.direction == "inbound").count()
    print(f"\n✉️ Total réponses reçues: {reponses}")
    
    # Messages avec reply_date
    replies = db.query(Message).filter(Message.reply_date.isnot(None)).count()
    print(f"Messages avec reply_date: {replies}")

def diagnostic_agents(db: Session):
    """Diagnostic des agents"""
    print("\n" + "=" * 50)
    print("🤖 DIAGNOSTIC AGENTS")  
    print("=" * 50)
    
    total_agents = db.query(Agent).count()
    print(f"Total agents: {total_agents}")
    
    # Statuts des agents
    statuts = db.query(Agent.status, func.count(Agent.id)).group_by(Agent.status).all()
    print("\n📋 Statuts des agents:")
    for statut, count in statuts:
        print(f"  - {statut}: {count} agents")
    
    # Types d'agents
    types = db.query(Agent.type, func.count(Agent.id)).group_by(Agent.type).all()
    print("\n🔧 Types d'agents:")
    for agent_type, count in types:
        print(f"  - {agent_type}: {count} agents")

def diagnostic_niches(db: Session):
    """Diagnostic des niches"""
    print("\n" + "=" * 50)
    print("📂 DIAGNOSTIC NICHES")
    print("=" * 50)
    
    total_niches = db.query(Niche).count()
    print(f"Total niches: {total_niches}")
    
    # Statuts des niches
    statuts = db.query(Niche.status, func.count(Niche.id)).group_by(Niche.status).all()
    print("\n📋 Statuts des niches:")
    for statut, count in statuts:
        print(f"  - {statut}: {count} niches")
    
    # Détail des niches
    niches = db.query(Niche).all()
    print(f"\n📄 Détail des niches:")
    for niche in niches:
        campaigns_count = db.query(Campaign).filter(Campaign.niche_id == niche.id).count()
        leads_count = db.query(Lead).filter(Lead.niche_id == niche.id).count()
        print(f"  - {niche.name} (ID: {niche.id}) - {campaigns_count} campagnes, {leads_count} leads")

def main():
    """Fonction principale de diagnostic"""
    print("🔍 DIAGNOSTIC COMPLET BASE DE DONNÉES BERINIA")
    print("=" * 60)
    
    # Connexion à la base
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Lancer tous les diagnostics
        diagnostic_leads(db)
        diagnostic_campaigns(db)
        diagnostic_messages(db)
        diagnostic_agents(db)
        diagnostic_niches(db)
        
        print("\n" + "=" * 60)
        print("✅ DIAGNOSTIC TERMINÉ")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erreur durant le diagnostic: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

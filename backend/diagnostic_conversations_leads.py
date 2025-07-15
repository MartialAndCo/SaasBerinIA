#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les conversations et leur mapping avec les leads
"""

import os
import sys
sys.path.append("/root/berinia/backend")

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.api.deps import get_db
from app.models.lead import Lead
from app.models.campaign import Campaign  
from app.models.message import Message

def analyze_conversations_leads_mapping(db: Session):
    """Analyser le mapping entre conversations et leads"""
    print("🔍 ANALYSE MAPPING CONVERSATIONS ↔ LEADS")
    print("=" * 60)
    
    # 1. Analyser tous les messages
    print("\n📧 ANALYSE DES MESSAGES:")
    print("-" * 30)
    
    total_messages = db.query(Message).count()
    outbound_messages = db.query(Message).filter(Message.direction == "outbound").count()
    inbound_messages = db.query(Message).filter(Message.direction == "inbound").count()
    
    print(f"Total messages: {total_messages}")
    print(f"Messages envoyés (outbound): {outbound_messages}")
    print(f"Messages reçus (inbound): {inbound_messages}")
    
    # 2. Analyser les leads liés aux messages
    print("\n👥 ANALYSE LEADS LIÉS AUX MESSAGES:")
    print("-" * 35)
    
    # Messages avec lead_id
    messages_with_lead = db.query(Message).filter(Message.lead_id.isnot(None)).count()
    messages_without_lead = db.query(Message).filter(Message.lead_id.is_(None)).count()
    
    print(f"Messages avec lead_id: {messages_with_lead}")
    print(f"Messages sans lead_id: {messages_without_lead}")
    
    # 3. Analyser les leads avec leurs statuts
    print("\n📊 ANALYSE STATUTS LEADS:")
    print("-" * 25)
    
    leads_stats = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    for status, count in leads_stats:
        print(f"  - {status}: {count} leads")
    
    # 4. VÉRIFICATION DÉTAILLÉE : Messages vs Leads
    print("\n🔍 VÉRIFICATION DÉTAILLÉE MAPPING:")
    print("-" * 40)
    
    # Récupérer les messages inbound avec leurs leads
    inbound_with_leads = db.query(Message, Lead).join(
        Lead, Message.lead_id == Lead.id, isouter=True
    ).filter(Message.direction == "inbound").all()
    
    print(f"\nMessages inbound analysés: {len(inbound_with_leads)}")
    
    mapping_issues = []
    
    for i, (message, lead) in enumerate(inbound_with_leads, 1):
        print(f"\n--- MESSAGE INBOUND #{i} ---")
        print(f"Message ID: {message.id}")
        print(f"Lead ID: {message.lead_id}")
        print(f"Lead Email: {message.lead_email}")
        print(f"Date: {message.sent_date}")
        print(f"Contenu (100 premiers chars): {message.content[:100] if message.content else 'N/A'}...")
        
        if lead:
            print(f"Lead trouvé: {lead.first_name} {lead.last_name}")
            print(f"Statut lead: {lead.status}")
            
            # Analyser le contenu pour voir si le statut correspond
            content_lower = (message.content or "").lower()
            
            # Indicateurs de réponse positive
            positive_indicators = ["intéresse", "intéressé", "oui", "merci", "contact", "rendez-vous", "rdv", "appelez", "discuter"]
            negative_indicators = ["non", "pas intéressé", "désolé", "merci mais", "ne correspond pas", "refuse"]
            
            has_positive = any(indicator in content_lower for indicator in positive_indicators)
            has_negative = any(indicator in content_lower for indicator in negative_indicators)
            
            print(f"Analyse contenu - Positif: {has_positive}, Négatif: {has_negative}")
            
            # Vérifier cohérence
            if has_positive and lead.status == "new":
                mapping_issues.append({
                    "message_id": message.id,
                    "lead_id": lead.id,
                    "issue": "Réponse positive mais lead status 'new'",
                    "suggestion": "Devrait être 'qualified'"
                })
            elif has_negative and lead.status == "qualified":
                mapping_issues.append({
                    "message_id": message.id,
                    "lead_id": lead.id,
                    "issue": "Réponse négative mais lead status 'qualified'",
                    "suggestion": "Devrait être 'new' ou autre statut négatif"
                })
        else:
            print("⚠️ PROBLÈME: Lead non trouvé pour ce message")
            mapping_issues.append({
                "message_id": message.id,
                "lead_id": message.lead_id,
                "issue": "Message sans lead correspondant",
                "suggestion": "Vérifier l'intégrité des données"
            })
    
    # 5. RÉSUMÉ DES INCOHÉRENCES
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES INCOHÉRENCES TROUVÉES")
    print("=" * 60)
    
    if mapping_issues:
        print(f"\n⚠️ {len(mapping_issues)} incohérences détectées:")
        for issue in mapping_issues:
            print(f"\n• Message {issue['message_id']} (Lead {issue['lead_id']}):")
            print(f"  Problème: {issue['issue']}")
            print(f"  Suggestion: {issue['suggestion']}")
    else:
        print("\n✅ Aucune incohérence majeure détectée dans le mapping")
    
    # 6. RECOMMANDATIONS
    print("\n" + "=" * 60)
    print("🎯 RECOMMANDATIONS")
    print("=" * 60)
    
    if messages_without_lead > 0:
        print(f"\n⚠️ {messages_without_lead} messages sans lead_id")
        print("→ Vérifier pourquoi ces messages ne sont pas liés à des leads")
    
    if len(mapping_issues) > 0:
        print(f"\n⚠️ {len(mapping_issues)} incohérences dans le mapping statuts")
        print("→ Recalculer les statuts selon le contenu des réponses")
    
    print(f"\n📊 Statistiques attendues:")
    print(f"→ Total conversations: {total_messages}")
    print(f"→ Réponses reçues: {inbound_messages}")
    print(f"→ Messages envoyés: {outbound_messages}")

def main():
    """Fonction principale"""
    print("🔍 DIAGNOSTIC CONVERSATIONS ↔ LEADS MAPPING")
    print("=" * 60)
    
    # Connexion à la base
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        analyze_conversations_leads_mapping(db)
        
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

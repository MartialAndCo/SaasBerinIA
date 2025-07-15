#!/usr/bin/env python3
"""
Script de diagnostic approfondi des VRAIES conversations pour détecter les stats hardcodées
"""

import os
import sys
sys.path.append("/root/berinia/backend")

from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc
from app.api.deps import get_db
from app.models.lead import Lead
from app.models.campaign import Campaign  
from app.models.message import Message
from datetime import datetime

def analyze_all_conversations_details(db: Session):
    """Analyser CHAQUE conversation en détail pour détecter le problème"""
    print("🚨 DIAGNOSTIC APPROFONDI DES VRAIES CONVERSATIONS")
    print("=" * 70)
    
    # 1. ANALYSER TOUS LES MESSAGES PAR TYPE ET DIRECTION
    print("\n📊 ANALYSE COMPLÈTE DES MESSAGES:")
    print("-" * 40)
    
    all_messages = db.query(Message).order_by(Message.sent_date).all()
    print(f"Total messages dans la base: {len(all_messages)}")
    
    outbound_count = 0
    inbound_count = 0
    
    print("\n📧 DÉTAIL DE CHAQUE MESSAGE:")
    print("-" * 50)
    
    for i, msg in enumerate(all_messages, 1):
        print(f"\n--- MESSAGE #{i} ---")
        print(f"ID: {msg.id}")
        print(f"Direction: {msg.direction}")
        print(f"Date: {msg.sent_date}")
        print(f"Lead ID: {msg.lead_id}")
        print(f"Lead Email: {msg.lead_email}")
        print(f"Message Type: {msg.message_type}")
        print(f"Contenu (200 chars): {(msg.content or '')[:200]}...")
        
        if msg.direction == "outbound":
            outbound_count += 1
        elif msg.direction == "inbound":
            inbound_count += 1
        
        # Analyser le contenu si c'est inbound
        if msg.direction == "inbound":
            content = (msg.content or "").lower()
            
            # Indicateurs positifs
            positive_words = ["intéresse", "intéressé", "oui", "merci", "contact", "rendez-vous", "rdv", "appelez", "discuter", "valide", "parfait", "confirmé"]
            negative_words = ["non", "pas intéressé", "désolé", "merci mais", "ne correspond pas", "refuse", "n'ai pas besoin"]
            
            has_positive = any(word in content for word in positive_words)
            has_negative = any(word in content for word in negative_words)
            
            print(f"ANALYSE SENTIMENT:")
            print(f"  Positif détecté: {has_positive}")
            print(f"  Négatif détecté: {has_negative}")
            if has_positive:
                matching_words = [word for word in positive_words if word in content]
                print(f"  Mots positifs trouvés: {matching_words}")
            if has_negative:
                matching_words = [word for word in negative_words if word in content]
                print(f"  Mots négatifs trouvés: {matching_words}")
    
    print(f"\n📊 RÉSUMÉ COMPTAGE MESSAGES:")
    print(f"Messages OUTBOUND (envoyés): {outbound_count}")
    print(f"Messages INBOUND (reçus): {inbound_count}")
    
    # 2. ANALYSER LES LEADS ET LEURS STATUTS
    print("\n\n👥 ANALYSE DES LEADS ET STATUTS:")
    print("-" * 40)
    
    leads = db.query(Lead).all()
    print(f"Total leads: {len(leads)}")
    
    for lead in leads:
        print(f"\n--- LEAD {lead.id} ---")
        print(f"Nom: {lead.first_name} {lead.last_name}")
        print(f"Email: {lead.email}")
        print(f"Statut: {lead.status}")
        print(f"Campagne ID: {lead.campagne_id}")
        print(f"Créé le: {lead.created_at}")
        
        # Compter les messages pour ce lead
        messages_for_lead = db.query(Message).filter(Message.lead_id == lead.id).all()
        outbound_for_lead = [m for m in messages_for_lead if m.direction == "outbound"]
        inbound_for_lead = [m for m in messages_for_lead if m.direction == "inbound"]
        
        print(f"Messages envoyés à ce lead: {len(outbound_for_lead)}")
        print(f"Messages reçus de ce lead: {len(inbound_for_lead)}")
        
        if inbound_for_lead:
            print("RÉPONSES REÇUES:")
            for msg in inbound_for_lead:
                print(f"  - {msg.sent_date}: {(msg.content or '')[:100]}...")
    
    # 3. VÉRIFIER S'IL Y A DES DONNÉES HARDCODÉES OU DE TEST
    print("\n\n🔍 RECHERCHE DONNÉES HARDCODÉES/TEST:")
    print("-" * 45)
    
    # Chercher des patterns suspects dans les données
    suspicious_emails = ["test@", "example@", "demo@", "fake@"]
    test_leads = []
    
    for lead in leads:
        if any(pattern in (lead.email or "").lower() for pattern in suspicious_emails):
            test_leads.append(lead)
        elif "test" in (lead.first_name or "").lower() or "test" in (lead.last_name or "").lower():
            test_leads.append(lead)
    
    if test_leads:
        print(f"⚠️ LEADS SUSPECTS (possibles données de test):")
        for lead in test_leads:
            print(f"  - {lead.first_name} {lead.last_name} ({lead.email}) - Statut: {lead.status}")
    else:
        print("✅ Aucun lead suspect détecté")
    
    # 4. VÉRIFIER LES DOUBLONS (RELANCES)
    print("\n\n🔄 DÉTECTION DES DOUBLONS/RELANCES:")
    print("-" * 40)
    
    # Grouper par lead_email pour détecter les doublons
    email_counts = {}
    for msg in all_messages:
        if msg.lead_email:
            if msg.lead_email not in email_counts:
                email_counts[msg.lead_email] = {"outbound": 0, "inbound": 0}
            email_counts[msg.lead_email][msg.direction] += 1
    
    duplicates_found = False
    for email, counts in email_counts.items():
        if counts["outbound"] > 1:
            duplicates_found = True
            print(f"⚠️ DOUBLON DÉTECTÉ - {email}:")
            print(f"   Messages envoyés: {counts['outbound']} (possibles relances)")
            print(f"   Messages reçus: {counts['inbound']}")
    
    if not duplicates_found:
        print("✅ Aucun doublon détecté")
    
    # 5. RECOMMANDATIONS FINALES
    print("\n" + "=" * 70)
    print("🎯 ANALYSE FINALE ET RECOMMANDATIONS")
    print("=" * 70)
    
    print(f"\n📊 VRAIS CHIFFRES DÉTECTÉS:")
    print(f"→ Messages envoyés (outbound): {outbound_count}")
    print(f"→ Messages reçus (inbound): {inbound_count}")
    print(f"→ Leads totaux: {len(leads)}")
    
    # Analyser manuellement les réponses positives
    truly_positive = 0
    truly_negative = 0
    neutral_or_unclear = 0
    
    print(f"\n🔍 ANALYSE MANUELLE DES {inbound_count} RÉPONSES:")
    for msg in all_messages:
        if msg.direction == "inbound":
            content = (msg.content or "").lower()
            if any(word in content for word in ["intéresse", "intéressé", "parfait", "valide", "confirmé", "oui"]):
                truly_positive += 1
                print(f"✅ POSITIVE: {(msg.content or '')[:100]}...")
            elif any(word in content for word in ["non", "pas", "désolé", "refuse"]):
                truly_negative += 1
                print(f"❌ NÉGATIVE: {(msg.content or '')[:100]}...")
            else:
                neutral_or_unclear += 1
                print(f"⚪ NEUTRE/FLOUE: {(msg.content or '')[:100]}...")
    
    print(f"\n📋 RÉSULTATS MANUELS:")
    print(f"→ Réponses VRAIMENT positives: {truly_positive}")
    print(f"→ Réponses négatives: {truly_negative}")
    print(f"→ Réponses neutres/floues: {neutral_or_unclear}")
    
    if truly_positive != inbound_count:
        print(f"\n⚠️ INCOHÉRENCE DÉTECTÉE:")
        print(f"   API retourne: {inbound_count} réponses")
        print(f"   Analyse manuelle: {truly_positive} vraiment positives")
        print(f"   → Les stats API sont INCORRECTES !")

def main():
    """Fonction principale"""
    print("🚨 DIAGNOSTIC APPROFONDI - DÉTECTION STATS HARDCODÉES")
    print("=" * 70)
    
    # Connexion à la base
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        analyze_all_conversations_details(db)
        
        print("\n" + "=" * 70)
        print("✅ DIAGNOSTIC APPROFONDI TERMINÉ")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Erreur durant le diagnostic: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

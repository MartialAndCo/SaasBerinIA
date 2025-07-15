#!/usr/bin/env python3
"""
Script pour créer des conversations complètes et des statuts avancés
"""

import sys
sys.path.append('/root/berinia/backend')
from app.database.session import SessionLocal
from sqlalchemy import text
from datetime import datetime, timedelta
import random

def create_advanced_conversations():
    """Crée des conversations bidirectionnelles complètes et des statuts avancés"""
    db = SessionLocal()
    try:
        print("🔄 Création de conversations avancées...")
        
        # 1. Ajouter de nouveaux statuts de contact avancés
        print("\n📊 Ajout de statuts avancés...")
        
        # Leads qui vont avoir des statuts avancés
        advanced_leads = [
            {"id": 25, "new_status": "signed"},  # Antoine Lopez - converti → signé
            {"id": 26, "new_status": "confirmed"},  # Françoise Garcia - confirmé
            {"id": 28, "new_status": "validated"},  # Marco Benedetti - validé
        ]
        
        for lead in advanced_leads:
            db.execute(text("""
                UPDATE leads 
                SET contact_status = :status, 
                    last_contact_status_update = :timestamp
                WHERE id = :lead_id
            """), {
                "status": lead["new_status"],
                "timestamp": datetime.now(),
                "lead_id": lead["id"]
            })
            print(f"   ✅ Lead {lead['id']} → statut '{lead['new_status']}'")
        
        # 2. Créer de vraies conversations bidirectionnelles
        print("\n💬 Création de conversations bidirectionnelles...")
        
        # Récupérer les threads existants avec réponses
        existing_conversations = db.execute(text("""
            SELECT DISTINCT m.thread_id, m.lead_id, l.first_name, l.last_name, 
                   l.email, l.contact_status, m.reply_content, m.reply_date
            FROM messages m
            JOIN leads l ON m.lead_id = l.id
            WHERE m.reply_content IS NOT NULL
            AND l.contact_status IN ('responded', 'converted', 'signed', 'confirmed', 'validated')
        """)).fetchall()
        
        conversation_scenarios = [
            {
                "responses": [
                    "Merci pour cette proposition intéressante. Pouvez-vous me donner plus de détails sur les tarifs ?",
                    "Les fonctionnalités semblent correspondre à nos besoins. Quand pouvons-nous faire une démonstration ?",
                    "Parfait ! Je valide cette solution. Pouvez-vous m'envoyer le contrat ?"
                ],
                "ai_responses": [
                    "Bien sûr ! Nos tarifs démarrent à 99€/mois. Je vous envoie une proposition détaillée.",
                    "Excellente nouvelle ! Je peux vous proposer une démo mardi ou mercredi. Quelle date vous convient ?",
                    "Formidable ! Je vous envoie le contrat dans l'heure. Merci pour votre confiance !"
                ]
            },
            {
                "responses": [
                    "Votre solution m'intéresse mais j'aimerais comprendre l'intégration avec nos systèmes existants.",
                    "L'intégration semble faisable. Quel est le délai de mise en œuvre ?",
                    "C'est confirmé, nous procédons avec cette solution."
                ],
                "ai_responses": [
                    "Nos solutions s'intègrent facilement via API. Nous supportons la plupart des systèmes standards.",
                    "La mise en œuvre prend généralement 2-3 semaines selon la complexité. Nous vous accompagnons.",
                    "Excellent choix ! Nous commençons dès que vous le souhaitez. Bienvenue dans l'équipe BerinIA !"
                ]
            }
        ]
        
        for i, conv in enumerate(existing_conversations[:2]):  # Prendre les 2 premières conversations
            scenario = conversation_scenarios[i]
            
            print(f"\n   📞 Conversation avec {conv.first_name} {conv.last_name}:")
            
            # Créer une séquence de messages pour cette conversation
            base_date = conv.reply_date or datetime.now() - timedelta(days=5)
            
            for j, (user_msg, ai_msg) in enumerate(zip(scenario["responses"], scenario["ai_responses"])):
                msg_date = base_date + timedelta(days=j+1, hours=random.randint(1, 23))
                
                # Message du client (inbound)
                db.execute(text("""
                    INSERT INTO messages (
                        lead_id, lead_name, lead_email, campaign_id, campaign_name,
                        subject, content, status, type, sent_date, reply_date,
                        created_at, updated_at, direction, sender_type, thread_id,
                        message_type, sentiment, received_date
                    ) VALUES (
                        :lead_id, :lead_name, :lead_email, :campaign_id, :campaign_name,
                        :subject, :content, 'received', 'email', :sent_date, :reply_date,
                        :created_at, :updated_at, 'inbound', 'human', :thread_id,
                        'email', 'positive', :received_date
                    )
                """), {
                    "lead_id": conv.lead_id,
                    "lead_name": f"{conv.first_name} {conv.last_name}",
                    "lead_email": conv.email,
                    "campaign_id": None,
                    "campaign_name": f"Conversation avec {conv.first_name}",
                    "subject": f"Re: Solution IA - Échange {j+1}",
                    "content": user_msg,
                    "sent_date": msg_date,
                    "reply_date": msg_date,
                    "created_at": msg_date,
                    "updated_at": msg_date,
                    "thread_id": conv.thread_id,
                    "received_date": msg_date
                })
                
                # Réponse de l'IA (outbound)
                ai_response_date = msg_date + timedelta(hours=random.randint(1, 4))
                
                db.execute(text("""
                    INSERT INTO messages (
                        lead_id, lead_name, lead_email, campaign_id, campaign_name,
                        subject, content, status, type, sent_date,
                        created_at, updated_at, direction, sender_type, thread_id,
                        message_type, sender_name
                    ) VALUES (
                        :lead_id, :lead_name, :lead_email, :campaign_id, :campaign_name,
                        :subject, :content, 'sent', 'email', :sent_date,
                        :created_at, :updated_at, 'outbound', 'ai', :thread_id,
                        'email', 'Louise BerinIA'
                    )
                """), {
                    "lead_id": conv.lead_id,
                    "lead_name": f"{conv.first_name} {conv.last_name}",
                    "lead_email": conv.email,
                    "campaign_id": None,
                    "campaign_name": f"Conversation avec {conv.first_name}",
                    "subject": f"Re: Solution IA - Réponse {j+1}",
                    "content": ai_msg,
                    "sent_date": ai_response_date,
                    "created_at": ai_response_date,
                    "updated_at": ai_response_date,
                    "thread_id": conv.thread_id
                })
                
                print(f"     💬 Échange {j+1}: Client → IA")
        
        # 3. Mettre à jour l'historique de contact
        print("\n📝 Mise à jour de l'historique de contact...")
        
        for lead in advanced_leads:
            db.execute(text("""
                INSERT INTO contact_history (
                    lead_id, contact_type, contact_method, previous_status, 
                    new_status, notes, created_at
                ) VALUES (
                    :lead_id, 'status_change', 'email', 'responded', 
                    :new_status, :notes, :timestamp
                )
            """), {
                "lead_id": lead["id"],
                "new_status": lead["new_status"],
                "notes": f"Lead progressé vers statut '{lead['new_status']}' après conversation avancée",
                "timestamp": datetime.now()
            })
        
        db.commit()
        
        # 4. Vérification finale
        print("\n📊 Vérification des nouvelles données:")
        
        # Compter les messages par direction
        stats = db.execute(text("""
            SELECT direction, COUNT(*) as count
            FROM messages 
            GROUP BY direction
            ORDER BY direction
        """)).fetchall()
        
        for stat in stats:
            print(f"   - Messages {stat.direction}: {stat.count}")
        
        # Compter les nouveaux statuts
        status_stats = db.execute(text("""
            SELECT contact_status, COUNT(*) as count
            FROM leads 
            GROUP BY contact_status
            ORDER BY contact_status
        """)).fetchall()
        
        print("\n   Statuts des leads:")
        for stat in status_stats:
            print(f"   - {stat.contact_status}: {stat.count}")
        
        # Conversations avec plusieurs messages
        conv_stats = db.execute(text("""
            SELECT thread_id, COUNT(*) as message_count
            FROM messages 
            GROUP BY thread_id
            HAVING COUNT(*) > 2
            ORDER BY COUNT(*) DESC
        """)).fetchall()
        
        print(f"\n   Conversations avec échanges multiples: {len(conv_stats)}")
        for conv in conv_stats:
            print(f"   - Thread {conv.thread_id}: {conv.message_count} messages")
        
        print("\n✅ Conversations avancées créées avec succès !")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Création de conversations avancées et statuts complets")
    print("=" * 60)
    create_advanced_conversations()

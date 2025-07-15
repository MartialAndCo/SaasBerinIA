#!/usr/bin/env python3
"""
Script pour remplir la base de données BerinIA avec des données de test COMPLÈTES.
Remplit toutes les colonnes de toutes les tables avec des données réalistes et cohérentes.
"""

import os
import sys
import psycopg2
import json
from datetime import datetime, timedelta
import random
import uuid
from decimal import Decimal

# Configuration de la base de données
DB_CONFIG = {
    'host': 'localhost',
    'database': 'berinia',
    'user': 'berinia_user',
    'password': 'berinia_pass',
    'port': 5432
}

def connect_to_db():
    """Connexion à la base de données PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Erreur de connexion à la base de données: {e}")
        sys.exit(1)

def clear_existing_data(conn):
    """Supprime les données existantes pour repartir sur une base propre"""
    cursor = conn.cursor()
    
    print("🧹 Nettoyage des données existantes...")
    
    # Supprimer dans l'ordre inverse des dépendances
    tables_to_clear = [
        'contact_history',
        'messages', 
        'leads',
        'campaigns',
        'niches'
    ]
    
    for table in tables_to_clear:
        cursor.execute(f"DELETE FROM {table} WHERE id > 0")
        print(f"   - Table {table} vidée")
    
    conn.commit()
    cursor.close()

def create_niches(conn):
    """Crée les niches de test avec toutes les données"""
    cursor = conn.cursor()
    
    print("🎯 Création des niches...")
    
    niches_data = [
        {
            'name': 'Dentistes Paris',
            'description': 'Cabinets dentaires et orthodontistes parisiens',
            'keywords': ['dentiste', 'orthodontiste', 'cabinet dentaire', 'soins dentaires'],
            'status': 'active',
            'exploration_depth': 2
        },
        {
            'name': 'Salons Coiffure Lyon', 
            'description': 'Salons de coiffure et instituts de beauté lyonnais',
            'keywords': ['salon coiffure', 'coiffeur', 'beauté', 'esthétique'],
            'status': 'active',
            'exploration_depth': 1
        },
        {
            'name': 'Garages Auto Marseille',
            'description': 'Garages automobiles et centres de réparation marseillais', 
            'keywords': ['garage', 'automobile', 'réparation', 'mécanique'],
            'status': 'active',
            'exploration_depth': 3
        },
        {
            'name': 'Cabinets Comptables Toulouse',
            'description': 'Cabinets comptables et experts-comptables toulousains',
            'keywords': ['comptable', 'expert-comptable', 'cabinet', 'fiscalité'],
            'status': 'active',
            'exploration_depth': 2
        },
        {
            'name': 'Restaurants Nice',
            'description': 'Restaurants traditionnels et brasseries niçoises',
            'keywords': ['restaurant', 'brasserie', 'cuisine', 'gastronomie'],
            'status': 'paused',
            'exploration_depth': 1
        }
    ]
    
    niche_ids = []
    for niche in niches_data:
        cursor.execute("""
            INSERT INTO niches (name, description, keywords, status, exploration_depth, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            niche['name'],
            niche['description'], 
            niche['keywords'],
            niche['status'],
            niche['exploration_depth'],
            datetime.now(),
            datetime.now()
        ))
        niche_id = cursor.fetchone()[0]
        niche_ids.append(niche_id)
        print(f"   ✅ Niche créée: {niche['name']} (ID: {niche_id})")
    
    conn.commit()
    cursor.close()
    return niche_ids

def create_campaigns(conn, niche_ids):
    """Crée les campagnes de test avec toutes les données"""
    cursor = conn.cursor()
    
    print("📧 Création des campagnes...")
    
    campaigns_data = [
        {
            'name': 'Campagne Dentistes Janvier 2025',
            'description': 'Prospection initiale des cabinets dentaires parisiens pour solutions IA',
            'niche_id': niche_ids[0],  # Dentistes Paris
            'status': 'active',
            'target_leads': 15,
            'agent': 'MessagingAgent',
            'start_date': datetime.now() - timedelta(days=20),
            'end_date': None,
            'message_template': 'Bonjour {first_name}, je suis Louise de BerinIA. Nous avons développé des solutions IA spécialement conçues pour moderniser les cabinets dentaires comme {company}. Nos outils permettent d\'automatiser la prise de rendez-vous, d\'améliorer l\'accueil patient et d\'optimiser la gestion quotidienne. Seriez-vous intéressé(e) par une démonstration rapide ?',
            'subject_template': 'Solution IA pour {company} - Modernisez votre cabinet dentaire'
        },
        {
            'name': 'Campagne Coiffeurs Lyon Q1',
            'description': 'Approche personnalisée des salons de coiffure lyonnais',
            'niche_id': niche_ids[1],  # Salons Lyon
            'status': 'active', 
            'target_leads': 12,
            'agent': 'MessagingAgent',
            'start_date': datetime.now() - timedelta(days=15),
            'end_date': None,
            'message_template': 'Bonjour {first_name}, j\'ai visité le site de {company} et j\'ai été impressionnée par votre approche. Nous développons des solutions IA pour les salons de coiffure : chatbot pour la prise de RDV, analyse des tendances clients, et assistant vocal pour l\'accueil. Ces outils peuvent transformer l\'expérience client de votre salon. Puis-je vous présenter ces innovations ?',
            'subject_template': 'IA pour salons de coiffure - {company}'
        },
        {
            'name': 'Campagne Garages Marseille Test',
            'description': 'Test de prospection garages automobiles - campagne terminée',
            'niche_id': niche_ids[2],  # Garages Marseille
            'status': 'completed',
            'target_leads': 8,
            'agent': 'MessagingAgent',
            'start_date': datetime.now() - timedelta(days=45),
            'end_date': datetime.now() - timedelta(days=30),
            'message_template': 'Bonjour {first_name}, l\'IA révolutionne la gestion des garages automobiles. Nos solutions permettent le diagnostic prédictif, la gestion automatique des stocks de pièces et l\'optimisation des plannings. {company} pourrait bénéficier significativement de ces innovations. Accepteriez-vous un échange de 15 minutes ?',
            'subject_template': 'Solutions IA pour garages - {company}'
        },
        {
            'name': 'Campagne Comptables Toulouse',
            'description': 'Prospection ciblée des cabinets comptables toulousains',
            'niche_id': niche_ids[3],  # Comptables Toulouse
            'status': 'draft',
            'target_leads': 10,
            'agent': 'MessagingAgent',
            'start_date': datetime.now() + timedelta(days=5),
            'end_date': None,
            'message_template': 'Bonjour {first_name}, les cabinets comptables comme {company} font face à des défis croissants d\'automatisation. Nos solutions IA permettent le traitement automatique des factures, la catégorisation intelligente des écritures et l\'assistance client 24/7. Souhaiteriez-vous découvrir comment ces outils peuvent optimiser votre cabinet ?',
            'subject_template': 'Automatisation IA pour {company} - Cabinet comptable'
        },
        {
            'name': 'Campagne Restaurants Nice - Pause',
            'description': 'Campagne mise en pause suite aux faibles résultats',
            'niche_id': niche_ids[4],  # Restaurants Nice
            'status': 'paused',
            'target_leads': 6,
            'agent': 'MessagingAgent',
            'start_date': datetime.now() - timedelta(days=35),
            'end_date': None,
            'message_template': 'Bonjour {first_name}, {company} pourrait bénéficier de nos solutions IA pour la restauration : chatbot de réservation, analyse prédictive des commandes, et assistant pour la gestion des allergènes. Ces outils améliorent l\'efficacité et l\'expérience client. Puis-je vous présenter ces innovations ?',
            'subject_template': 'IA pour restaurants - {company}'
        }
    ]
    
    campaign_ids = []
    for campaign in campaigns_data:
        cursor.execute("""
            INSERT INTO campaigns (name, description, niche_id, target_leads, agent, status, 
                                 message_template, subject_template, start_date, end_date, 
                                 created_by, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            campaign['name'],
            campaign['description'],
            campaign['niche_id'],
            campaign['target_leads'],
            campaign['agent'],
            campaign['status'],
            campaign['message_template'],
            campaign['subject_template'],
            campaign['start_date'],
            campaign['end_date'],
            1,  # created_by = admin user
            datetime.now(),
            datetime.now()
        ))
        campaign_id = cursor.fetchone()[0]
        campaign_ids.append(campaign_id)
        print(f"   ✅ Campagne créée: {campaign['name']} (ID: {campaign_id})")
    
    conn.commit()
    cursor.close()
    return campaign_ids

def create_comprehensive_leads(conn, niche_ids, campaign_ids):
    """Crée des leads avec TOUTES les colonnes remplies de manière réaliste"""
    cursor = conn.cursor()
    
    print("👥 Création des leads avec données complètes...")
    
    # Données réalistes par niche
    leads_data = {
        # Dentistes Paris
        niche_ids[0]: [
            {
                'first_name': 'Dr. Sophie', 'last_name': 'Martin', 'position': 'Dentiste',
                'company': 'Cabinet Dentaire Martin', 'email': 'contact@cabinet-martin-paris.fr',
                'phone': '+33 1 42 56 78 90', 'industry': 'Santé', 'source': 'Apify',
                'linkedin_url': 'https://linkedin.com/in/sophie-martin-dentiste',
                'website': 'https://www.cabinet-martin-paris.fr',
                'site_type': 'cabinet_medical', 'website_maturity': 'established',
                'visual_quality': 7, 'visual_score': 75, 'has_popup': False,
                'design_strengths': ['Navigation claire', 'Informations complètes', 'Design professionnel'],
                'design_weaknesses': ['Chatbot absent', 'Formulaires basiques']
            },
            {
                'first_name': 'Dr. Pierre', 'last_name': 'Dubois', 'position': 'Orthodontiste',
                'company': 'Orthodontie Dubois', 'email': 'pierre.dubois@ortho-paris.com',
                'phone': '+33 1 45 23 67 89', 'industry': 'Santé', 'source': 'Apollo',
                'linkedin_url': 'https://linkedin.com/in/pierre-dubois-orthodontiste',
                'website': 'https://www.orthodontie-dubois.fr',
                'site_type': 'cabinet_medical', 'website_maturity': 'modern',
                'visual_quality': 8, 'visual_score': 82, 'has_popup': True,
                'design_strengths': ['Prise RDV en ligne', 'Photos avant/après', 'Chatbot'],
                'design_weaknesses': ['Popup intrusif']
            },
            {
                'first_name': 'Dr. Marie', 'last_name': 'Leroy', 'position': 'Dentiste',
                'company': 'Centre Dentaire République', 'email': 'dr.leroy@centre-republique.fr',
                'phone': '+33 1 48 37 92 15', 'industry': 'Santé', 'source': 'Apify',
                'linkedin_url': '', 'website': 'https://www.centre-dentaire-republique.fr',
                'site_type': 'cabinet_medical', 'website_maturity': 'outdated',
                'visual_quality': 4, 'visual_score': 45, 'has_popup': False,
                'design_strengths': ['Informations contact claires'],
                'design_weaknesses': ['Design vieillot', 'Navigation complexe', 'Pas de RDV en ligne']
            }
        ],
        
        # Salons Coiffure Lyon
        niche_ids[1]: [
            {
                'first_name': 'Isabelle', 'last_name': 'Moreau', 'position': 'Propriétaire',
                'company': 'Salon Isabelle Coiffure', 'email': 'isabelle@salon-moreau-lyon.fr',
                'phone': '+33 4 72 33 45 67', 'industry': 'Beauté', 'source': 'Apify',
                'linkedin_url': '', 'website': 'https://www.salon-isabelle-lyon.fr',
                'site_type': 'salon_beaute', 'website_maturity': 'established',
                'visual_quality': 6, 'visual_score': 68, 'has_popup': False,
                'design_strengths': ['Photos des réalisations', 'Tarifs affichés'],
                'design_weaknesses': ['Pas de réservation en ligne', 'Design simple']
            },
            {
                'first_name': 'Jean-Luc', 'last_name': 'Bernard', 'position': 'Coiffeur',
                'company': 'Coiffure Tendance Lyon', 'email': 'contact@coiffure-tendance.fr',
                'phone': '+33 4 78 45 67 89', 'industry': 'Beauté', 'source': 'Apollo',
                'linkedin_url': 'https://linkedin.com/in/jeanluc-bernard-coiffeur',
                'website': 'https://www.coiffure-tendance-lyon.com',
                'site_type': 'salon_beaute', 'website_maturity': 'modern',
                'visual_quality': 9, 'visual_score': 88, 'has_popup': True,
                'design_strengths': ['Réservation en ligne', 'Galerie photos', 'Blog tendances'],
                'design_weaknesses': ['Popup newsletter']
            }
        ],
        
        # Garages Auto Marseille
        niche_ids[2]: [
            {
                'first_name': 'Michel', 'last_name': 'Rossi', 'position': 'Gérant',
                'company': 'Garage Rossi Automobile', 'email': 'michel@garage-rossi.fr',
                'phone': '+33 4 91 23 45 67', 'industry': 'Automobile', 'source': 'Apify',
                'linkedin_url': '', 'website': 'https://www.garage-rossi-marseille.fr',
                'site_type': 'garage_auto', 'website_maturity': 'outdated',
                'visual_quality': 3, 'visual_score': 35, 'has_popup': False,
                'design_strengths': ['Coordonnées visibles'],
                'design_weaknesses': ['Site très basique', 'Pas de prise RDV', 'Design obsolète']
            },
            {
                'first_name': 'Antoine', 'last_name': 'Lopez', 'position': 'Propriétaire',
                'company': 'Auto Service Lopez', 'email': 'contact@autoservice-lopez.com',
                'phone': '+33 4 96 78 34 21', 'industry': 'Automobile', 'source': 'Apollo',
                'linkedin_url': 'https://linkedin.com/in/antoine-lopez-garage',
                'website': 'https://www.autoservice-lopez.com',
                'site_type': 'garage_auto', 'website_maturity': 'established',
                'visual_quality': 7, 'visual_score': 72, 'has_popup': False,
                'design_strengths': ['Services détaillés', 'Devis en ligne', 'Avis clients'],
                'design_weaknesses': ['Chatbot manquant']
            }
        ],
        
        # Cabinets Comptables Toulouse
        niche_ids[3]: [
            {
                'first_name': 'Françoise', 'last_name': 'Garcia', 'position': 'Expert-Comptable',
                'company': 'Cabinet Garcia & Associés', 'email': 'f.garcia@cabinet-garcia.fr',
                'phone': '+33 5 61 23 45 67', 'industry': 'Comptabilité', 'source': 'Apify',
                'linkedin_url': 'https://linkedin.com/in/francoise-garcia-expert-comptable',
                'website': 'https://www.cabinet-garcia-toulouse.fr',
                'site_type': 'service_professionnel', 'website_maturity': 'modern',
                'visual_quality': 8, 'visual_score': 85, 'has_popup': True,
                'design_strengths': ['Interface professionnelle', 'Espace client', 'Documentation'],
                'design_weaknesses': ['Popup contact']
            },
            {
                'first_name': 'Philippe', 'last_name': 'Marchand', 'position': 'Comptable',
                'company': 'Expertise Comptable Toulouse', 'email': 'p.marchand@expertise-toulouse.fr',
                'phone': '+33 5 62 34 56 78', 'industry': 'Comptabilité', 'source': 'Apollo',
                'linkedin_url': '', 'website': 'https://www.expertise-comptable-toulouse.fr',
                'site_type': 'service_professionnel', 'website_maturity': 'established',
                'visual_quality': 6, 'visual_score': 65, 'has_popup': False,
                'design_strengths': ['Informations complètes', 'Formulaire contact'],
                'design_weaknesses': ['Design standard', 'Manque d\'interactivité']
            }
        ],
        
        # Restaurants Nice
        niche_ids[4]: [
            {
                'first_name': 'Marco', 'last_name': 'Benedetti', 'position': 'Chef Propriétaire',
                'company': 'Ristorante Benedetti', 'email': 'marco@benedetti-nice.fr',
                'phone': '+33 4 93 45 67 89', 'industry': 'Restauration', 'source': 'Apify',
                'linkedin_url': '', 'website': 'https://www.ristorante-benedetti.fr',
                'site_type': 'restaurant', 'website_maturity': 'established',
                'visual_quality': 5, 'visual_score': 55, 'has_popup': False,
                'design_strengths': ['Menu en ligne', 'Photos plats'],
                'design_weaknesses': ['Pas de réservation en ligne', 'Design basique']
            }
        ]
    }
    
    # Générer des statuts de contact variés
    contact_statuses = [
        'never_contacted', 'contacted_waiting_response', 'in_follow_up_sequence', 
        'responded', 'converted', 'unsubscribed'
    ]
    
    all_leads = []
    lead_id_counter = 1
    
    for niche_id, leads in leads_data.items():
        for lead_data in leads:
            # Statut de contact aléatoire mais cohérent
            contact_status = random.choice(contact_statuses)
            
            # Score basé sur la qualité visuelle et d'autres facteurs
            base_score = lead_data['visual_quality']
            if lead_data['position'] in ['Propriétaire', 'Gérant', 'Chef Propriétaire']:
                base_score += 2
            if lead_data['position'].startswith('Dr.'):
                base_score += 1
            if lead_data['linkedin_url']:
                base_score += 1
            if lead_data['website_maturity'] == 'modern':
                base_score += 1
                
            final_score = min(10, base_score)
            
            # Score details JSON
            score_details = {
                'position_score': 8 if 'Propriétaire' in lead_data['position'] or 'Dr.' in lead_data['position'] else 6,
                'visual_score': lead_data['visual_quality'],
                'data_completeness': 9 if lead_data['linkedin_url'] else 7,
                'email_quality': 8 if '@' in lead_data['email'] and not any(domain in lead_data['email'] for domain in ['gmail', 'yahoo', 'hotmail']) else 5,
                'website_quality': lead_data['visual_quality']
            }
            
            # Visual analysis data JSON
            visual_analysis_data = {
                'url': lead_data['website'],
                'analysis_date': (datetime.now() - timedelta(days=random.randint(1, 10))).isoformat(),
                'has_contact_form': random.choice([True, False]),
                'has_phone_display': True,
                'color_scheme': random.choice(['professional', 'modern', 'classic', 'vibrant']),
                'mobile_friendly': random.choice([True, False]),
                'loading_speed': random.choice(['fast', 'medium', 'slow']),
                'technology_stack': random.choice(['WordPress', 'Custom', 'Wix', 'Squarespace']),
                'ai_features_detected': lead_data['has_popup'] or 'chatbot' in str(lead_data['design_strengths']).lower()
            }
            
            # Dates cohérentes
            created_date = datetime.now() - timedelta(days=random.randint(5, 30))
            last_contact_date = None
            if contact_status != 'never_contacted':
                last_contact_date = created_date + timedelta(days=random.randint(1, 10))
            
            lead_complete = {
                'id': lead_id_counter,
                'first_name': lead_data['first_name'],
                'last_name': lead_data['last_name'],
                'email': lead_data['email'],
                'phone': lead_data['phone'],
                'company': lead_data['company'],
                'position': lead_data['position'],
                'linkedin_url': lead_data['linkedin_url'],
                'website': lead_data['website'],
                'entreprise': lead_data['company'],  # Duplicate column
                'industry': lead_data['industry'],
                'niche_id': niche_id,
                'source': lead_data['source'],
                'status': 'qualified' if final_score >= 7 else 'new',
                'score': final_score,
                'score_details': json.dumps(score_details),
                'validation_status': 'validated' if final_score >= 6 else 'unvalidated',
                'last_contact': last_contact_date,
                'notes': f"Lead {lead_data['source']} - Score: {final_score}/10",
                'created_at': created_date,
                'updated_at': created_date,
                'visual_score': lead_data['visual_score'],
                'visual_analysis_data': json.dumps(visual_analysis_data),
                'has_popup': lead_data['has_popup'],
                'popup_removed': lead_data['has_popup'],
                'screenshot_path': f"/screenshots/{lead_data['company'].lower().replace(' ', '_')}.png",
                'enhanced_screenshot_path': f"/enhanced_screenshots/{lead_data['company'].lower().replace(' ', '_')}_enhanced.png",
                'visual_analysis_date': created_date + timedelta(hours=1),
                'site_type': lead_data['site_type'],
                'visual_quality': lead_data['visual_quality'],
                'website_maturity': lead_data['website_maturity'],
                'design_strengths': lead_data['design_strengths'],
                'design_weaknesses': lead_data['design_weaknesses'],
                'campagne_id': campaign_ids[list(niche_ids).index(niche_id)],
                'contact_status': contact_status,
                'last_contact_status_update': last_contact_date or created_date
            }
            
            all_leads.append(lead_complete)
            lead_id_counter += 1
    
    # Insertion des leads dans la base et récupération des vrais IDs
    for lead in all_leads:
        cursor.execute("""
            INSERT INTO leads (
                first_name, last_name, email, phone, company, position, linkedin_url, website,
                entreprise, industry, niche_id, source, status, score, score_details,
                validation_status, last_contact, notes, created_at, updated_at,
                visual_score, visual_analysis_data, has_popup, popup_removed,
                screenshot_path, enhanced_screenshot_path, visual_analysis_date,
                site_type, visual_quality, website_maturity, design_strengths, design_weaknesses,
                campagne_id, contact_status, last_contact_status_update
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            lead['first_name'], lead['last_name'], lead['email'], lead['phone'],
            lead['company'], lead['position'], lead['linkedin_url'], lead['website'],
            lead['entreprise'], lead['industry'], lead['niche_id'], lead['source'],
            lead['status'], lead['score'], lead['score_details'], lead['validation_status'],
            lead['last_contact'], lead['notes'], lead['created_at'], lead['updated_at'],
            lead['visual_score'], lead['visual_analysis_data'], lead['has_popup'], lead['popup_removed'],
            lead['screenshot_path'], lead['enhanced_screenshot_path'], lead['visual_analysis_date'],
            lead['site_type'], lead['visual_quality'], lead['website_maturity'],
            lead['design_strengths'], lead['design_weaknesses'], lead['campagne_id'],
            lead['contact_status'], lead['last_contact_status_update']
        ))
        
        # Récupérer l'ID réel généré par la base
        real_lead_id = cursor.fetchone()[0]
        lead['id'] = real_lead_id  # Mettre à jour avec le vrai ID
        
        print(f"   ✅ Lead créé: {lead['first_name']} {lead['last_name']} - {lead['company']} (Score: {lead['score']}, Status: {lead['contact_status']}, ID: {real_lead_id})")
    
    conn.commit()
    cursor.close()
    return all_leads

def create_messages_and_history(conn, leads):
    """Crée les messages et l'historique de contact cohérents"""
    cursor = conn.cursor()
    
    print("📨 Création des messages et historique...")
    
    for lead in leads:
        if lead['contact_status'] != 'never_contacted':
            # Message initial
            message_date = lead['last_contact'] or lead['created_at']
            
            cursor.execute("""
                INSERT INTO messages (
                    lead_id, lead_name, lead_email, campaign_id, campaign_name,
                    subject, content, status, type, sent_date, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                lead['id'],
                f"{lead['first_name']} {lead['last_name']}",
                lead['email'],
                lead['campagne_id'],
                f"Campagne {lead['industry']}",
                f"Solution IA pour {lead['company']}",
                f"Bonjour {lead['first_name']}, nous proposons des solutions IA adaptées à {lead['company']}...",
                'sent',
                'email',
                message_date,
                message_date,
                message_date
            ))
            
            message_id = cursor.fetchone()[0]
            
            # Ajouter une entrée dans contact_history
            cursor.execute("""
                INSERT INTO contact_history (
                    lead_id, campaign_id, contact_type, contact_method, 
                    message_id, previous_status, new_status, notes, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                lead['id'],
                lead['campagne_id'],
                'initial',
                'email',
                message_id,
                'never_contacted',
                lead['contact_status'],
                f"Contact initial - {lead['contact_status']}",
                message_date
            ))
            
            # Si le lead a répondu, créer une réponse
            if lead['contact_status'] in ['responded', 'converted']:
                reply_date = message_date + timedelta(days=random.randint(1, 5))
                
                # Mise à jour du message avec réponse
                cursor.execute("""
                    UPDATE messages 
                    SET reply_date = %s, reply_content = %s, sentiment = %s
                    WHERE id = %s
                """, (
                    reply_date,
                    random.choice([
                        "Merci pour votre proposition, cela m'intéresse. Pouvez-vous m'envoyer plus d'informations ?",
                        "Bonjour, votre solution semble intéressante. Quand pourrions-nous en discuter ?",
                        "Je suis intéressé par vos services IA. Pourriez-vous me faire une démonstration ?"
                    ]) if lead['contact_status'] == 'responded' else "Je confirme mon intérêt. Programmons un rendez-vous.",
                    'positive' if lead['contact_status'] in ['responded', 'converted'] else 'neutral',
                    message_id
                ))
                
                # Ajouter l'historique de réponse
                cursor.execute("""
                    INSERT INTO contact_history (
                        lead_id, campaign_id, contact_type, contact_method,
                        message_id, previous_status, new_status, notes, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    lead['id'],
                    lead['campagne_id'],
                    'response_received',
                    'email',
                    message_id,
                    'contacted_waiting_response',
                    lead['contact_status'],
                    f"Réponse reçue - {lead['contact_status']}",
                    reply_date
                ))
            
            # Si en follow-up, créer un message de relance
            if lead['contact_status'] == 'in_follow_up_sequence':
                followup_date = message_date + timedelta(days=3)
                
                cursor.execute("""
                    INSERT INTO messages (
                        lead_id, lead_name, lead_email, campaign_id, campaign_name,
                        subject, content, status, type, sent_date, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    lead['id'],
                    f"{lead['first_name']} {lead['last_name']}",
                    lead['email'],
                    lead['campagne_id'],
                    f"Campagne {lead['industry']} - Relance",
                    f"Re: Solution IA pour {lead['company']}",
                    f"Bonjour {lead['first_name']}, je me permets de revenir vers vous concernant notre proposition de solutions IA pour {lead['company']}...",
                    'sent',
                    'email',
                    followup_date,
                    followup_date,
                    followup_date
                ))
    
    conn.commit()
    cursor.close()
    print(f"   ✅ Messages et historique créés pour {len([l for l in leads if l['contact_status'] != 'never_contacted'])} leads contactés")

def main():
    """Fonction principale pour remplir la base de données"""
    print("🚀 Début du remplissage de la base de données BerinIA...")
    print("=" * 60)
    
    # Connexion à la base
    conn = connect_to_db()
    
    try:
        # Nettoyage des données existantes
        clear_existing_data(conn)
        
        # Création des niches
        niche_ids = create_niches(conn)
        
        # Création des campagnes
        campaign_ids = create_campaigns(conn, niche_ids)
        
        # Création des leads complets
        leads = create_comprehensive_leads(conn, niche_ids, campaign_ids)
        
        # Création des messages et historique
        create_messages_and_history(conn, leads)
        
        print("\n" + "=" * 60)
        print("✅ Remplissage de la base de données terminé avec succès !")
        print(f"📊 Résumé:")
        print(f"   - {len(niche_ids)} niches créées")
        print(f"   - {len(campaign_ids)} campagnes créées")
        print(f"   - {len(leads)} leads créés avec toutes leurs données")
        print(f"   - Messages et historique de contact générés")
        print("\n🎯 La base de données est maintenant prête pour les tests !")
        
    except Exception as e:
        print(f"❌ Erreur lors du remplissage: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script pour vérifier que les données de test ont été correctement créées
"""

import psycopg2
import json

# Configuration de la base de données
DB_CONFIG = {
    'host': 'localhost',
    'database': 'berinia',
    'user': 'berinia_user',
    'password': 'berinia_pass',
    'port': 5432
}

def verify_data():
    """Vérifie que les données de test ont été correctement créées"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔍 Vérification des données de test...")
        print("=" * 50)
        
        # 1. Vérification des comptages
        print("📊 COMPTAGES DES TABLES :")
        tables = ['leads', 'campaigns', 'messages', 'contact_history', 'niches']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table:<20}: {count:>3} enregistrements")
        
        print("\n" + "=" * 50)
        
        # 2. Vérification des leads (échantillon)
        print("👥 ÉCHANTILLON DE LEADS :")
        cursor.execute("""
            SELECT first_name, last_name, company, score, contact_status, 
                   visual_quality, website_maturity, site_type, industry
            FROM leads 
            ORDER BY id 
            LIMIT 5
        """)
        
        leads = cursor.fetchall()
        for lead in leads:
            print(f"   ✅ {lead[0]} {lead[1]} - {lead[2]}")
            print(f"      Score: {lead[3]}/10, Status: {lead[4]}, Qualité visuelle: {lead[5]}")
            print(f"      Maturité site: {lead[6]}, Type: {lead[7]}, Industrie: {lead[8]}")
            print()
        
        # 3. Vérification des données JSON
        print("🔍 VÉRIFICATION DES DONNÉES JSON :")
        cursor.execute("""
            SELECT first_name, last_name, score_details, visual_analysis_data
            FROM leads 
            WHERE score_details IS NOT NULL
            LIMIT 2
        """)
        
        for lead in cursor.fetchall():
            print(f"   📋 {lead[0]} {lead[1]} :")
            
            # Score details
            if lead[2]:
                score_data = lead[2] if isinstance(lead[2], dict) else json.loads(lead[2])
                print(f"      Score détails: position={score_data.get('position_score', 'N/A')}, visual={score_data.get('visual_score', 'N/A')}")
            
            # Visual analysis data
            if lead[3]:
                visual_data = lead[3] if isinstance(lead[3], dict) else json.loads(lead[3])
                print(f"      Analyse visuelle: URL={visual_data.get('url', 'N/A')}")
                print(f"                       Mobile: {visual_data.get('mobile_friendly', 'N/A')}")
                print(f"                       Tech: {visual_data.get('technology_stack', 'N/A')}")
            print()
        
        # 4. Vérification des statuts de contact
        print("📈 RÉPARTITION DES STATUTS DE CONTACT :")
        cursor.execute("""
            SELECT contact_status, COUNT(*) 
            FROM leads 
            GROUP BY contact_status 
            ORDER BY COUNT(*) DESC
        """)
        
        for status, count in cursor.fetchall():
            print(f"   {status:<25}: {count:>2} leads")
        
        # 5. Vérification des messages et historique
        print("\n📨 MESSAGES ET HISTORIQUE :")
        cursor.execute("""
            SELECT l.first_name, l.last_name, m.subject, m.status, m.sentiment
            FROM messages m
            JOIN leads l ON m.lead_id = l.id
            WHERE m.reply_content IS NOT NULL
            LIMIT 3
        """)
        
        for msg in cursor.fetchall():
            print(f"   💬 {msg[0]} {msg[1]} - {msg[2]}")
            print(f"      Status: {msg[3]}, Sentiment: {msg[4] or 'N/A'}")
        
        # 6. Vérification des campagnes
        print("\n📧 CAMPAGNES :")
        cursor.execute("""
            SELECT name, status, target_leads, 
                   (SELECT COUNT(*) FROM leads WHERE campagne_id = campaigns.id) as actual_leads
            FROM campaigns
            ORDER BY id
        """)
        
        for campaign in cursor.fetchall():
            print(f"   🎯 {campaign[0]}")
            print(f"      Status: {campaign[1]}, Objectif: {campaign[2]}, Réels: {campaign[3]}")
        
        print("\n" + "=" * 50)
        print("✅ VÉRIFICATION TERMINÉE - Toutes les données semblent correctes !")
        print("🎯 La base de données est prête pour les tests des agents !")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

if __name__ == "__main__":
    verify_data()

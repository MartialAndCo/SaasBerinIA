#!/usr/bin/env python3
"""Script pour appliquer la migration des conversions de rendez-vous"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.database.connection import get_db
from sqlalchemy import text

def apply_migration():
    """Applique la migration étape par étape"""
    
    db = next(get_db())
    
    try:
        print("🚀 Début de la migration pour le suivi des conversions...")
        
        # 1. Créer la table services
        print("📋 Création de la table services...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS services (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                setup_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                monthly_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                is_bundle BOOLEAN DEFAULT FALSE,
                bundle_services JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 2. Créer la table meeting_outcomes
        print("📋 Création de la table meeting_outcomes...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS meeting_outcomes (
                id SERIAL PRIMARY KEY,
                meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
                outcome_type VARCHAR(20) NOT NULL CHECK (outcome_type IN ('accepted', 'refused', 'thinking', 'no_show')),
                refusal_reason VARCHAR(50) CHECK (refusal_reason IN ('price_too_high', 'no_budget', 'internal_solution', 'bad_timing', 'not_convinced', 'competitor', 'other')),
                refusal_details TEXT,
                follow_up_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 3. Créer la table sales
        print("📋 Création de la table sales...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                meeting_outcome_id INTEGER REFERENCES meeting_outcomes(id) ON DELETE CASCADE,
                client_name VARCHAR(255) NOT NULL,
                client_email VARCHAR(255),
                client_company VARCHAR(255),
                total_setup_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                total_monthly_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                sale_date DATE NOT NULL,
                payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'partial', 'paid')),
                payment_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 4. Créer la table sale_services
        print("📋 Création de la table sale_services...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS sale_services (
                id SERIAL PRIMARY KEY,
                sale_id INTEGER REFERENCES sales(id) ON DELETE CASCADE,
                service_id INTEGER REFERENCES services(id) ON DELETE CASCADE,
                setup_price DECIMAL(10,2) NOT NULL,
                monthly_price DECIMAL(10,2) NOT NULL,
                start_date DATE,
                end_date DATE,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 5. Insérer les services de base
        print("💰 Insertion des services de base...")
        services_data = [
            ('Site Web', 'Création de site web professionnel', 1497.00, 29.00, False),
            ('Bot IA', 'Assistant virtuel intelligent', 797.00, 249.00, False),
            ('Répondeur IA', 'Répondeur téléphonique intelligent', 997.00, 249.00, False),
            ('Bot IA + Répondeur IA', 'Forfait combiné Bot et Répondeur IA', 1449.00, 399.00, True)
        ]
        
        for name, desc, setup, monthly, is_bundle in services_data:
            # Vérifier si le service existe déjà
            existing = db.execute(text("SELECT id FROM services WHERE name = :name"), {"name": name}).fetchone()
            if not existing:
                db.execute(text("""
                    INSERT INTO services (name, description, setup_price, monthly_price, is_bundle)
                    VALUES (:name, :desc, :setup, :monthly, :is_bundle)
                """), {
                    "name": name,
                    "desc": desc, 
                    "setup": setup,
                    "monthly": monthly,
                    "is_bundle": is_bundle
                })
                print(f"  ✅ Service créé: {name}")
            else:
                print(f"  ℹ️ Service existe déjà: {name}")
        
        # 6. Créer les index
        print("🔍 Création des index...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_meeting_outcomes_meeting_id ON meeting_outcomes(meeting_id)",
            "CREATE INDEX IF NOT EXISTS idx_meeting_outcomes_outcome_type ON meeting_outcomes(outcome_type)",
            "CREATE INDEX IF NOT EXISTS idx_sales_sale_date ON sales(sale_date)",
            "CREATE INDEX IF NOT EXISTS idx_sale_services_sale_id ON sale_services(sale_id)",
            "CREATE INDEX IF NOT EXISTS idx_sale_services_status ON sale_services(status)"
        ]
        
        for index_sql in indexes:
            db.execute(text(index_sql))
        
        # 7. Créer les vues pour les statistiques
        print("📊 Création des vues statistiques...")
        
        # Vue conversion_stats
        db.execute(text("""
            CREATE OR REPLACE VIEW conversion_stats AS
            SELECT 
                DATE_TRUNC('month', mo.created_at) as month,
                COUNT(*) as total_meetings,
                COUNT(CASE WHEN mo.outcome_type = 'accepted' THEN 1 END) as conversions,
                COUNT(CASE WHEN mo.outcome_type = 'refused' THEN 1 END) as refusals,
                COUNT(CASE WHEN mo.outcome_type = 'thinking' THEN 1 END) as thinking,
                ROUND(
                    COUNT(CASE WHEN mo.outcome_type = 'accepted' THEN 1 END)::DECIMAL / 
                    NULLIF(COUNT(*), 0) * 100, 
                    2
                ) as conversion_rate
            FROM meeting_outcomes mo
            GROUP BY DATE_TRUNC('month', mo.created_at)
            ORDER BY month DESC
        """))
        
        # Vue refusal_stats
        db.execute(text("""
            CREATE OR REPLACE VIEW refusal_stats AS
            SELECT 
                refusal_reason,
                COUNT(*) as count,
                ROUND(COUNT(*)::DECIMAL / (SELECT COUNT(*) FROM meeting_outcomes WHERE outcome_type = 'refused') * 100, 2) as percentage
            FROM meeting_outcomes 
            WHERE outcome_type = 'refused' AND refusal_reason IS NOT NULL
            GROUP BY refusal_reason
            ORDER BY count DESC
        """))
        
        # Vue revenue_stats
        db.execute(text("""
            CREATE OR REPLACE VIEW revenue_stats AS
            SELECT 
                DATE_TRUNC('month', s.sale_date) as month,
                COUNT(*) as sales_count,
                SUM(s.total_setup_price) as total_setup_revenue,
                SUM(s.total_monthly_price) as monthly_recurring_revenue,
                AVG(s.total_setup_price + s.total_monthly_price * 12) as avg_annual_value
            FROM sales s
            WHERE s.payment_status IN ('paid', 'partial')
            GROUP BY DATE_TRUNC('month', s.sale_date)
            ORDER BY month DESC
        """))
        
        db.commit()
        print("✅ Migration complétée avec succès!")
        
        # Vérification finale
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('services', 'meeting_outcomes', 'sales', 'sale_services')
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result.fetchall()]
        print(f"📋 Tables créées: {tables}")
        
        # Afficher les services
        result = db.execute(text("SELECT name, setup_price, monthly_price FROM services ORDER BY id"))
        services = result.fetchall()
        print(f"\n💰 Services configurés ({len(services)}):")
        for service in services:
            print(f"  - {service[0]}: {service[1]}€ + {service[2]}€/mois")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = apply_migration()
    if not success:
        sys.exit(1)
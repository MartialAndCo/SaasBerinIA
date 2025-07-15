-- Migration pour ajouter le suivi des conversions de rendez-vous
-- Date: 2025-06-30

-- Table des services disponibles
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    setup_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    monthly_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    is_bundle BOOLEAN DEFAULT FALSE,
    bundle_services JSONB, -- Pour les forfaits combinés
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des résultats de rendez-vous
CREATE TABLE IF NOT EXISTS meeting_outcomes (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    outcome_type VARCHAR(20) NOT NULL CHECK (outcome_type IN ('accepted', 'refused', 'thinking', 'no_show')),
    refusal_reason VARCHAR(50) CHECK (refusal_reason IN ('price_too_high', 'no_budget', 'internal_solution', 'bad_timing', 'not_convinced', 'competitor', 'other')),
    refusal_details TEXT, -- Pour "autre" ou précisions
    follow_up_date DATE, -- Pour les "thinking"
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des ventes réalisées
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
);

-- Table des services achetés par vente
CREATE TABLE IF NOT EXISTS sale_services (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER REFERENCES sales(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES services(id) ON DELETE CASCADE,
    setup_price DECIMAL(10,2) NOT NULL,
    monthly_price DECIMAL(10,2) NOT NULL,
    start_date DATE,
    end_date DATE, -- NULL pour abonnements actifs
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insérer les services de base
INSERT INTO services (name, description, setup_price, monthly_price, is_bundle) VALUES
('Site Web', 'Création de site web professionnel', 1497.00, 29.00, FALSE),
('Bot IA', 'Assistant virtuel intelligent', 797.00, 249.00, FALSE),
('Répondeur IA', 'Répondeur téléphonique intelligent', 997.00, 249.00, FALSE),
('Bot IA + Répondeur IA', 'Forfait combiné Bot et Répondeur IA', 1449.00, 399.00, TRUE)
ON CONFLICT (name) DO NOTHING;

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_meeting_outcomes_meeting_id ON meeting_outcomes(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_outcomes_outcome_type ON meeting_outcomes(outcome_type);
CREATE INDEX IF NOT EXISTS idx_sales_sale_date ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sale_services_sale_id ON sale_services(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_services_status ON sale_services(status);

-- Vue pour les statistiques de conversion
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
ORDER BY month DESC;

-- Vue pour les raisons de refus
CREATE OR REPLACE VIEW refusal_stats AS
SELECT 
    refusal_reason,
    COUNT(*) as count,
    ROUND(COUNT(*)::DECIMAL / (SELECT COUNT(*) FROM meeting_outcomes WHERE outcome_type = 'refused') * 100, 2) as percentage
FROM meeting_outcomes 
WHERE outcome_type = 'refused' AND refusal_reason IS NOT NULL
GROUP BY refusal_reason
ORDER BY count DESC;

-- Vue pour le CA généré
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
ORDER BY month DESC;
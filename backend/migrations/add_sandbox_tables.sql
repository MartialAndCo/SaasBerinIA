-- Migration pour ajouter les tables du sandbox de messagerie
-- Date: 2025-01-05

-- Table pour les leads de test du sandbox
CREATE TABLE IF NOT EXISTS sandbox_leads (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR,
    email VARCHAR NOT NULL,
    phone VARCHAR,
    company VARCHAR,
    position VARCHAR,
    linkedin_url VARCHAR,
    website VARCHAR,
    entreprise VARCHAR,
    industry VARCHAR,
    niche_id INTEGER,
    source VARCHAR,
    status VARCHAR DEFAULT 'new',
    score INTEGER,
    score_details JSONB,
    validation_status VARCHAR DEFAULT 'unvalidated',
    last_contact TIMESTAMP,
    notes TEXT,
    
    -- Champs d'analyse visuelle
    visual_score INTEGER,
    visual_analysis_data JSONB,
    has_popup BOOLEAN,
    popup_removed BOOLEAN,
    screenshot_path VARCHAR,
    enhanced_screenshot_path VARCHAR,
    visual_analysis_date TIMESTAMP,
    site_type VARCHAR,
    visual_quality INTEGER,
    website_maturity VARCHAR,
    design_strengths TEXT[],
    design_weaknesses TEXT[],
    
    -- Champs spécifiques au sandbox
    is_test BOOLEAN DEFAULT TRUE,
    test_platform VARCHAR NOT NULL,
    template_used VARCHAR,
    created_by_user VARCHAR,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Relations
    campagne_id INTEGER REFERENCES campaigns(id)
);

-- Table pour stocker les conversations du sandbox
CREATE TABLE IF NOT EXISTS sandbox_conversations (
    id SERIAL PRIMARY KEY,
    sandbox_lead_id INTEGER REFERENCES sandbox_leads(id) ON DELETE CASCADE,
    messages JSONB NOT NULL,
    platform VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour les templates de profils prédéfinis
CREATE TABLE IF NOT EXISTS sandbox_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    template_data JSONB NOT NULL,
    category VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_sandbox_leads_test_platform ON sandbox_leads(test_platform);
CREATE INDEX IF NOT EXISTS idx_sandbox_leads_created_by_user ON sandbox_leads(created_by_user);
CREATE INDEX IF NOT EXISTS idx_sandbox_conversations_lead_id ON sandbox_conversations(sandbox_lead_id);
CREATE INDEX IF NOT EXISTS idx_sandbox_conversations_platform ON sandbox_conversations(platform);
CREATE INDEX IF NOT EXISTS idx_sandbox_templates_category ON sandbox_templates(category);

-- Insérer quelques templates par défaut
INSERT INTO sandbox_templates (name, description, template_data, category) VALUES 
(
    'Restaurant Traditionnel',
    'Profil type d''un restaurant traditionnel avec site basique',
    '{
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@legourmand.fr",
        "phone": "0123456789",
        "company": "Le Gourmand",
        "position": "Propriétaire",
        "website": "www.legourmand-lyon.fr",
        "industry": "Restauration",
        "score": 65,
        "visual_score": 45,
        "site_type": "vitrine",
        "visual_quality": 6,
        "website_maturity": "basique",
        "has_popup": false,
        "design_strengths": ["Menu visible", "Contact clair"],
        "design_weaknesses": ["Design daté", "Pas responsive"]
    }',
    'restaurant'
),
(
    'E-commerce Moderne',
    'Profil type d''un e-commerce avec site avancé',
    '{
        "first_name": "Marie",
        "last_name": "Martin",
        "email": "marie@boutique-tendance.com",
        "phone": "0987654321",
        "company": "Boutique Tendance",
        "position": "Directrice",
        "website": "www.boutique-tendance.com",
        "industry": "Commerce",
        "score": 85,
        "visual_score": 90,
        "site_type": "e-commerce",
        "visual_quality": 9,
        "website_maturity": "avancé",
        "has_popup": true,
        "popup_removed": true,
        "design_strengths": ["Design moderne", "UX optimisée", "Mobile friendly"],
        "design_weaknesses": ["Popup intrusive"]
    }',
    'commerce'
),
(
    'Artisan Local',
    'Profil type d''un artisan avec site intermédiaire',
    '{
        "first_name": "Pierre",
        "last_name": "Moreau",
        "email": "contact@plomberie-moreau.fr",
        "phone": "0456789123",
        "company": "Plomberie Moreau",
        "position": "Artisan plombier",
        "website": "www.plomberie-moreau.fr",
        "industry": "Artisanat",
        "score": 70,
        "visual_score": 55,
        "site_type": "vitrine",
        "visual_quality": 7,
        "website_maturity": "intermédiaire",
        "has_popup": false,
        "design_strengths": ["Informations claires", "Témoignages clients"],
        "design_weaknesses": ["Navigation confuse", "Images de mauvaise qualité"]
    }',
    'artisan'
);

-- Message de confirmation
SELECT 'Tables sandbox créées avec succès ! Templates par défaut ajoutés.' as message;

-- Migration pour ajouter les champs d'analyse visuelle à la table leads
-- Cette migration ajoute les champs nécessaires pour stocker les données générées par le VisualAnalyzer

-- Connexion à la base de données
\c berinia;

-- Ajout des champs d'analyse visuelle à la table leads
ALTER TABLE leads
ADD COLUMN visual_score INTEGER,
ADD COLUMN visual_analysis_data JSONB,
ADD COLUMN has_popup BOOLEAN,
ADD COLUMN popup_removed BOOLEAN,
ADD COLUMN screenshot_path VARCHAR(255),
ADD COLUMN enhanced_screenshot_path VARCHAR(255),
ADD COLUMN visual_analysis_date TIMESTAMP,
ADD COLUMN site_type VARCHAR(100),
ADD COLUMN visual_quality INTEGER,
ADD COLUMN website_maturity VARCHAR(50),
ADD COLUMN design_strengths TEXT[],
ADD COLUMN design_weaknesses TEXT[];

-- Création d'index pour les nouveaux champs
CREATE INDEX idx_leads_visual_score ON leads(visual_score);
CREATE INDEX idx_leads_visual_analysis_date ON leads(visual_analysis_date);
CREATE INDEX idx_leads_site_type ON leads(site_type);
CREATE INDEX idx_leads_website_maturity ON leads(website_maturity);

-- Message de fin
SELECT 'Champs d''analyse visuelle ajoutés à la table leads avec succès!' as message;

-- Migration: Ajout de la colonne web_metadata à la table leads
-- Date: 2025-05-05

-- Vérifier d'abord si la colonne existe déjà
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'web_metadata'
    ) THEN
        -- Ajouter la colonne web_metadata de type JSONB pour stocker les métadonnées web
        ALTER TABLE leads ADD COLUMN web_metadata JSONB;
        
        -- Ajouter un commentaire explicatif sur la colonne
        COMMENT ON COLUMN leads.web_metadata IS 'Métadonnées web du lead (présence web, maturité digitale, technologies détectées)';

        -- Créer un index GIN sur la colonne pour améliorer les performances des requêtes
        CREATE INDEX idx_leads_web_metadata ON leads USING GIN (web_metadata);
        
        RAISE NOTICE 'Colonne web_metadata ajoutée avec succès à la table leads';
    ELSE
        RAISE NOTICE 'La colonne web_metadata existe déjà dans la table leads';
    END IF;
END $$;

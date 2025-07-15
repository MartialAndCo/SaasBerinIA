-- Migration pour ajouter le système de tracking des contacts
-- Cette migration ajoute les champs et tables nécessaires pour tracker l'état des contacts avec les leads

-- Ajout du champ contact_status à la table leads
ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_status VARCHAR(50) DEFAULT 'never_contacted';

-- Création de la table contact_history pour l'historique des contacts
CREATE TABLE IF NOT EXISTS contact_history (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
    contact_type VARCHAR(50) NOT NULL, -- 'initial', 'follow_up', 'response_received'
    contact_method VARCHAR(20) NOT NULL, -- 'email', 'sms', 'phone'
    message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création des index pour la table contact_history
CREATE INDEX IF NOT EXISTS idx_contact_history_lead_id ON contact_history(lead_id);
CREATE INDEX IF NOT EXISTS idx_contact_history_campaign_id ON contact_history(campaign_id);
CREATE INDEX IF NOT EXISTS idx_contact_history_created_at ON contact_history(created_at);
CREATE INDEX IF NOT EXISTS idx_contact_history_contact_type ON contact_history(contact_type);

-- Ajout d'un champ last_contact_status_update à la table leads
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_contact_status_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Index pour le nouveau champ contact_status
CREATE INDEX IF NOT EXISTS idx_leads_contact_status ON leads(contact_status);

-- Fonction pour mettre à jour automatiquement last_contact_status_update
CREATE OR REPLACE FUNCTION update_lead_contact_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_contact_status_update = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour automatiquement le timestamp quand contact_status change
DROP TRIGGER IF EXISTS trigger_update_lead_contact_timestamp ON leads;
CREATE TRIGGER trigger_update_lead_contact_timestamp
    BEFORE UPDATE ON leads
    FOR EACH ROW
    WHEN (OLD.contact_status IS DISTINCT FROM NEW.contact_status)
    EXECUTE FUNCTION update_lead_contact_timestamp();

-- Fonction pour ajouter automatiquement une entrée dans contact_history
CREATE OR REPLACE FUNCTION log_contact_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Seulement si le contact_status a changé
    IF OLD.contact_status IS DISTINCT FROM NEW.contact_status THEN
        INSERT INTO contact_history (
            lead_id,
            contact_type,
            contact_method,
            previous_status,
            new_status,
            notes
        ) VALUES (
            NEW.id,
            CASE 
                WHEN NEW.contact_status = 'contacted_waiting_response' THEN 'initial'
                WHEN NEW.contact_status = 'in_follow_up_sequence' THEN 'follow_up'
                WHEN NEW.contact_status = 'responded' THEN 'response_received'
                ELSE 'status_change'
            END,
            'email', -- Par défaut, peut être mis à jour manuellement
            OLD.contact_status,
            NEW.contact_status,
            'Automatic status update'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour logger automatiquement les changements de statut
DROP TRIGGER IF EXISTS trigger_log_contact_status_change ON leads;
CREATE TRIGGER trigger_log_contact_status_change
    AFTER UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION log_contact_status_change();

-- Mise à jour des données existantes : initialiser contact_status basé sur les données existantes
UPDATE leads 
SET contact_status = CASE 
    WHEN last_contact IS NOT NULL THEN 'contacted_waiting_response'
    ELSE 'never_contacted'
END
WHERE contact_status = 'never_contacted';

-- Ajout de contraintes pour valider les valeurs de contact_status
ALTER TABLE leads 
ADD CONSTRAINT chk_contact_status 
CHECK (contact_status IN (
    'never_contacted',
    'contacted_waiting_response', 
    'in_follow_up_sequence',
    'responded',
    'converted',
    'unsubscribed',
    'bounced'
));

-- Ajout de contraintes pour valider les valeurs de contact_type
ALTER TABLE contact_history 
ADD CONSTRAINT chk_contact_type 
CHECK (contact_type IN (
    'initial',
    'follow_up', 
    'response_received',
    'status_change',
    'conversion',
    'unsubscribe'
));

-- Ajout de contraintes pour valider les valeurs de contact_method
ALTER TABLE contact_history 
ADD CONSTRAINT chk_contact_method 
CHECK (contact_method IN ('email', 'sms', 'phone', 'linkedin', 'other'));

-- Commentaires pour documenter les nouvelles colonnes et tables
COMMENT ON COLUMN leads.contact_status IS 'Statut actuel du contact avec ce lead';
COMMENT ON COLUMN leads.last_contact_status_update IS 'Timestamp de la dernière mise à jour du contact_status';
COMMENT ON TABLE contact_history IS 'Historique de tous les contacts et changements de statut pour chaque lead';
COMMENT ON COLUMN contact_history.contact_type IS 'Type de contact : initial, follow_up, response_received, etc.';
COMMENT ON COLUMN contact_history.contact_method IS 'Méthode de contact utilisée : email, sms, phone, etc.';

SELECT 'Système de tracking des contacts ajouté avec succès!' as message;

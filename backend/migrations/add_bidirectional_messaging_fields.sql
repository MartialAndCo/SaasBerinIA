-- Migration pour ajouter les champs nécessaires à la messagerie bidirectionnelle
-- Date: 2025-05-27
-- Auteur: Assistant IA

-- Ajouter les champs manquants pour la messagerie conversationnelle
ALTER TABLE messages ADD COLUMN IF NOT EXISTS direction VARCHAR DEFAULT 'outbound';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS sender_type VARCHAR DEFAULT 'ai';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS thread_id VARCHAR;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_type VARCHAR DEFAULT 'email';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS sender_name VARCHAR;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS received_date TIMESTAMP;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_id_external VARCHAR; -- Pour les IDs de messages externes (Instantly, Twilio)

-- Créer des index pour optimiser les requêtes conversationnelles
CREATE INDEX IF NOT EXISTS idx_messages_direction ON messages(direction);
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_type ON messages(sender_type);
CREATE INDEX IF NOT EXISTS idx_messages_message_type ON messages(message_type);
CREATE INDEX IF NOT EXISTS idx_messages_received_date ON messages(received_date);

-- Commentaires sur les nouveaux champs
COMMENT ON COLUMN messages.direction IS 'Direction du message: inbound (reçu) ou outbound (envoyé)';
COMMENT ON COLUMN messages.sender_type IS 'Type d''expéditeur: ai (BerinIA), user (utilisateur manuel), lead (prospect)';
COMMENT ON COLUMN messages.thread_id IS 'Identifiant de fil de conversation, généralement lead_id pour grouper par conversation';
COMMENT ON COLUMN messages.message_type IS 'Type de message: email, sms, whatsapp, etc.';
COMMENT ON COLUMN messages.sender_name IS 'Nom de l''expéditeur (pour messages entrants)';
COMMENT ON COLUMN messages.received_date IS 'Date de réception (pour messages entrants)';
COMMENT ON COLUMN messages.message_id_external IS 'ID du message dans le système externe (Instantly, Twilio, etc.)';

-- Mise à jour des données existantes pour compatibilité
UPDATE messages SET 
    direction = 'outbound',
    sender_type = 'ai',
    thread_id = CAST(lead_id AS VARCHAR),
    message_type = 'email',
    sender_name = 'BerinIA'
WHERE direction IS NULL;

-- Migration pour ajouter les tables de paramètres IA
-- Fichier: add_ai_settings_tables.sql

-- Table pour les paramètres IA par conversation
CREATE TABLE IF NOT EXISTS conversation_ai_settings (
    thread_id VARCHAR(255) PRIMARY KEY,
    ai_enabled BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour les paramètres globaux IA
CREATE TABLE IF NOT EXISTS global_ai_settings (
    key VARCHAR(255) PRIMARY KEY,
    value BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertion des paramètres par défaut
INSERT INTO global_ai_settings (key, value) 
VALUES ('ai_enabled', TRUE)
ON CONFLICT (key) DO NOTHING;

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_conversation_ai_settings_thread_id 
ON conversation_ai_settings(thread_id);

CREATE INDEX IF NOT EXISTS idx_global_ai_settings_key 
ON global_ai_settings(key);

-- Commentaires pour documentation
COMMENT ON TABLE conversation_ai_settings IS 'Paramètres IA spécifiques par conversation';
COMMENT ON TABLE global_ai_settings IS 'Paramètres IA globaux du système';
COMMENT ON COLUMN conversation_ai_settings.thread_id IS 'Identifiant unique de la conversation';
COMMENT ON COLUMN conversation_ai_settings.ai_enabled IS 'IA activée (true) ou désactivée (false) pour cette conversation';
COMMENT ON COLUMN global_ai_settings.key IS 'Clé du paramètre global';
COMMENT ON COLUMN global_ai_settings.value IS 'Valeur du paramètre (true/false)';

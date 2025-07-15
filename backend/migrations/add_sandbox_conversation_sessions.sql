-- Migration pour ajouter le système de sessions aux conversations sandbox
-- Objectif: Permettre le reset/réinitialisation et la persistance des conversations

ALTER TABLE sandbox_conversations 
ADD COLUMN conversation_session_id VARCHAR(100) DEFAULT NULL;

ALTER TABLE sandbox_conversations 
ADD COLUMN message_order INTEGER DEFAULT 0;

ALTER TABLE sandbox_conversations 
ADD COLUMN message_type VARCHAR(20) DEFAULT 'exchange'; -- 'start', 'user', 'ai', 'exchange'

-- Supprimer les anciennes colonnes qui ne servent plus
ALTER TABLE sandbox_conversations 
DROP COLUMN IF EXISTS user_message;

ALTER TABLE sandbox_conversations 
DROP COLUMN IF EXISTS ai_response;

ALTER TABLE sandbox_conversations 
DROP COLUMN IF EXISTS action;

-- Modifier la colonne messages pour avoir un format plus structuré
-- Elle contiendra maintenant: {"user": "message utilisateur", "ai": "réponse IA", "timestamp": "...", "platform": "sms"}

-- Ajouter un index sur conversation_session_id pour les performances
CREATE INDEX IF NOT EXISTS idx_sandbox_conversations_session_id 
ON sandbox_conversations(conversation_session_id);

-- Ajouter un index composé pour récupérer l'historique ordonné
CREATE INDEX IF NOT EXISTS idx_sandbox_conversations_session_order 
ON sandbox_conversations(conversation_session_id, message_order);

-- Commentaire pour expliquer le nouveau système
COMMENT ON COLUMN sandbox_conversations.conversation_session_id IS 
'Identifiant unique de session de conversation (ex: conv_20250606_1234567)';

COMMENT ON COLUMN sandbox_conversations.message_order IS 
'Ordre chronologique des messages dans la session (1, 2, 3...)';

COMMENT ON COLUMN sandbox_conversations.message_type IS 
'Type de message: start (premier), user (utilisateur), ai (IA), exchange (échange complet)';

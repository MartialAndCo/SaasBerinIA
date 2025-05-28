-- Migration pour supprimer le champ from_email devenu obsolète
-- suite à la mise à jour de l'intégration Instantly.ai

-- Supprimer l'entrée from_email de la table system_settings
DELETE FROM system_settings WHERE name = 'from_email' AND category = 'integrations';

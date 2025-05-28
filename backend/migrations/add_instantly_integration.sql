-- Migration pour ajouter les paramètres d'intégration Instantly.ai et WhatsApp à la table system_settings

-- Vérifier et ajouter les paramètres Instantly.ai
INSERT INTO system_settings (name, value, data_type, category, description, is_editable)
VALUES
    ('instantly_api_key', '', 'string', 'integrations', 'Clé API pour le service Instantly.ai', true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO system_settings (name, value, data_type, category, description, is_editable)
VALUES
    ('instantly_integration_active', 'false', 'boolean', 'integrations', 'Indique si l''intégration Instantly.ai est active', true)
ON CONFLICT (name) DO NOTHING;

-- Vérifier et ajouter les paramètres WhatsApp
INSERT INTO system_settings (name, value, data_type, category, description, is_editable)
VALUES
    ('whatsapp_integration_active', 'false', 'boolean', 'integrations', 'Indique si l''intégration WhatsApp est active', true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO system_settings (name, value, data_type, category, description, is_editable)
VALUES
    ('whatsapp_notification_group', '', 'string', 'integrations', 'ID du groupe WhatsApp pour les notifications', true)
ON CONFLICT (name) DO NOTHING;

-- Ajouter le canal de notification WhatsApp
INSERT INTO system_settings (name, value, data_type, category, description, is_editable)
VALUES
    ('report_channel_whatsapp', 'false', 'boolean', 'scheduling', 'Envoyer les rapports quotidiens via WhatsApp', true)
ON CONFLICT (name) DO NOTHING;

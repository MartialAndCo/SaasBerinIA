-- Script de création de la base de données BerinIA
-- Ce script supprime et recrée toutes les tables nécessaires au système BerinIA

-- Création de la base de données (déjà fait en dehors de ce script)
-- CREATE DATABASE berinia;

-- Connexion à la base de données
\c berinia;

-- Suppression des tables existantes (si elles existent)
DROP TABLE IF EXISTS agent_interactions CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS agent_logs CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS niches CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;
DROP TABLE IF EXISTS logs CASCADE;

-- Création des tables

-- Table des utilisateurs
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Table des agents
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'inactive',
    config JSONB,
    last_run TIMESTAMP,
    leads_generes INTEGER DEFAULT 0,
    campagnes_actives INTEGER DEFAULT 0,
    derniere_execution TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des logs des agents
CREATE TABLE agent_logs (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des niches de marché
CREATE TABLE niches (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    keywords TEXT[],
    created_by INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'active',
    exploration_depth INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des leads (prospects)
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    position VARCHAR(100),
    linkedin_url VARCHAR(255),
    website VARCHAR(255),
    entreprise VARCHAR(255),
    industry VARCHAR(100),
    niche_id INTEGER REFERENCES niches(id),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    score INTEGER,
    score_details JSONB,
    validation_status VARCHAR(50) DEFAULT 'unvalidated',
    last_contact TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des campaigns
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    niche_id INTEGER REFERENCES niches(id),
    target_leads INTEGER DEFAULT 0,
    agent VARCHAR(100),
    status VARCHAR(50) DEFAULT 'draft',
    message_template TEXT,
    subject_template VARCHAR(255),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    lead_name VARCHAR(255),
    lead_email VARCHAR(255),
    campaign_id INTEGER REFERENCES campaigns(id),
    campaign_name VARCHAR(255),
    subject VARCHAR(255),
    content TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    type VARCHAR(50) DEFAULT 'email',
    sent_date TIMESTAMP,
    open_date TIMESTAMP,
    reply_date TIMESTAMP,
    reply_content TEXT,
    sentiment VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des interactions entre agents
CREATE TABLE agent_interactions (
    id SERIAL PRIMARY KEY,
    from_agent_id INTEGER REFERENCES agents(id),
    to_agent_id INTEGER REFERENCES agents(id),
    message TEXT NOT NULL,
    context_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'sent',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des tâches planifiées
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    action VARCHAR(100) NOT NULL,
    parameters JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 3,
    scheduled_time TIMESTAMP NOT NULL,
    execution_time TIMESTAMP,
    is_recurring BOOLEAN DEFAULT false,
    recurrence_interval INTEGER, -- en secondes
    last_run TIMESTAMP,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des paramètres système
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    data_type VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    is_editable BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des logs système
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL,
    module VARCHAR(100),
    message TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création des index

-- Index pour les agents
CREATE INDEX idx_agents_name ON agents(name);
CREATE INDEX idx_agents_type ON agents(type);
CREATE INDEX idx_agents_status ON agents(status);

-- Index pour les logs des agents
CREATE INDEX idx_agent_logs_agent_id ON agent_logs(agent_id);
CREATE INDEX idx_agent_logs_timestamp ON agent_logs(timestamp);

-- Index pour les niches
CREATE INDEX idx_niches_name ON niches(name);
CREATE INDEX idx_niches_status ON niches(status);

-- Index pour les leads
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_company ON leads(company);
CREATE INDEX idx_leads_niche_id ON leads(niche_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_score ON leads(score);

-- Index pour les campagnes
CREATE INDEX idx_campaigns_name ON campaigns(name);
CREATE INDEX idx_campaigns_niche_id ON campaigns(niche_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- Index pour les messages
CREATE INDEX idx_messages_lead_id ON messages(lead_id);
CREATE INDEX idx_messages_campaign_id ON messages(campaign_id);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_sent_date ON messages(sent_date);

-- Index pour les interactions entre agents
CREATE INDEX idx_agent_interactions_from_agent_id ON agent_interactions(from_agent_id);
CREATE INDEX idx_agent_interactions_to_agent_id ON agent_interactions(to_agent_id);
CREATE INDEX idx_agent_interactions_created_at ON agent_interactions(created_at);

-- Index pour les tâches
CREATE INDEX idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_scheduled_time ON tasks(scheduled_time);
CREATE INDEX idx_tasks_is_recurring ON tasks(is_recurring);

-- Insertion de données initiales

-- Utilisateur admin par défaut (mot de passe: berinia_admin)
INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser) 
VALUES ('admin@berinia.io', '$2b$12$CwTycUXWue0Thq9StjUM0uECa6kI.DF.FTnlRXsOH2tHBGsyukOcy', 'Admin', true, true);

-- Agents principaux du système
INSERT INTO agents (name, description, type, status) VALUES 
('OverseerAgent', 'Agent superviseur qui coordonne les autres agents', 'orchestrator', 'active'),
('AdminInterpreterAgent', 'Agent qui interprète les commandes administratives', 'interface', 'active'),
('SchedulerAgent', 'Agent qui planifie et exécute les tâches', 'system', 'active'),
('LoggerAgent', 'Agent qui gère les journaux du système', 'system', 'active'),
('ScrapingSupervisorAgent', 'Superviseur du processus de scraping', 'supervisor', 'active'),
('QualificationSupervisorAgent', 'Superviseur du processus de qualification', 'supervisor', 'active'),
('ProspectionSupervisorAgent', 'Superviseur du processus de prospection', 'supervisor', 'active'),
('NicheExplorerAgent', 'Agent d''exploration de niches', 'worker', 'active'),
('ScraperAgent', 'Agent de collecte de données', 'worker', 'active'),
('CleanerAgent', 'Agent de nettoyage de données', 'worker', 'active'),
('ValidatorAgent', 'Agent de validation de leads', 'worker', 'active'),
('ScoringAgent', 'Agent d''attribution de scores', 'worker', 'active'),
('DuplicateCheckerAgent', 'Agent de détection de doublons', 'worker', 'active'),
('MessagingAgent', 'Agent de création de messages', 'worker', 'active'),
('FollowUpAgent', 'Agent de relance', 'worker', 'active'),
('ResponseListenerAgent', 'Agent d''écoute des réponses', 'worker', 'active'),
('ResponseInterpreterAgent', 'Agent d''interprétation des réponses', 'worker', 'active'),
('PivotStrategyAgent', 'Agent de stratégie de pivot', 'strategic', 'active');

-- Paramètres système initiaux
INSERT INTO system_settings (name, value, data_type, category, description) VALUES
('openai_api_key', '', 'string', 'api', 'Clé API pour OpenAI'),
('openai_model', 'gpt-4', 'string', 'llm', 'Modèle OpenAI à utiliser'),
('max_tokens_response', '2000', 'integer', 'llm', 'Nombre maximum de tokens pour les réponses'),
('scraping_rate_limit', '10', 'integer', 'scraping', 'Limite de requêtes par minute pour le scraping'),
('max_leads_per_campaign', '100', 'integer', 'campaign', 'Nombre maximum de leads par campagne'),
('email_sending_interval', '60', 'integer', 'messaging', 'Intervalle entre les envois d''emails (secondes)'),
('system_language', 'fr', 'string', 'system', 'Langue du système'),
('log_level', 'info', 'string', 'logging', 'Niveau de journalisation'),
('webhook_secret', '', 'string', 'security', 'Clé secrète pour les webhooks');

-- Message de fin
SELECT 'Base de données BerinIA initialisée avec succès!' as message;

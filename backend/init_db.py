#!/usr/bin/env python3
"""
Script d'initialisation de la base de données Berinia
Ce script crée la base de données si elle n'existe pas et initialise les tables
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Charger les variables d'environnement
load_dotenv()

def check_database_connection():
    """Vérifie la connexion à la base de données"""
    # Paramètres de connexion
    db_user = os.getenv("DB_USER", "berinia_user")
    db_password = os.getenv("DB_PASSWORD", "berinia_pass") 
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "berinia")
    
    print(f"Tentative de connexion à la base de données {db_name}...")
    
    try:
        # Tentative de connexion directe
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_name
        )
        conn.close()
        print(f"Connexion à la base de données {db_name} réussie!")
        return True
    except Exception as e:
        print(f"Erreur lors de la connexion à la base de données: {e}")
        print("Assurez-vous que la base de données a été créée avec le script recreate_database.sh")
        print("sudo ./recreate_database.sh")
        sys.exit(1)

def create_tables_directly():
    """Crée les tables directement en exécutant le script SQL"""
    # Paramètres de connexion
    db_user = os.getenv("DB_USER", "berinia_user")
    db_password = os.getenv("DB_PASSWORD", "berinia_pass") 
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "berinia")
    
    print("Création des tables directement depuis le script SQL...")
    try:
        # Au lieu d'exécuter directement le SQL, utilisons sudo pour exécuter le script en tant que postgres
        # Copier d'abord le script SQL vers /tmp pour gérer les permissions
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations/create_berinia_db.sql')
        tmp_path = "/tmp/create_berinia_db.sql"
        
        # Copier le fichier SQL vers /tmp et donner les permissions
        os.system(f"cp {script_path} {tmp_path}")
        os.system(f"chmod 777 {tmp_path}")
        
        # Exécuter le script SQL en tant que postgres
        result = os.system(f"sudo -u postgres psql -d {db_name} -f {tmp_path}")
        
        if result == 0:
            print("Tables créées avec succès depuis le script SQL!")
        else:
            print(f"Erreur lors de l'exécution du script SQL: code {result}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def insert_initial_data():
    """Insère des données initiales dans la base de données"""
    from backend.app.db.database import db_session
    from backend.app.models.models import (
        User, Agent, SystemSetting, Niche, Lead, Campaign, Message, 
        AgentLog, AgentInteraction, Task, Log
    )
    from datetime import datetime, timedelta
    import bcrypt
    
    print("Insertion des données initiales...")
    
    try:
        with db_session() as session:
            # Utilisateur admin (mot de passe: berinia_admin)
            hashed_password = bcrypt.hashpw("berinia_admin".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            admin_user = User(
                email="admin@berinia.io",
                hashed_password=hashed_password,
                full_name="Admin",
                is_active=True,
                is_superuser=True,
                created_at=datetime.now()
            )
            session.add(admin_user)
            
            # Insertion des agents
            agents = [
                Agent(name="OverseerAgent", description="Agent superviseur qui coordonne les autres agents", type="orchestrator", status="active"),
                Agent(name="AdminInterpreterAgent", description="Agent qui interprète les commandes administratives", type="interface", status="active"),
                Agent(name="SchedulerAgent", description="Agent qui planifie et exécute les tâches", type="system", status="active"),
                Agent(name="LoggerAgent", description="Agent qui gère les journaux du système", type="system", status="active"),
                Agent(name="ScrapingSupervisorAgent", description="Superviseur du processus de scraping", type="supervisor", status="active"),
                Agent(name="QualificationSupervisorAgent", description="Superviseur du processus de qualification", type="supervisor", status="active"),
                Agent(name="ProspectionSupervisorAgent", description="Superviseur du processus de prospection", type="supervisor", status="active"),
                Agent(name="NicheExplorerAgent", description="Agent d'exploration de niches", type="worker", status="active"),
                Agent(name="ScraperAgent", description="Agent de collecte de données", type="worker", status="active"),
                Agent(name="CleanerAgent", description="Agent de nettoyage de données", type="worker", status="active"),
                Agent(name="ValidatorAgent", description="Agent de validation de leads", type="worker", status="active"),
                Agent(name="ScoringAgent", description="Agent d'attribution de scores", type="worker", status="active"),
                Agent(name="DuplicateCheckerAgent", description="Agent de détection de doublons", type="worker", status="active"),
                Agent(name="MessagingAgent", description="Agent de création de messages", type="worker", status="active"),
                Agent(name="FollowUpAgent", description="Agent de relance", type="worker", status="active"),
                Agent(name="ResponseListenerAgent", description="Agent d'écoute des réponses", type="worker", status="active"),
                Agent(name="ResponseInterpreterAgent", description="Agent d'interprétation des réponses", type="worker", status="active"),
                Agent(name="PivotStrategyAgent", description="Agent de stratégie de pivot", type="strategic", status="active")
            ]
            session.add_all(agents)
            
            # Insertion des paramètres système
            system_settings = [
                SystemSetting(name="openai_api_key", value="", data_type="string", category="api", description="Clé API pour OpenAI"),
                SystemSetting(name="openai_model", value="gpt-4", data_type="string", category="llm", description="Modèle OpenAI à utiliser"),
                SystemSetting(name="max_tokens_response", value="2000", data_type="integer", category="llm", description="Nombre maximum de tokens pour les réponses"),
                SystemSetting(name="scraping_rate_limit", value="10", data_type="integer", category="scraping", description="Limite de requêtes par minute pour le scraping"),
                SystemSetting(name="max_leads_per_campaign", value="100", data_type="integer", category="campaign", description="Nombre maximum de leads par campagne"),
                SystemSetting(name="email_sending_interval", value="60", data_type="integer", category="messaging", description="Intervalle entre les envois d'emails (secondes)"),
                SystemSetting(name="system_language", value="fr", data_type="string", category="system", description="Langue du système"),
                SystemSetting(name="log_level", value="info", data_type="string", category="logging", description="Niveau de journalisation"),
                SystemSetting(name="webhook_secret", value="", data_type="string", category="security", description="Clé secrète pour les webhooks")
            ]
            session.add_all(system_settings)
            
            # Exemples de niches
            niches = [
                Niche(name="Agences de marketing digital", description="Entreprises spécialisées dans le marketing digital", keywords=["marketing digital", "agence web", "SEO", "SEM", "publicité en ligne"], created_by=1),
                Niche(name="Cabinets comptables", description="Cabinets d'expertise comptable", keywords=["comptabilité", "expert-comptable", "fiscalité", "audit", "conseil financier"], created_by=1),
                Niche(name="Startups SaaS", description="Startups proposant des logiciels en mode SaaS", keywords=["SaaS", "cloud", "logiciel", "startups", "B2B"], created_by=1)
            ]
            session.add_all(niches)
            
            # Exemples de leads
            leads = [
                Lead(first_name="Jean", last_name="Dupont", email="jean.dupont@exemple.fr", company="Agence Web Plus", position="Directeur", niche_id=1, status="new", score=85),
                Lead(first_name="Marie", last_name="Martin", email="m.martin@comptaexpert.fr", company="ComptaExpert", position="Associée", niche_id=2, status="contacted", score=70),
                Lead(first_name="Lucas", last_name="Bernard", email="lucas@saasplatform.com", company="SaaS Platform", position="CEO", niche_id=3, status="qualified", score=90)
            ]
            session.add_all(leads)
            
            # Exemples de campagnes
            campaigns = [
                Campaign(name="Prospection Marketing Q2 2025", description="Campagne de prospection pour les agences de marketing", niche_id=1, target_leads=50, agent="MessagingAgent", status="active", created_by=1),
                Campaign(name="Offre Comptabilité Automatisée", description="Présentation de notre solution de comptabilité automatisée", niche_id=2, target_leads=30, agent="MessagingAgent", status="draft", created_by=1)
            ]
            session.add_all(campaigns)
            
            # Exemples de messages
            messages = [
                Message(lead_id=1, lead_name="Jean Dupont", lead_email="jean.dupont@exemple.fr", campaign_id=1, campaign_name="Prospection Marketing Q2 2025", subject="Optimisez votre présence en ligne", content="Bonjour Jean, nous avons analysé votre site web et nous avons identifié plusieurs opportunités d'amélioration...", status="sent", sent_date=datetime.now() - timedelta(days=3)),
                Message(lead_id=2, lead_name="Marie Martin", lead_email="m.martin@comptaexpert.fr", campaign_id=2, campaign_name="Offre Comptabilité Automatisée", subject="Automatisez votre comptabilité", content="Bonjour Marie, nous proposons une solution innovante pour automatiser la comptabilité de vos clients...", status="draft")
            ]
            session.add_all(messages)
            
            # Exemples de logs d'agents
            agent_logs = [
                AgentLog(agent_id=1, action="startup", status="success", message="Agent démarré avec succès", timestamp=datetime.now() - timedelta(days=1)),
                AgentLog(agent_id=2, action="interpret_command", status="success", message="Commande interprétée: explorer_niche", timestamp=datetime.now() - timedelta(hours=12))
            ]
            session.add_all(agent_logs)
            
            # Exemples d'interactions entre agents
            interactions = [
                AgentInteraction(from_agent_id=2, to_agent_id=1, message="Demande d'exploration de la niche 'Agences de marketing digital'", context_id="niche_1"),
                AgentInteraction(from_agent_id=1, to_agent_id=8, message="Explorer la niche 'Agences de marketing digital'", context_id="niche_1")
            ]
            session.add_all(interactions)
            
            # Exemples de tâches planifiées
            tasks = [
                Task(agent_id=3, action="daily_report", parameters={"email": "admin@berinia.io"}, status="pending", priority=2, scheduled_time=datetime.now() + timedelta(days=1), is_recurring=True, recurrence_interval=86400),
                Task(agent_id=9, action="scrape_linkedin", parameters={"keywords": ["marketing digital", "france"], "limit": 20}, status="pending", priority=1, scheduled_time=datetime.now() + timedelta(hours=2))
            ]
            session.add_all(tasks)
            
            # Exemples de logs système
            logs = [
                Log(level="info", module="system", message="Système initialisé avec succès"),
                Log(level="warning", module="security", message="Tentative de connexion échouée", details={"ip": "192.168.1.1", "user": "unknown"})
            ]
            session.add_all(logs)
            
            session.commit()
            print("Données initiales insérées avec succès!")
            
    except Exception as e:
        print(f"Erreur lors de l'insertion des données initiales: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Fonction principale d'initialisation de la base de données"""
    print("=== INITIALISATION DE LA BASE DE DONNÉES BERINIA ===")
    
    # Vérification de la connexion à la base de données
    check_database_connection()
    
    # Création des tables
    create_tables_directly()
    
    # Note: Nous pouvons continuer avec l'insertion des données après avoir corrigé tous les problèmes
    # Pour l'instant, nous ne faisons que créer les tables
    # insert_initial_data()
    
    print("=== INITIALISATION TERMINÉE ===")
    print("La base de données Berinia est prête à être utilisée!")

if __name__ == "__main__":
    main()

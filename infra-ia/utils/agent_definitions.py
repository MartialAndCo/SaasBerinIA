"""
Définitions centralisées des agents du système BerinIA

Ce fichier est la source unique de vérité pour tous les agents du système.
Tous les autres composants (registry, webhook, etc.) doivent se référer
à ce fichier pour obtenir la liste des agents disponibles.
"""

from typing import Dict, List, Optional, Any, Tuple

# Liste complète des agents avec leurs métadonnées
# Cette structure permet de :
# - Centraliser la définition des agents en un seul endroit
# - Associer des métadonnées utiles à chaque agent
# - Faciliter l'ajout de nouveaux agents
AGENT_DEFINITIONS = [
    # Agents centraux
    {
        "name": "LoggerAgent",
        "module_path": "agents.logger.logger_agent",
        "class_name": "LoggerAgent",
        "category": "core",
        "description": "Enregistre toutes les interactions entre agents",
        "config_path": "agents/logger/config.json"
    },
    {
        "name": "OverseerAgent",
        "module_path": "agents.overseer.overseer_agent",
        "class_name": "OverseerAgent",
        "category": "core",
        "description": "Orchestrateur central du système",
        "config_path": "agents/overseer/config.json"
    },
    {
        "name": "AdminInterpreterAgent",
        "module_path": "agents.admin_interpreter.admin_interpreter_agent",
        "class_name": "AdminInterpreterAgent",
        "category": "core",
        "description": "Interface en langage naturel pour l'administrateur",
        "config_path": "agents/admin_interpreter/config.json"
    },
    
    # Superviseurs
    {
        "name": "ScrapingSupervisor",
        "module_path": "agents.scraping_supervisor.scraping_supervisor",
        "class_name": "ScrapingSupervisor",
        "category": "supervisor",
        "description": "Supervise le processus de scraping",
        "config_path": "agents/scraping_supervisor/config.json"
    },
    {
        "name": "QualificationSupervisor",
        "module_path": "agents.qualification_supervisor.qualification_supervisor",
        "class_name": "QualificationSupervisor",
        "category": "supervisor",
        "description": "Supervise le processus de qualification",
        "config_path": "agents/qualification_supervisor/config.json"
    },
    {
        "name": "ProspectionSupervisor",
        "module_path": "agents.prospection_supervisor.prospection_supervisor",
        "class_name": "ProspectionSupervisor",
        "category": "supervisor",
        "description": "Supervise le processus de prospection",
        "config_path": "agents/prospection_supervisor/config.json"
    },
    
    # Agents de scraping
    {
        "name": "NicheExplorerAgent",
        "module_path": "agents.niche_explorer.niche_explorer_agent",
        "class_name": "NicheExplorerAgent",
        "category": "scraping",
        "description": "Explore et identifie les niches pertinentes",
        "config_path": "agents/niche_explorer/config.json"
    },
    {
        "name": "ScraperAgent",
        "module_path": "agents.scraper.scraper_agent",
        "class_name": "ScraperAgent",
        "category": "scraping",
        "description": "Récupère les leads depuis diverses sources",
        "config_path": "agents/scraper/config.json"
    },
    {
        "name": "CleanerAgent",
        "module_path": "agents.cleaner.cleaner_agent",
        "class_name": "CleanerAgent",
        "category": "scraping",
        "description": "Nettoie et formate les données des leads",
        "config_path": "agents/cleaner/config.json"
    },
    
    # Agents de qualification
    {
        "name": "ScoringAgent",
        "module_path": "agents.scoring.scoring_agent",
        "class_name": "ScoringAgent",
        "category": "qualification",
        "description": "Attribue un score aux leads",
        "config_path": "agents/scoring/config.json"
    },
    {
        "name": "ValidatorAgent",
        "module_path": "agents.validator.validator_agent",
        "class_name": "ValidatorAgent",
        "category": "qualification",
        "description": "Valide les données des leads",
        "config_path": "agents/validator/config.json"
    },
    {
        "name": "DuplicateCheckerAgent",
        "module_path": "agents.duplicate_checker.duplicate_checker_agent",
        "class_name": "DuplicateCheckerAgent",
        "category": "qualification",
        "description": "Vérifie les doublons dans la base de données",
        "config_path": "agents/duplicate_checker/config.json"
    },
    
    # Agents de prospection
    {
        "name": "MessagingAgent",
        "module_path": "agents.messaging.messaging_agent",
        "class_name": "MessagingAgent",
        "category": "prospection",
        "description": "Gère l'envoi de messages (email, SMS)",
        "config_path": "agents/messaging/config.json"
    },
    {
        "name": "FollowUpAgent",
        "module_path": "agents.follow_up.follow_up_agent",
        "class_name": "FollowUpAgent",
        "category": "prospection",
        "description": "Gère les relances automatiques",
        "config_path": "agents/follow_up/config.json"
    },
    {
        "name": "ResponseInterpreterAgent",
        "module_path": "agents.response_interpreter.response_interpreter_agent",
        "class_name": "ResponseInterpreterAgent",
        "category": "prospection",
        "description": "Analyse les réponses reçues",
        "config_path": "agents/response_interpreter/config.json"
    },
    {
        "name": "ResponseListenerAgent",
        "module_path": "agents.response_listener.response_listener_agent",
        "class_name": "ResponseListenerAgent",
        "category": "prospection",
        "description": "Écoute les réponses entrantes (webhooks)",
        "config_path": "agents/response_listener/config.json"
    },
    
    # Agents d'analyse et d'optimisation
    {
        "name": "PivotStrategyAgent",
        "module_path": "agents.pivot_strategy.pivot_strategy_agent",
        "class_name": "PivotStrategyAgent",
        "category": "analytics",
        "description": "Analyse les performances et suggère des optimisations",
        "config_path": "agents/pivot_strategy/config.json"
    },
    {
        "name": "NicheClassifierAgent",
        "module_path": "agents.niche_classifier.niche_classifier_agent",
        "class_name": "NicheClassifierAgent",
        "category": "analytics",
        "description": "Classifie les niches et personnalise les approches",
        "config_path": "agents/niche_classifier/config.json"
    },
    {
        "name": "VisualAnalyzerAgent",
        "module_path": "agents.visual_analyzer.visual_analyzer_agent_wrapper",
        "class_name": "VisualAnalyzerAgent",
        "category": "analytics",
        "description": "Analyse visuellement les sites web des leads",
        "config_path": "agents/visual_analyzer/config.json"
    },
    
    # Agents utilitaires
    {
        "name": "AgentSchedulerAgent",
        "module_path": "agents.scheduler.agent_scheduler_agent",
        "class_name": "AgentSchedulerAgent",
        "category": "utility",
        "description": "Planifie l'exécution des tâches dans le temps",
        "config_path": "agents/scheduler/config.json"
    },
    {
        "name": "DatabaseQueryAgent",
        "module_path": "agents.database_query.database_query_agent",
        "class_name": "DatabaseQueryAgent",
        "category": "utility",
        "description": "Interroge la base de données en langage naturel",
        "config_path": "agents/database_query/config.json"
    },
    {
        "name": "MetaAgent",
        "module_path": "agents.meta.meta_agent",
        "class_name": "MetaAgent",
        "category": "intelligence",
        "description": "Intelligence conversationnelle du système",
        "config_path": "agents/meta/config.json"
    },
    {
        "name": "WebPresenceCheckerAgent",
        "module_path": "agents.web_presence_checker.web_checker_agent",
        "class_name": "WebPresenceCheckerAgent",
        "category": "utility", 
        "description": "Vérifie la présence web des leads",
        "config_path": "agents/web_presence_checker/config.json"
    },
    {
        "name": "TestAgent",
        "module_path": "agents.test.test_agent",
        "class_name": "TestAgent",
        "category": "utility",
        "description": "Agent de test pour le développement",
        "config_path": "agents/test/config.json"
    }
]

# Dictionnaire pour un accès rapide par nom
AGENT_DICT = {agent["name"]: agent for agent in AGENT_DEFINITIONS}

# Liste de tous les noms d'agents (utile pour les validations)
ALL_AGENT_NAMES = [agent["name"] for agent in AGENT_DEFINITIONS]

# Fonction pour obtenir facilement la définition d'un agent
def get_agent_definition(agent_name: str) -> Optional[Dict[str, Any]]:
    """
    Récupère la définition d'un agent par son nom
    
    Args:
        agent_name: Nom de l'agent
        
    Returns:
        Définition de l'agent ou None si non trouvé
    """
    return AGENT_DICT.get(agent_name)

# Fonction pour obtenir tous les agents d'une catégorie
def get_agents_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Récupère tous les agents d'une catégorie spécifique
    
    Args:
        category: Catégorie d'agents (core, supervisor, scraping, etc.)
        
    Returns:
        Liste des définitions d'agents de cette catégorie
    """
    return [agent for agent in AGENT_DEFINITIONS if agent["category"] == category]

# Fonction pour obtenir les informations d'import d'un agent
def get_agent_import_info(agent_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Récupère les informations d'import d'un agent (module_path, class_name)
    
    Args:
        agent_name: Nom de l'agent
        
    Returns:
        Tuple (module_path, class_name) ou (None, None) si non trouvé
    """
    agent = get_agent_definition(agent_name)
    if not agent:
        return None, None
    return agent["module_path"], agent["class_name"]

# Fonction pour obtenir les noms de tous les agents disponibles
def get_all_agent_names() -> List[str]:
    """
    Retourne la liste des noms de tous les agents disponibles
    
    Returns:
        Liste des noms d'agents
    """
    return ALL_AGENT_NAMES

# Liste d'agents requis par le webhook (maintenue pour compatibilité)
# Note: Cette liste n'est plus utilisée directement, mais est conservée pour référence
WEBHOOK_REQUIRED_AGENTS = [
    "LoggerAgent",
    "OverseerAgent",
    "ResponseListenerAgent",
    "ResponseInterpreterAgent",
    "AdminInterpreterAgent",
    "MessagingAgent",
    "PivotStrategyAgent",
    "MetaAgent",
    "DatabaseQueryAgent"
]

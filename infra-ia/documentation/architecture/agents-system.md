# Système d'Agents

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [Hiérarchie des agents](#hiérarchie-des-agents)
- [Rôles et responsabilités](#rôles-et-responsabilités)
- [Cycle de vie d'un agent](#cycle-de-vie-dun-agent)
- [Implémentation technique](#implémentation-technique)
- [Extensibilité](#extensibilité)

## Vue d'ensemble

Le système BerinIA est basé sur une architecture multi-agents hiérarchique où chaque agent est spécialisé dans une tâche spécifique. Cette approche permet une grande modularité, une séparation claire des responsabilités et une orchestration intelligente centralisée.

## Hiérarchie des agents

Le système est organisé en quatre niveaux hiérarchiques :

```
                             Admin (Humain)
                                   │
                       [Langage naturel libre]
                                   │
                      ┌────────────▼────────────┐
                      │   AdminInterpreterAgent │
                      └────────────┬────────────┘
                                   │
                    [JSON structuré si confirmé]
                                   │
                      ┌────────────▼────────────┐
                      │      OverseerAgent      │
                      └────────────┬────────────┘
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
  ScrapingSupervisor   QualificationSupervisor   ProspectionSupervisor
             │                    │                    │
             ▼                    ▼                    ▼
     Agents opérationnels    Agents opérationnels   Agents opérationnels
```

### Niveau 0 – L'admin (humain)

* Écrit librement des instructions ou demandes en langage naturel
* Peut donner des ordres directs, poser des questions ou demander une analyse

### Niveau 1 – AdminInterpreterAgent

* Reçoit chaque message de l'admin
* Interprète l'intention avec un LLM
* Si le sens est clair → génère une action structurée
* Si ambiguïté → demande confirmation à l'admin avant de transmettre

### Niveau 2 – OverseerAgent

* Supervise l'ensemble du système
* Prend les décisions globales
* Connaît l'état de chaque agent, ses performances, ses erreurs éventuelles
* Reçoit toutes les instructions de l'admin (via l'InterpreterAgent)

### Niveau 3 – Superviseurs par domaine

Superviseurs spécialisés pour chaque domaine fonctionnel :

* **ScrapingSupervisor** : Coordonne le processus de scraping et nettoyage des leads
* **QualificationSupervisor** : Coordonne le processus de qualification des leads
* **ProspectionSupervisor** : Coordonne le processus d'envoi et suivi des messages

### Niveau 4 – Agents opérationnels

Agents spécialisés pour des tâches spécifiques, comme :

* **ScraperAgent** : Récupère les leads via diverses sources
* **CleanerAgent** : Nettoie les leads
* **ScoringAgent** : Évalue et score les leads
* **MessagingAgent** : Rédige et envoie les messages

## Rôles et responsabilités

### Agents centraux

#### OverseerAgent

* **Rôle principal** : Coordonner l'ensemble du système
* **Responsabilités** :
  - Déléguer les tâches aux superviseurs appropriés
  - Suivre l'état global du système
  - Gérer les événements système
  - Orchestrer les workflows complexes
  - Réagir aux instructions administrateur

#### AdminInterpreterAgent

* **Rôle principal** : Interface entre l'humain et le système
* **Responsabilités** :
  - Interpréter les demandes en langage naturel
  - Transformer ces demandes en actions structurées
  - Demander des clarifications si nécessaire
  - Présenter les résultats de manière compréhensible

#### AgentSchedulerAgent

* **Rôle principal** : Planifier l'exécution de tâches dans le temps
* **Responsabilités** :
  - Maintenir une file d'attente de tâches planifiées
  - Exécuter les tâches au moment approprié
  - Gérer les tâches récurrentes
  - Adapter la planification selon les priorités

### Superviseurs spécialisés

#### ScrapingSupervisor

* **Rôle principal** : Coordonner la découverte et collecte de leads
* **Responsabilités** :
  - Gérer le processus de scraping
  - Coordonner l'exploration de niches
  - Superviser le nettoyage des données
  - Optimiser les stratégies de scraping

#### QualificationSupervisor

* **Rôle principal** : Coordonner la qualification des leads
* **Responsabilités** :
  - Superviser la validation des leads
  - Coordonner le scoring
  - Gérer la détection de doublons
  - Optimiser les critères de qualification

#### ProspectionSupervisor

* **Rôle principal** : Coordonner les activités de prospection
* **Responsabilités** :
  - Superviser l'envoi de messages
  - Gérer les relances
  - Coordonner le traitement des réponses
  - Optimiser les stratégies de prospection

### Agents spécialisés

Chaque agent spécialisé a un rôle unique et focused :

* **ScraperAgent** : Extraction de leads depuis diverses sources
* **CleanerAgent** : Nettoyage et normalisation des données
* **ScoringAgent** : Évaluation et scoring des leads
* **ValidatorAgent** : Validation des données selon des critères business
* **DuplicateCheckerAgent** : Détection et gestion des doublons
* **MessagingAgent** : Génération et envoi de messages personnalisés
* **FollowUpAgent** : Gestion des relances selon un scénario dynamique
* **ResponseInterpreterAgent** : Analyse des réponses reçues
* **VisualAnalyzerAgent** : Analyse visuelle des sites web
* **NicheClassifierAgent** : Classification des niches et personnalisation
* **MetaAgent** : Intelligence conversationnelle centralisée

## Cycle de vie d'un agent

### 1. Initialisation

```python
def __init__(self, config_path: str = None):
    self.name = self.__class__.__name__
    self.config = self.load_config(config_path)
    self.setup_logger()
```

### 2. Chargement de configuration

```python
def load_config(self, config_path: str = None) -> dict:
    if not config_path:
        config_path = f"agents/{self.name.lower()}/config.json"
    
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        return {}
```

### 3. Exécution

```python
def run(self, input_data: dict) -> dict:
    """Méthode principale que l'OverseerAgent appelle"""
    action = input_data.get("action", "default")
    
    if hasattr(self, f"action_{action}"):
        method = getattr(self, f"action_{action}")
        return method(input_data)
    else:
        return {"status": "error", "message": f"Action '{action}' non supportée"}
```

### 4. Communication

```python
def speak(self, message: str, target: str = None):
    """Enregistre un message dans les logs d'interactions"""
    LoggerAgent.log_interaction(self.name, target, message)
```

## Implémentation technique

### Structure standard d'un agent

Tous les agents suivent le même modèle dans leur implémentation :

```
agents/agent_name/
├── agent_name_agent.py     # Code principal de l'agent
├── config.json             # Configuration de l'agent
└── prompt.txt              # Prompt template pour le LLM
```

### Classe de base des agents

Tous les agents héritent d'une classe de base commune (`AgentBase`) :

```python
class AgentBase:
    def __init__(self, config_path: str = None):
        self.name = self.__class__.__name__
        self.config = self.load_config(config_path)
        self.logger = setup_logger(self.name)
    
    def load_config(self, config_path: str = None) -> dict:
        # Logique de chargement de configuration
        
    def run(self, input_data: dict) -> dict:
        # Méthode principale d'exécution
        
    def speak(self, message: str, target: str = None):
        # Méthode de communication inter-agents
        
    def update_config(self, key: str, value: Any) -> bool:
        # Méthode pour mettre à jour la configuration
```

### Registre d'agents

Un registre central gère la création et l'accès aux agents :

```python
class AgentRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance._agents = {}
            cls._instance._initialized = False
        return cls._instance
    
    def get(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)
    
    def register(self, name: str, agent: Agent) -> None:
        self._agents[name] = agent
    
    def get_or_create(self, name: str, config_path: Optional[str] = None) -> Optional[Agent]:
        # Logique pour récupérer ou créer un agent
```

## Extensibilité

Le système est conçu pour être facilement extensible :

### Ajout d'un nouvel agent

1. Créer un dossier dans `agents/new_agent/`
2. Définir une classe qui hérite de `AgentBase`
3. Implémenter la méthode `run()` et les méthodes spécifiques
4. Ajouter l'agent à `agent_definitions.py`

### Ajout d'un nouveau superviseur

1. Créer un dossier dans `agents/new_supervisor/`
2. Implémenter les méthodes de délégation spécifiques
3. Ajouter des méthodes pour coordonner les agents sous sa supervision
4. Enregistrer le superviseur dans l'OverseerAgent

### Exemple d'ajout d'agent

```python
# agents/example_agent/example_agent.py
from core.agent_base import AgentBase

class ExampleAgent(AgentBase):
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
    
    def run(self, input_data: dict) -> dict:
        action = input_data.get("action", "default")
        if action == "custom_action":
            return self.action_custom_action(input_data)
        return {"status": "error", "message": f"Action '{action}' non supportée"}
    
    def action_custom_action(self, input_data: dict) -> dict:
        # Logique spécifique
        return {"status": "success", "result": {...}}
```

---

[Retour à l'accueil](../index.md) | [Communication inter-agents →](communication.md)

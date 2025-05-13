# Architecture du Système BerinIA

## Vue d'ensemble

BerinIA est un système d'agents IA interconnectés conçu pour automatiser le processus de prospection commerciale. Le système s'articule autour d'une architecture multi-agents hiérarchique, où chaque agent est spécialisé dans une tâche particulière et communique avec les autres pour former un système cohérent et évolutif.

```
┌───────────────────────────────────┐
│         Interface Admin           │
│    (AdminInterpreterAgent)        │
└─────────────────┬─────────────────┘
                  │
                  ▼
┌───────────────────────────────────┐      ┌───────────────────────────────────┐
│         Orchestrateur             │      │        Planificateur              │
│        (OverseerAgent)            │◄────►│      (AgentSchedulerAgent)        │
└──┬────────────┬─────────┬─────────┘      └───────────────────────────────────┘
   │            │         │
   ▼            ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│Scraping │ │Qualifi- │ │Prospec- │
│Supervis.│ │cation   │ │tion     │
└──┬──────┘ └──┬──────┘ └──┬──────┘
   │           │           │
   ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐    ┌───────────────────────────────────┐
│Agents de│ │Agents de│ │Agents de│    │      Analyse & Optimisation        │
│Scraping │ │Scoring  │ │Messaging│    │      (PivotStrategyAgent)          │
└─────────┘ └─────────┘ └─────────┘    └───────────────────────────────────┘
                                                       ▲
┌───────────────────────────────────┐                  │
│     Écoute des Réponses           │                  │
│    (ResponseListenerAgent)        │──────────────────┘
└───────────────────────────────────┘
```

## Composants principaux

### 1. Agents centraux

#### OverseerAgent (Orchestrateur central)
- **Rôle**: Coordonne tous les agents et supervise le système
- **Responsabilités**:
  - Déléguer les tâches aux superviseurs spécialisés
  - Gérer les événements système
  - Maintenir l'état global du système
  - Contrôler et répartir les ressources

#### AdminInterpreterAgent (Interface d'administration)
- **Rôle**: Interface en langage naturel pour l'administrateur
- **Responsabilités**:
  - Interpréter les commandes en texte libre
  - Traduire en actions structurées pour le système
  - Fournir des réponses en langage naturel

#### AgentSchedulerAgent (Planificateur de tâches)
- **Rôle**: Orchestrer l'exécution des tâches dans le temps
- **Responsabilités**:
  - Planifier des tâches ponctuelles ou récurrentes
  - Maintenir une file de priorité des tâches à exécuter
  - Gérer la persistance des tâches planifiées

### 2. Superviseurs spécialisés

#### ScrapingSupervisor
- **Rôle**: Coordonner le processus de scraping et nettoyage des leads
- **Agents supervisés**: ScraperAgent, CleanerAgent, NicheExplorerAgent

#### QualificationSupervisor
- **Rôle**: Coordonner le processus de qualification des leads
- **Agents supervisés**: ValidatorAgent, ScoringAgent, DuplicateCheckerAgent

#### ProspectionSupervisor
- **Rôle**: Coordonner le processus d'envoi et suivi des messages
- **Agents supervisés**: MessagingAgent, FollowUpAgent

### 3. Agents spécialisés

#### ResponseListenerAgent
- **Rôle**: Écouter et traiter les réponses entrantes
- **Responsabilités**:
  - Recevoir les webhooks (email, SMS)
  - Extraire les métadonnées et informations clés
  - Transmettre au système pour traitement

#### PivotStrategyAgent
- **Rôle**: Analyser et optimiser les performances du système
- **Responsabilités**:
  - Analyser les métriques de performance
  - Identifier les opportunités d'amélioration
  - Recommander des ajustements stratégiques

#### VisualAnalyzerAgent
- **Rôle**: Analyser visuellement les sites web des leads
- **Responsabilités**:
  - Détecter et fermer automatiquement les popups et obstacles
  - Analyser la structure et la qualité visuelle des sites web
  - Calculer un score de maturité digitale
  - Enrichir les données des leads avec des métriques visuelles
  - Fournir des données pour NicheClassifierAgent

#### NicheClassifierAgent
- **Rôle**: Classifier les niches et personnaliser les approches
- **Responsabilités**:
  - Classifier automatiquement une niche dans sa famille (santé, commerce, immobilier, etc.)
  - Combiner les données de hiérarchie des niches avec l'analyse visuelle
  - Générer des approches personnalisées selon la niche et la maturité du site
  - Recommander les besoins IA adaptés à chaque contexte
  - Fournir des données de personnalisation au MessagingAgent

## Architecture technique

### Structure du code

La structure du projet suit une organisation modulaire par agent:

```
berinia/
├── infra-ia/
│   ├── agents/                 # Tous les agents du système
│   │   ├── admin_interpreter/  # Interprète les commandes admin
│   │   ├── cleaner/            # Nettoie les données
│   │   ├── duplicate_checker/  # Vérifie les doublons
│   │   ├── follow_up/          # Gère les relances
│   │   ├── logger/             # Enregistre les interactions
│   │   ├── messaging/          # Envoie les messages
│   │   ├── niche_explorer/     # Explore les niches
│   │   ├── niche_classifier/   # Classe et personnalise les approches par niches
│   │   ├── overseer/           # Supervise le système
│   │   ├── pivot_strategy/     # Analyse les performances
│   │   ├── prospection_supervisor/ # Supervise la prospection
│   │   ├── qualification_supervisor/ # Supervise la qualification
│   │   ├── response_interpreter/ # Interprète les réponses
│   │   ├── scheduler/          # Planifie les tâches
│   │   ├── scorer/             # Score les leads
│   │   ├── scraper/            # Extrait les leads
│   │   ├── scraping_supervisor/ # Supervise le scraping
│   │   ├── validator/          # Valide les données
│   │   └── visual_analyzer/    # Analyse visuelle et détection de maturité des sites web
│   │
│   ├── core/                   # Modules centraux
│   │   ├── agent_base.py       # Classe de base des agents
│   │   └── db.py               # Interface avec la base de données
│   │
│   ├── utils/                  # Utilitaires
│   │   ├── llm.py              # Service d'accès aux LLM
│   │   └── qdrant.py           # Service d'accès à Qdrant
│   │
│   ├── webhook/                # Serveur de webhooks
│   │   └── run_webhook.py      # Serveur FastAPI
│   │
│   ├── init_system.py          # Script d'initialisation
│   ├── interact.py             # Interface CLI
│   ├── verify_installation.py  # Vérification de l'installation
│   ├── setup_venv.sh           # Script de configuration de l'environnement
│   └── requirements.txt        # Dépendances Python
```

### Flux de données

1. **Orchestration**:
   - L'AdminInterpreterAgent reçoit des instructions en langage naturel
   - Ces instructions sont converties en commandes structurées pour l'OverseerAgent
   - L'OverseerAgent délègue aux superviseurs spécialisés
   - Les superviseurs coordonnent leurs agents spécialisés

2. **Scraping & Qualification**:
   - ScrapingSupervisor coordonne la découverte et le nettoyage des leads
   - QualificationSupervisor gère la validation et le scoring des leads
   - Les leads qualifiés sont stockés dans la base de données

3. **Prospection**:
   - ProspectionSupervisor coordonne l'envoi de messages personnalisés
   - Les réponses sont captées par le ResponseListenerAgent via webhooks
   - Les réponses sont traitées et transmises au système pour suivi

4. **Planification & Automatisation**:
   - AgentSchedulerAgent gère l'exécution automatisée des tâches
   - Les tâches récurrentes (scraping, relances) sont exécutées selon leur planification

5. **Analyse & Optimisation**:
   - PivotStrategyAgent analyse les performances des campagnes et niches
   - Il génère des recommandations pour améliorer les stratégies

### Technologies clés

- **Traitement du langage**: OpenAI API (GPT-4, embeddings)
- **Base de connaissances vectorielle**: Qdrant
- **API Webhooks**: FastAPI
- **Stockage relationnel**: SQLAlchemy + SQLite/PostgreSQL
- **Automatisation**: Système de planification personnalisé

## Interactions entre agents

### Communication inter-agents

Le système utilise deux mécanismes de communication principaux:

1. **Appels directs**: Pour les interactions synchrones et critiques
   ```python
   result = agent.run({"action": "specific_action", "parameters": {...}})
   ```

2. **Messages asynchrones**: Pour les notifications et événements non-bloquants
   ```python
   agent.speak("Message important", target="OverseerAgent")
   ```

### Délégation de tâches

L'OverseerAgent utilise un mécanisme de délégation pour distribuer les tâches:

```python
result = overseer.delegate_to_supervisor("QualificationSupervisor", {
    "action": "qualify_leads",
    "parameters": {
        "leads": [...],
        "min_score": 70
    }
})
```

## Extensibilité

Le système est conçu pour être facilement extensible:

1. **Nouveaux agents**: Création de classes héritant de `Agent` avec leur propre implémentation de `run()`
2. **Nouveaux superviseurs**: Ajout de nouveaux superviseurs pour coordonner des domaines spécialisés
3. **Nouveaux webhooks**: Extension du serveur webhook pour recevoir de nouvelles sources de données

## Mécanismes de sécurité

- Validation des entrées sur tous les webhooks
- Vérification des signatures pour les webhooks externes (Mailgun, Twilio)
- Limitation de débit pour éviter les abus
- Logging complet de toutes les actions pour auditabilité

## Configuration et déploiement

Le système utilise un fichier de configuration central (`config.json`) qui définit les paramètres pour tous les composants:

- Modèles LLM à utiliser et leurs paramètres
- Configuration des agents (seuils, priorités)
- Paramètres du serveur webhook
- Configuration de la base de données vectorielle
- Paramètres de monitoring et sécurité

Le déploiement est simplifié par le script `run.py` qui initialise tous les composants et démarre le système complet en une seule commande.

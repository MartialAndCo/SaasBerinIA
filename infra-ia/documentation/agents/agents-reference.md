# Référence complète des agents

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Introduction](#introduction)
- [Agents centraux](#agents-centraux)
- [Superviseurs](#superviseurs)
- [Agents d'acquisition](#agents-dacquisition)
- [Agents de qualification](#agents-de-qualification)
- [Agents de communication](#agents-de-communication)
- [Agents d'analyse](#agents-danalyse)
- [Agents utilitaires](#agents-utilitaires)

## Introduction

Ce document fournit une référence complète de tous les agents disponibles dans le système BerinIA. Chaque agent est spécialisé dans une tâche particulière et communique avec les autres pour former un système cohérent et évolutif.

## Agents centraux

### OverseerAgent

- **Rôle**: Orchestrateur central du système
- **Responsabilités**: 
  - Déléguer les tâches aux superviseurs spécialisés
  - Gérer les événements système
  - Maintenir l'état global du système
  - Contrôler et répartir les ressources
- **Fichier**: `agents/overseer/overseer_agent.py`
- **Interactions principales**: Tous les agents et superviseurs

### AdminInterpreterAgent

- **Rôle**: Interface en langage naturel pour l'administrateur
- **Responsabilités**:
  - Interpréter les commandes en texte libre
  - Traduire en actions structurées pour le système
  - Fournir des réponses en langage naturel
  - Demander des clarifications si nécessaire
- **Fichier**: `agents/admin_interpreter/admin_interpreter_agent.py`
- **Interactions principales**: OverseerAgent, utilisateur humain

### MetaAgent

- **Rôle**: Système d'intelligence conversationnelle central
- **Responsabilités**:
  - Analyser les demandes en langage naturel
  - Découvrir automatiquement les capacités du système
  - Router intelligemment les demandes
  - Maintenir le contexte des conversations
- **Fichier**: `agents/meta/meta_agent.py`
- **Interactions principales**: Tous les agents du système
- **Voir aussi**: [MetaAgent - Documentation détaillée](meta-agent.md)

### AgentSchedulerAgent

- **Rôle**: Planificateur de tâches dans le temps
- **Responsabilités**:
  - Planifier des tâches ponctuelles ou récurrentes
  - Maintenir une file de priorité des tâches à exécuter
  - Gérer la persistance des tâches planifiées
  - Adapter la planification selon les priorités
- **Fichier**: `agents/scheduler/scheduler_agent.py`
- **Interactions principales**: OverseerAgent

## Superviseurs

### ScrapingSupervisor

- **Rôle**: Coordonner le processus de scraping et nettoyage des leads
- **Responsabilités**:
  - Gérer le processus de scraping
  - Coordonner l'exploration de niches
  - Superviser le nettoyage des données
  - Optimiser les stratégies de scraping
- **Fichier**: `agents/scraping_supervisor/scraping_supervisor_agent.py`
- **Agents supervisés**: ScraperAgent, CleanerAgent, NicheExplorerAgent

### QualificationSupervisor

- **Rôle**: Coordonner le processus de qualification des leads
- **Responsabilités**:
  - Superviser la validation des leads
  - Coordonner le scoring
  - Gérer la détection de doublons
  - Optimiser les critères de qualification
- **Fichier**: `agents/qualification_supervisor/qualification_supervisor_agent.py`
- **Agents supervisés**: ValidatorAgent, ScoringAgent, DuplicateCheckerAgent

### ProspectionSupervisor

- **Rôle**: Coordonner le processus d'envoi et suivi des messages
- **Responsabilités**:
  - Superviser l'envoi de messages personnalisés
  - Gérer les relances
  - Coordonner le traitement des réponses
  - Optimiser les stratégies de prospection
- **Fichier**: `agents/prospection_supervisor/prospection_supervisor_agent.py`
- **Agents supervisés**: MessagingAgent, FollowUpAgent

## Agents d'acquisition

### NicheExplorerAgent

- **Rôle**: Explorer et analyser des niches commerciales
- **Responsabilités**:
  - Identifier des niches à potentiel
  - Analyser le marché et les tendances
  - Proposer des niches viables
  - Évaluer la concurrence
- **Fichier**: `agents/niche_explorer/niche_explorer_agent.py`
- **Interactions principales**: ScrapingSupervisor

### ScraperAgent

- **Rôle**: Extraire des leads de diverses sources
- **Responsabilités**:
  - Récupérer les leads via Apify, Apollo, etc.
  - Extraire les informations pertinentes
  - Respecter les limites de scraping
  - Gérer les erreurs et exceptions
- **Fichier**: `agents/scraper/scraper_agent.py`
- **Interactions principales**: ScrapingSupervisor, CleanerAgent

### CleanerAgent

- **Rôle**: Nettoyer et normaliser les données de leads
- **Responsabilités**:
  - Nettoyer les leads (emails invalides, doublons simples, etc.)
  - Normaliser les formats de données
  - Enrichir les données quand possible
  - Préparer les leads pour la qualification
- **Fichier**: `agents/cleaner/cleaner_agent.py`
- **Interactions principales**: ScrapingSupervisor, QualificationSupervisor

## Agents de qualification

### ValidatorAgent

- **Rôle**: Valider les leads selon des critères business
- **Responsabilités**:
  - Vérifier la validité des données
  - Appliquer des règles métier
  - Rejeter les leads non conformes
  - Normaliser les données validées
- **Fichier**: `agents/validator/validator_agent.py`
- **Interactions principales**: QualificationSupervisor

### ScoringAgent

- **Rôle**: Attribuer un score aux leads
- **Responsabilités**:
  - Appliquer des critères de scoring
  - Calculer un score global
  - Identifier les leads à fort potentiel
  - Ajuster les critères selon les performances
- **Fichier**: `agents/scoring/scoring_agent.py`
- **Interactions principales**: QualificationSupervisor

### DuplicateCheckerAgent

- **Rôle**: Détecter les doublons dans la base
- **Responsabilités**:
  - Vérifier l'unicité des leads
  - Détecter les doublons par différents critères
  - Fusionner les données si nécessaire
  - Maintenir l'intégrité de la base
- **Fichier**: `agents/duplicate_checker/duplicate_checker_agent.py`
- **Interactions principales**: QualificationSupervisor

### WebPresenceCheckerAgent

- **Rôle**: Vérifier la présence web des leads
- **Responsabilités**:
  - Vérifier l'existence et la disponibilité du site web
  - Valider les adresses email et profils sociaux
  - Enrichir les données avec la présence web
  - Détecter les sites obsolètes ou inaccessibles
- **Fichier**: `agents/web_presence_checker/web_presence_checker_agent.py`
- **Interactions principales**: QualificationSupervisor

## Agents de communication

### MessagingAgent

- **Rôle**: Générer et envoyer des messages personnalisés
- **Responsabilités**:
  - Rédiger des messages adaptés à chaque lead
  - Envoyer les messages via Mailgun / Twilio
  - Suivre l'état des envois
  - Gérer les erreurs d'envoi
- **Fichier**: `agents/messaging/messaging_agent.py`
- **Interactions principales**: ProspectionSupervisor

### FollowUpAgent

- **Rôle**: Gérer les relances selon un scénario dynamique
- **Responsabilités**:
  - Planifier les relances
  - Adapter le rythme selon les réponses
  - Générer des messages de relance pertinents
  - Savoir quand arrêter les relances
- **Fichier**: `agents/follow_up/follow_up_agent.py`
- **Interactions principales**: ProspectionSupervisor, AgentSchedulerAgent

### ResponseListenerAgent

- **Rôle**: Écouter et recevoir les réponses entrantes
- **Responsabilités**:
  - Recevoir les webhooks (email, SMS, WhatsApp)
  - Extraire les données pertinentes
  - Normaliser le format des réponses
  - Transmettre au ResponseInterpreterAgent
- **Fichier**: `agents/response_listener/response_listener_agent.py`
- **Interactions principales**: Webhooks, ResponseInterpreterAgent

### ResponseInterpreterAgent

- **Rôle**: Analyser et interpréter les réponses reçues
- **Responsabilités**:
  - Analyser le contenu des réponses
  - Déterminer l'intention (positif/neutre/négatif)
  - Décider de l'action à prendre
  - Transmettre l'information au système
- **Fichier**: `agents/response_interpreter/response_interpreter_agent.py`
- **Interactions principales**: ResponseListenerAgent, OverseerAgent

## Agents d'analyse

### PivotStrategyAgent

- **Rôle**: Analyser et optimiser les performances du système
- **Responsabilités**:
  - Analyser les métriques de performance
  - Identifier les opportunités d'amélioration
  - Recommander des ajustements stratégiques
  - Générer des rapports d'analyse
- **Fichier**: `agents/pivot_strategy/pivot_strategy_agent.py`
- **Interactions principales**: OverseerAgent

### VisualAnalyzerAgent

- **Rôle**: Analyser visuellement les sites web des leads
- **Responsabilités**:
  - Capturer des screenshots des sites web
  - Détecter et fermer les popups
  - Analyser la structure et qualité visuelle
  - Calculer un score de maturité digitale
- **Fichier**: `agents/visual_analyzer/visual_analyzer_agent.py`
- **Interactions principales**: QualificationSupervisor, NicheClassifierAgent
- **Voir aussi**: [VisualAnalyzerAgent - Documentation détaillée](visual-analyzer.md)

### NicheClassifierAgent

- **Rôle**: Classifier les niches et personnaliser les approches
- **Responsabilités**:
  - Classifier les niches en familles
  - Combiner avec l'analyse visuelle
  - Générer des approches personnalisées
  - Recommander des besoins IA adaptés
- **Fichier**: `agents/niche_classifier/niche_classifier_agent.py`
- **Interactions principales**: VisualAnalyzerAgent, MessagingAgent
- **Voir aussi**: [NicheClassifierAgent - Documentation détaillée](niche-classifier.md)

## Agents utilitaires

### LoggerAgent

- **Rôle**: Enregistrer les interactions et actions du système
- **Responsabilités**:
  - Centraliser les logs
  - Enregistrer les interactions entre agents
  - Fournir des outils de visualisation
  - Gérer la rotation des logs
- **Fichier**: `agents/logger/logger_agent.py`
- **Interactions principales**: Tous les agents

### DatabaseQueryAgent

- **Rôle**: Interroger la base de données en langage naturel
- **Responsabilités**:
  - Traduire les questions en requêtes SQL
  - Formater les résultats de manière lisible
  - Gérer les requêtes prédéfinies
  - Précharger le schéma de la base
- **Fichier**: `agents/database_query/database_query_agent.py`
- **Interactions principales**: AdminInterpreterAgent, OverseerAgent

### TestAgent

- **Rôle**: Tester le système et ses composants
- **Responsabilités**:
  - Exécuter des scénarios de test
  - Vérifier le bon fonctionnement des agents
  - Simuler des interactions
  - Générer des rapports de test
- **Fichier**: `agents/test/test_agent.py`
- **Interactions principales**: Utilisé uniquement en développement/test

---

[Retour à l'accueil](../index.md)

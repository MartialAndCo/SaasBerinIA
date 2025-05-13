# Vue d'ensemble de l'architecture

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Introduction](#introduction)
- [Architecture multi-agents](#architecture-multi-agents)
- [Composants principaux](#composants-principaux)
- [Flux de données](#flux-de-données)
- [Technologies clés](#technologies-clés)
- [Diagramme d'architecture](#diagramme-darchitecture)

## Introduction

BerinIA est un système d'agents IA interconnectés conçu pour automatiser le processus de prospection commerciale. Le système s'articule autour d'une architecture multi-agents hiérarchique, où chaque agent est spécialisé dans une tâche particulière et communique avec les autres pour former un système cohérent et évolutif.

## Architecture multi-agents

L'architecture de BerinIA repose sur une hiérarchie d'agents à plusieurs niveaux:

1. **Niveau central** - Agents responsables de l'orchestration globale
2. **Niveau supervision** - Superviseurs spécialisés par domaine fonctionnel
3. **Niveau opérationnel** - Agents d'exécution spécialisés par tâche

Cette structure hiérarchique permet une grande modularité et une séparation claire des responsabilités, tout en maintenant une orchestration intelligente centralisée.

## Composants principaux

### Agents centraux

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

### Superviseurs spécialisés

#### ScrapingSupervisor
- **Rôle**: Coordonner le processus de scraping et nettoyage des leads
- **Agents supervisés**: ScraperAgent, CleanerAgent, NicheExplorerAgent

#### QualificationSupervisor
- **Rôle**: Coordonner le processus de qualification des leads
- **Agents supervisés**: ValidatorAgent, ScoringAgent, DuplicateCheckerAgent

#### ProspectionSupervisor
- **Rôle**: Coordonner le processus d'envoi et suivi des messages
- **Agents supervisés**: MessagingAgent, FollowUpAgent

### Agents spécialisés clés

#### MetaAgent
- **Rôle**: Système d'intelligence conversationnelle central
- **Responsabilités**:
  - Analyse des demandes en langage naturel
  - Découverte automatique des capacités des agents
  - Routage intelligent des demandes

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

#### VisualAnalyzerAgent et NicheClassifierAgent
- **Rôles combinés**: Analyse visuelle et classification des niches
- **Responsabilités**:
  - Analyser la maturité digitale des sites web
  - Classifier les niches et personnaliser les approches

## Flux de données

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

## Technologies clés

- **Traitement du langage**: OpenAI API (GPT-4.1, embeddings)
- **Base de connaissances vectorielle**: Qdrant
- **API Webhooks**: FastAPI
- **Stockage relationnel**: SQLAlchemy + PostgreSQL
- **Communication WhatsApp**: whatsapp-web.js (Node.js)
- **Communication SMS**: Twilio API
- **Analyse visuelle**: Playwright

## Diagramme d'architecture

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

## Pour en savoir plus

- [Système d'agents](agents-system.md) - Détails sur l'organisation des agents
- [Communication inter-agents](communication.md) - Protocoles de communication
- [Agents spécialisés](../agents/meta-agent.md) - Documentation détaillée des agents

---

[Retour à l'accueil](../index.md) | [Système d'agents →](agents-system.md)

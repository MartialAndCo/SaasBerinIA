# Synthèse complète du système BerinIA

## Introduction et vue d'ensemble

BerinIA est un écosystème d'agents IA autonomes et collaboratifs, orchestrés par une logique centrale intelligente, conçu pour automatiser le processus complet de prospection commerciale. Le système s'articule autour de plusieurs composants majeurs qui travaillent ensemble pour :

- Scraper des leads qualifiés dans des niches précises
- Nettoyer, valider et scorer ces leads
- Analyser visuellement les sites web des leads pour évaluer leur maturité digitale
- Classifier les leads en familles de niches commerciales
- Envoyer des messages personnalisés en cold outreach (email et SMS)
- Relancer automatiquement selon des scénarios dynamiques
- Analyser les réponses reçues
- Optimiser les performances en continu

## Architecture système

### Organisation hiérarchique

Le système utilise une architecture multi-agents à plusieurs niveaux hiérarchiques :

1. **Niveau 0 - Administrateur (humain)** : Interagit avec le système en langage naturel
2. **Niveau 1 - AdminInterpreterAgent** : Interprète les intentions de l'administrateur
3. **Niveau 2 - OverseerAgent** : Orchestre l'ensemble du système
4. **Niveau 3 - Superviseurs spécialisés** :
   - **ScrapingSupervisor** : Coordonne la découverte et collection de leads
   - **QualificationSupervisor** : Coordonne la qualification des leads
   - **ProspectionSupervisor** : Coordonne l'envoi et le suivi des messages
5. **Niveau 4 - Agents opérationnels** : Agents spécialisés pour des tâches précises

Cette hiérarchie permet une séparation claire des responsabilités tout en maintenant une orchestration centralisée.

### Flux de données

1. **Orchestration**
   - Les instructions en langage naturel sont reçues par l'AdminInterpreterAgent
   - Ces instructions sont converties en commandes structurées pour l'OverseerAgent
   - L'OverseerAgent délègue aux superviseurs spécialisés

2. **Scraping & Qualification**
   - ScrapingSupervisor coordonne la découverte et le nettoyage des leads
   - QualificationSupervisor gère la validation et le scoring
   - Les leads qualifiés sont stockés en base de données

3. **Analyse & Enrichissement**
   - VisualAnalyzerAgent analyse les sites web pour déterminer leur maturité digitale
   - NicheClassifierAgent classe les niches et personnalise les approches
   - Ces données enrichissent les leads pour une prospection plus ciblée

4. **Prospection**
   - ProspectionSupervisor coordonne l'envoi de messages personnalisés
   - Les réponses sont captées par le ResponseListenerAgent via webhooks
   - Les réponses sont traitées et transmises au système pour suivi

5. **Planification & Automatisation**
   - AgentSchedulerAgent gère l'exécution automatisée des tâches
   - Les tâches récurrentes sont exécutées selon leur planification

## Agents clés et leurs rôles

### Agents centraux

#### OverseerAgent (Orchestrateur central)
- **Rôle** : Coordonne tous les agents et supervise le système
- **Responsabilités** :
  - Déléguer les tâches aux superviseurs spécialisés
  - Maintenir l'état global du système
  - Gérer les événements système
  - Contrôler et répartir les ressources

#### AdminInterpreterAgent (Interface d'administration)
- **Rôle** : Interface en langage naturel pour l'administrateur
- **Responsabilités** :
  - Interpréter les commandes en texte libre
  - Traduire en actions structurées pour le système
  - Demander des clarifications si nécessaire
  - Fournir des réponses en langage naturel

#### MetaAgent (Intelligence conversationnelle)
- **Rôle** : Système d'intelligence conversationnelle central
- **Fonctionnalités** :
  - Analyse sémantique des demandes utilisateur
  - Découverte automatique des capacités des agents
  - Routage intelligent des demandes
  - Mémoire conversationnelle
  - Post-traitement intelligent des réponses

#### AgentSchedulerAgent (Planificateur)
- **Rôle** : Orchestrer l'exécution des tâches dans le temps
- **Responsabilités** :
  - Planifier des tâches ponctuelles ou récurrentes
  - Maintenir une file de priorité des tâches
  - Gérer la persistance des tâches planifiées

### Agents spécialisés majeurs

#### VisualAnalyzerAgent
- **Rôle** : Analyse visuelle des sites web des leads
- **Fonctionnalités** :
  - Capture d'écran automatique des sites web
  - Analyse de maturité digitale (score de 1 à 10)
  - Classification du niveau de maturité (basic, intermediate, advanced)
  - Détection des éléments UI/UX (navigation, CTA, formulaires)
  - Enrichissement des leads avec des métadonnées visuelles
- **Architecture technique** :
  - Playwright pour la navigation web et captures d'écran
  - OpenAI Vision API pour l'analyse visuelle
  - Détection et contournement des popups

#### NicheClassifierAgent
- **Rôle** : Classification et personnalisation des niches
- **Fonctionnalités** :
  - Classification contextuelle des niches en familles
  - Intégration des données d'analyse visuelle
  - Personnalisation des messages par niche
  - Enrichissement des leads avec des métadonnées de classification
- **Familles de niches** :
  - Métiers de la santé (Chiropracteurs, Ostéopathes, etc.)
  - Commerces physiques (Coiffeurs, Restaurants, etc.)
  - Immobilier & Habitat (Agents immobiliers, Architectes, etc.)
  - B2B Services (Experts-comptables, Avocats, etc.)
  - Artisans & Construction (Plombiers, Électriciens, etc.)

#### DatabaseQueryAgent
- **Rôle** : Interface en langage naturel pour la base de données
- **Fonctionnalités** :
  - Traduction des questions en requêtes SQL
  - Préchargement du schéma de la base de données
  - Gestion de requêtes prédéfinies pour les questions courantes
  - Retour de résultats formatés en langage naturel

#### ResponseListenerAgent
- **Rôle** : Écouter et traiter les réponses entrantes
- **Responsabilités** :
  - Recevoir les webhooks (email, SMS, WhatsApp)
  - Extraire les métadonnées et informations clés
  - Transmettre au système pour traitement

### Agents opérationnels

- **ScraperAgent** : Extraction de leads depuis diverses sources web
- **CleanerAgent** : Nettoyage et normalisation des données
- **NicheExplorerAgent** : Exploration des niches de marché
- **ValidatorAgent** : Validation des données selon critères business
- **ScoringAgent** : Évaluation et scoring des leads
- **DuplicateCheckerAgent** : Détection et gestion des doublons
- **MessagingAgent** : Génération et envoi de messages personnalisés
- **FollowUpAgent** : Gestion des relances selon scénario dynamique
- **PivotStrategyAgent** : Analyse des performances et optimisation
- **ResponseInterpreterAgent** : Analyse sémantique des réponses

## Intégrations externes

### WhatsApp
- **Architecture** : Service Node.js basé sur whatsapp-web.js
- **Fonctionnalités** :
  - Envoi/réception de messages via groupes WhatsApp
  - Support des messages vocaux avec transcription automatique
  - Intelligence conversationnelle améliorée pour réponses naturelles
- **Structure des groupes** dans la communauté "BerinIA" :
  - 📣 Annonces officielles (lecture seule)
  - 📊 Performances & Stats (lecture seule)
  - 🛠️ Logs techniques (lecture seule)
  - 🤖 Support IA / Chatbot (lecture/écriture)
  - 🧠 Tactiques & Tests (lecture/écriture)
  - 💬 Discussion libre (lecture/écriture)

### SMS (Twilio)
- **Architecture** : Webhook FastAPI qui reçoit les notifications Twilio
- **Fonctionnalités** :
  - Réception des SMS via webhook Twilio
  - Traitement des réponses SMS
  - Vérification des signatures Twilio pour la sécurité
- **Flux de données** :
  1. Réception du SMS par Twilio
  2. Notification webhook BerinIA
  3. Traitement par ResponseListenerAgent
  4. Analyse par ResponseInterpreterAgent
  5. Action déclenchée selon l'interprétation

### Base de données
- **Structure principale** : PostgreSQL avec les tables suivantes :
  - **leads** : Informations sur les leads prospectés (enrichies par analyse visuelle)
  - **campaigns** : Campagnes de prospection
  - **messages** : Messages envoyés et reçus
  - **niches** : Niches commerciales exploitées
  - **stats** : Statistiques de performance
- **Migrations** : Scripts dans `backend/migrations/`

## Système de webhook

- **Framework** : FastAPI sur port 8001 (local)
- **Proxy inverse** : Nginx pour exposition publique
- **Endpoints** :
  - `/webhook/sms-response` : Réponses SMS via Twilio
  - `/webhook/whatsapp` : Messages WhatsApp
  - `/webhook/email-response` : Réponses email via Mailgun
  - `/webhook/logs` : Accès aux logs récents
- **Sécurité** :
  - Vérification des signatures pour Twilio et Mailgun
  - Limitation de débit pour éviter les abus
  - Validation des entrées

## Système de logs unifié

- **Centralisation** : Tous les logs dans `/root/berinia/unified_logs/`
- **Fichiers principaux** :
  - `system.log` : Journal principal du système
  - `error.log` : Erreurs et exceptions
  - `agents.log` : Logs du fonctionnement des agents
  - `webhook.log` : Logs du serveur webhook
  - `whatsapp.log` : Logs de l'intégration WhatsApp
  - `agent_interactions.jsonl` : Format JSON Lines pour analyse
- **Niveaux** : ERROR, WARNING, INFO, DEBUG
- **Méthode speak() des agents** :
  ```python
  self.speak(
    "J'ai récupéré 47 leads dans la niche coaching.",
    target="CleanerAgent"
  )
  ```

## Améliorations récentes (Mai 2025)

### Résolution des problèmes de base de données
- Correction des erreurs d'authentification
- Mise à jour du module DatabaseService pour SQLAlchemy moderne
- Adaptation des requêtes SQL aux structures de tables existantes

### Amélioration de l'intelligence conversationnelle
- Élimination des salutations répétitives
- Enrichissement du contexte temporel dans les conversations
- Restructuration de l'historique conversationnel
- Post-traitement intelligent des réponses

### Fonctionnalités WhatsApp
- Support des messages vocaux avec transcription via OpenAI Whisper
- Amélioration du mappage des noms de groupes
- Configuration pour utiliser la dernière version de whatsapp-web.js

## Implémentation technique

### Structure d'un agent

```
agents/agent_name/
├── agent_name_agent.py    # Code principal
├── config.json            # Configuration
└── prompt.txt             # Prompt pour le LLM
```

### Cycle de vie d'un agent

1. **Initialisation** : Chargement de la configuration
2. **Exécution** : Méthode `run()` appelée par l'OverseerAgent
3. **Communication** : Méthode `speak()` pour les interactions

### Chargement automatique des agents

- Système de chargement automatique via `get_all_agent_names()`
- Registre central d'agents (singleton `AgentRegistry`)
- Validation et correction des noms d'agents pour éviter les "hallucinations" de LLM

### Technologies clés

- **Traitement du langage** : OpenAI API (GPT-4.1, embeddings)
- **Base de connaissances vectorielle** : Qdrant
- **API Webhooks** : FastAPI
- **Stockage relationnel** : SQLAlchemy + PostgreSQL
- **Communication WhatsApp** : whatsapp-web.js (Node.js)
- **Communication SMS** : Twilio API
- **Analyse visuelle** : Playwright + OpenAI Vision API

## Installation et configuration

### Prérequis
- Python 3.8+
- Clé API OpenAI pour GPT-4.1 family
- PostgreSQL 14+
- Node.js 18+ (pour WhatsApp)

### Configuration principale
1. Fichier `.env` dans `infra-ia/` :
   ```
   OPENAI_API_KEY=votre_clé_api_openai
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=berinia
   DB_USER=berinia_user
   DB_PASSWORD=votre_mot_de_passe
   QDRANT_URL=http://localhost:6333
   MAILGUN_API_KEY=votre_clé_api_mailgun
   MAILGUN_DOMAIN=votre_domaine_mailgun
   TWILIO_SID=votre_sid_twilio
   TWILIO_TOKEN=votre_token_twilio
   TWILIO_PHONE=+votre_numéro_twilio
   ```

2. Services systemd :
   - `berinia-webhook.service` : Serveur webhook FastAPI
   - `berinia-whatsapp.service` : Service WhatsApp

### Démarrage du système
- Interface CLI : `python interact.py`
- Serveur webhook : `python webhook/run_webhook.py`
- WhatsApp : Service systemd `berinia-whatsapp.service`

## Utilisation et commandes courantes

### Exemples de commandes en langage naturel
- **Explorer une niche** : `Explore la niche des consultants en cybersécurité`
- **Récupérer des leads** : `Récupère 50 leads dans cette niche`
- **Préparer une campagne** : `Prépare une campagne d'emails avec comme sujet "Sécurisez votre entreprise"`
- **Envoyer une campagne** : `Envoie cette campagne aux 20 meilleurs leads`
- **Planifier une relance** : `Planifie une relance dans 3 jours`
- **Voir les statistiques** : `Montre-moi les statistiques de la dernière campagne`

### Utilisation du VisualAnalyzerAgent
```python
# Analyse d'un site web
result = overseer.execute_agent("VisualAnalyzerAgent", {
    "action": "analyze_website",
    "url": "https://example.com",
    "lead_id": 123
})
```

### Utilisation du NicheClassifierAgent
```python
# Classification d'une niche
result = overseer.execute_agent("NicheClassifierAgent", {
    "action": "classify",
    "niche": "Dentiste"
})
```

### Utilisation du DatabaseQueryAgent
```
Combien de leads avons-nous dans la niche "plombier" ?
```

### Envoi de message WhatsApp
```bash
# Via script
node test-send.js "Logs techniques" "Votre message ici"

# Via API
curl -X POST http://localhost:3030/send \
  -H "Content-Type: application/json" \
  -d '{"group": "Logs techniques", "message": "Votre message ici"}'
```

## Conclusion

BerinIA est un système complet d'agents IA collaboratifs conçu pour automatiser l'ensemble du processus de prospection commerciale. Son architecture modulaire, ses agents spécialisés et ses intégrations externes (WhatsApp, SMS, email) en font une solution puissante et flexible.

La récente amélioration de l'intelligence conversationnelle et la résolution des problèmes de base de données ont renforcé la stabilité et l'efficacité du système. Les fonctionnalités d'analyse visuelle et de classification de niches offrent une personnalisation avancée des approches commerciales.

Pour intégrer efficacement le système dans un workflow quotidien, il est recommandé de se familiariser avec l'interface en langage naturel et les commandes courantes, tout en explorant les capacités avancées des agents spécialisés selon les besoins spécifiques de prospection.

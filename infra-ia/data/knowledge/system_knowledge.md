# Base de Connaissances du Système BerinIA

## 1. Vue d'ensemble du système

BerinIA est un écosystème intelligent d'agents autonomes orchestrés par une logique centralisée, conçu pour automatiser le processus de prospection commerciale. Le système permet de :

- Scraper des leads qualifiés dans des niches précises
- Nettoyer, valider et scorer ces leads
- Envoyer des messages personnalisés en cold outreach (email et SMS)
- Relancer automatiquement selon des scénarios dynamiques
- Analyser les réponses reçues
- Apprendre de ses performances pour optimiser ses comportements
- Réagir en temps réel aux événements entrants (réponses)
- Être piloté en langage naturel libre par l'administrateur

## 2. Architecture hiérarchique des agents

La structure du système suit une hiérarchie claire :

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
     Agents de Scraping    Agents de Qualification     Agents de Prospection
```

## 3. Composants techniques principaux

### 3.1 Outils et services externes

| Outil/Service | Utilisation | Notes techniques |
|---------------|-------------|------------------|
| **Apify** | Scraping de leads | API d'extraction de données |
| **Apollo** | Scraping de leads | Source secondaire |
| **Mailgun** | Envoi d'emails | API d'envoi d'emails en masse |
| **Twilio** | Envoi de SMS | API de communication SMS |
| **PostgreSQL** | Base de données relationnelle | Stockage des leads, campagnes, messages |
| **Qdrant** | Base de données vectorielle | Stockage des connaissances et embeddings |
| **WhatsApp-web.js** | Client WhatsApp | Communication via WhatsApp |
| **FastAPI** | Serveur de webhooks | Réception des événements (emails, SMS, WhatsApp) |

### 3.2 Structure du code

```
berinia/
├── infra-ia/
│   ├── agents/                 # Tous les agents du système
│   │   ├── admin_interpreter/  # Interprète les commandes admin
│   │   ├── cleaner/            # Nettoie les données
│   │   ├── database_query/     # Interroge la base de données
│   │   ├── duplicate_checker/  # Vérifie les doublons
│   │   ├── follow_up/          # Gère les relances
│   │   ├── logger/             # Enregistre les interactions
│   │   ├── messaging/          # Envoie les messages
│   │   ├── meta/               # Agent central d'intelligence
│   │   ├── niche_explorer/     # Explore les niches
│   │   ├── niche_classifier/   # Classe et personnalise par niches
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
│   │   └── visual_analyzer/    # Analyse visuelle des sites web
```

## 4. Détail des agents principaux

### 4.1 Agents centraux

#### OverseerAgent

**Rôle** : Cerveau central du système, supervise l'ensemble des opérations

**Fonctionnalités** :
- Coordonne tous les agents et superviseurs
- Prend les décisions globales sur le fonctionnement du système
- Connaît l'état de chaque agent et ses performances
- Transmet des messages entre agents

**Points d'intégration** :
- Reçoit des instructions de l'AdminInterpreterAgent
- Délègue aux superviseurs spécialisés
- Communique avec l'AgentSchedulerAgent pour planifier des tâches

#### MetaAgent

**Rôle** : Intelligence conversationnelle centralisée

**Fonctionnalités** :
- Analyse les demandes utilisateur en langage naturel
- Comprend les intentions et le contexte des messages
- Route les requêtes vers les agents appropriés
- Point central d'entrée pour les interactions WhatsApp et SMS

**Points d'intégration** :
- Interface avec le webhook WhatsApp
- Communique avec le DatabaseQueryAgent pour les requêtes de données
- Transmet des résultats à l'OverseerAgent

#### AdminInterpreterAgent

**Rôle** : Interface en langage naturel pour l'administrateur

**Fonctionnalités** :
- Interprète les commandes en texte libre
- Traduit en actions structurées pour le système
- Demande confirmation en cas d'ambiguïté
- Fournit des réponses en langage naturel

**Points d'intégration** :
- Interagit avec l'administrateur
- Transmet des instructions à l'OverseerAgent

### 4.2 Superviseurs spécialisés

#### ScrapingSupervisor

**Rôle** : Coordonne le processus de découverte et extraction de leads

**Fonctionnalités** :
- Gère les sources de scraping (Apify, Apollo)
- Supervise le nettoyage et la préparation des leads
- Contrôle l'exploration de nouvelles niches

**Agents supervisés** :
- NicheExplorerAgent
- ScraperAgent
- CleanerAgent

#### QualificationSupervisor

**Rôle** : Coordonne la qualification et validation des leads

**Fonctionnalités** :
- Applique les règles business (score, validité)
- Gère la détection de doublons
- Supervise le scoring des leads

**Agents supervisés** :
- ValidatorAgent
- ScoringAgent
- DuplicateCheckerAgent

#### ProspectionSupervisor

**Rôle** : Coordonne le processus de communication avec les leads

**Fonctionnalités** :
- Gère les envois de messages (email, SMS)
- Supervise les relances automatiques
- Contrôle l'interprétation des réponses

**Agents supervisés** :
- MessagingAgent
- FollowUpAgent
- ResponseInterpreterAgent

### 4.3 Agents opérationnels clés

#### DatabaseQueryAgent

**Rôle** : Interroge la base de données pour obtenir des statistiques et informations

**Fonctionnalités** :
- Traduit les questions en langage naturel en requêtes SQL
- Fournit des statistiques sur les leads, campagnes, et performances
- Génère des réponses formatées à partir des données

**Points d'intégration** :
- Utilisé par le MetaAgent pour répondre aux questions
- Interface avec PostgreSQL pour les requêtes
- Formate les résultats pour les autres agents

#### ScraperAgent

**Rôle** : Extrait les leads des sources définies

**Fonctionnalités** :
- Utilisation des API de scraping (Apify, Apollo)
- Extraction structurée des informations
- Respect des limites et quotas

**Points d'intégration** :
- API Apify pour le scraping principal
- API Apollo comme source secondaire
- Communique les résultats au CleanerAgent

#### MessagingAgent

**Rôle** : Gère l'envoi des messages aux leads

**Fonctionnalités** :
- Rédaction personnalisée des messages
- Envoi via les différents canaux (email, SMS)
- Gestion des templates et personnalisation

**Points d'intégration** :
- API Mailgun pour les emails
- API Twilio pour les SMS
- API WhatsApp pour la messagerie instantanée

#### ResponseInterpreterAgent

**Rôle** : Analyse les réponses reçues des leads

**Fonctionnalités** :
- Détection du sentiment (positif/négatif/neutre)
- Classification des intentions (intérêt, refus, question)
- Proposition d'actions suivantes

**Points d'intégration** :
- Reçoit des messages du ResponseListenerAgent
- Utilise le LLM pour l'analyse
- Communique les résultats au ProspectionSupervisor

## 5. Interactions et flux de données

### 5.1 Flux de travail principal

1. **Découverte et extraction** :
   - Le ScrapingSupervisor coordonne l'exploration des niches
   - Le ScraperAgent extrait les leads des sources sélectionnées
   - Le CleanerAgent prépare et nettoie les données

2. **Qualification et validation** :
   - Le QualificationSupervisor coordonne la qualification
   - Le ValidatorAgent vérifie la validité des leads
   - Le ScoringAgent attribue un score selon les critères business
   - Le DuplicateCheckerAgent élimine les doublons

3. **Prospection et suivi** :
   - Le ProspectionSupervisor coordonne la communication
   - Le MessagingAgent envoie les messages personnalisés
   - Le FollowUpAgent gère les relances automatiques
   - Le ResponseInterpreterAgent analyse les réponses

### 5.2 Réception et traitement des webhooks

#### Webhook WhatsApp

```
Client WhatsApp → WhatsApp Bot → Webhook FastAPI → WhatsApp Webhook Handler → MetaAgent → Agents spécifiques → Réponse
```

#### Webhook Email (Mailgun)

```
Réponse Email → Mailgun → Webhook FastAPI → Email Webhook Handler → ResponseListenerAgent → ResponseInterpreterAgent → Actions
```

#### Webhook SMS (Twilio)

```
Réponse SMS → Twilio → Webhook FastAPI → SMS Webhook Handler → ResponseListenerAgent → ResponseInterpreterAgent → Actions
```

## 6. Aspects techniques spécifiques

### 6.1 Communication entre agents

Les agents communiquent par appels directs et logs centralisés :

```python
# Appel direct
result = agent.run({"action": "specific_action", "parameters": {...}})

# Communication loggée
agent.speak("Message important", target="OverseerAgent")
```

### 6.2 Configuration des agents

Chaque agent possède un fichier de configuration (`config.json`) qui définit son comportement :

```json
{
  "limit_per_run": 50,
  "language": "fr",
  "preferred_sources": ["apify", "apollo"],
  "blacklisted_niches": ["crypto", "adult"]
}
```

### 6.3 Base de données

Le système utilise PostgreSQL pour stocker :
- Leads et leurs métadonnées
- Campagnes et leur statut
- Messages envoyés et reçus
- Statistiques et performances
- Logs d'activité

### 6.4 Mémoire vectorielle

Qdrant est utilisé pour stocker :
- Base de connaissances du système
- Embeddings des documents de référence
- Historique des conversations pour contexte
- Exemples de messages et réponses

## 7. Sources de leads et intégrations externes

### 7.1 Sources de scraping

#### Apify

**Utilisation principale** : Extraction structurée de leads à partir de diverses sources web
**Configuration** :
- API Key stockée dans les variables d'environnement
- Acteurs Apify utilisés : LinkedIn Scraper, Website Content Crawler

#### Apollo

**Utilisation secondaire** : Source complémentaire de leads B2B
**Configuration** :
- API Key stockée dans les variables d'environnement
- Filtres par industrie, taille d'entreprise, etc.

### 7.2 Services de messagerie

#### Mailgun

**Utilisation** : Envoi d'emails de prospection et réception des réponses
**Configuration** :
- API Key et domaine dans les variables d'environnement
- Webhook configuré pour les réponses
- Templates d'emails stockés dans `/data/templates/`

#### Twilio

**Utilisation** : Envoi et réception de SMS
**Configuration** :
- SID et Token dans les variables d'environnement
- Numéro d'expéditeur configuré
- Webhook pour réception des réponses

### 7.3 WhatsApp Integration

**Utilisation** : Communication bidirectionnelle via WhatsApp
**Configuration** :
- Service basé sur whatsapp-web.js
- Authentification par QR code
- Webhook pour traitement des messages

## 8. Gestion des erreurs et debuggage

### 8.1 Niveaux de logs

Le système utilise plusieurs niveaux de logs :
- **DEBUG** : Informations détaillées pour le développement
- **INFO** : Événements normaux et actions exécutées
- **WARNING** : Situations anormales mais non critiques
- **ERROR** : Erreurs empêchant l'exécution normale
- **CRITICAL** : Erreurs critiques nécessitant intervention

### 8.2 Messages d'erreur

Les erreurs sont maintenant exposées dans les réponses pour faciliter le debuggage :

```json
{
  "error": "Erreur de traitement: DatabaseError",
  "debug": "Traceback complet...",
  "response": "Une erreur est survenue lors de l'interrogation de la base de données"
}
```

### 8.3 Sources supportées

Le système supporte nativement les sources suivantes :
- Apify (leads scraping)
- Apollo (leads B2B)
- LinkedIn (via Apify)
- Sites web génériques (via Apify)
- WhatsApp (messages et réponses)
- Email (via Mailgun)
- SMS (via Twilio)

## 9. Workflows typiques

### 9.1 Exploration et qualification d'une niche

1. L'admin demande d'explorer une nouvelle niche
2. Le NicheExplorerAgent analyse la niche et sa viabilité
3. Le ScraperAgent extrait des leads potentiels
4. Le CleanerAgent nettoie et prépare les données
5. Les agents de qualification évaluent et scorent les leads
6. L'OverseerAgent présente les résultats et suggère une approche

### 9.2 Lancement d'une campagne

1. L'admin approuve une niche et demande une campagne
2. L'OverseerAgent crée la structure de campagne
3. Le MessagingAgent prépare des templates personnalisés
4. Les messages sont envoyés selon un calendrier défini
5. Le FollowUpAgent planifie les relances
6. Le ResponseInterpreterAgent analyse les réponses reçues
7. Les leads intéressés sont transférés au CRM

### 9.3 Interaction via WhatsApp

1. Un utilisateur envoie un message WhatsApp
2. Le webhook reçoit le message et le transmet au MetaAgent
3. Le MetaAgent analyse l'intention et le contexte
4. Si nécessaire, le DatabaseQueryAgent est consulté pour les données
5. Une réponse intelligente est générée et renvoyée
6. L'interaction est loggée pour analyse future

## 10. Améliorations récentes et roadmap

### 10.1 Améliorations récentes

- Intégration du MetaAgent comme point d'entrée pour WhatsApp
- Meilleure gestion des erreurs avec exposition des détails
- Normalisation du format des contextes entre agents
- Correction des problèmes de communication entre agents

### 10.2 Roadmap future

- Threads de conversation pour WhatsApp (conservation du contexte)
- Support multilingue avec détection automatique
- Reconnaissance d'images pour WhatsApp
- Monitoring avancé des performances
- Cache des réponses fréquentes

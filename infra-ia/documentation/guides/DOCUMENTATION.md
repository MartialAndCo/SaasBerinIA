🧩 PARTIE 1 – PRÉSENTATION GÉNÉRALE DU SYSTÈME BERINIA
🎯 Objectif du système
Le système BerinIA est un écosystème intelligent d’agents autonomes, orchestrés par une logique centralisée, qui a pour mission de :

Scraper des leads qualifiés dans des niches précises

Les nettoyer, valider et scorer

Envoyer des messages personnalisés en cold outreach (email et SMS)

Relancer automatiquement selon des scénarios dynamiques

Analyser les réponses reçues

Apprendre de ses performances pour optimiser ses comportements

Réagir en temps réel aux événements entrants (réponses)

Être piloté à tout moment en langage naturel libre, par l’admin

🧠 Philosophie de conception
La conception repose sur les principes suivants :

Centralisation intelligente : un OverseerAgent supervise et décide de tout, aucun graphe automatique ou traitement en chaîne sans validation.

Modularité : chaque agent a un rôle clair, autonome, paramétrable et réutilisable.

Communication naturelle : l’admin interagit en langage libre via un agent interprète.

Réactivité temps réel : les réponses aux emails/SMS sont traitées dès réception (via webhook).

Adaptation continue : les agents apprennent de leurs performances et ajustent leur comportement sans intervention manuelle.

Traçabilité complète : toutes les actions, décisions, échanges sont historisés et visibles dans un fil de discussion centralisé.

🧱 Vue d’ensemble de l’architecture
Le système est structuré en 4 couches :

Interaction humaine

Tu parles librement en langage naturel

L'agent AdminInterpreterAgent comprend et transmet les consignes

Cerveau central

Le OverseerAgent supervise tout le système

Il décide de ce que chaque agent doit faire à chaque étape

Supervision par domaine

Scraping, Qualification, Prospection : chaque pôle a un superviseur dédié

Agents opérationnels

Chaque tâche est assurée par un agent autonome (scraping, nettoyage, scoring, messagerie, relance, etc.)

🔁 Fonctionnement en continu
Un AgentSchedulerAgent tourne en arrière-plan 24/7

Il programme, déclenche, ou reporte des tâches

Il peut être modifié à tout moment par l’admin (ex. “relance les campagnes à 18h”)

Il n’utilise aucun crédit LLM tant qu’aucun appel n’est déclenché

🧩 Ce qui rend BerinIA unique
Une vraie orchestration intelligente par agent, pas un système à logique rigide

Une interface admin en langage naturel sans aucune syntaxe à respecter

Une visualisation des échanges entre agents pour comprendre comment ils coopèrent

Une capacité d’apprentissage native, sans retrain ni intervention externe

Un design pensé pour évoluer facilement, avec des agents remplaçables ou extensibles


Parfait. Voici la **PARTIE 2 – Rôles et hiérarchie des agents**, entièrement rédigée pour figer qui fait quoi dans BerinIA, comment les agents sont organisés, et comment les décisions circulent.

---

# 🧩 PARTIE 2 – HIÉRARCHIE ET RÔLES DES AGENTS

---

## 🧠 Structure hiérarchique des agents

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

---

## 🧩 Niveau 0 – L’admin (toi)

* Écrit librement des instructions ou demandes en langage naturel.
* Peut donner des ordres directs (“passe le scraping à 20 leads”), poser des questions (“est-ce que le MessagingAgent tourne bien ?”) ou demander une analyse.

---

## 🧩 Niveau 1 – `AdminInterpreterAgent`

### Rôle :

* Reçoit chaque message de l’admin.
* Interprète l’intention avec un LLM.
* Si le sens est clair → génère une action structurée.
* Si ambiguïté → demande confirmation à l’admin avant de transmettre.

### Exemple de sortie :

```json
{
  "action": "update_config",
  "target_agent": "ScraperAgent",
  "key": "limit_per_run",
  "value": 20
}
```

---

## 🧩 Niveau 2 – `OverseerAgent`

### Rôle :

* Supervise l’ensemble du système.
* Prend les décisions globales.
* Connaît l’état de chaque agent, ses performances, ses erreurs éventuelles.
* Reçoit toutes les instructions de l’admin (via l’InterpreterAgent).
* Peut :

  * Lancer ou arrêter un agent
  * Modifier une config
  * Rebooter une chaîne
  * Reprioriser une niche ou une campagne
  * Transmettre des messages à un superviseur ou à tous les agents

---

## 🧩 Niveau 3 – Superviseurs par domaine

---

### 🔷 `ScrapingSupervisor`

* Pilote tous les agents liés à la recherche de leads.
* Gère la logique de scraping par niche.
* Peut changer de source (Apify, Apollo).
* Peut relancer ou arrêter un scraping.
* Joue le rôle de coordinateur entre découverte de niche, scraping, et nettoyage.

#### Gère :

* `NicheExplorerAgent`
* `ScraperAgent`
* `CleanerAgent`

---

### 🔷 `QualificationSupervisor`

* Pilote les agents qui analysent et valident les leads.
* Applique les règles business (score, email pro, entreprise identifiable…).
* Peut blacklister un lead, noter un profil, etc.

#### Gère :

* `ScoringAgent`
* `ValidatorAgent`
* `DuplicateCheckerAgent`

---

### 🔷 `ProspectionSupervisor`

* Gère tous les agents qui contactent les leads.
* Supervise les relances, les messages, et l’interprétation des réponses.
* Peut suspendre une campagne, adapter une séquence, ou proposer une nouvelle approche.

#### Gère :

* `MessagingAgent`
* `FollowUpAgent`
* `ResponseInterpreterAgent`

---

## 🧩 Niveau 4 – Agents opérationnels

---

### 🔹 `NicheExplorerAgent`

* Cherche des niches à fort potentiel.
* Analyse le marché, les tendances, les signaux faibles.
* Propose des niches viables au ScrapingSupervisor.

---

### 🔹 `ScraperAgent`

* Récupère les leads via Apify, Apollo, ou autre.
* Utilise la niche reçue et scrape selon les paramètres du `config.json`.

---

### 🔹 `CleanerAgent`

* Nettoie les leads (emails invalides, noms manquants, doublons simples…).
* Prépare les leads pour la qualification.

---

### 🔹 `ScoringAgent`

* Attribue un score à chaque lead selon des critères business.

---

### 🔹 `ValidatorAgent`

* Vérifie que le lead est exploitable.
* Peut rejeter un lead incomplet ou incohérent.

---

### 🔹 `DuplicateCheckerAgent`

* Vérifie l’unicité du lead dans la mémoire (via PostgreSQL).

---

### 🔹 `MessagingAgent`

* Rédige et envoie les messages personnalisés à chaque lead (Mailgun / Twilio).

---

### 🔹 `FollowUpAgent`

* Gère les relances selon un scénario dynamique.
* Peut adapter le rythme selon le niveau de réponse.

---

### 🔹 `ResponseInterpreterAgent`

* Lit les réponses reçues (email ou SMS).
* Analyse leur ton, leur sens (positif / neutre / négatif).
* Décide de :

  * Transférer au CRM
  * Relancer via MessagingAgent
  * Clôturer

---

## 🧠 Agents supplémentaires

---

### 🔸 `AgentSchedulerAgent`

* Tourne en continu (process Python).
* Planifie les actions dans le temps (ex : “relance cette campagne demain à 10h”).
* Ne consomme aucun crédit tant qu’il n’appelle pas un LLM.

---

### 🔸 `PivotStrategyAgent` (ou `KnowledgeEvaluator`)

* Analyse les performances globales :

  * Conversions
  * Réponse par niche
  * Qualité des messages
  * Efficacité des chunks de knowledge
* Peut proposer des ajustements (restructuration, pause, changement de stratégie)
Voici maintenant la **PARTie 3 – Logique de fonctionnement du système**, où tout est décrit avec précision : déclenchement des agents, enchaînements, configurations, réactivité, apprentissage, etc. Tout est posé ici pour que l’écosystème soit **prévisible, stable, et intelligent**.

---

# 🧩 PARTIE 3 – LOGIQUE DE FONCTIONNEMENT DU SYSTÈME

---

## 🧠 1. Déclenchement des agents

### 🔹 Décision par le `OverseerAgent` uniquement

* Lorsqu’un agent termine une tâche, **aucun autre agent ne prend la suite automatiquement.**
* Le `OverseerAgent` décide, en temps réel, de :

  * Qui doit intervenir ensuite
  * Avec quels paramètres
  * Sur quelles données

### 🔹 Les agents ne s'appellent **jamais entre eux** directement.

Ils transmettent leurs résultats au `OverseerAgent`, qui orchestre la suite.

---

## 🔗 2. Mode de communication entre agents

### ✅ Appels Python directs uniquement

* Pas de queue, pas de base de données relationnelle pour les échanges internes.
* Chaque agent expose une méthode `run(input: dict) → dict` exécutée par l’Overseer.

### Exemple :

```python
data = ScraperAgent().run({"niche": "coaching"})
cleaned = CleanerAgent().run(data)
scored = ScoringAgent().run(cleaned)
```

→ L’Overseer contient la logique qui décide **si** et **quand** ces appels ont lieu.

---

## ⚙️ 3. Configuration dynamique des agents

Chaque agent lit son propre fichier de configuration `config.json` :

```json
{
  "limit_per_run": 50,
  "blacklisted_niches": ["crypto", "casino"],
  "preferred_sources": ["apify", "apollo"],
  "language": "fr"
}
```

* Ce fichier est modifié uniquement par le `OverseerAgent` ou par instruction admin.
* L’agent recharge sa configuration à chaque appel `run()`.

### Méthode :

```python
def update_config(self, key, value):
    self.config[key] = value
    save_config()
```

---

## 📜 4. Prompt logique

Chaque agent a un prompt template (`prompt.txt`) qui décrit son rôle, son contexte, et ses instructions.

### Exemple :

```txt
Tu es un ScraperAgent. Tu travailles sur la niche {niche}.

Consignes :
- Nombre max : {limit_per_run}
- Langue : {language}
- Sources : {preferred_sources}
- À éviter : {blacklisted_niches}

Ne réponds qu'en JSON structuré avec les leads valides.
```

> Les variables sont injectées automatiquement depuis le `config.json` + contexte dynamique (`campaign_id`, etc.)

---

## 🧠 5. Réactivité en temps réel

### Webhooks en FastAPI :

```http
POST /webhook/email-response  ← pour Mailgun  
POST /webhook/sms-response    ← pour Twilio
```

Ces endpoints déclenchent :

* le `ResponseListenerAgent`, qui transmet à :
* le `ResponseInterpreterAgent`, qui :

  * lit la réponse,
  * prend une décision (CRM / relance / suppression),
  * transmet cette décision au `OverseerAgent`.

### ⏱ Temps de réponse : immédiat

Aucune latence, aucun batch

---

## 🕒 6. Planification dans le temps

### Agent : `AgentSchedulerAgent`

* Tourne en continu
* Contient une file de tâches planifiées comme :

```json
{
  "agent": "MessagingAgent",
  "task": "relancer campagne coaching",
  "scheduled_for": "2025-05-04T10:00:00"
}
```

* À l’heure prévue, il appelle le `OverseerAgent` pour exécution
* Ne consomme aucun crédit tant qu’il ne déclenche pas un LLM

---

## 🧠 7. Logique d’apprentissage

### Suivi de performance :

Chaque action est loggée avec son effet :

* taux de réponse
* durée moyenne de réponse
* conversion CRM
* échec / succès

### Stockage :

* En PostgreSQL (leads, stats, performances)
* Éventuellement, résumé vectorisé dans Qdrant pour mémoire d’apprentissage à long terme

### Décision :

* Le `PivotStrategyAgent` est chargé d’observer les résultats
* Il peut suggérer (ou appliquer automatiquement) :

  * une pause de niche
  * un changement de wording
  * une réduction ou augmentation de volume

---

## 🧠 8. Interaction admin dynamique

* Tu envoies un message libre, par exemple :

  > "J’ai l’impression que la niche beauté est saturée, arrête-la un moment."

* L’`AdminInterpreterAgent` interprète (via LLM) et transmet au `OverseerAgent` :

```json
{
  "action": "update_config",
  "target_agent": "ScraperAgent",
  "key": "blacklisted_niches",
  "value": ["crypto", "casino", "beauté"]
}
```

* Si doute → il te demande confirmation.

# 🧩 PARTIE 4 – CANAL DE DISCUSSION ENTRE AGENTS

---

## 🎯 Objectif

Tu veux un système dans lequel :

* Tous les agents **parlent entre eux de manière lisible**
* Chaque échange est **loggé proprement**
* Tu peux **consulter l’historique conversationnel** comme dans un chat
* Et **voir ce qui a été dit, décidé, transmis, ou corrigé**

---

## 🧱 Principe

### ✅ Chaque agent possède une méthode `speak()` :

Elle permet d’envoyer un message lisible vers un canal de log centralisé.

```python
def speak(self, message: str, target: str = None):
    LoggerAgent.log_interaction(self.name, target, message)
```

---

## 🧠 Exemple d’usage dans un agent

```python
self.speak(
  "J’ai récupéré 47 leads dans la niche coaching. Je transmets à CleanerAgent.",
  target="CleanerAgent"
)
```

---

## 🔐 LoggerAgent – Agent central de traçage

### Rôle :

* Enregistre toutes les interactions
* Ajoute un horodatage
* Lie les messages à une campagne ou un contexte
* Enregistre les messages dans :

  * PostgreSQL ou fichier `.jsonl`
  * Un cache lisible en front-end

---

### Format du message :

```json
{
  "timestamp": "2025-05-03T18:52:14",
  "from": "ScraperAgent",
  "to": "CleanerAgent",
  "message": "J’ai terminé le scraping sur la niche coaching. Voici 47 leads.",
  "context_id": "campaign_042"
}
```

---

## 👁️ Visualisation en “chat d’agents”

Dans ton interface sandbox (ou admin), tu pourras voir :

```
🧠 OverseerAgent → ScrapingSupervisor :
    Reprends le scraping sur la niche "menuisier" demain à 10h.

🔎 ScraperAgent → CleanerAgent :
    Voici 38 leads valides sur la niche immobilier B2C.

🧽 CleanerAgent → QualificationSupervisor :
    Tous les leads ont été nettoyés. 2 doublons supprimés.
```

* Les messages sont stylisés par agent.
* L’affichage suit une logique de fil de discussion avec filtre par :

  * agent
  * campagne
  * plage de dates

---

## ✍️ Communication admin incluse

Quand tu écris un message en langage naturel, il est aussi loggé :

```json
{
  "timestamp": "...",
  "from": "Admin (Yann)",
  "to": "AdminInterpreterAgent",
  "message": "Passe le scraping à 20 leads par niche max",
  "context_id": "global"
}
```

Et l’interprétation + exécution aussi :

```json
{
  "from": "AdminInterpreterAgent",
  "to": "OverseerAgent",
  "message": "L’admin souhaite limiter le scraping à 20 leads. Action JSON générée."
}
```

---

## ✅ Résultat final

* Tu as une **traçabilité complète du raisonnement des agents**
* Tu peux **relire tout ce qui s’est passé**
* Tu peux comprendre **pourquoi une décision a été prise**
* Et tu peux **intervenir ou modifier à tout moment**, sans rien casser
---

# 🧩 PARTIE 5 – RÉACTIVITÉ EN TEMPS RÉEL

---

## 🎯 Objectif

Le système doit pouvoir :

* Réagir **immédiatement** aux réponses reçues par email ou SMS.
* Analyser le contenu de la réponse dès réception.
* Déclencher une décision (relancer / clôturer / transférer au CRM) sans délai.
* Ne **pas dépendre de tâches cron** ou de passage cyclique.

---

## 🔔 1. Événements concernés

Deux types d’événements peuvent arriver à tout moment :

* 📩 Email reçu via **Mailgun**
* 💬 SMS reçu via **Twilio**

Ces événements sont capturés via **webhooks**.

---

## 🔌 2. Endpoints d’écoute (FastAPI)

Le backend expose deux routes :

```http
POST /webhook/email-response      ← pour Mailgun
POST /webhook/sms-response        ← pour Twilio
```

Chaque webhook reçoit un payload contenant :

* L’expéditeur (adresse ou numéro)
* Le contenu du message
* L’ID de la campagne (si traçable)
* Le timestamp

---

## 🔁 3. Traitement de l’événement

### Étapes :

1. Le webhook appelle une méthode du `ResponseListenerAgent`
2. Le `ResponseListenerAgent` :

   * formate proprement le message
   * ajoute le contexte
   * transmet au `ResponseInterpreterAgent` via appel Python direct

### Exemple de code :

```python
@app.post("/webhook/email-response")
async def receive_email(data: dict):
    ResponseListenerAgent().handle(data)
    return {"status": "ok"}
```

---

## 🧠 4. Analyse par `ResponseInterpreterAgent`

### Rôle :

* Lire la réponse

* Déterminer :

  * 📗 Réponse positive (intérêt → CRM)
  * 📘 Réponse neutre (→ relance)
  * 📕 Refus ou désinscription (→ clôture)

* Le message analysé est loggué via le `LoggerAgent`

### Exemple :

```json
{
  "lead_id": "abc-123",
  "response": "Oui ça m'intéresse, vous pouvez m’en dire plus",
  "status": "positive",
  "action": "transfer_to_crm"
}
```

---

## 🧩 5. Suite déclenchée dynamiquement

Le `ResponseInterpreterAgent` transmet sa conclusion au `OverseerAgent` :

```python
OverseerAgent().handle_event(response_result)
```

→ Le `OverseerAgent` décide de la suite :

* Transfert au CRM
* Nouvelle tâche pour le `MessagingAgent`
* Suppression du lead

---

## 🧾 6. Traçabilité des événements

Tous les événements entrants sont loggés comme les échanges internes :

```json
{
  "timestamp": "...",
  "from": "Lead: +33782345678",
  "to": "ResponseInterpreterAgent",
  "message": "C’est bon pour moi, envoyez les détails.",
  "detected_intent": "positive"
}
```

---

## 🧩 7. Ce que ce système permet

* Tu n’as **pas besoin d’attendre** un cycle ou une relance
* Tu peux répondre **en quelques secondes** à une personne intéressée
* Tu gardes **le contexte conversationnel** exact (message analysé + décision + action)
* Et tu peux **remonter dans les réponses** pour savoir ce qui a été dit, quand, et par qui

---

# 🧩 PARTIE 6 – IMPLÉMENTATION TECHNIQUE GÉNÉRALE

---

## 📁 1. Arborescence d’un agent

Chaque agent a son propre dossier, contenant sa logique, sa configuration, son prompt et ses éventuels logs.

### Exemple pour `ScraperAgent` :

```
agents/
├── scraper_agent/
│   ├── config.json         ← paramètres dynamiques
│   ├── prompt.txt          ← prompt template du LLM
│   ├── scraper_agent.py    ← logique principale (classe)
│   └── logs/               ← logs spécifiques (optionnel)
```

---

## ⚙️ 2. Structure standard d’un agent (`.py`)

Tous les agents respectent la même interface :

```python
class ScraperAgent:
    def __init__(self, config_path: str = "config.json"):
        self.name = "ScraperAgent"
        self.config = load_config(config_path)

    def run(self, input_data: dict) -> dict:
        prompt = self.build_prompt(input_data)
        response = call_llm(prompt)
        return self.parse_output(response)

    def build_prompt(self, context: dict) -> str:
        with open("prompt.txt", "r") as f:
            template = f.read()
        return template.format(**self.config, **context)

    def parse_output(self, raw: str) -> dict:
        # À adapter selon la sortie attendue (JSON, liste, etc.)
        return json.loads(raw)

    def update_config(self, key: str, value):
        self.config[key] = value
        save_config(self.config)
```

> Tous les agents peuvent être appelés comme `agent.run(input_data)`

---

## 🔧 3. Fichier `config.json`

Chaque agent a un fichier de configuration comme :

```json
{
  "limit_per_run": 50,
  "language": "fr",
  "preferred_sources": ["apify", "apollo"],
  "blacklisted_niches": ["crypto", "adult"]
}
```

* Le fichier est lu à chaque appel `run()`
* Peut être modifié à chaud par le `OverseerAgent`
* C’est **la base de contrôle des comportements** agent par agent

---

## 🧾 4. Fichier `prompt.txt`

Contient le rôle de l’agent + ses consignes. Variables injectées dynamiquement.

### Exemple pour ScraperAgent :

```txt
Tu es un ScraperAgent.
Tu travailles sur la niche suivante : {niche}.
- Nombre maximal de leads : {limit_per_run}
- Langue : {language}
- Sources à utiliser : {preferred_sources}
- À exclure : {blacklisted_niches}

Ne retourne que des leads valides (nom, entreprise, email) au format JSON.
```

---

## 📡 5. Fonction d’appel au LLM

Le système utilise les modèles **ChatGPT 4.1**, **4.1 Mini**, et **4.1 Nano**, selon la tâche :

| Complexité de la tâche                                                    | Modèle utilisé |
| ------------------------------------------------------------------------- | -------------- |
| Raisonnement stratégique / décision                                       | `gpt-4.1`      |
| Tâches intermédiaires (analyse, scoring, interprétation de réponse, etc.) | `gpt-4.1-mini` |
| Extraction simple, reformulation, relance automatique, etc.               | `gpt-4.1-nano` |

### Fonction type :

```python
def call_llm(prompt: str, complexity: str = "high") -> str:
    if complexity == "high":
        model = "gpt-4.1"
    elif complexity == "medium":
        model = "gpt-4.1-mini"
    else:
        model = "gpt-4.1-nano"

    return openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )["choices"][0]["message"]["content"]
```

> Le choix du modèle est fait automatiquement selon l’agent ou la tâche, configurable si besoin dans les `config.json`.

---

## 🧠 6. Connexion à la mémoire

Les agents peuvent interroger **Qdrant** (mémoire vectorielle) selon leurs besoins.

```python
from utils.qdrant import query_knowledge

knowledge = query_knowledge("prospection B2B cold coaching")
```

> Le résultat peut être injecté dans le prompt si pertinent.

---

## 🧾 7. Suivi d’état et logiques

* Tous les agents utilisent un `LoggerAgent` pour parler :

```python
self.speak("J’ai terminé le nettoyage des 43 leads.", target="QualificationSupervisor")
```

* L’`OverseerAgent` décide toujours des suites à donner.

---

## 🧱 8. Convention d’identification

Chaque `lead`, `campagne`, `niche`, etc. doit avoir un `uuid` stable pour le suivi.

```json
{
  "lead_id": "ae2b1fca-c3ef-11ed-afa1-0242ac120002",
  "campaign_id": "c_44",
  "niche": "coaching B2C"
}
```

---

## 🧭 9. Ordre d’implémentation recommandé

Pour un MVP complet :

1. `OverseerAgent` + `AdminInterpreterAgent`
2. `ScraperAgent` → `CleanerAgent` → `ScoringAgent`
3. `MessagingAgent` + `FollowUpAgent`
4. `ResponseInterpreterAgent` + webhook Mailgun/Twilio
5. `LoggerAgent` + visualisation sandbox
6. `AgentSchedulerAgent` (fonctionnel sans UI)
7. `PivotStrategyAgent` (en dernier, quand données disponibles)

---
🧩 PARTIE 7 – ENVIRONNEMENT ET DÉPENDANCES DES AGENTS
📦 Environnement Python
Tous les agents fonctionnent dans un environnement Python isolé (venv) indépendant du backend et du frontend.

Pourquoi un venv ?
Éviter les conflits de versions avec d'autres parties du projet (FastAPI, etc.)

Gérer les dépendances spécifiques aux agents

Travailler/modifier les agents sans impacter le backend

🧪 Création de l’environnement
À la racine du dossier des agents :

bash
Copy
Edit
python3 -m venv .venv
source .venv/bin/activate
📚 Librairies à installer
Voici la liste complète des dépendances nécessaires au bon fonctionnement des agents :

txt
Copy
Edit
openai                # pour les appels à GPT-4.1, mini et nano
qdrant-client         # pour la mémoire vectorielle (Qdrant)
python-dotenv         # pour charger les variables d’environnement depuis .env
httpx                 # pour faire des requêtes HTTP (webhooks, APIs)
pydantic              # pour structurer/valider les données
tqdm                  # pour les barres de progression si besoin
orjson                # parsing JSON rapide et robuste
Elles doivent être installées via :

bash
Copy
Edit
pip install -r requirements.txt
ou manuellement :

bash
Copy
Edit
pip install openai qdrant-client python-dotenv httpx pydantic orjson tqdm
🔐 Variables d’environnement (fichier .env requis)
Le fichier .env doit contenir les clés nécessaires aux agents :

env
Copy
Edit
OPENAI_API_KEY=sk-...
QDRANT_URL=http://localhost:6333
MAILGUN_API_KEY=...
MAILGUN_DOMAIN=...
TWILIO_SID=...
TWILIO_TOKEN=...
TWILIO_PHONE=+33...


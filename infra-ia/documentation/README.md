# 🧠 BerinIA - Écosystème d'Agents Intelligents

BerinIA est un système d'agents autonomes collaboratifs, orchestrés par une logique centrale intelligente, conçu pour:

- Scraper des leads qualifiés dans des niches précises
- Nettoyer, valider et scorer ces leads
- Envoyer des messages personnalisés en cold outreach (email et SMS)
- Relancer automatiquement selon des scénarios dynamiques
- Analyser les réponses reçues
- Apprendre et optimiser ses performances
- Réagir en temps réel aux événements (réponses)

## 🎯 Philosophie du système

Le système BerinIA repose sur plusieurs principes clés:

- **Centralisation intelligente**: L'OverseerAgent supervise et oriente tous les agents du système
- **Modularité**: Chaque agent a un rôle clair, autonome et réutilisable
- **Communication en langage naturel**: Interaction avec l'admin en langage libre
- **Réactivité temps réel**: Traitement immédiat des réponses (emails, SMS)
- **Adaptation continue**: Apprentissage et optimisation des performances
- **Traçabilité complète**: Historisation de toutes les actions et décisions

## 🔧 Prérequis

- Python 3.8 ou supérieur
- Une clé API OpenAI (pour GPT-4.1, GPT-4.1-mini et GPT-4.1-nano)
- Optionnel: Comptes Mailgun et Twilio pour les fonctionnalités d'envoi d'emails et SMS

## 📦 Installation

1. Clonez ce dépôt:
   ```bash
   git clone https://github.com/berinai/berinia.git
   cd berinia/infra-ia
   ```

2. Créez et activez un environnement virtuel Python:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Pour Linux/Mac
   # OU
   .venv\Scripts\activate  # Pour Windows
   ```

3. Installez les dépendances:
   ```bash
   pip install -r requirements.txt
   ```

4. Créez un fichier `.env` avec vos clés API:
   ```
   OPENAI_API_KEY=sk-...
   
   # Optionnel - Qdrant pour la mémoire vectorielle
   QDRANT_URL=http://localhost:6333
   
   # Optionnel - Mailgun pour les emails
   MAILGUN_API_KEY=...
   MAILGUN_DOMAIN=...
   
   # Optionnel - Twilio pour les SMS
   TWILIO_SID=...
   TWILIO_TOKEN=...
   TWILIO_PHONE=+33...
   ```

5. Vérifiez votre installation:
   ```bash
   python verify_installation.py
   # Pour une vérification complète (test de l'API OpenAI):
   python verify_installation.py --full
   ```

## 🚀 Démarrage du système

### Interface de ligne de commande

```bash
python interact.py
```

Cette commande démarre l'interface interactive où vous pouvez communiquer avec le système en langage naturel.

### Serveur de webhooks (réception des réponses)

```bash
python webhook/run_webhook.py
```

Ce serveur écoute les notifications de réponses (emails, SMS) et les transmet aux agents appropriés.

## 📊 Structure du projet

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

## 🔄 Fonctionnement global

1. L'OverseerAgent initialise et orchestre tous les agents
2. L'AdminInterpreterAgent reçoit vos instructions en langage naturel
3. L'AdminInterpreterAgent les traduit en actions structurées pour l'OverseerAgent
4. L'OverseerAgent décide quels agents doivent intervenir et comment
5. Les agents effectuent leurs tâches spécifiques et renvoient les résultats
6. Le VisualAnalyzerAgent et le NicheClassifierAgent peuvent enrichir les leads avec des analyses visuelles et des approches personnalisées par secteur
7. L'OverseerAgent transmet la réponse finale à l'admin

## 🌟 Exemple d'utilisation

```
>>> Explore la niche des consultants en cybersécurité

[NicheExplorerAgent] Je vais explorer cette niche...

>>> Récupère 50 leads dans cette niche

[ScraperAgent] Je vais chercher 50 leads...
[CleanerAgent] Je nettoie les données...
[Score] Les leads ont été analysés et scorés...

>>> Prépare une campagne d'emails avec comme sujet "Sécurisez votre entreprise"

[MessagingAgent] Campagne préparée...

>>> Envoie cette campagne aux 20 meilleurs leads

[MessagingAgent] Emails envoyés à 20 leads...

>>> Planifie une relance dans 3 jours

[SchedulerAgent] Relance programmée pour le 2025-05-06 à 10h00...
```

## 📊 Architecture technique des agents

Chaque agent est construit sur le même modèle:

```
agents/agent_name/
├── agent_name.py     # Code principal de l'agent
├── config.json       # Configuration de l'agent
└── prompt.txt        # Prompt spécifique pour le LLM
```

L'architecture à base de prompts permet une grande flexibilité et réutilisabilité.

## 📝 Ressources supplémentaires

Pour plus d'informations sur chaque agent, consultez la documentation spécifique dans leurs dossiers respectifs.

## 🔒 Sécurité

- Ne partagez jamais vos clés API
- Stockez-les uniquement dans le fichier `.env` (non commité)
- Pour la production, utilisez des vérifications de signature sur les webhooks

## 📄 Licence

Copyright © 2025 BerinIA - Tous droits réservés

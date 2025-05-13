# Guide de gestion des agents BerinIA

## Structure unifiée des agents

La gestion des agents dans BerinIA a été unifiée et standardisée pour suivre le format snake_case. Ce document explique la nouvelle architecture et les conventions adoptées.

## Architecture centralisée

### 1. Définition centralisée des agents

Tous les agents du système sont désormais définis dans un fichier centralisé:

```
infra-ia/utils/agent_definitions.py
```

Ce fichier contient:
- La liste complète de tous les agents du système
- Leurs métadonnées (nom, classe, catégorie, chemin de configuration)
- Des fonctions utilitaires pour accéder aux définitions

Pour ajouter un nouvel agent au système, il suffit de l'ajouter à la liste `AGENT_DEFINITIONS` dans ce fichier.

### 2. Convention de nommage unifiée

Tous les agents respectent maintenant la convention snake_case:

- **Dossiers**: `agents/agent_name/`
- **Modules**: `agent_name_agent.py`
- **Classes**: `AgentNameAgent`

### 3. Registre central

Le registre d'agents (`registry.py`) a été amélioré pour utiliser les définitions centralisées, ce qui permet:
- Création dynamique des agents à partir des définitions
- Gestion transparente des instances d'agents
- Chargement par catégories

## Comment ajouter un nouvel agent

1. **Créer le dossier et les fichiers**:
   ```
   agents/nouvel_agent/
   ├── nouvel_agent_agent.py
   └── config.json
   ```

2. **Ajouter la définition** dans `utils/agent_definitions.py`:
   ```python
   {
       "name": "NouvelAgent",
       "module_path": "agents.nouvel_agent.nouvel_agent_agent",
       "class_name": "NouvelAgent",
       "category": "catégorie_appropriée",
       "description": "Description de l'agent",
       "config_path": "agents/nouvel_agent/config.json"
   }
   ```

3. **Ajouter aux listes spéciales** si nécessaire:
   - `WEBHOOK_REQUIRED_AGENTS` si l'agent doit être disponible pour le webhook

## Composants principaux

### Fichier de définitions (`agent_definitions.py`)

Contient:
- `AGENT_DEFINITIONS`: Liste principale des agents
- `ALL_AGENT_NAMES`: Liste des noms d'agents pour validation
- `get_agent_definition()`: Fonction pour obtenir la définition d'un agent
- `get_agents_by_category()`: Fonction pour obtenir les agents d'une catégorie
- `WEBHOOK_REQUIRED_AGENTS`: Liste des agents requis par le webhook

### Registre d'agents (`registry.py`)

Le registre est un singleton qui:
- Crée et maintient les instances d'agents
- Utilise les définitions centralisées pour leur création
- Offre des méthodes comme `get_or_create()` et `create_all_agents()`

## Tests

Pour vérifier que tous les agents sont correctement configurés:

```bash
python3 test_agent_loading.py
```

Ce script teste:
1. Le chargement de tous les modules d'agents
2. La création d'instances via le registre

## Dépendances externes

Certains agents nécessitent des packages Python spécifiques:
- ScraperAgent: `tldextract`
- MessagingAgent: `twilio`
- VisualAnalyzerAgent: `playwright`

Ces dépendances doivent être installées dans l'environnement virtuel:

```bash
source venv/bin/activate
pip install tldextract twilio playwright
python -m playwright install
```

## Structure des dossiers snake_case standardisée

Tous les dossiers d'agents suivent maintenant la convention snake_case:

```
agents/
├── admin_interpreter/
├── cleaner/
├── database_query/
├── duplicate_checker/
├── follow_up/
├── logger/
├── messaging/
├── meta/
├── niche_classifier/
├── niche_explorer/
├── overseer/
├── pivot_strategy/
├── prospection_supervisor/
├── qualification_supervisor/
├── response_interpreter/
├── response_listener/
├── scheduler/
├── scoring/
├── scraper/
├── scraping_supervisor/
├── test/
├── validator/
├── visual_analyzer/
└── web_presence_checker/
```

Les anciens dossiers suivant la convention camelCase ont été supprimés pour une meilleure lisibilité et cohérence.

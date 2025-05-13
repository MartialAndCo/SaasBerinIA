# Rapport de diagnostic du webhook SMS BerinIA

## Résumé du problème

Le webhook SMS situé dans `/root/berinia/infra-ia/webhook/run_webhook.py` ne parvient pas à traiter correctement les requêtes SMS entrantes, renvoyant une erreur 500. Notre diagnostic a identifié le problème principal: une incompatibilité entre les chemins d'import des agents et leur structure réelle dans le système de fichiers.

## Analyse détaillée

### 1. Structure des agents et incompatibilité d'imports

Notre diagnostic révèle que les agents "Response" existent dans une structure à base de **snake_case**:
- `/agents/response_listener/response_listener_agent.py`
- `/agents/response_interpreter/response_interpreter_agent.py`

Tandis que:
- Le webhook tente probablement de les importer en utilisant une convention différente
- D'autres agents utilisent une structure **camelCase**: `/agents/overseeragent/overseeragent.py`

### 2. Mécanisme d'initialisation des agents

Dans le fichier `init_system.py`, les agents sont définis avec:
```python
agent_definitions = [
    {
        "name": "ResponseListenerAgent",
        "class_path": "agents.response_listener.response_listener_agent"
        ...
    }
]
```

Mais ils sont probablement importés par le webhook d'une manière différente qui ne correspond pas à cette structure.

### 3. Problème d'accès du webhook aux agents

Le webhook tente d'accéder aux agents avec une syntaxe du type:
```python
if "ResponseListenerAgent" in agents:
    response_listener = agents["ResponseListenerAgent"]
```

Le problème est que les agents ne sont pas correctement chargés dans le dictionnaire `agents` que le webhook consulte.

## Solutions recommandées

Deux approches sont possibles, sans modifier les fichiers existants:

### Option 1: Ajuster le chemin d'importation (recommandée)

Créer un fichier de configuration spécifique pour le webhook qui corrige le chemin d'importation:

```python
# /root/berinia/infra-ia/webhook/webhook_config.py
from agents.response_listener.response_listener_agent import ResponseListenerAgent
from agents.response_interpreter.response_interpreter_agent import ResponseInterpreterAgent

# Dictionnaire d'agents explicitement défini pour le webhook
webhook_agents = {
    "ResponseListenerAgent": ResponseListenerAgent(),
    "ResponseInterpreterAgent": ResponseInterpreterAgent()
}
```

Puis modifier le webhook pour utiliser cette configuration.

### Option 2: Adapter les agents via des symlinks

Créer des symlinks qui permettent au webhook de trouver les agents dans la structure qu'il attend:

```bash
# Exemple de commande (à ajuster selon l'analyse détaillée)
ln -s /root/berinia/infra-ia/agents/response_listener /root/berinia/infra-ia/agents/responselisteneragent
ln -s /root/berinia/infra-ia/agents/response_interpreter /root/berinia/infra-ia/agents/responseinterpreteragent
```

## Recommandation finale

1. Implémenter l'Option 1 en créant un fichier de configuration spécifique
2. Mettre à jour le service webhook pour utiliser cette configuration
3. Standardiser à long terme la convention de nommage (choisir soit snake_case soit camelCase pour tous les agents)

---

Le diagnostic complet est disponible dans les logs:
- `/root/berinia/infra-ia/tests/temp_webhook_test/agent_init_debug.log`

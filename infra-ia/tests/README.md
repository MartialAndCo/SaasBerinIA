# Tests du système BerinIA

Ce répertoire contient les tests pour les différents composants du système BerinIA.

## Structure

- `test_agent_functionality.py` - Tests des fonctionnalités de base des agents
- `test_agent_integration.py` - Tests d'intégration entre agents
- `test_overseer_delegation.py` - Tests de la délégation par l'OverseerAgent
- `test_llm_integration.py` - Tests d'intégration avec les modèles de langage
- `test_qdrant_integration.py` - Tests d'intégration avec la base vectorielle Qdrant
- `test_response_listener.py` - Tests du ResponseListenerAgent
- `test_scheduler.py` - Tests de l'AgentSchedulerAgent
- `test_system_initialization.py` - Tests de l'initialisation du système

## Problèmes connus

### Blocage des tests de l'AgentSchedulerAgent

Les tests unitaires pour l'AgentSchedulerAgent peuvent se bloquer en raison d'interactions complexes avec d'autres composants, notamment:

1. La méthode `speak` de la classe `Agent` appelle `LoggerAgent.log_interaction`
2. Le `LoggerAgent` est une dépendance statique qui peut provoquer des blocages dans un contexte de test
3. Même en remplaçant ces dépendances par des mocks, des blocages peuvent survenir

#### Solution de contournement

Un script de diagnostic standalone a été créé pour tester l'AgentSchedulerAgent de manière isolée:

```bash
python3 diagnose_cancel_task.py
```

Ce script fournit un environnement plus contrôlé et montre que l'agent fonctionne correctement lorsqu'il est testé de manière isolée.

#### Recommandation pour les développeurs

1. Pour tester l'AgentSchedulerAgent, utilisez de préférence le script de diagnostic ou des tests fonctionnels
2. Si vous modifiez `test_scheduler.py`, assurez-vous de patcher complètement:
   - `LoggerAgent` (via patch de classe)
   - `LoggerAgent.log_interaction` (via patch de méthode statique)
   - `Agent.speak` (via patch de méthode d'instance)
   - Toute interaction avec des fichiers ou des ressources externes

3. L'approche la plus fiable reste d'isoler complètement le composant en testant directement ses fonctionnalités principales, comme le fait le script `diagnose_cancel_task.py`.

## Exécution des tests

Pour exécuter un test spécifique:

```bash
python -m unittest tests/test_agent_functionality.py
```

Pour exécuter tous les tests:

```bash
python -m unittest discover -s tests
```

> **Note**: Pour les tests qui peuvent se bloquer, il est recommandé de les exécuter individuellement et avec un timeout.

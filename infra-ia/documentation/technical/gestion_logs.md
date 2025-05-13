# Système de Logs Unifié pour BerinIA

Ce document présente le nouveau système de logs unifié pour le projet BerinIA. L'objectif est de centraliser tous les logs dans un seul emplacement avec une structure claire et cohérente.

## Structure des Logs

Tous les logs sont maintenant centralisés dans un répertoire unique :
```
/root/berinia/unified_logs/
```

### Fichiers de Logs Principaux

| Fichier | Description |
|---------|-------------|
| `system.log` | Journal principal du système contenant tous les messages importants |
| `error.log` | Journal ne contenant que les erreurs et exceptions |
| `agents.log` | Logs spécifiques au fonctionnement des agents |
| `webhook.log` | Logs du serveur webhook |
| `whatsapp.log` | Logs spécifiques à l'intégration WhatsApp |
| `agent_interactions.jsonl` | Format JSON Lines pour les interactions des agents (pour analyse) |

## Utilisation du Système de Logs

Le module `utils/logging_config.py` fournit une interface simple pour utiliser ce système.

### Initialisation de Base

```python
from utils.logging_config import get_logger

# Obtenir un logger pour un module spécifique
logger = get_logger("nom_du_module")

# Utilisation
logger.info("Message d'information")
logger.warning("Avertissement")
logger.error("Erreur")
logger.debug("Message de débogage")
```

### Configuration Complète pour un Service

Pour initialiser un service complet avec tous les handlers configurés :

```python
from utils.logging_config import setup_logging

# Initialiser le logger principal pour un service
logger = setup_logging("nom_du_service")

# Utilisation
logger.info("Démarrage du service")
```

## Niveaux de Logs

- **ERROR** : Erreurs empêchant le bon fonctionnement du système
- **WARNING** : Problèmes potentiels nécessitant une attention
- **INFO** : Informations générales sur le fonctionnement du système
- **DEBUG** : Informations détaillées pour le débogage

## Bonnes Pratiques

- Utilisez des messages clairs et informatifs
- Incluez les informations contextuelles importantes (ID d'utilisateur, références, etc.)
- Utilisez le niveau de log approprié
- Ne loggez pas de données sensibles (mots de passe, tokens)
- Pour les exceptions, incluez la stack trace :
  ```python
  try:
      # code qui peut lever une exception
  except Exception as e:
      logger.error(f"Une erreur est survenue: {str(e)}")
      import traceback
      logger.error(traceback.format_exc())
  ```

## Rotation des Logs

Pour éviter que les fichiers de logs ne deviennent trop volumineux, une politique d'archivage sera implémentée ultérieurement.

En attendant, vous pouvez archiver manuellement les logs si nécessaire :
```bash
# Exemple de rotation manuelle
cd /root/berinia/unified_logs/
mv system.log system.log.old
touch system.log
```

## API d'Accès aux Logs

Le serveur webhook fournit un endpoint pour accéder aux logs récents :
```
GET /webhook/logs?lines=50
```
Ce endpoint retourne les 50 dernières lignes du journal webhook.log par défaut (paramètre configurable).

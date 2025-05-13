# Système de Logs Unifié

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [Structure des logs](#structure-des-logs)
- [Utilisation du système de logs](#utilisation-du-système-de-logs)
- [Niveaux de logs](#niveaux-de-logs)
- [Bonnes pratiques](#bonnes-pratiques)
- [Rotation des logs](#rotation-des-logs)
- [API d'accès aux logs](#api-daccès-aux-logs)

## Vue d'ensemble

BerinIA utilise un système de logs unifié qui centralise tous les messages dans un répertoire unique avec une structure cohérente. Cette approche permet une meilleure traçabilité des événements, facilite le débogage et offre une vue complète sur les opérations du système.

## Structure des logs

Tous les logs sont centralisés dans un répertoire unique :
```
/root/berinia/unified_logs/
```

### Fichiers de logs principaux

| Fichier | Description |
|---------|-------------|
| `system.log` | Journal principal du système contenant tous les messages importants |
| `error.log` | Journal ne contenant que les erreurs et exceptions |
| `agents.log` | Logs spécifiques au fonctionnement des agents |
| `webhook.log` | Logs du serveur webhook |
| `whatsapp.log` | Logs spécifiques à l'intégration WhatsApp |
| `agent_interactions.jsonl` | Format JSON Lines pour les interactions des agents (pour analyse) |

### Format des messages d'interaction entre agents

Les interactions entre agents sont enregistrées dans un format JSON structuré :

```json
{
  "timestamp": "2025-05-03T18:52:14",
  "from": "ScraperAgent",
  "to": "CleanerAgent",
  "message": "J'ai terminé le scraping sur la niche coaching. Voici 47 leads.",
  "context_id": "campaign_042"
}
```

Ce format permet :
- Une traçabilité précise des communications
- L'analyse des flux de travail
- L'identification des problèmes dans la chaîne de traitement

## Utilisation du système de logs

Le module `utils/logging_config.py` fournit une interface simple pour utiliser ce système.

### Initialisation de base

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

### Configuration complète pour un service

Pour initialiser un logger principal pour un service complet :

```python
from utils.logging_config import setup_logging

# Initialiser le logger principal pour un service
logger = setup_logging("nom_du_service")

# Utilisation
logger.info("Démarrage du service")
```

### Méthode speak() des agents

Chaque agent possède une méthode `speak()` qui permet d'envoyer un message vers un canal de log centralisé :

```python
def speak(self, message: str, target: str = None):
    """
    Envoie un message à un autre agent ou au log général.
    
    Args:
        message: Le message à envoyer
        target: L'agent destinataire (optionnel)
    """
    LoggerAgent.log_interaction(self.name, target, message)
```

Exemple d'utilisation dans un agent :
```python
self.speak(
  "J'ai récupéré 47 leads dans la niche coaching. Je transmets à CleanerAgent.",
  target="CleanerAgent"
)
```

## Niveaux de logs

Le système utilise les niveaux de logs standards de Python :

- **ERROR** : Erreurs empêchant le bon fonctionnement du système
- **WARNING** : Problèmes potentiels nécessitant une attention
- **INFO** : Informations générales sur le fonctionnement du système
- **DEBUG** : Informations détaillées pour le débogage

## Bonnes pratiques

### Messages clairs et informatifs

Privilégiez des messages qui contiennent :
- L'action ou l'événement concerné
- Les identifiants pertinents (ID de lead, de campagne, etc.)
- Le résultat ou l'état

Exemple :
```python
logger.info(f"Analyse terminée pour le lead {lead_id} avec un score de {score}/100")
```

### Inclusion du contexte

Ajoutez toujours le contexte nécessaire pour comprendre le message :

```python
logger.info(f"Campaign {campaign_id} started | Target: {target_niche} | Leads: {lead_count}")
```

### Gestion des exceptions

Pour les exceptions, incluez toujours la stack trace :

```python
try:
    # code qui peut lever une exception
except Exception as e:
    logger.error(f"Une erreur est survenue: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
```

### Ne pas logger de données sensibles

Évitez d'inclure dans les logs :
- Mots de passe
- Tokens d'API
- Informations personnelles des leads
- Clés d'accès

## Rotation des logs

Pour éviter que les fichiers de logs ne deviennent trop volumineux, un système de rotation automatique basé sur la taille est en place. Chaque fichier de log est limité à environ 1000 lignes (environ 150 KB), après quoi une rotation est effectuée automatiquement.

### Fonctionnement de la rotation

- Lorsqu'un fichier de log atteint la taille maximale (environ 1000 lignes), il est automatiquement archivé
- Les fichiers archivés sont stockés dans un sous-dossier `archives` du dossier de logs principal
- Le système conserve les 5 derniers fichiers archivés pour chaque type de log
- Les fichiers sont nommés avec un suffixe numérique (e.g., `system.log.1`, `system.log.2`, ...)
- La rotation est gérée par `CustomRotatingFileHandler` dans le module `utils/logging_config.py`

### Organisation des fichiers

```
/root/berinia/infra-ia/logs/
├── system.log            # Fichier de log actif
├── webhook.log           # Fichier de log actif
├── whatsapp.log          # Fichier de log actif
├── ...
└── archives/             # Dossier contenant les anciens logs
    ├── system.log.1      # Fichier archivé le plus récent
    ├── system.log.2      # Fichier archivé plus ancien
    ├── webhook.log.1
    └── ...
```

Cette organisation permet de garder le dossier principal propre tout en conservant un historique des logs.

### Test de la rotation

Un script de test est disponible pour vérifier le bon fonctionnement de la rotation :

```bash
# Exécution du test de rotation
cd /root/berinia/infra-ia
python tests/test_log_rotation.py
```

Ce test va générer suffisamment de messages pour déclencher plusieurs rotations et vous permettre de valider le fonctionnement du système. Après l'exécution du test, vous devriez voir :
- Un fichier `test_rotation.log` dans le dossier principal des logs
- Plusieurs fichiers `test_rotation.log.1`, `test_rotation.log.2`, etc. dans le sous-dossier `archives`

## API d'accès aux logs

Le serveur webhook fournit un endpoint pour accéder aux logs récents :

```
GET /webhook/logs?lines=50&type=system
```

Paramètres :
- `lines` : Nombre de lignes à récupérer (défaut: 50)
- `type` : Type de log (system, error, agents, webhook, whatsapp)

Exemple de réponse :

```json
{
  "status": "success",
  "log_type": "system",
  "lines": [
    "2025-05-08 13:45:22 | INFO | OverseerAgent | Starting lead enrichment workflow",
    "2025-05-08 13:45:23 | INFO | ScraperAgent | Retrieved 25 leads for niche 'consultant'",
    "2025-05-08 13:45:25 | WARNING | CleanerAgent | 3 leads had invalid email formats"
  ]
}
```

### Visualisation en "chat d'agents"

Dans l'interface sandbox (ou admin), vous pouvez visualiser les interactions entre agents comme un fil de discussion :

```
🧠 OverseerAgent → ScrapingSupervisor :
    Reprends le scraping sur la niche "menuisier" demain à 10h.

🔎 ScraperAgent → CleanerAgent :
    Voici 38 leads valides sur la niche immobilier B2C.

🧽 CleanerAgent → QualificationSupervisor :
    Tous les leads ont été nettoyés. 2 doublons supprimés.
```

Les messages sont stylisés par agent et filtrables par :
- Agent
- Campagne
- Plage de dates

---

[Retour à l'accueil](../index.md) | [Configuration des webhooks →](webhooks.md)

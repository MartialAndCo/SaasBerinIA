# Intégration des Services Systemd dans BerinIA

## Vue d'ensemble

BerinIA utilise systemd pour gérer ses différents services. Cette intégration permet:

- Surveillance facile de l'état des services
- Gestion (démarrage, arrêt, redémarrage) des services via l'interface utilisateur
- Accès aux logs pour le diagnostic de problèmes
- Redémarrage automatique des services en cas d'échec

Cette documentation décrit l'implémentation technique de cette intégration et comment l'utiliser.

## Services gérés

BerinIA gère les services systemd suivants:

| Service | Description | Rôle |
|---------|-------------|------|
| `berinia.service` | API backend principale | Gère les fonctionnalités principales du backend |
| `berinia-next.service` | Frontend Next.js | Interface utilisateur web |
| `berinia-webhook.service` | Serveur webhook | Réception d'événements externes |
| `berinia-whatsapp.service` | Intégration WhatsApp | Communication avec WhatsApp |
| `berinia-qdrant.service` | Base de données vectorielle | Stockage et recherche vectorielle |
| `berinia-agents.service` | Agents IA | Environnement d'exécution des agents IA |
| `berinia-scheduler.service` | Planificateur | Exécution des tâches planifiées |

## Architecture technique

### Backend

Le service `ServicesService` dans `/backend/app/services/services_service.py` implémente la logique métier pour:

- Récupérer l'état des services
- Exécuter des actions sur les services (start, stop, restart, enable, disable)
- Récupérer les logs des services

Ce service utilise les commandes systemctl pour interagir avec systemd.

### API REST

Les endpoints API sont définis dans `/backend/app/api/endpoints/services.py`:

- `GET /api/services` - Liste tous les services gérés
- `GET /api/services/{service_name}` - Obtient les détails d'un service spécifique
- `POST /api/services/{service_name}/action?action={action}` - Exécute une action sur un service
- `GET /api/services/{service_name}/logs` - Récupère les logs d'un service

### Frontend

Le frontend utilise des proxys API dans:
- `frontend/app/api/system/services/route.ts` - Pour récupérer l'état des services
- `frontend/app/api/system/service-control/route.ts` - Pour contrôler les services

L'interface utilisateur dans `frontend/app/admin/settings/components/services-tab.tsx` permet de visualiser et gérer les services.

## Utilisation de l'API

### Récupérer l'état de tous les services

```http
GET /api/services
```

Exemple de réponse:
```json
{
  "status": "success",
  "data": [
    {
      "name": "berinia-qdrant.service",
      "status": "active",
      "uptime": "0j 2h 55m"
    },
    {
      "name": "berinia-webhook.service",
      "status": "active",
      "uptime": "0j 19h 41m"
    },
    {
      "name": "berinia-agents.service",
      "status": "inactive",
      "uptime": null
    }
  ]
}
```

### Récupérer les détails d'un service spécifique

```http
GET /api/services/{service_name}
```

Exemple de réponse:
```json
{
  "status": "success",
  "data": {
    "name": "berinia-qdrant.service",
    "display_name": "berinia-qdrant",
    "description": "Base vectorielle Qdrant",
    "status": "active",
    "is_active": true,
    "is_enabled": true,
    "uptime": "2j 5h 20m"
  }
}
```

### Exécuter une action sur un service

```http
POST /api/services/{service_name}/action?action={action}
```

où `{action}` peut être:
- `start` - Démarrer le service
- `stop` - Arrêter le service
- `restart` - Redémarrer le service
- `enable` - Activer le démarrage automatique
- `disable` - Désactiver le démarrage automatique

Exemple de réponse:
```json
{
  "status": "success",
  "data": {
    "success": true,
    "message": "Action start exécutée avec succès sur berinia-agents.service",
    "service": {
      "name": "berinia-agents.service",
      "display_name": "berinia-agents",
      "description": "Environnement d'exécution des agents IA",
      "status": "activating",
      "is_active": false,
      "is_enabled": true,
      "uptime": null
    }
  }
}
```

### Récupérer les logs d'un service

```http
GET /api/services/{service_name}/logs?lines={number_of_lines}
```

Exemple de réponse:
```json
{
  "status": "success",
  "data": {
    "service": "berinia-agents.service",
    "logs": [
      "mai 16, 15:30:22 berinia[12345]: INFO:     Started server process [12345]",
      "mai 16, 15:30:22 berinia[12345]: INFO:     Waiting for application startup.",
      "mai 16, 15:30:22 berinia[12345]: INFO:     Application startup complete."
    ]
  }
}
```

## Interface utilisateur

L'interface utilisateur permet de:

1. Visualiser l'état de tous les services avec leur statut (actif/inactif) et uptime
2. Démarrer, arrêter et redémarrer les services
3. Voir les logs des services
4. Recevoir des notifications sur les changements d'état importants

## Sécurité

L'exécution des commandes systemctl nécessite des privilèges sudo. La configuration sudo doit être correctement configurée pour permettre à l'utilisateur exécutant le service backend d'exécuter ces commandes sans mot de passe.

## Résolution de problèmes

Si un service ne démarre pas correctement:

1. Vérifiez les logs du service avec `GET /api/services/{service_name}/logs`
2. Assurez-vous que les dépendances du service sont installées et configurées correctement
3. Vérifiez les permissions des fichiers de service et des répertoires de travail
4. Essayez de redémarrer le service manuellement avec `sudo systemctl restart {service_name}`

## Notes techniques

- Les temps d'uptime sont formatés pour être lisibles par les utilisateurs (ex: "2j 5h 20m")
- Les services sont considérés comme inactifs si leur statut n'est pas "active"
- Les autorisations sudo sont nécessaires pour les opérations de contrôle des services

# API Paramètres Système (System Settings)

Ce document décrit les endpoints API dédiés aux paramètres système et à la gestion des services systemd.

## Aperçu

L'API Paramètres Système permet de :
- Lire et modifier les paramètres d'intégration (Twilio, Instantly.ai, WhatsApp)
- Lire et modifier les paramètres de planification
- Consulter l'état des services systemd en temps réel
- Contrôler les services (démarrage, arrêt, redémarrage)

## Endpoints principaux

### Paramètres d'intégration

- `GET /api/system/integrations` - Récupérer tous les paramètres d'intégration
- `POST /api/system/integrations` - Mettre à jour les paramètres d'intégration
- `GET /api/system/integrations/instantly` - Récupérer les paramètres Instantly.ai
- `POST /api/system/integrations/instantly` - Mettre à jour les paramètres Instantly.ai
- `GET /api/system/integrations/whatsapp` - Récupérer les paramètres WhatsApp
- `POST /api/system/integrations/whatsapp` - Mettre à jour les paramètres WhatsApp

### Paramètres de planification

- `GET /api/system/scheduling` - Récupérer tous les paramètres de planification
- `POST /api/system/scheduling` - Mettre à jour les paramètres de planification

### Gestion des services

- `GET /api/system/services` - Récupérer l'état des services systemd
- `POST /api/system/service-control` - Contrôler un service (démarrer/arrêter/redémarrer)

## Exemples d'utilisation

### Récupérer l'état des services

```javascript
const response = await fetch('/api/system/services');
const data = await response.json();

// Exemple de réponse
{
  "status": "success",
  "data": [
    {
      "name": "berinia-qdrant.service",
      "status": "active",
      "uptime": "3j 5h 22m"
    },
    {
      "name": "berinia-webhook.service",
      "status": "active", 
      "uptime": "2j 15h 47m"
    },
    {
      "name": "berinia-agents.service",
      "status": "inactive"
    }
  ]
}
```

### Contrôler un service

```javascript
const response = await fetch('/api/system/service-control', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    service: "berinia-agents.service",
    action: "start" // Peut être "start", "stop" ou "restart"
  })
});

const result = await response.json();

// Exemple de réponse
{
  "status": "success",
  "data": {
    "success": true,
    "service": "berinia-agents.service",
    "action": "start"
  }
}
```

## Paramètres dans la base de données

Les paramètres système sont stockés dans la table `system_settings` avec la structure suivante :

| Champ | Description |
|-------|-------------|
| `name` | Nom du paramètre (clé unique) |
| `value` | Valeur du paramètre (stockée en string) |
| `data_type` | Type de données (string, boolean, integer, float, json) |
| `category` | Catégorie du paramètre (integrations, scheduling) |
| `description` | Description du paramètre |

## Initialisation des paramètres

Les paramètres système sont automatiquement initialisés au démarrage de l'application à partir des variables d'environnement. Le script `init_system_settings.py` se charge de créer ou mettre à jour les paramètres dans la base de données.

Les paramètres par défaut incluent :

### Paramètres d'intégration

| Nom | Variable d'environnement | Description |
|-----|--------------------------|-------------|
| `twilio_account_sid` | `TWILIO_ACCOUNT_SID` | SID du compte Twilio |
| `twilio_auth_token` | `TWILIO_AUTH_TOKEN` | Token d'authentification Twilio |
| `twilio_integration_active` | `TWILIO_INTEGRATION_ACTIVE` | État d'activation de Twilio |
| `instantly_api_key` | `INSTANTLY_API_KEY` | Clé API Instantly.ai |
| `instantly_integration_active` | `INSTANTLY_INTEGRATION_ACTIVE` | État d'activation d'Instantly.ai |
| `whatsapp_integration_active` | `WHATSAPP_INTEGRATION_ACTIVE` | État d'activation de WhatsApp |
| `whatsapp_notification_group` | `WHATSAPP_NOTIFICATION_GROUP` | ID du groupe de notification WhatsApp |

### Paramètres de planification

| Nom | Variable d'environnement | Description |
|-----|--------------------------|-------------|
| `agent_frequency` | `AGENT_FREQUENCY` | Fréquence d'exécution des agents |
| `agent_execution_time` | `AGENT_EXECUTION_TIME` | Heure d'exécution des agents |
| `agent_active` | `AGENT_ACTIVE` | Activation des exécutions automatiques |
| `custom_hours_interval` | `CUSTOM_HOURS_INTERVAL` | Intervalle personnalisé (en heures) |
| `daily_report_active` | `DAILY_REPORT_ACTIVE` | Activation des rapports quotidiens |
| `daily_report_time` | `DAILY_REPORT_TIME` | Heure d'envoi des rapports |
| `report_channel_email` | `REPORT_CHANNEL_EMAIL` | Envoi des rapports par email |
| `report_channel_slack` | `REPORT_CHANNEL_SLACK` | Envoi des rapports sur Slack |
| `report_channel_whatsapp` | `REPORT_CHANNEL_WHATSAPP` | Envoi des rapports sur WhatsApp |

## Sécurité

- Le contrôle des services est limité à une liste prédéfinie de services autorisés.
- La validation des entrées est effectuée pour tous les paramètres.
- La gestion d'erreurs est intégrée pour éviter les injections SQL et les exécutions non autorisées.

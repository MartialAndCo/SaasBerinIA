# API de gestion des variables d'environnement

Cette documentation décrit l'API permettant de gérer les variables d'environnement du système BerinIA.

## Vue d'ensemble

L'API de gestion des variables d'environnement permet de :
- Récupérer les variables d'environnement actuelles
- Mettre à jour ces variables

Ces variables sont stockées dans le fichier `.env` situé dans le répertoire `/root/berinia/infra-ia/`.

## Endpoints

### GET /api/system/env-variables

Récupère les variables d'environnement actuelles.

**Réponse** :
```json
{
  "status": "success",
  "data": {
    "OPENAI_API_KEY": "sk-...",
    "INSTANTLY_API_KEY": "...",
    "TWILIO_SID": "...",
    "TWILIO_TOKEN": "...",
    "TWILIO_PHONE": "...",
    "APIFY_API_KEY": "...",
    "APOLLO_API_KEY": "..."
  }
}
```

### POST /api/system/env-variables

Met à jour les variables d'environnement.

**Paramètres** :
```json
{
  "OPENAI_API_KEY": "sk-...",
  "INSTANTLY_API_KEY": "...",
  "TWILIO_SID": "...",
  "TWILIO_TOKEN": "...",
  "TWILIO_PHONE": "...",
  "APIFY_API_KEY": "...",
  "APOLLO_API_KEY": "..."
}
```

**Réponse** :
```json
{
  "status": "success",
  "data": {
    "OPENAI_API_KEY": "sk-...",
    "INSTANTLY_API_KEY": "...",
    "TWILIO_SID": "...",
    "TWILIO_TOKEN": "...",
    "TWILIO_PHONE": "...",
    "APIFY_API_KEY": "...",
    "APOLLO_API_KEY": "..."
  }
}
```

## Activation de la fonctionnalité

Pour activer cette API, le serveur backend doit être redémarré après l'ajout du fichier `backend/app/api/endpoints/env_settings.py`.

```bash
# Arrêter le serveur API actuel
sudo systemctl stop berinia.service

# Redémarrer le serveur API
sudo systemctl start berinia.service
```

Ou si vous exécutez le serveur manuellement :

```bash
# Depuis le répertoire /root/berinia/backend
cd /root/berinia/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Sécurité

Cette API doit être utilisée avec précaution car elle permet de modifier des variables d'environnement sensibles. Assurez-vous que :

1. L'accès à cette API est limité aux administrateurs système
2. Les communications sont chiffrées (HTTPS)
3. Les clés API et autres secrets sont manipulés de manière sécurisée
4. Les valeurs modifiées sont validées avant d'être enregistrées

## Interface utilisateur

Cette API est utilisée par l'interface d'administration de BerinIA, dans la section "Paramètres > API" pour permettre une gestion visuelle des variables d'environnement.

# Intégration Frontend-Backend

Ce document explique comment le frontend Next.js et le backend FastAPI communiquent entre eux, les problèmes potentiels et leurs solutions.

## Architecture générale

L'architecture du système est composée de deux parties principales :

1. **Backend FastAPI** (port 8000) : Fournit les API pour accéder aux données et contrôler les services système
2. **Frontend Next.js** (port 3000) : Interface utilisateur qui communique avec le backend via des appels API

```
┌─────────────┐           ┌─────────────┐
│             │  API HTTP │             │
│  Frontend   │ ◄─────────┤  Backend    │
│  (Next.js)  │           │  (FastAPI)  │
│  Port 3000  │           │  Port 8000  │
└─────────────┘           └─────────────┘
```

## Communication API

### Routes d'API principales

Le système utilise les endpoints suivants :

- `/api/system/services` - Gestion des statuts des services système
- `/api/system/integrations` - Configuration des intégrations (Instantly.ai, WhatsApp)
- `/api/system/scheduling` - Configuration de la planification des tâches
- `/api/system/service-control` - Contrôle des services (démarrer, arrêter, redémarrer)

### Middleware Next.js

Un middleware Next.js a été mis en place pour gérer la communication avec le backend. Ce middleware :

1. Intercepte les requêtes API spécifiques
2. Force l'utilisation d'IPv4 (127.0.0.1) pour la communication avec le backend
3. Gère les erreurs de façon centralisée
4. Fournit des logs détaillés pour le débogage

## Solutions aux problèmes courants

### Problème de double préfixe `/api/`

**Symptôme :** Les requêtes API échouent avec des erreurs 404

**Cause :** Dans le fichier de configuration, l'URL de base contenait déjà `/api`, mais les endpoints spécifiques ajoutaient également un préfixe `/api/`.

**Solution :** Modification de la configuration dans `frontend/src/config.js` pour éviter ce doublon :

```javascript
// Avant
export const API_BASE_URL = 'https://app.berinia.com/api';
export const API_ENDPOINTS = {
  LOGIN: `${API_BASE_URL}/api/auth/login`, // Devient /api/api/auth/login
};

// Après
export const API_BASE_URL = 'https://app.berinia.com';
export const API_ENDPOINTS = {
  LOGIN: `${API_BASE_URL}/api/auth/login`, // Correct: /api/auth/login
};
```

### Problème IPv6 vs IPv4

**Symptôme :** Erreurs de connexion avec : `connect ECONNREFUSED ::1:8000`

**Cause :** Node.js/Next.js tente d'utiliser IPv6 (::1) par défaut, mais le backend n'est peut-être pas configuré pour écouter sur IPv6.

**Solutions :**

1. **Utilisation explicite d'IPv4 dans les routes API :**
   ```javascript
   const BACKEND_URL = 'http://127.0.0.1:8000/api/system/services';
   ```

2. **Configuration de Node.js pour privilégier IPv4 :**
   Dans `package.json` :
   ```json
   "scripts": {
     "dev": "NODE_OPTIONS='--dns-result-order=ipv4first' next dev",
     "start": "NODE_OPTIONS='--dns-result-order=ipv4first' next start"
   }
   ```

3. **Middleware pour forcer l'utilisation d'IPv4 :**
   Création d'un middleware qui intercepte les requêtes et force l'utilisation de 127.0.0.1.

## Redéploiement et maintenance

Lors du redéploiement ou de la mise à jour du système, suivre ces étapes :

1. Vérifier les configurations IP dans les fichiers de route API
2. S'assurer que le middleware est correctement configuré
3. Redémarrer les services dans cet ordre :
   ```bash
   sudo systemctl restart berinia-api.service
   sudo systemctl restart berinia-next.service
   ```

## Diagnostic

Pour diagnostiquer des problèmes de communication API :

1. Vérifier les logs du service Next.js :
   ```bash
   sudo journalctl -u berinia-next.service -n 50
   ```

2. Tester directement les API backend :
   ```bash
   curl -v "http://127.0.0.1:8000/api/system/services"
   ```

3. Tester les API via le frontend :
   ```bash
   curl -v "http://localhost:3000/api/system/services"

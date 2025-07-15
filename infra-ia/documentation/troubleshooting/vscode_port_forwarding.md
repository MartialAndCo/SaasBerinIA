# Résolution du problème de Port Forwarding VS Code

## Problème identifié

VS Code effectuait un port forwarding automatique agressif, créant des forwards pour de nombreux ports non utilisés ou non nécessaires, ce qui pouvait :
- Créer de la confusion sur les ports réellement utilisés
- Exposer potentiellement des services non intentionnellement
- Poser des problèmes de sécurité

## Ports légitimes BerinIA

Les seuls ports qui devraient être utilisés par BerinIA sont :

| Port | Service | Description | Sécurité |
|------|---------|-------------|----------|
| 3000 | berinia-next.service | Frontend Next.js | Public |
| 5432 | PostgreSQL | Base de données | Localhost uniquement |
| 6333 | berinia-qdrant.service | Base de données vectorielle Qdrant | Localhost uniquement |
| 8000 | berinia-api.service | API Backend principale | Public |
| 8001 | berinia-webhook.service | Serveur webhook | Public (si nécessaire) |
| 80 | Nginx | Serveur web | Public |

## Solution mise en place

### 1. Configuration VS Code (.vscode/settings.json)

```json
{
  "remote.autoForwardPorts": false,
  "remote.autoForwardPortsSource": "output",
  "remote.forwardOnOpen": false,
  "remote.portAttributes": {
    "3000": {
      "label": "BerinIA Frontend (Next.js)",
      "onAutoForward": "notify"
    },
    "8000": {
      "label": "BerinIA API Backend",
      "onAutoForward": "notify"
    },
    "8001": {
      "label": "BerinIA Webhook Server",
      "onAutoForward": "ignore"
    },
    "6333": {
      "label": "Qdrant Vector DB",
      "onAutoForward": "ignore"
    },
    "5432": {
      "label": "PostgreSQL",
      "onAutoForward": "ignore"
    },
    "80": {
      "label": "Nginx",
      "onAutoForward": "ignore"
    }
  }
}
```

Cette configuration :
- **Désactive le port forwarding automatique** (`autoForwardPorts: false`)
- **Définit des règles spécifiques** pour chaque port BerinIA
- **Ignore les ports sensibles** (PostgreSQL, Qdrant) pour éviter leur exposition
- **Notifie uniquement** pour les ports frontend et API principaux

### 2. Script de vérification des ports

Un script de monitoring a été créé : `infra-ia/utils/check_ports.py`

**Utilisation :**
```bash
# Vérification interactive
python3 infra-ia/utils/check_ports.py

# Rapport JSON pour l'API
python3 infra-ia/utils/check_ports.py --json
```

**Fonctionnalités :**
- Détecte tous les ports en écoute
- Identifie les ports BerinIA légitimes
- Signale les ports suspects
- Vérifie la sécurité des liaisons (localhost vs public)
- Génère des rapports détaillés

## Vérification du résultat

Après application de la solution :

```
🔍 Vérification des ports BerinIA...
============================================================
Port    80 | nginx            | all interfaces  | ✅ LÉGITIME
Port  3000 | next-server      | all interfaces  | ✅ LÉGITIME  
Port  5432 | postgres         | localhost       | ✅ LÉGITIME
Port  6333 | docker-proxy     | localhost       | ✅ LÉGITIME
Port  8000 | uvicorn          | all interfaces  | ✅ LÉGITIME

✅ Ports BerinIA légitimes trouvés: 5/6
🔒 Configuration de sécurité: CORRECTE
```

## Recommandations pour l'avenir

### 1. Surveillance régulière
Exécuter le script de vérification périodiquement :
```bash
# Ajouter à crontab pour vérification quotidienne
0 9 * * * /usr/bin/python3 /root/berinia/infra-ia/utils/check_ports.py >> /var/log/berinia-ports.log 2>&1
```

### 2. Configuration des nouveaux environnements
Pour tout nouvel environnement de développement :
1. Copier le fichier `.vscode/settings.json`
2. Adapter les ports selon les besoins
3. Tester avec le script de vérification

### 3. Sécurité des ports sensibles
**Toujours vérifier que :**
- PostgreSQL (5432) n'est accessible que depuis localhost
- Qdrant (6333) n'est accessible que depuis localhost
- Les services publics (3000, 8000, 80) sont intentionnellement exposés

## Intégration API

Le script peut être intégré à l'API BerinIA pour surveillance automatique :

```python
# Endpoint proposé : GET /api/system/ports
import subprocess
import json

def get_port_status():
    result = subprocess.run([
        'python3', '/root/berinia/infra-ia/utils/check_ports.py', '--json'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        return {"error": "Port check failed", "details": result.stderr}
```

## Dépannage

### VS Code continue à auto-forward des ports
1. Vérifier que `.vscode/settings.json` est bien présent
2. Redémarrer VS Code
3. Vérifier les paramètres utilisateur VS Code (peuvent override)

### Ports suspects détectés
1. Identifier le processus : `ss -tlnp | grep :PORT`
2. Vérifier s'il s'agit d'un service légitime
3. Ajouter à la configuration si nécessaire
4. Arrêter le service s'il est indésirable

### Services BerinIA sur mauvais ports
1. Vérifier la configuration des services systemd
2. Redémarrer les services concernés
3. Vérifier les variables d'environnement

---

**Résolution effectuée le :** 14/06/2025  
**Statut :** ✅ RÉSOLU  
**Impact :** Sécurité améliorée, clarté des ports utilisés

# Services Systemd de BerinIA

Ce document décrit les différents services systemd utilisés dans le système BerinIA pour gérer les composants et assurer leur fonctionnement continu.

## Vue d'ensemble des services

| Service | Description | Dépendances | Port |
|---------|-------------|-------------|------|
| berinia-api.service | API backend principale | PostgreSQL | 8000 |
| berinia-next.service | Frontend Next.js | berinia-api | 3000 |
| berinia-webhook.service | Serveur webhook pour réception d'événements externes | berinia-api | 8001 |
| berinia-whatsapp.service | Intégration WhatsApp | - | - |
| berinia-qdrant.service | Base de données vectorielle Qdrant | Docker | 6333 |
| berinia-agents.service | Environnement d'exécution des agents IA | PostgreSQL, berinia-qdrant | - |
| berinia-scheduler.service | Planificateur de tâches et exécutions planifiées | PostgreSQL | - |

## Commandes de gestion des services

```bash
# Vérifier l'état d'un service
sudo systemctl status berinia-api.service

# Démarrer un service
sudo systemctl start berinia-webhook.service

# Arrêter un service
sudo systemctl stop berinia-webhook.service

# Redémarrer un service (après modifications)
sudo systemctl restart berinia-webhook.service

# Activer le démarrage automatique
sudo systemctl enable berinia-qdrant.service

# Désactiver le démarrage automatique
sudo systemctl disable berinia-qdrant.service

# Voir les logs d'un service
sudo journalctl -u berinia-webhook.service

# Voir les logs en continu (comme tail -f)
sudo journalctl -u berinia-webhook.service -f

# Voir les 50 dernières lignes de logs
sudo journalctl -u berinia-webhook.service -n 50 --no-pager
```

## Configuration des services

### berinia-api.service

API backend principale FastAPI.

```ini
[Unit]
Description=BerinIA API Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
User=root
Group=root
WorkingDirectory=/root/berinia/backend
ExecStart=/root/berinia/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10
Environment="PATH=/root/berinia/backend/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="DATABASE_URL=postgresql://berinia_user:berinia_pass@localhost/berinia"
Environment="PYTHONPATH=/root/berinia/backend"

[Install]
WantedBy=multi-user.target
```

### berinia-qdrant.service

Service gérant le conteneur Docker de la base de données vectorielle Qdrant.

```ini
[Unit]
Description=Qdrant Vector Database Service for BerinIA
Documentation=https://qdrant.tech/documentation/
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=simple
User=root
Restart=always
RestartSec=5
TimeoutStartSec=0
ExecStartPre=-/usr/bin/docker stop qdrant-secure
ExecStartPre=-/usr/bin/docker rm qdrant-secure
ExecStart=/usr/bin/docker run --name qdrant-secure \
    --restart=no \
    -p 127.0.0.1:6333:6333 \
    -p 127.0.0.1:6334:6334 \
    -v /opt/qdrant/storage:/qdrant/storage \
    qdrant/qdrant:latest

ExecStop=/usr/bin/docker stop qdrant-secure

[Install]
WantedBy=multi-user.target
```

### berinia-agents.service

Service gérant l'environnement d'exécution des agents IA.

```ini
[Unit]
Description=BerinIA Agents Environment Service
After=network.target postgresql.service berinia-qdrant.service
Requires=berinia-qdrant.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/berinia/infra-ia
ExecStart=/bin/bash -c "source venv/bin/activate && python run.py"
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment="DATABASE_URL=postgresql://berinia_user:berinia_pass@localhost/berinia"

# Security
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

### berinia-scheduler.service

Service gérant les tâches planifiées et leur exécution.

```ini
[Unit]
Description=BerinIA Task Scheduler Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/berinia/infra-ia
ExecStart=/bin/bash -c "source venv/bin/activate && python scheduler.py"
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment="DATABASE_URL=postgresql://berinia_user:berinia_pass@localhost/berinia"

# Security
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

## Gestion via l'API

Le système BerinIA dispose d'une API permettant de gérer les services systemd:

### Endpoints de services

#### GET /api/services/
Liste tous les services systemd gérés.

Exemple de réponse:
```json
{
  "status": "success",
  "data": [
    {
      "name": "berinia-api.service",
      "display_name": "berinia-api",
      "description": "API backend principale",
      "status": "active",
      "is_active": true,
      "is_enabled": true,
      "uptime": "3d 4h 12m"
    },
    {
      "name": "berinia-agents.service",
      "display_name": "berinia-agents",
      "description": "Environnement d'exécution des agents IA",
      "status": "inactive",
      "is_active": false,
      "is_enabled": true,
      "uptime": null
    }
  ]
}
```

#### POST /api/services/{service_name}/action
Exécute une action sur un service.

Exemple de requête:
```json
{
  "action": "restart"
}
```

Actions disponibles:
- `start` : Démarrer le service
- `stop` : Arrêter le service
- `restart` : Redémarrer le service

#### GET /api/services/{service_name}/logs
Récupère les logs d'un service.

Paramètres de requête:
- `lines` : Nombre de lignes à récupérer (défaut: 50)

## Ordre de démarrage recommandé

Pour un démarrage correct du système, respectez l'ordre suivant:

1. Services de base de données:
   - PostgreSQL (service système)
   - `berinia-qdrant.service`

2. Services d'API:
   - `berinia-api.service`
   - `berinia-webhook.service`

3. Services d'agents:
   - `berinia-agents.service`
   - `berinia-scheduler.service`

4. Services frontend et intégrations:
   - `berinia-next.service`
   - `berinia-whatsapp.service`

## Notes importantes

### Dépendances et stockage

- Qdrant stocke ses données dans `/opt/qdrant/storage`
- Ne pas modifier les ports sans mettre à jour les configurations correspondantes

### Sécurité

Tous les services sont configurés pour:
- Redémarrer automatiquement en cas de panne
- Limiter les privilèges autant que possible
- Isoler les données temporaires

### Journalisation

Les logs des services systemd sont gérés par journald et peuvent être consultés via:
- `journalctl`
- L'API BerinIA (`/api/services/{service_name}/logs`)

Pour une rotation appropriée des logs, assurez-vous que journald est configuré correctement.

## Gestion des logs système

### Configuration automatique de la rotation des logs

Le système BerinIA dispose d'une configuration automatique de rotation des logs pour éviter l'accumulation excessive d'entrées de logs.

#### Configuration journald

La configuration se trouve dans `/etc/systemd/journald.conf.d/berinia.conf` :

```ini
[Journal]
# Limitation de la rétention des logs à 1 semaine
MaxRetentionSec=1week

# Limitation de l'espace disque utilisé par les logs (1Go max)
SystemMaxUse=1G

# Limitation du nombre de fichiers de logs
SystemMaxFiles=50

# Taille maximale par fichier de log (128Mo)
SystemMaxFileSize=128M

# Compression des logs anciens
Compress=yes
```

#### Script de nettoyage automatique

Un script de nettoyage automatique est configuré : `/root/berinia/infra-ia/utils/cleanup_logs.sh`

Ce script :
- Nettoie les logs journald plus anciens que 7 jours
- Supprime les logs applicatifs anciens des dossiers `/root/berinia/logs` et `/root/berinia/infra-ia/logs`
- **Nettoie les logs de la base de données PostgreSQL** (tables `system_logs`, `agent_logs`, `logs`)
- Génère un rapport dans `/var/log/berinia-cleanup.log`

Le script s'exécute automatiquement chaque jour à 2h du matin via cron.

#### Nettoyage de la base de données

Un script spécialisé gère le nettoyage des logs stockés en base de données : `/root/berinia/backend/cleanup_database_logs.py`

Ce script :
- Supprime les logs de plus de 7 jours dans les tables `system_logs`, `agent_logs`, et `logs`
- Optimise les tables après suppression (VACUUM ANALYZE)
- Génère un rapport détaillé dans `/var/log/berinia-db-cleanup.log`

**Tables de logs nettoyées :**
- `system_logs` : Logs système des agents et composants
- `agent_logs` : Logs spécifiques aux agents IA
- `logs` : Logs généraux de l'application

#### Optimisation intelligente des logs

Un script d'optimisation avancée : `/root/berinia/backend/optimize_logs.py`

Ce script effectue un nettoyage intelligent :
- **Reclassification automatique** : Les erreurs marquées incorrectement comme "INFO" sont reclassifiées en "ERROR"
- **Suppression du spam** : Supprime les messages répétitifs de configuration (garde 1 occurrence/jour)
- **Nettoyage agressif** : 
  - Logs INFO : rétention réduite à 3 jours (au lieu de 7)
  - Logs ERROR : rétention de 2 semaines
  - Suppression des messages verbeux en excès
- **Suppression des doublons** : Élimine les doublons exacts par minute
- Génère un rapport dans `/var/log/berinia-logs-optimization.log`

**Exemples de messages spam automatiquement supprimés :**
- "Configuration de personnalité chargée"
- "Configuration globale chargée" 
- "Client Instantly.ai initialisé"
- Messages de configuration répétitifs

**Résultat typique :** Réduction de 90-95% du volume de logs tout en conservant les informations importantes.

#### Commandes de maintenance manuelle

```bash
# Nettoyage manuel des logs de plus de 7 jours
sudo journalctl --vacuum-time=7d

# Vérification de l'espace utilisé par les logs
journalctl --disk-usage

# Exécution manuelle du script de nettoyage
/root/berinia/infra-ia/utils/cleanup_logs.sh

# Vérification du rapport de nettoyage
cat /var/log/berinia-cleanup.log
```

#### Surveillance des logs

Pour surveiller l'accumulation des logs :

```bash
# Vérifier l'espace disque total utilisé par les logs
journalctl --disk-usage

# Compter le nombre d'entrées de logs pour un service
journalctl -u postgresql.service --no-pager | wc -l

# Voir les logs récents d'un service spécifique
journalctl -u berinia-api.service -n 50 --no-pager
```

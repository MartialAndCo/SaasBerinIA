# Configuration et Maintenance des Webhooks

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [Architecture du serveur webhook](#architecture-du-serveur-webhook)
- [Configuration du service](#configuration-du-service)
- [Endpoints disponibles](#endpoints-disponibles)
- [Sécurité](#sécurité)
- [Maintenance et surveillance](#maintenance-et-surveillance)
- [Problèmes courants](#problèmes-courants)

## Vue d'ensemble

Le système BerinIA utilise un serveur webhook central pour recevoir les notifications externes et les réponses aux messages (emails, SMS, WhatsApp). Ce serveur agit comme un point d'entrée unique pour tous les événements entrants et les transmet aux agents appropriés pour traitement.

## Architecture du serveur webhook

### Composants principaux

Le serveur webhook est basé sur FastAPI et est configuré comme un service systemd pour assurer sa disponibilité permanente.

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│ Services        │      │ Serveur         │      │ Agents          │
│ externes        │─────►│ webhook         │─────►│ BerinIA         │
│ (Twilio, etc.)  │      │ (FastAPI)       │      │                 │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### Configuration technique

- **Framework**: FastAPI
- **Port d'écoute**: 8001 (local)
- **Proxy inverse**: Nginx (pour exposition publique)
- **Lancement**: Service systemd (`berinia-webhook.service`)

## Configuration du service

### Service systemd

Le fichier de service systemd (`/etc/systemd/system/berinia-webhook.service`) est configuré comme suit:

```ini
[Unit]
Description=BerinIA Webhook Server
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/berinia/infra-ia
Environment="PATH=/root/berinia/infra-ia/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/root/berinia/infra-ia/.venv/bin/python webhook/run_webhook.py --host 127.0.0.1 --port 8001
Restart=on-failure
RestartSec=5s
Environment=PYTHONUNBUFFERED=1

# Sécurité
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

### Configuration Nginx

Le webhook est exposé publiquement via Nginx qui agit comme un proxy inverse:

```nginx
# Configuration Nginx pour les webhooks
location /webhook/ {
    proxy_pass http://127.0.0.1:8001/webhook/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Timeouts plus longs pour les webhooks
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;
}
```

## Endpoints disponibles

Le serveur webhook expose plusieurs endpoints pour gérer différents types de notifications:

### SMS (Twilio)

```
POST /webhook/sms-response
```
- **Description**: Reçoit les réponses SMS via Twilio
- **Agent responsable**: `ResponseListenerAgent`
- **Paramètres attendus**: `From`, `To`, `Body`, `MessageSid`
- **Sécurité**: Vérification de signature Twilio

### WhatsApp

```
POST /webhook/whatsapp
```
- **Description**: Reçoit les messages WhatsApp
- **Agent responsable**: Déterminé par le groupe WhatsApp d'origine, généralement `MetaAgent` ou `AdminInterpreterAgent`
- **Paramètres attendus**: `source`, `type`, `group`, `author`, `content`, `timestamp`, `messageId`
- **Sécurité**: Vérification d'IP source

### Email (Mailgun)

```
POST /webhook/email-response
```
- **Description**: Reçoit les réponses email via Mailgun
- **Agent responsable**: `ResponseListenerAgent`
- **Paramètres attendus**: `sender`, `recipient`, `subject`, `body-plain`, `stripped-text`, `message-id`
- **Sécurité**: Vérification de signature Mailgun

### Logs (API d'accès)

```
GET /webhook/logs
```
- **Description**: Permet d'accéder aux logs récents
- **Paramètres**: `lines` (nombre de lignes), `type` (type de log)
- **Sécurité**: Authentification basique (à implémenter)

## Sécurité

### Vérification des signatures

Pour les webhooks provenant de services externes (Twilio, Mailgun), des vérifications de signature sont implémentées :

```python
def verify_twilio_signature(
    x_twilio_signature: str = Header(...),
    request: Request = None,
):
    """Vérifie la signature Twilio pour sécuriser les webhooks."""
    auth_token = os.getenv("TWILIO_TOKEN")
    
    if not auth_token:
        logger.error("ERREUR: TWILIO_TOKEN non défini dans les variables d'environnement")
        return False
    
    validator = RequestValidator(auth_token)
    url = str(request.url)
    params = dict(request.form)
    
    is_valid = validator.validate(url, params, x_twilio_signature)
    
    if not is_valid:
        logger.warning(f"ALERTE: Signature Twilio invalide pour {url}")
        
    return is_valid
```

### Limitation de débit

Pour éviter les abus, une limitation de débit est implémentée sur tous les endpoints :

```python
# Limitation à 100 requêtes par minute par adresse IP
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.post("/webhook/sms-response", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
async def receive_sms_response(...):
    # ...
```

### Validation des entrées

Tous les webhooks incluent une validation des entrées pour s'assurer que les données requises sont présentes et correctement formatées :

```python
# Vérification des champs requis
required_fields = ["From", "To", "Body"]
missing_fields = [field for field in required_fields if field not in data]

if missing_fields:
    error_msg = f"Champs manquants: {', '.join(missing_fields)}"
    logger.error(error_msg)
    raise HTTPException(status_code=400, detail=error_msg)
```

## Maintenance et surveillance

### Démarrage et arrêt du service

```bash
# Démarrer le service
sudo systemctl start berinia-webhook.service

# Arrêter le service
sudo systemctl stop berinia-webhook.service

# Redémarrer le service
sudo systemctl restart berinia-webhook.service

# Vérifier l'état du service
sudo systemctl status berinia-webhook.service
```

### Logs du service

Les logs du webhook sont disponibles via journalctl:

```bash
# Voir les logs en temps réel
sudo journalctl -u berinia-webhook.service -f

# Voir les logs depuis le dernier démarrage
sudo journalctl -u berinia-webhook.service -b

# Voir les logs des dernières heures
sudo journalctl -u berinia-webhook.service --since "2 hours ago"
```

### Logs applicatifs

Des logs plus détaillés sont disponibles dans les fichiers de logs:

```bash
# Logs du webhook
tail -f /root/berinia/unified_logs/webhook.log

# Logs de chaque type d'intégration
tail -f /root/berinia/unified_logs/whatsapp.log
tail -f /root/berinia/unified_logs/sms.log
tail -f /root/berinia/unified_logs/email.log
```

## Problèmes courants

### Webhook inaccessible

Si le webhook est inaccessible:

1. Vérifiez que le service est en cours d'exécution:
   ```bash
   sudo systemctl status berinia-webhook.service
   ```

2. Vérifiez que le port est bien ouvert:
   ```bash
   sudo netstat -tulpn | grep 8001
   ```

3. Vérifiez la configuration Nginx:
   ```bash
   sudo nginx -t
   ```

4. Vérifiez les logs pour des erreurs:
   ```bash
   sudo journalctl -u berinia-webhook.service --since "10 minutes ago"
   ```

### Signatures invalides

Si vous recevez des erreurs de signature:

1. Vérifiez que les tokens d'authentification sont correctement définis dans `.env`:
   ```
   TWILIO_TOKEN=your_token
   MAILGUN_API_KEY=your_key
   ```

2. Vérifiez que l'URL du webhook dans la console du service (Twilio, Mailgun) correspond exactement à l'URL attendue.

3. Assurez-vous que la requête n'est pas altérée en transit (vérifiez la configuration du proxy).

### Autres problèmes

Pour d'autres problèmes:

1. Consultez les logs détaillés pour identifier la source du problème.
2. Vérifiez que les agents nécessaires sont correctement initialisés au démarrage du webhook.
3. Si nécessaire, relancez le service avec debug activé:
   ```bash
   DEBUG=1 python webhook/run_webhook.py --host 127.0.0.1 --port 8001
   ```

---

[Retour à l'accueil](../index.md) | [Journal des mises à jour →](updates.md)

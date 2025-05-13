# Documentation du système de webhooks pour SMS entrants

## Architecture et fonctionnement des webhooks BerinIA

### Vue d'ensemble

Le système BerinIA est capable de recevoir et traiter des réponses SMS envoyées par les leads via un mécanisme de webhook Twilio. Cette documentation détaille l'architecture, l'implémentation et la configuration de cette fonctionnalité.

```
+-------------+       +----------------+      +---------------------+      +-------------------+
|             |       |                |      |                     |      |                   |
| SMS Client  | ----> | Twilio Service | ---> | BerinIA Webhook     | ---> | ResponseListener  |
| (Utilisateur)|      | (Notification) |      | (Serveur FastAPI)   |      | (Agent BerinIA)   |
|             |       |                |      |                     |      |                   |
+-------------+       +----------------+      +---------------------+      +-------------------+
                                                        |
                                                        v
                                              +-------------------+
                                              |                   |
                                              | ResponseInterpreter
                                              | (Traitement)      |
                                              |                   |
                                              +-------------------+
```

### Composants principaux

1. **Serveur de webhook (FastAPI)**
   - Hébergé sur app.berinia.com via le service systemd `berinia-webhook.service`
   - Écoute sur le port 8001 en local
   - Accessible publiquement via HTTPS à l'URL `https://app.berinia.com/webhook/sms-response`

2. **Agents impliqués**
   - `ResponseListenerAgent`: Reçoit et normalise les SMS entrants
   - `ResponseInterpreterAgent`: Interprète et traite les réponses

3. **Sécurité**
   - Vérification des signatures Twilio pour garantir l'authenticité des requêtes
   - Communication HTTPS pour le chiffrement des données

## Implémentation technique

### 1. Configuration du serveur webhook

Le serveur webhook est implémenté en utilisant FastAPI et est configuré pour fonctionner comme un service systemd:

```bash
# Localisation du service
/etc/systemd/system/berinia-webhook.service

# Code principal
/root/berinia/infra-ia/webhook/run_webhook.py
```

#### Structure du service systemd

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

### 2. Endpoint de réception des SMS

L'endpoint `/webhook/sms-response` est configuré dans `run_webhook.py`:

```python
@app.post("/webhook/sms-response")
async def receive_sms_response(
    request: Request,
    auth: bool = Depends(verify_twilio_signature)
):
    """
    Endpoint pour recevoir les réponses SMS via Twilio.
    """
    try:
        # Récupération du corps de la requête
        payload = await request.form()
        data = dict(payload)
        
        logger.info(f"Notification de réponse SMS reçue: {data.get('From')}")
        
        # Vérification des champs requis
        required_fields = ["From", "To", "Body"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            error_msg = f"Champs manquants: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Traitement par ResponseListenerAgent
        # ...
```

### 3. Vérification des signatures Twilio

Pour garantir l'authenticité des requêtes, une vérification de signature a été implémentée:

```python
def verify_twilio_signature(
    x_twilio_signature: str = Header(...),
    request: Request = None,
):
    """Vérifie la signature Twilio pour sécuriser les webhooks."""
    auth_token = os.getenv("TWILIO_TOKEN")
    
    if not auth_token:
        logger.error("ERREUR: TWILIO_TOKEN non défini dans les variables d'environnement")
        return True  # En développement seulement
    
    validator = RequestValidator(auth_token)
    url = str(request.url)
    params = dict(request.form)
    
    is_valid = validator.validate(url, params, x_twilio_signature)
    
    if not is_valid:
        logger.warning(f"ALERTE: Signature Twilio invalide pour {url}")
        
    return True  # En développement; en production, retourner `is_valid`
```

### 4. Intégration avec Nginx

Le webhook est exposé publiquement via Nginx, qui agit comme un proxy inverse:

```nginx
# Configuration Nginx pour le webhook Twilio
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

## Configuration dans la console Twilio

Pour que Twilio envoie les notifications de SMS au webhook BerinIA, il faut configurer le numéro Twilio:

1. Connectez-vous à la [console Twilio](https://www.twilio.com/console)
2. Naviguez vers **Phone Numbers** > **Manage Numbers**
3. Sélectionnez le numéro concerné
4. Dans la section **Messaging**:
   - Pour **A MESSAGE COMES IN**, sélectionnez **Webhook**
   - URL: `https://app.berinia.com/webhook/sms-response`
   - Méthode: `HTTP POST`
5. Enregistrez les modifications

## Traitement des SMS entrants

### Flux de données

1. **Réception**: Le SMS arrive à Twilio
2. **Notification**: Twilio envoie une requête HTTP POST au webhook BerinIA
3. **Vérification**: BerinIA vérifie la signature de la requête
4. **Extraction**: Les données du SMS sont extraites (expéditeur, contenu, etc.)
5. **Traitement initial**: Le `ResponseListenerAgent` normalise les données
6. **Interprétation**: Le `ResponseInterpreterAgent` analyse le contenu
7. **Action**: Une action est déclenchée en fonction de l'interprétation

### Formats de données

#### Format de requête Twilio (entrant)

```json
{
  "From": "+33612345678",  // Numéro de l'expéditeur
  "To": "+33757594999",    // Numéro Twilio
  "Body": "Oui je suis intéressé",  // Contenu du SMS
  "MessageSid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  // Identifiant unique du message
}
```

#### Format traité par ResponseListenerAgent

```json
{
  "source": "sms",
  "sender": "+33612345678",
  "content": "Oui je suis intéressé",
  "campaign_id": "campaign_123",  // Si identifiable
  "received_at": "2025-05-06T12:53:13.762894",
  "extracted_data": {
    // Données extraites par analyse
  },
  "raw_data": {
    // Données brutes complètes
  }
}
```

## Déploiement et mise à jour

### Déploiement initial

Le service webhook a été configuré pour démarrer automatiquement avec le système:

```bash
# Installation
sudo cp berinia-webhook.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable berinia-webhook.service
sudo systemctl start berinia-webhook.service
```

### Mise à jour du code

Pour mettre à jour le code de gestion des webhooks:

1. Modifiez les fichiers nécessaires dans `/root/berinia/infra-ia/webhook/`
2. Redémarrez le service webhook:
   ```bash
   sudo systemctl restart berinia-webhook.service
   ```

## Surveillance et dépannage

### Logs

Les logs du webhook sont disponibles à plusieurs endroits:

1. **Logs du service systemd**:
   ```bash
   sudo journalctl -u berinia-webhook.service -f
   ```

2. **Logs applicatifs**:
   ```bash
   tail -f /root/berinia/infra-ia/logs/berinia_webhook.log
   ```

3. **Logs des agents**:
   ```bash
   tail -f /root/berinia/infra-ia/logs/berinia.log | grep ResponseListener
   ```

### Vérification de l'état du service

Pour vérifier que le service fonctionne correctement:

```bash
# État du service
sudo systemctl status berinia-webhook.service

# Vérification de l'accès local
curl http://127.0.0.1:8001/

# Vérification de l'accès public (depuis une autre machine)
curl https://app.berinia.com/webhook/
```

### Problèmes courants

1. **Webhook inaccessible**
   - Vérifiez que le service est en cours d'exécution
   - Vérifiez la configuration Nginx
   - Vérifiez les pare-feu et les règles de sécurité

2. **Signatures invalides**
   - Vérifiez que `TWILIO_TOKEN` est correctement défini
   - Vérifiez que l'URL du webhook dans la console Twilio correspond exactement à l'URL attendue

3. **Échec de traitement**
   - Vérifiez les logs pour des erreurs spécifiques
   - Vérifiez que les agents `ResponseListenerAgent` et `ResponseInterpreterAgent` sont correctement initialisés

## Sécurité

### Bonnes pratiques

1. **En production**, modifiez `verify_twilio_signature` pour refuser les requêtes avec des signatures invalides:
   ```python
   def verify_twilio_signature(...):
       # ...
       return is_valid  # Retourner False pour les signatures invalides
   ```

2. **Limitez l'accès** à l'endpoint webhook aux seules adresses IP de Twilio si possible

3. **Examinez régulièrement les logs** pour détecter des comportements suspects

4. **Mettez à jour** régulièrement les dépendances, notamment le SDK Twilio

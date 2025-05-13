# Installation et Configuration Détaillée

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Prérequis](#prérequis)
- [Installation de l'environnement](#installation-de-lenvironnement)
- [Configuration des services externes](#configuration-des-services-externes)
- [Installation de la base de données](#installation-de-la-base-de-données)
- [Configuration du serveur Webhook](#configuration-du-serveur-webhook)
- [Configuration de WhatsApp](#configuration-de-whatsapp)
- [Configuration de Qdrant](#configuration-de-qdrant)
- [Vérification de l'installation](#vérification-de-linstallation)

## Prérequis

### Matériel recommandé
- Processeur: 4 cœurs minimum
- Mémoire: 8 Go RAM minimum
- Espace disque: 20 Go minimum

### Logiciels requis
- Python 3.8 ou supérieur
- PostgreSQL 14 ou supérieur
- Node.js 18 ou supérieur (pour l'intégration WhatsApp)
- Docker (optionnel, pour Qdrant)
- Nginx (pour exposer les webhooks)

### Comptes externes nécessaires
- Compte OpenAI avec clé API (pour GPT-4.1, GPT-4.1-mini et GPT-4.1-nano)
- Compte Twilio (pour SMS)
- Compte Mailgun (pour emails)
- Compte WhatsApp actif (pour l'intégration WhatsApp)

## Installation de l'environnement

### 1. Clonage du dépôt

```bash
# Cloner le dépôt
git clone https://github.com/berinai/berinia.git
cd berinia
```

### 2. Environnement virtuel Python

```bash
# Créer et activer l'environnement virtuel pour l'infrastructure IA
cd infra-ia
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OU
.venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Fichier de configuration `.env`

Créez un fichier `.env` dans le dossier `infra-ia` avec le contenu suivant:

```
# API OpenAI
OPENAI_API_KEY=votre_clé_api_openai

# Base de données
DB_HOST=localhost
DB_PORT=5432
DB_NAME=berinia
DB_USER=berinia_user
DB_PASSWORD=votre_mot_de_passe

# Qdrant (mémoire vectorielle)
QDRANT_URL=http://localhost:6333

# Mailgun (emails)
MAILGUN_API_KEY=votre_clé_api_mailgun
MAILGUN_DOMAIN=votre_domaine_mailgun

# Twilio (SMS)
TWILIO_SID=votre_sid_twilio
TWILIO_TOKEN=votre_token_twilio
TWILIO_PHONE=+votre_numéro_twilio
```

## Configuration des services externes

### Configuration OpenAI

1. Créez un compte sur [platform.openai.com](https://platform.openai.com/) si vous n'en avez pas déjà un
2. Générez une clé API dans les paramètres du compte
3. Assurez-vous d'avoir accès aux modèles GPT-4.1, GPT-4.1-mini et GPT-4.1-nano

### Configuration Twilio

1. Créez un compte sur [twilio.com](https://www.twilio.com/)
2. Achetez un numéro de téléphone avec capacité SMS
3. Notez votre SID de compte et votre token d'authentification
4. Configurez le webhook SMS:
   - Dans la console Twilio, allez dans **Phone Numbers** > **Manage**
   - Sélectionnez votre numéro
   - Dans la section **Messaging**:
     - Pour **A MESSAGE COMES IN**, sélectionnez **Webhook**
     - URL: `https://votre-domaine.com/webhook/sms-response`
     - Méthode: `HTTP POST`

### Configuration Mailgun

1. Créez un compte sur [mailgun.com](https://www.mailgun.com/)
2. Ajoutez et vérifiez votre domaine
3. Notez votre clé API et votre domaine vérifié
4. Configurez le webhook email:
   - Dans la console Mailgun, allez dans **Receiving** > **Create Route**
   - Expression: `match_recipient(".*@votre-domaine.com")`
   - Action: **Forward**
   - Destination: `https://votre-domaine.com/webhook/email-response`

## Installation de la base de données

### 1. Installation de PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo dnf install postgresql postgresql-server
sudo postgresql-setup --initdb
sudo systemctl start postgresql
```

### 2. Création de la base de données et de l'utilisateur

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer l'utilisateur et la base de données
CREATE USER berinia_user WITH PASSWORD 'votre_mot_de_passe';
CREATE DATABASE berinia;
GRANT ALL PRIVILEGES ON DATABASE berinia TO berinia_user;
\q
```

### 3. Application des migrations

```bash
cd /root/berinia/backend
./recreate_database.sh
```

Cette commande exécute l'ensemble des scripts SQL de migration:
- `migrations/create_berinia_db.sql`
- `migrations/add_messages_table.sql`
- `migrations/add_missing_columns.sql`
- `migrations/add_visual_analysis_fields.sql`

## Configuration du serveur Webhook

### 1. Installation du service systemd

Créez le fichier `/etc/systemd/system/berinia-webhook.service`:

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

### 2. Activation du service

```bash
sudo systemctl daemon-reload
sudo systemctl enable berinia-webhook.service
sudo systemctl start berinia-webhook.service
```

### 3. Configuration Nginx

Créez un fichier dans `/etc/nginx/sites-available/berinia`:

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    # Redirection vers HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name votre-domaine.com;

    # Configuration SSL
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # Webhook routes
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
}
```

Activez la configuration:

```bash
sudo ln -s /etc/nginx/sites-available/berinia /etc/nginx/sites-enabled/
sudo nginx -t  # Vérifiez la configuration
sudo systemctl restart nginx
```

## Configuration de WhatsApp

### 1. Installation des dépendances

```bash
cd /root/berinia/whatsapp-bot
npm install -g pnpm
pnpm install
```

### 2. Configuration initiale

Créez un fichier `.env` dans le dossier `/root/berinia/whatsapp-bot`:

```
BERINIA_WEBHOOK_URL=http://localhost:8001/webhook/whatsapp
```

### 3. Configuration du service systemd

Créez le fichier `/etc/systemd/system/berinia-whatsapp.service`:

```ini
[Unit]
Description=BerinIA WhatsApp Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/berinia/whatsapp-bot
ExecStart=/usr/bin/node index.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

### 4. Connexion WhatsApp

Avant de démarrer le service, générez un QR code pour la connexion:

```bash
cd /root/berinia/whatsapp-bot
node capture-qr.js
```

Scannez le QR code avec votre téléphone WhatsApp, puis arrêtez le script avec Ctrl+C.

### 5. Activation du service

```bash
sudo systemctl daemon-reload
sudo systemctl enable berinia-whatsapp.service
sudo systemctl start berinia-whatsapp.service
```

## Configuration de Qdrant

Qdrant est utilisé comme base de données vectorielle pour stocker les embeddings.

### 1. Installation via Docker (recommandé)

```bash
docker pull qdrant/qdrant
docker run -d -p 6333:6333 -v /root/berinia/qdrant_data:/qdrant/storage qdrant/qdrant
```

### 2. Initialisation de Qdrant

```bash
cd /root/berinia/infra-ia
source .venv/bin/activate
python initialize_qdrant.py
```

Ce script crée les collections nécessaires dans Qdrant.

### 3. Chargement des connaissances dans Qdrant

```bash
python load_system_knowledge.py
```

Ce script charge les connaissances de base dans la mémoire vectorielle.

## Vérification de l'installation

### 1. Test de la connexion à la base de données

```bash
cd /root/berinia/backend
python test_db_connection.py
```

### 2. Test de l'installation de BerinIA

```bash
cd /root/berinia/infra-ia
python verify_installation.py --full
```

L'option `--full` teste également la connexion à l'API OpenAI.

### 3. Test du webhook Twilio

```bash
python test_sms_webhook.py
```

Ce script simule une requête webhook de Twilio pour vérifier que le traitement fonctionne correctement.

### 4. Test du service WhatsApp

```bash
cd /root/berinia/whatsapp-bot
node test-send.js "Logs techniques" "Test d'installation réussi"
```

### 5. Démarrer l'interface interactive

```bash
cd /root/berinia/infra-ia
python interact.py
```

Cette commande démarre l'interface CLI pour interagir avec le système BerinIA. Vous pouvez maintenant envoyer des commandes en langage naturel.

## Conclusion

Vous avez maintenant installé et configuré l'ensemble du système BerinIA avec:
- L'infrastructure IA principale
- La base de données PostgreSQL
- Le serveur webhook pour les notifications externes
- L'intégration WhatsApp
- La mémoire vectorielle Qdrant

Pour des détails sur l'utilisation quotidienne du système, consultez le [Guide de démarrage rapide](quick-start.md).

---

[Retour à l'accueil](../index.md) | [Résolution des problèmes →](troubleshooting.md)

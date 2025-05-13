# BerinIA WhatsApp Integration

Cette intégration permet de connecter WhatsApp à l'écosystème BerinIA, créant une communauté WhatsApp contrôlée par votre numéro personnel en mode multi-device.

## Fonctionnalités

- Connexion WhatsApp en mode multi-device (utilisation simultanée avec vos autres appareils)
- Écoute des messages dans les groupes spécifiques de la communauté
- Envoi de messages aux groupes depuis le backend BerinIA
- Intégration avec les agents BerinIA via webhook

## Prérequis

- Node.js v14 ou supérieur
- Un numéro WhatsApp actif (votre numéro personnel)
- Accès au serveur BerinIA
- Connexion Internet stable

## Structure des fichiers

```
whatsapp-bot/
├── index.js                   # Point d'entrée principal
├── package.json               # Dépendances npm
├── .env                       # Configuration d'environnement
├── berinia-whatsapp.service   # Configuration systemd
├── src/
│   ├── services/
│   │   ├── whatsapp-client.js # Client WhatsApp
│   │   └── api-service.js     # API REST pour envoi de messages
│   ├── utils/
│   │   └── logger.js          # Utilitaire de logging
│   └── config/
│       └── groups.js          # Configuration des groupes
└── logs/                      # Dossier pour les logs (créé automatiquement)
```

## Installation

### 1. Cloner le dépôt

```bash
cd /root/berinia
# Le dossier whatsapp-bot est déjà créé dans cette installation
```

### 2. Installer les dépendances

```bash
cd /root/berinia/whatsapp-bot
npm install
```

### 3. Configurer le service systemd

```bash
# Copier le fichier de service
sudo cp /root/berinia/whatsapp-bot/berinia-whatsapp.service /etc/systemd/system/

# Recharger systemd
sudo systemctl daemon-reload

# Activer le service au démarrage
sudo systemctl enable berinia-whatsapp.service
```

## Configuration

### 1. Configuration WhatsApp

Lorsque vous démarrez le service pour la première fois, vous devrez scanner un QR code avec votre application WhatsApp mobile pour établir la connexion multi-device:

```bash
# Démarrer le service et afficher les logs pour voir le QR code
sudo systemctl start berinia-whatsapp.service
sudo journalctl -f -u berinia-whatsapp.service
```

### 2. Création de la communauté WhatsApp

Vous devez créer manuellement la communauté WhatsApp et ses groupes depuis votre application WhatsApp mobile:

1. Créez une nouvelle communauté nommée "BerinIA"
2. Créez les groupes suivants dans cette communauté:
   - 📣 Annonces officielles (lecture seule)
   - 📊 Performances & Stats (lecture seule)
   - 🛠️ Logs techniques (lecture seule)
   - 🤖 Support IA / Chatbot
   - 🧠 Tactiques & Tests
   - 💬 Discussion libre

## Utilisation

### API d'envoi de messages

L'intégration expose une API REST locale pour l'envoi de messages:

- **Endpoint**: `http://localhost:3000/send`
- **Méthode**: POST
- **Corps**:
  ```json
  {
    "group": "📊 Performances & Stats",
    "message": "Votre message ici"
  }
  ```

### Vérification de l'état

```bash
# Vérifier l'état du service
sudo systemctl status berinia-whatsapp.service

# Consulter les logs
sudo journalctl -u berinia-whatsapp.service -f

# Redémarrer le service si nécessaire
sudo systemctl restart berinia-whatsapp.service
```

## Webhook BerinIA

Les messages entrants de la communauté WhatsApp sont transmis au backend BerinIA via l'endpoint:

- **URL**: `http://localhost:8000/webhook/whatsapp`
- **Format du message**:
  ```json
  {
    "source": "whatsapp",
    "type": "group",
    "group": "Nom du groupe",
    "author": "ID de l'auteur",
    "content": "Contenu du message",
    "timestamp": "2025-05-03T12:34:56Z",
    "messageId": "ID du message"
  }
  ```

## Dépannage

### Problèmes de connexion WhatsApp

Si le bot perd la connexion WhatsApp:

1. Vérifiez les logs: `sudo journalctl -u berinia-whatsapp.service -f`
2. Redémarrez le service: `sudo systemctl restart berinia-whatsapp.service`
3. Si un nouveau QR code apparaît, scannez-le avec l'application WhatsApp mobile
4. Vérifiez que le mode multi-device est activé sur votre compte WhatsApp

### Problèmes avec l'API locale

Si l'API d'envoi de messages ne fonctionne pas:

1. Vérifiez que le service est en cours d'exécution: `sudo systemctl status berinia-whatsapp.service`
2. Testez l'API directement: `curl -X POST http://localhost:3000/health`
3. Vérifiez les logs pour les erreurs: `sudo journalctl -u berinia-whatsapp.service -f`

### Problèmes avec le webhook

Si les messages ne sont pas transmis au backend BerinIA:

1. Vérifiez que le serveur webhook BerinIA est en cours d'exécution
2. Testez le webhook directement: `curl -X POST http://localhost:8000/webhook/whatsapp -H "Content-Type: application/json" -d '{"source":"whatsapp","type":"group","group":"Test","author":"test","content":"test"}'`
3. Vérifiez les logs du webhook: `tail -f /root/berinia/infra-ia/logs/berinia.log | grep webhook`

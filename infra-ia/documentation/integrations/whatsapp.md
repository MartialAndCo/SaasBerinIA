# Intégration WhatsApp

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Installation et configuration](#installation-et-configuration)
- [Utilisation](#utilisation)
- [Dépannage](#dépannage)
- [Mise à jour récente](#mise-à-jour-récente)

## Vue d'ensemble

L'intégration WhatsApp permet à BerinIA d'envoyer et de recevoir des messages entre les agents et des groupes WhatsApp. Cette fonctionnalité facilite la communication avec l'équipe et offre une interface accessible pour interagir avec le système.

## Architecture

### Composants principaux

1. **Service WhatsApp (berinia-whatsapp.service)** : Service systemd s'exécutant en arrière-plan
2. **API REST** : API HTTP locale permettant l'envoi de messages (port 3030)
3. **Webhook** : Point d'entrée pour les messages reçus de WhatsApp
4. **Communauté WhatsApp** : Communauté "BerinIA" contenant les groupes

```
+-----------------+     +------------------+     +----------------+     +----------------+
| WhatsApp Client | <-> | Whatsapp-Bot API | <-> | Webhook | API  | <-> | Agents BerinIA |
+-----------------+     +------------------+     +----------------+     +----------------+
```

### Structure des groupes

La communauté WhatsApp "BerinIA" est organisée avec les groupes suivants :

| Nom du Groupe | Description | Configuration |
|---------------|-------------|--------------|
| 📣 Annonces officielles | Annonces stratégiques du système BerinIA | Lecture seule |
| 📊 Performances & Stats | Résumés automatiques des performances | Lecture seule |
| 🛠️ Logs techniques | Logs automatiques (erreurs, exécution) | Lecture seule |
| 🤖 Support IA / Chatbot | Questions et retours sur les agents IA | Lecture/écriture |
| 🧠 Tactiques & Tests | Tests stratégiques, pivots, brainstorm | Lecture/écriture |
| 💬 Discussion libre | Espace libre pour retours et idées | Lecture/écriture |

### Flux des messages

#### Messages entrants
1. L'utilisateur envoie un message dans un groupe WhatsApp
2. Le bot WhatsApp détecte le message via les événements `message` ou `message_create`
3. Le bot transmet le message au webhook BerinIA avec les métadonnées appropriées
4. Le webhook identifie l'agent cible en fonction du groupe d'origine
5. L'agent approprié (généralement AdminInterpreterAgent ou MetaAgent) traite le message
6. La réponse est renvoyée au bot WhatsApp qui l'envoie au groupe d'origine

#### Messages sortants
1. Un agent génère une réponse ou une notification
2. Le webhook envoie la réponse à l'API du bot WhatsApp
3. Le bot WhatsApp transmet la réponse au groupe approprié

### Mappage Groupe → Agent

Le système utilise un mappage pour router les messages vers les agents appropriés :

```python
GROUP_AGENT_MAPPING = {
    # Versions sans émojis
    "Annonces officielles": "OverseerAgent",
    "Performances & Stats": "PivotStrategyAgent", 
    "Logs techniques": "LoggerAgent",
    "Support IA / Chatbot": "AdminInterpreterAgent",
    "Tactiques & Tests": "PivotStrategyAgent",
    "Discussion libre": "AdminInterpreterAgent",
    
    # Versions avec émojis
    "📣 Annonces officielles": "OverseerAgent",
    "📊 Performances & Stats": "PivotStrategyAgent",
    "🛠️ Logs techniques": "LoggerAgent",
    "🤖 Support IA / Chatbot": "AdminInterpreterAgent",
    "🧠 Tactiques & Tests": "PivotStrategyAgent",
    "💬 Discussion libre": "AdminInterpreterAgent"
}
```

## Installation et configuration

### Prérequis

- Node.js v18+
- Compte WhatsApp sur un smartphone
- Accès à Internet sur le serveur

### Installation

1. Le service WhatsApp est installé dans `/root/berinia/whatsapp-bot/`
2. Un fichier de service systemd `berinia-whatsapp.service` gère le démarrage automatique
3. La configuration se trouve dans le fichier `.env`

### Configuration

Les principaux fichiers de configuration sont :

1. `.env` - Variables d'environnement :
   ```
   BERINIA_WEBHOOK_URL=http://localhost:8001/webhook/whatsapp
   ```

2. `src/config/groups.js` - Configuration des groupes
3. `berinia-whatsapp.service` - Configuration du service systemd

## Utilisation

### Envoyer un message

#### Via ligne de commande

```bash
# Utiliser le script test-send.js
cd /root/berinia/whatsapp-bot
node test-send.js "Logs techniques" "Votre message ici"

# Alternativement, utiliser l'outil de gestion
node manage-whatsapp.js send "Logs techniques" "Votre message ici"
```

#### Via l'API

```bash
curl -X POST http://localhost:3030/send \
  -H "Content-Type: application/json" \
  -d '{"group": "Logs techniques", "message": "Votre message ici"}'
```

### Recevoir des messages

Les messages reçus sur WhatsApp sont automatiquement transmis via le webhook configuré dans le fichier `.env` (variable `BERINIA_WEBHOOK_URL`).

### Outils de gestion

Un outil de gestion est disponible :

```bash
cd /root/berinia/whatsapp-bot
node manage-whatsapp.js --help
```

#### Commandes disponibles

| Commande | Description |
|----------|-------------|
| `list` | Liste toutes les communautés et groupes |
| `connect` | Connecte WhatsApp et maintient la connexion active |
| `send <groupe> <message>` | Envoie un message à un groupe |
| `status` | Affiche l'état de l'intégration WhatsApp |
| `fix` | Corrige les problèmes de configuration courants |

## Dépannage

### Réauthentification

Si l'authentification WhatsApp est perdue :

```bash
sudo systemctl stop berinia-whatsapp.service
cd /root/berinia/whatsapp-bot
node capture-qr.js
# Scannez le code QR avec votre téléphone
# Appuyez sur Ctrl+C quand c'est fait
sudo systemctl start berinia-whatsapp.service
```

### Problèmes courants

#### Messages non détectés
- Vérifiez que le service `berinia-whatsapp.service` est actif
- Consultez les logs: `/root/berinia/whatsapp-bot/logs/whatsapp-bot.log`
- Assurez-vous que les événements `message` et `message_create` sont correctement gérés

#### Messages détectés mais sans réponse
- Vérifiez que le service `berinia-webhook.service` est actif
- Consultez les logs du webhook
- Vérifiez le mappage des groupes vers les agents

#### Réponses générées mais non envoyées
- Vérifiez la connexion entre le webhook et l'API WhatsApp
- Vérifiez que l'URL du webhook est correcte dans le fichier `.env`
- Assurez-vous que le format des réponses est correct

#### "Group not found in BerinIA community"
- Vérifiez que la communauté existe et est nommée exactement "BerinIA"
- Vérifiez que les groupes ont les noms exacts configurés dans `src/config/groups.js`
- Exécutez `node manage-whatsapp.js list` pour voir les groupes disponibles

#### "Community ID not yet identified"
- Redémarrez le service : `sudo systemctl restart berinia-whatsapp.service`
- Vérifiez que vous êtes toujours connecté sur WhatsApp

### Commandes utiles

```bash
# État du service
sudo systemctl status berinia-whatsapp.service

# Redémarrage du service
sudo systemctl restart berinia-whatsapp.service

# Consulter les logs
sudo tail -n 100 /root/berinia/whatsapp-bot/logs/whatsapp-bot.log

# Consulter les logs du webhook
sudo journalctl -u berinia-webhook.service --since "5 minutes ago"
```

## Fonctionnalités avancées

### Support des messages vocaux

BerinIA prend désormais en charge les messages vocaux sur WhatsApp. Cette fonctionnalité permet aux utilisateurs d'envoyer des messages vocaux qui sont automatiquement transcrits en texte, puis traités par le système comme des messages textuels normaux.

#### Comment ça fonctionne

Le processus de traitement des messages vocaux WhatsApp se déroule ainsi :

1. **Réception** : L'utilisateur envoie un message vocal dans un groupe WhatsApp
2. **Détection** : Le bot WhatsApp identifie automatiquement qu'il s'agit d'un message vocal
3. **Téléchargement** : Le fichier audio est téléchargé temporairement
4. **Conversion** : Le format audio est optimisé pour la transcription (OGG → MP3)
5. **Transcription** : Le contenu audio est transcrit en texte via l'API OpenAI Whisper
6. **Traitement** : Le texte transcrit est envoyé au webhook BerinIA pour traitement normal
7. **Réponse** : La réponse est renvoyée à l'utilisateur dans le groupe d'origine

```
┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌───────────┐    ┌───────────┐
│ Message  │    │ Téléchargement│    │ Conversion │    │Transcription│  │ Traitement│
│  vocal   │───>│  temporaire  │───>│  en MP3    │───>│  Whisper   │──>│  normal   │
└──────────┘    └──────────────┘    └────────────┘    └───────────┘    └───────────┘
```

#### Configuration requise

Pour que le système de transcription fonctionne, les éléments suivants sont nécessaires :

1. **Clé API OpenAI** : Une clé API valide configurée dans le fichier `.env`
2. **Dépendances** : Les packages requis sont `@ffmpeg-installer/ffmpeg`, `openai`, et `form-data`

#### Format des messages vocaux

Lorsqu'un message vocal est transcrit, il est envoyé au webhook avec les métadonnées suivantes :

```json
{
  "source": "whatsapp",
  "type": "group",
  "group": "Nom du groupe",
  "author": "ID de l'expéditeur",
  "content": "[Texte transcrit du message vocal]",
  "isVoiceMessage": true,
  "timestamp": "2025-05-08T15:30:00.000Z",
  "messageId": "ID unique du message"
}
```

Le champ `isVoiceMessage` permet d'identifier qu'il s'agit d'un message vocal transcrit.

#### Conseils pour une meilleure transcription

Pour optimiser la qualité de transcription :

1. **Parler clairement** : Articuler et parler à un rythme normal
2. **Éviter les bruits de fond** : Choisir un environnement calme si possible
3. **Durée optimale** : Les messages de 10-15 secondes sont idéaux
4. **Préférer le français** : Le système est optimisé pour la transcription en français

#### Dépannage des messages vocaux

| Problème | Cause possible | Solution |
|----------|----------------|----------|
| Message "Transcription audio non disponible" | Clé API OpenAI invalide | Vérifier la clé API dans `.env` |
| | Problème de connexion à l'API | Vérifier la connectivité Internet |
| | Fichier audio corrompu | Réessayer avec un nouveau message vocal |
| Transcription de mauvaise qualité | Bruit de fond excessif | Enregistrer dans un environnement plus calme |
| | Accent ou diction peu claire | Parler plus lentement et clairement |

### Intelligence conversationnelle améliorée

BerinIA dispose désormais d'une intelligence conversationnelle améliorée pour les interactions WhatsApp, offrant des réponses plus naturelles et contextuelles.

#### Améliorations apportées

L'intégration WhatsApp a été améliorée pour résoudre plusieurs problèmes de qualité des réponses :

1. **Réponses complètes et conversationnelles** : Les réponses brutes des agents spécialisés sont désormais reformatées pour être plus naturelles et complètes
2. **Gestion intelligente des erreurs** : Les erreurs techniques sont transformées en messages utiles et exploitables
3. **Style de communication unifié** : Toutes les réponses suivent un style conversationnel cohérent, quelle que soit leur source

#### Exemples de transformation

**Avant** :
```
Message: "Combien de leads ont été contactés ?"
Réponse: "0"
```

**Après** :
```
Message: "Combien de leads ont été contactés ?"
Réponse: "Il y a actuellement 0 leads qui ont été contactés dans la base de données."
```

**Avant** :
```
Message: "Es-tu capable de planifier des campagnes ?"
Réponse: "Erreur: relation 'campagnes' does not exist"
```

**Après** :
```
Message: "Es-tu capable de planifier des campagnes ?"
Réponse: "Je peux planifier des campagnes, mais je ne trouve pas cette fonctionnalité dans la base de données actuellement. Cette fonctionnalité n'est probablement pas encore implémentée."
```

#### Architecture de post-traitement

Le flux de traitement des messages inclut désormais une étape de post-traitement :

```
1. [Message reçu] → 2. [MetaAgent analyse] → 3. [Agent spécialisé traite] → 
4. [MetaAgent reformate] → 5. [Réponse envoyée]
```

#### Implémentation technique

Ces améliorations reposent sur deux nouvelles fonctionnalités principales :

1. **Formatage intelligent des réponses** : Le MetaAgent analyse le contexte de la question pour générer des réponses plus complètes
2. **Gestion contextuelle des erreurs** : Les erreurs sont interprétées et reformulées en langage naturel

Si vous rencontrez des problèmes avec le formatage des réponses, vérifiez que le MetaAgent est correctement chargé et que les logs ne contiennent pas d'erreurs de formatage.

## Mise à jour récente

### Mai 2025
- Ajout du support pour les messages vocaux avec transcription automatique via OpenAI Whisper
- Amélioration de l'intelligence conversationnelle avec reformatage des réponses
- Configuration de whatsapp-web.js pour utiliser toujours la dernière version disponible
- Mise à jour de puppeteer à la version 22.15.0+ pour résoudre les avertissements de dépréciation
- Amélioration du mappage des noms de groupes pour gérer les versions avec et sans émojis
- Ajout de la détection des événements `message_create` pour capter tous les messages
- Amélioration des logs pour faciliter le dépannage

---

[Retour à l'accueil](../index.md) | [Intégration SMS Twilio →](sms-twilio.md)

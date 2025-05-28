# Intégration d'Instantly.ai

Ce document présente l'intégration complète d'Instantly.ai dans le système BerinIA pour l'envoi et le suivi d'emails.

## 1. Vue d'ensemble

Instantly.ai est utilisé comme service principal d'envoi d'emails, remplaçant les implémentations précédentes (SMTP et Mailgun). Cette intégration permet de :

- Envoyer des emails via l'API Instantly.ai
- Exploiter la rotation automatique d'adresses d'expédition
- Recevoir des webhooks pour les événements liés aux emails (réponses, ouvertures, clics)
- Traquer les statistiques des campagnes d'emails

## 2. Architecture technique

L'intégration se compose de trois parties principales :

1. **InstantlyClient** : Client API pour interagir avec Instantly.ai
2. **MessagingAgent** : Agent responsable de l'envoi des messages
3. **ResponseListenerAgent** : Agent responsable de la réception des webhooks

### 2.1 InstantlyClient

Classe utilitaire qui encapsule les appels à l'API Instantly.ai. Elle gère :
- L'authentification à l'API
- L'envoi d'emails
- Les réponses aux emails
- Le parsing des webhooks
- La gestion des erreurs et le rate limiting

### 2.2 MessagingAgent

L'agent MessagingAgent a été adapté pour utiliser Instantly.ai :
- L'initialisation utilise l'InstantlyClient
- La méthode d'envoi d'email utilise l'API Instantly
- Le suivi des statistiques d'envoi est maintenu

### 2.3 ResponseListenerAgent

L'agent ResponseListenerAgent traite les webhooks d'Instantly.ai :
- Détection si un webhook provient d'Instantly
- Traitement spécifique selon le type d'événement (réponse, ouverture, clic)
- Transmission des réponses au ResponseInterpreterAgent pour analyse

## 3. Configuration système

### 3.1 Paramètres dans system_settings

L'intégration avec Instantly.ai utilise les paramètres suivants, stockés dans la table `system_settings`:

| Nom du paramètre | Type | Description |
|-----------------|------|-------------|
| `instantly_api_key` | string | Clé API pour l'authentification auprès d'Instantly.ai |
| `instantly_integration_active` | boolean | Indique si l'intégration avec Instantly.ai est activée |

### 3.2 Activation de l'intégration

Pour activer l'intégration:

1. Définissez `instantly_api_key` avec votre clé API Instantly.ai
2. Réglez `instantly_integration_active` sur `true`
3. Redémarrez le service webhook avec `sudo systemctl restart berinia-webhook.service`

### 3.3 Configuration de l'agent MessagingAgent

Dans le fichier `config.json` :

```json
{
  "email": {
    "service": "instantly",
    "instantly_api_key": "VOTRE_CLE_API_INSTANTLY"
  }
}
```

### 3.4 Configuration du ResponseListenerAgent

Dans le fichier `config.json` :

```json
{
  "instantly_api_key": "VOTRE_CLE_API_INSTANTLY"
}
```

### 3.5 Variables d'environnement

Vous pouvez aussi configurer via une variable d'environnement :

```bash
export INSTANTLY_API_KEY="votre_clé_api_instantly"
```

## 4. Endpoints API

### 4.1 Récupérer les paramètres actuels

```
GET /api/system-settings/integrations/instantly
```

Réponse:
```json
{
  "status": "success",
  "data": {
    "instantly_api_key": "********",
    "instantly_integration_active": true
  }
}
```

### 4.2 Mettre à jour les paramètres

```
POST /api/system-settings/integrations/instantly
```

Corps de la requête:
```json
{
  "instantly_api_key": "votre_clé_api",
  "instantly_integration_active": true
}
```

Cette requête redémarrera automatiquement le service webhook si l'intégration est activée.

## 5. Webhooks Instantly

Pour recevoir les événements d'Instantly.ai, vous devez configurer les webhooks :

1. Accédez à la section "Settings" > "Integrations" > "Webhooks" dans l'interface Instantly
2. Ajoutez une URL webhook : `https://votredomaine.com/webhook/instantly`
3. Sélectionnez les événements à recevoir (emails ouverts, réponses, clics, etc.)

## 6. Types d'événements supportés

Les événements Instantly.ai suivants sont traités :

- `reply_received` : Une réponse à un email a été reçue
- `email_opened` : Un email a été ouvert par le destinataire
- `link_clicked` : Un lien dans un email a été cliqué
- Autres événements : Enregistrés mais pas d'action spécifique

## 7. Tracking des messages

Chaque message envoyé via Instantly inclut :
- Un ID de tracking unique
- L'ID de campagne
- Des variables personnalisées basées sur les données du lead

## 8. Tests

Un script de test est disponible pour valider l'intégration :

```bash
python -m infra-ia.tests.test_instantly_integration
```

## 9. Notes techniques

### 9.1 Rate Limiting

L'API Instantly a une limite de 600 requêtes par minute. Le client implémente un mécanisme de backoff exponentiel.

### 9.2 Réponses directes

Lorsqu'une réponse est reçue, l'ID du message original est conservé pour permettre une réponse directe via la méthode `reply_to_email`, ce qui maintient le fil de discussion intact.

### 9.3 Rotation d'adresses

Le système utilise la rotation automatique d'adresses fournie par Instantly.ai et n'a pas besoin de spécifier une adresse d'envoi fixe.

## 10. Dépannage

### 10.1 Problèmes d'authentification

Si vous rencontrez des erreurs d'authentification, vérifiez :
- Que votre clé API Instantly est correcte
- Que la clé a les permissions nécessaires

### 10.2 Problèmes de webhook

Si les webhooks ne sont pas traités correctement :
- Vérifiez l'accessibilité de votre endpoint webhook
- Vérifiez les logs du serveur pour détecter d'éventuelles erreurs
- Assurez-vous que les événements sont bien configurés dans l'interface Instantly

## 11. Limitations connues

- L'API Instantly ne permet pas actuellement l'envoi d'attachements via certains endpoints
- La synchronisation des comptes email doit être gérée manuellement dans l'interface Instantly

## 12. Évolutions futures

- Ajout de la gestion des pièces jointes
- Implémentation de campagnes automatisées via l'API Instantly
- Intégration des statistiques avancées dans le dashboard BerinIA

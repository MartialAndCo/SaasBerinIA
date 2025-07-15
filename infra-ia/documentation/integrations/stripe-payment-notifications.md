# Système de notifications de paiement Stripe pour Telegram

## Vue d'ensemble

Le système de notifications de paiement permet au bot Telegram BerinIA de recevoir et transmettre automatiquement les notifications de paiement Stripe aux administrateurs.

## Architecture

### 1. Backend (API)

#### Modèle de données
- **Table** : `payment_notifications`
- **Fichier** : `/backend/app/models/payment_notification.py`

**Champs principaux :**
- `stripe_event_id` : ID unique de l'événement Stripe
- `stripe_event_type` : Type d'événement (invoice.payment_succeeded, etc.)
- `notification_type` : Type simplifié (payment_success, payment_failed)
- `amount` : Montant en centimes
- `client_name` / `client_email` : Informations client
- `sent_to_telegram` : Statut d'envoi
- Relations : `invoice_id`, `lead_id`

#### Service de notifications
- **Fichier** : `/backend/app/services/notification_service.py`

**Méthodes principales :**
- `create_payment_notification()` : Créer une notification
- `get_unsent_notifications()` : Récupérer les notifications non envoyées
- `mark_as_sent()` / `mark_as_failed()` : Marquer l'état d'envoi
- `format_telegram_message()` : Formater les messages
- `get_daily_summary()` : Résumé quotidien

#### Endpoint webhook Stripe
- **Fichier** : `/backend/app/api/endpoints/stripe_webhooks.py`
- **URL** : `/stripe/webhook`

**Événements gérés :**
- `invoice.payment_succeeded` : Paiement de facture réussi
- `invoice.payment_failed` : Paiement de facture échoué
- `charge.succeeded` : Charge réussie
- `charge.failed` : Charge échouée

**Endpoints de notification :**
- `GET /notifications/payments/unsent` : Récupérer les notifications non envoyées
- `POST /notifications/payments/{id}/mark-sent` : Marquer comme envoyé
- `POST /notifications/payments/{id}/mark-failed` : Marquer comme échoué
- `GET /notifications/payments/daily-summary` : Résumé quotidien

### 2. Bot Telegram

#### Service de notification
- **Fichier** : `/infra-ia/telegram_bot/services/payment_notifier.py`

**Fonctionnalités :**
- Polling automatique des notifications (toutes les 30 secondes)
- Envoi aux administrateurs configurés
- Résumé quotidien automatique (18h00)
- Gestion des erreurs et retry

**Méthodes principales :**
- `start()` / `stop()` : Démarrer/arrêter le service
- `_check_and_send_notifications()` : Vérifier et envoyer
- `_send_daily_summary()` : Résumé quotidien
- `send_test_notification()` : Test des notifications

#### Intégration au bot principal
- **Fichier** : `/infra-ia/telegram_bot/main.py`
- Démarrage automatique dans `post_init()`
- Arrêt propre dans `post_shutdown()`

#### Commandes de test
- **Fichier** : `/infra-ia/telegram_bot/handlers/payment_test.py`
- Commandes : `/test_payment`, `/test_paiement`

## Configuration

### 1. Variables d'environnement

Dans `/root/berinia/infra-ia/.env` :
```bash
# Stripe
STRIPE_API_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_IDS=123456789,987654321
```

### 2. Configuration Stripe Dashboard

1. Aller dans **Developers > Webhooks**
2. Créer un nouveau webhook endpoint
3. URL : `https://votre-domaine.com/stripe/webhook`
4. Événements à écouter :
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `charge.succeeded`
   - `charge.failed`

### 3. Sécurité

Le webhook Stripe vérifie automatiquement la signature si `STRIPE_WEBHOOK_SECRET` est configuré.

## Formats de notification

### Paiement réussi
```
💰 Paiement reçu

📄 Facture: #123
💳 Montant: 150.00 EUR
👤 Client: Jean Dupont
📧 Email: jean@example.com

🕐 Date: 04/07/2025 14:30
```

### Paiement échoué
```
❌ Paiement échoué

📄 Facture: #123
💳 Montant: 150.00 EUR
👤 Client: Jean Dupont
📧 Email: jean@example.com

⚠️ Raison de l'échec: Insufficient funds

🕐 Date: 04/07/2025 14:30
```

### Résumé quotidien
```
📊 Résumé des paiements du 04/07/2025

✅ Paiements réussis: 5
💰 Montant total: 750.00 EUR

❌ Paiements échoués: 1
💸 Montant perdu: 150.00 EUR
```

## Déploiement

### 1. Migration de base de données
```bash
cd /root/berinia/backend
source venv/bin/activate
alembic upgrade head
```

### 2. Redémarrage des services
```bash
sudo systemctl restart berinia-api
sudo systemctl restart berinia-telegram-bot
```

### 3. Test du système
```bash
# Test via commande Telegram
/test_payment

# Test manuel via API
curl -X GET http://localhost:8000/notifications/payments/unsent
```

## Surveillance et logs

### Logs du backend
```bash
journalctl -u berinia-api -f | grep payment
```

### Logs du bot Telegram
```bash
journalctl -u berinia-telegram-bot -f | grep payment
```

### Métriques importantes
- Nombre de notifications en attente
- Temps de traitement des webhooks
- Erreurs d'envoi Telegram
- Taux de réussite des notifications

## Dépannage

### Problèmes courants

1. **Notifications non reçues**
   - Vérifier la configuration du webhook Stripe
   - Vérifier la variable `STRIPE_WEBHOOK_SECRET`
   - Vérifier les logs du backend

2. **Bot Telegram ne notifie pas**
   - Vérifier que le service `payment_notifier` est démarré
   - Vérifier les `TELEGRAM_ADMIN_IDS`
   - Tester avec `/test_payment`

3. **Webhook Stripe échoue**
   - Vérifier que l'API backend est accessible
   - Vérifier la signature du webhook
   - Consulter les logs Stripe Dashboard

### Commandes de diagnostic

```bash
# Vérifier les notifications en attente
curl http://localhost:8000/notifications/payments/unsent

# Tester le webhook manuellement
curl -X POST http://localhost:8000/stripe/webhook \
  -H "Content-Type: application/json" \
  -d '{"type": "test", "data": {}}'

# Vérifier l'état du bot
systemctl status berinia-telegram-bot
```

## Évolutions futures

### Fonctionnalités possibles
- Notifications pour d'autres événements Stripe (abonnements, remboursements)
- Tableaux de bord de paiement dans Telegram
- Alertes pour les paiements importants
- Intégration avec d'autres plateformes de paiement
- Notifications conditionnelles basées sur des seuils

### Améliorations techniques
- Système de queue pour les notifications
- Retry automatique avec backoff exponentiel
- Métriques et monitoring avancés
- Cache des notifications pour éviter les doublons
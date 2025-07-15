# 🚀 Guide de Configuration Stripe - BerinIA

## 📋 Étapes rapides

### 1. Créer un compte Stripe
1. Aller sur [stripe.com](https://stripe.com)
2. Créer un compte ou se connecter
3. Activer le mode test pour les développements

### 2. Récupérer les clés API
1. **Dashboard Stripe** → **Développeurs** → **Clés API**
2. Copier la **"Clé secrète"** (commence par `sk_test_` en mode test)
3. Noter la **"Clé publique"** (commence par `pk_test_`) pour le frontend si nécessaire

### 3. Configurer BerinIA
Éditer le fichier `/root/berinia/infra-ia/.env` :

```bash
# Remplacer la ligne existante :
STRIPE_API_KEY=sk_test_YOUR_STRIPE_SECRET_KEY_HERE

# Par votre vraie clé :
STRIPE_API_KEY=sk_test_51ABC123def456...
```

### 4. Configurer les Webhooks (Optionnel)
1. **Dashboard Stripe** → **Développeurs** → **Webhooks**
2. **Ajouter un endpoint** : `https://votre-domaine.com/api/billing/webhook`
3. Sélectionner les événements : `invoice.payment_succeeded`, `invoice.payment_failed`
4. Copier le **"Secret de signature"** (commence par `whsec_`)
5. Ajouter dans `/root/berinia/infra-ia/.env` :

```bash
STRIPE_WEBHOOK_SECRET=whsec_1234abcd...
```

### 5. Tester la configuration
```bash
cd /root/berinia/backend
source venv/bin/activate
python test_stripe_config.py
```

## 🔐 Sécurité

### ⚠️ IMPORTANT
- **Jamais** commiter les vraies clés dans Git
- Utiliser les clés de **test** (`sk_test_`) pour le développement
- Passer aux clés de **production** (`sk_live_`) uniquement pour la mise en production

### 🛡️ Bonnes pratiques
- Garder les clés secrètes dans le fichier `.env`
- Vérifier que `.env` est dans `.gitignore`
- Changer les clés en cas de compromission

## 🧪 Modes Stripe

### Mode Test (Développement)
- Clés commencent par `sk_test_` et `pk_test_`
- Aucun vrai paiement n'est effectué
- Utiliser les [cartes de test Stripe](https://stripe.com/docs/testing#cards)

### Mode Production (Live)
- Clés commencent par `sk_live_` et `pk_live_`
- Vrais paiements et factures
- Compte bancaire requis pour recevoir les fonds

## 💳 Cartes de test utiles

```
Visa réussie:           4242 4242 4242 4242
Visa échec générique:   4000 0000 0000 0002
Visa échec fonds:       4000 0000 0000 9995
Mastercard réussie:     5555 5555 5555 4444

Code CVC: n'importe quel 3 chiffres
Date expiration: n'importe quelle date future
```

## 📞 Support

### Problèmes fréquents
1. **"Invalid API key"** → Vérifier la clé dans `.env`
2. **"Test clock"** → Utiliser clés de test, pas de production
3. **"Webhook failed"** → Vérifier l'URL et les événements

### Documentation Stripe
- [Documentation officielle](https://stripe.com/docs)
- [API Reference](https://stripe.com/docs/api)
- [Guide Webhooks](https://stripe.com/docs/webhooks)

---

🎯 **Une fois configuré, votre système de facturation BerinIA sera opérationnel !**
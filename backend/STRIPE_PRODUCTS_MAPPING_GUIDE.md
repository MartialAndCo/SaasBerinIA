# Guide d'utilisation - Association automatique Produits/Abonnements Stripe

## Vue d'ensemble

Ce système gère automatiquement l'association entre les produits Stripe et leurs abonnements obligatoires ou optionnels lors de la création de factures.

## Associations configurées

### 1. Bot IA (prod_Sc1yH37xXqZkQu)
- **Abonnement associé**: Abonnement Bot IA (prod_Sc1zTYgekMuTpJ)
- **Prix abonnement**: 249€/mois
- **Type**: OBLIGATOIRE
- **Description**: Hébergement, mises à jour et support du Bot IA

### 2. Téléphone IA (prod_Sc20qI5hNsXqdd)
- **Abonnement associé**: Abonnement Répondeur IA (prod_Sc20IaGedKG2Vz)
- **Prix abonnement**: 249€/mois
- **Type**: OBLIGATOIRE
- **Description**: Hébergement, mises à jour et support du Répondeur IA

### 3. Site internet IA (prod_Sc1xkiIBLkWXZt)
- **Abonnement associé**: Maintenance site IA (prod_Sc1zOJX6C2DJu2)
- **Prix abonnement**: 29€/mois
- **Type**: OPTIONNEL
- **Description**: Maintenance et hébergement du site internet

### 4. Pack Combiné (prod_Sc21TjcwoabG1w)
- **Abonnement associé**: Abonnement Combiné (prod_Sc21O8xzouv0ix)
- **Prix abonnement**: 399€/mois
- **Type**: OBLIGATOIRE
- **Description**: Hébergement et support combiné Bot + Répondeur IA

## Endpoints API

### 1. Validation des items de facture

```http
POST /api/billing/validate-invoice-items
Content-Type: application/json

[
  {
    "product_id": "prod_Sc1yH37xXqZkQu",
    "price_id": "price_1RgnukIqOtT2zh8vgqGn7rTG",
    "quantity": 1
  }
]
```

**Réponse**:
```json
{
  "valid": true,
  "items": [
    {
      "product_id": "prod_Sc1yH37xXqZkQu",
      "price_id": "price_1RgnukIqOtT2zh8vgqGn7rTG",
      "quantity": 1,
      "product_name": "Bot IA (Chatbot intelligent)",
      "unit_amount": 79700,
      "currency": "eur",
      "price_type": "one_time"
    },
    {
      "product_id": "prod_Sc1zTYgekMuTpJ",
      "price_id": "price_1RgnvTIqOtT2zh8vVOxCC7lk",
      "quantity": 1,
      "product_name": "Abonnement Bot IA",
      "unit_amount": 24900,
      "currency": "eur",
      "price_type": "recurring",
      "auto_added": true,
      "reason": "Abonnement mensuel obligatoire pour hébergement et support du Bot IA"
    }
  ],
  "warnings": [
    "Abonnement obligatoire ajouté automatiquement: Abonnement mensuel obligatoire pour hébergement et support du Bot IA"
  ],
  "errors": []
}
```

### 2. Création de facture avec validation

```http
POST /api/billing/create-invoice-with-validation
Content-Type: application/json

{
  "lead_id": 123,
  "items": [
    {
      "product_id": "prod_Sc1yH37xXqZkQu",
      "price_id": "price_1RgnukIqOtT2zh8vgqGn7rTG",
      "quantity": 1
    }
  ],
  "send_email": true,
  "due_date": "2025-02-28T00:00:00"
}
```

### 3. Vérifier le mapping d'un produit

```http
GET /api/billing/product-subscription-mapping/prod_Sc1yH37xXqZkQu
```

**Réponse**:
```json
{
  "product_id": "prod_Sc1yH37xXqZkQu",
  "has_subscription": true,
  "subscription": {
    "product_id": "prod_Sc1zTYgekMuTpJ",
    "product_name": "Abonnement Bot IA",
    "price_id": "price_1RgnvTIqOtT2zh8vVOxCC7lk",
    "unit_amount": 24900,
    "currency": "eur",
    "recurring": {
      "interval": "month",
      "interval_count": 1
    },
    "required": true,
    "description": "Abonnement mensuel obligatoire pour hébergement et support du Bot IA"
  }
}
```

## Intégration Frontend

### 1. Validation avant soumission

```javascript
// Valider les items sélectionnés
const validateItems = async (selectedItems) => {
  const response = await fetch('/api/billing/validate-invoice-items', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(selectedItems)
  });
  
  const result = await response.json();
  
  if (result.warnings.length > 0) {
    // Afficher les warnings à l'utilisateur
    console.log('Abonnements ajoutés:', result.warnings);
  }
  
  return result;
};
```

### 2. Affichage des totaux

```javascript
const calculateTotals = (items) => {
  let totalOneTime = 0;
  let totalRecurring = 0;
  
  items.forEach(item => {
    const amount = item.unit_amount / 100;
    if (item.price_type === 'one_time') {
      totalOneTime += amount * item.quantity;
    } else {
      totalRecurring += amount * item.quantity;
    }
  });
  
  return {
    oneTime: totalOneTime,
    recurring: totalRecurring
  };
};
```

## Cas d'usage

### Cas 1: Client sélectionne Bot IA
1. Sélection: Bot IA (797€)
2. Système ajoute automatiquement: Abonnement Bot IA (249€/mois)
3. Total: 797€ + 249€/mois

### Cas 2: Client sélectionne Site Internet
1. Sélection: Site internet (1497€)
2. Système propose (optionnel): Maintenance site (29€/mois)
3. Total: 1497€ + 29€/mois (si accepté)

### Cas 3: Client sélectionne Pack Combiné
1. Sélection: Pack Combiné (1449€)
2. Système ajoute automatiquement: Abonnement Combiné (399€/mois)
3. Total: 1449€ + 399€/mois

## Configuration

Le mapping est défini dans `/root/berinia/backend/app/config/stripe_products_mapping.py`.

Pour modifier les associations:
1. Éditer le dictionnaire `PRODUCT_TO_SUBSCRIPTION_MAPPING`
2. Redémarrer le service API
3. Tester avec le script de test fourni

## Test

Utiliser le script de test:
```bash
cd /root/berinia/backend
python test_stripe_subscription_mapping.py
```

## Notes importantes

1. Les abonnements obligatoires sont ajoutés automatiquement
2. Les abonnements optionnels génèrent un warning mais ne sont pas ajoutés automatiquement
3. Le système empêche l'ajout en double d'abonnements
4. Les produits qui sont eux-mêmes des abonnements ne peuvent pas avoir d'abonnements associés
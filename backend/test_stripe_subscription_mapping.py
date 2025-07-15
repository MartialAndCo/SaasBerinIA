#!/usr/bin/env python3
"""
Script de test pour la logique d'association automatique produits/abonnements Stripe
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://localhost:8000/api"

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def test_get_products():
    """Récupérer et afficher tous les produits Stripe"""
    print_section("1. RÉCUPÉRATION DES PRODUITS STRIPE")
    
    response = requests.get(f"{API_BASE_URL}/billing/stripe-products")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['count']} produits récupérés\n")
        
        for product in data['products']:
            print(f"📦 {product['name']}")
            print(f"   ID: {product['id']}")
            print(f"   Description: {product['description'][:80]}...")
            for price in product['prices']:
                price_type = "Récurrent" if price['type'] == 'recurring' else "Unique"
                amount = price['unit_amount'] / 100
                print(f"   💰 Prix: {amount}€ ({price_type})")
            print()
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")

def test_product_mapping(product_id):
    """Tester le mapping d'un produit spécifique"""
    response = requests.get(f"{API_BASE_URL}/billing/product-subscription-mapping/{product_id}")
    if response.status_code == 200:
        data = response.json()
        if data['has_subscription']:
            sub = data['subscription']
            print(f"✅ Abonnement associé trouvé:")
            print(f"   - Produit: {sub['product_name']}")
            print(f"   - Prix: {sub['unit_amount']/100}€/mois")
            print(f"   - Obligatoire: {'Oui' if sub['required'] else 'Non'}")
            print(f"   - Description: {sub['description']}")
        else:
            print(f"ℹ️  Pas d'abonnement associé")
    else:
        print(f"❌ Erreur: {response.status_code}")

def test_validation_scenarios():
    """Tester différents scénarios de validation"""
    print_section("2. TEST DES SCÉNARIOS DE VALIDATION")
    
    scenarios = [
        {
            "name": "Bot IA seul",
            "items": [
                {
                    "product_id": "prod_Sc1yH37xXqZkQu",  # Bot IA
                    "price_id": "price_1RgnukIqOtT2zh8vgqGn7rTG",
                    "quantity": 1
                }
            ]
        },
        {
            "name": "Téléphone IA seul",
            "items": [
                {
                    "product_id": "prod_Sc20qI5hNsXqdd",  # Téléphone IA
                    "price_id": "price_1RgnwEIqOtT2zh8vGEozlics",
                    "quantity": 1
                }
            ]
        },
        {
            "name": "Site internet IA seul",
            "items": [
                {
                    "product_id": "prod_Sc1xkiIBLkWXZt",  # Site internet
                    "price_id": "price_1RgntpIqOtT2zh8vQQGpnTP7",
                    "quantity": 1
                }
            ]
        },
        {
            "name": "Pack Combiné",
            "items": [
                {
                    "product_id": "prod_Sc21TjcwoabG1w",  # Pack Combiné
                    "price_id": "price_1RgnxIIqOtT2zh8vfUzQvBZF",
                    "quantity": 1
                }
            ]
        },
        {
            "name": "Bot IA + Site internet",
            "items": [
                {
                    "product_id": "prod_Sc1yH37xXqZkQu",  # Bot IA
                    "price_id": "price_1RgnukIqOtT2zh8vgqGn7rTG",
                    "quantity": 1
                },
                {
                    "product_id": "prod_Sc1xkiIBLkWXZt",  # Site internet
                    "price_id": "price_1RgntpIqOtT2zh8vQQGpnTP7",
                    "quantity": 1
                }
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🔍 Scénario: {scenario['name']}")
        print("-" * 40)
        
        response = requests.post(
            f"{API_BASE_URL}/billing/validate-invoice-items",
            json=scenario['items']
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Validation: {'Réussie' if result['valid'] else 'Échouée'}")
            print(f"📋 Items finaux: {len(result['items'])}")
            
            # Afficher les items
            total_unique = 0
            total_recurrent = 0
            
            for item in result['items']:
                amount = item['unit_amount'] / 100
                if item['price_type'] == 'one_time':
                    total_unique += amount * item.get('quantity', 1)
                    print(f"   - {item['product_name']}: {amount}€ (paiement unique)")
                else:
                    total_recurrent += amount * item.get('quantity', 1)
                    interval = item['recurring']['interval'] if item.get('recurring') else 'mois'
                    print(f"   - {item['product_name']}: {amount}€/{interval}")
                
                if item.get('auto_added'):
                    print(f"     ⚡ Ajouté automatiquement: {item.get('reason', '')}")
            
            print(f"\n💰 Total unique: {total_unique}€")
            print(f"💰 Total récurrent: {total_recurrent}€/mois")
            
            # Afficher les warnings
            if result.get('warnings'):
                print(f"\n⚠️  Avertissements:")
                for warning in result['warnings']:
                    print(f"   - {warning}")
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")

def test_invoice_creation_with_validation():
    """Test de création de facture avec validation"""
    print_section("3. TEST DE CRÉATION DE FACTURE AVEC VALIDATION")
    
    # Simuler une création de facture pour le lead de test
    invoice_data = {
        "lead_id": 1,  # ID d'un lead de test existant
        "items": [
            {
                "product_id": "prod_Sc1yH37xXqZkQu",  # Bot IA
                "price_id": "price_1RgnukIqOtT2zh8vgqGn7rTG",
                "quantity": 1
            }
        ],
        "send_email": False,  # Ne pas envoyer réellement l'email pour le test
        "due_date": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    print("📝 Test de création de facture avec Bot IA...")
    print(f"   Items envoyés: {len(invoice_data['items'])}")
    
    # Note: Ce test ne fonctionnera que si un lead avec ID=1 existe et a un stripe_customer_id
    # Pour un vrai test, il faudrait d'abord créer un lead de test
    
    print("\n⚠️  Note: Pour tester la création réelle, assurez-vous d'avoir:")
    print("   1. Un lead existant avec un stripe_customer_id valide")
    print("   2. Une clé API Stripe configurée dans /root/berinia/infra-ia/.env")

def main():
    """Fonction principale"""
    print("\n🚀 TEST DE LA LOGIQUE D'ASSOCIATION PRODUITS/ABONNEMENTS STRIPE")
    print("=" * 60)
    
    # 1. Récupérer les produits
    test_get_products()
    
    # 2. Tester les mappings individuels
    print_section("TEST DES MAPPINGS PRODUIT → ABONNEMENT")
    
    products_to_test = [
        ("prod_Sc1yH37xXqZkQu", "Bot IA"),
        ("prod_Sc20qI5hNsXqdd", "Téléphone IA"),
        ("prod_Sc1xkiIBLkWXZt", "Site internet IA"),
        ("prod_Sc21TjcwoabG1w", "Pack Combiné")
    ]
    
    for product_id, product_name in products_to_test:
        print(f"\n📦 {product_name} ({product_id})")
        test_product_mapping(product_id)
    
    # 3. Tester les scénarios de validation
    test_validation_scenarios()
    
    # 4. Test de création (simulé)
    test_invoice_creation_with_validation()
    
    print("\n✅ Tests terminés!")

if __name__ == "__main__":
    main()
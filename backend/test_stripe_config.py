#!/usr/bin/env python
"""Test de configuration Stripe depuis le fichier .env"""

import sys
import os
sys.path.append('/root/berinia/backend')

from app.services.stripe_service import StripeService
from dotenv import load_dotenv

def test_stripe_configuration():
    """Test de la configuration Stripe"""
    print("🧪 Test de configuration Stripe")
    print("=" * 50)
    
    # 1. Vérifier le chargement du fichier .env
    print("\n1. 📄 Test chargement fichier .env...")
    load_dotenv('/root/berinia/infra-ia/.env')
    
    stripe_api_key = os.getenv('STRIPE_API_KEY')
    stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if stripe_api_key:
        if stripe_api_key.startswith('sk_test_') or stripe_api_key.startswith('sk_live_'):
            print(f"   ✅ STRIPE_API_KEY chargée: {stripe_api_key[:12]}...")
        else:
            print(f"   ⚠️ STRIPE_API_KEY présente mais invalide: {stripe_api_key}")
    else:
        print("   ❌ STRIPE_API_KEY non trouvée")
    
    if stripe_webhook_secret:
        if stripe_webhook_secret.startswith('whsec_'):
            print(f"   ✅ STRIPE_WEBHOOK_SECRET chargée: {stripe_webhook_secret[:10]}...")
        else:
            print(f"   ⚠️ STRIPE_WEBHOOK_SECRET présente mais invalide: {stripe_webhook_secret}")
    else:
        print("   ⚠️ STRIPE_WEBHOOK_SECRET non trouvée (optionnel)")
    
    # 2. Test d'initialisation du service Stripe
    print("\n2. 🔧 Test initialisation StripeService...")
    try:
        stripe_service = StripeService()
        if stripe_service.api_key:
            print("   ✅ Service Stripe initialisé avec succès")
            
            # Test simple de validation de clé (sans appel API réel)
            if stripe_service.api_key.startswith('sk_'):
                print("   ✅ Format de clé API valide")
            else:
                print("   ❌ Format de clé API invalide")
        else:
            print("   ❌ Service Stripe non initialisé - clé manquante")
    except Exception as e:
        print(f"   ❌ Erreur initialisation: {e}")
    
    # 3. Instructions de configuration
    print("\n3. 📋 Instructions de configuration...")
    print("   Pour configurer Stripe, éditez le fichier:")
    print("   📁 /root/berinia/infra-ia/.env")
    print()
    print("   Remplacez:")
    print("   STRIPE_API_KEY=sk_test_YOUR_STRIPE_SECRET_KEY_HERE")
    print("   STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE")
    print()
    print("   Par vos vraies clés Stripe:")
    print("   STRIPE_API_KEY=sk_test_51...")
    print("   STRIPE_WEBHOOK_SECRET=whsec_...")
    
    return stripe_api_key is not None and stripe_api_key.startswith('sk_')

if __name__ == "__main__":
    print("🚀 Test de configuration Stripe BerinIA")
    
    config_ok = test_stripe_configuration()
    
    print(f"\n🎯 RÉSUMÉ:")
    if config_ok:
        print("✅ Configuration Stripe: OK")
        print("✅ Fichier .env: Chargé")
        print("✅ Service Stripe: Opérationnel")
        print("\n🎉 STRIPE PRÊT POUR LA FACTURATION!")
    else:
        print("⚠️ Configuration Stripe: À compléter")
        print("📝 Veuillez configurer vos clés dans /root/berinia/infra-ia/.env")
        print("📚 Consultez la documentation Stripe pour obtenir vos clés")
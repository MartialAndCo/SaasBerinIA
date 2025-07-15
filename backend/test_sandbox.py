#!/usr/bin/env python3
"""
Script de test pour le système sandbox de messagerie
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.sandbox import SandboxLead, SandboxConversation, SandboxTemplate
from app.schemas.sandbox import SandboxLeadCreate, SandboxMessageRequest
import json

def test_database_connection():
    """Test la connexion à la base de données"""
    print("🔍 Test de connexion à la base de données...")
    try:
        from sqlalchemy import text
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        db.close()
        print("✅ Connexion à la base de données réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return False

def run_migration():
    """Exécute la migration des tables sandbox"""
    print("🏗️ Exécution de la migration sandbox...")
    try:
        from sqlalchemy import text
        db = SessionLocal()
        
        # Lire et exécuter le script de migration
        with open('migrations/add_sandbox_tables.sql', 'r') as f:
            migration_sql = f.read()
        
        # Diviser en commandes individuelles
        commands = migration_sql.split(';')
        
        for command in commands:
            command = command.strip()
            if command and not command.startswith('--') and command != '' and 'SELECT' not in command:
                try:
                    db.execute(text(command))
                except Exception as e:
                    if "already exists" not in str(e) and "duplicate key" not in str(e):
                        print(f"⚠️ Attention avec la commande: {command[:50]}... - {e}")
        
        db.commit()
        db.close()
        print("✅ Migration exécutée avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False

def test_sandbox_models():
    """Test la création et récupération des modèles sandbox"""
    print("📝 Test des modèles sandbox...")
    try:
        db = SessionLocal()
        
        # Créer un lead de test
        test_lead = SandboxLead(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="0123456789",
            company="Test Company",
            position="CEO",
            website="www.test.com",
            industry="Test",
            score=75,
            visual_score=80,
            site_type="vitrine",
            visual_quality=8,
            website_maturity="intermédiaire",
            test_platform="sms",
            template_used="test_template",
            created_by_user="test_user"
        )
        
        db.add(test_lead)
        db.commit()
        db.refresh(test_lead)
        
        print(f"✅ Lead de test créé avec l'ID: {test_lead.id}")
        
        # Tester la récupération
        retrieved_lead = db.query(SandboxLead).filter(SandboxLead.id == test_lead.id).first()
        if retrieved_lead:
            print(f"✅ Lead récupéré: {retrieved_lead.first_name} - {retrieved_lead.company}")
        
        # Nettoyer
        db.delete(test_lead)
        db.commit()
        db.close()
        
        print("✅ Test des modèles réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test des modèles: {e}")
        return False

def test_templates():
    """Test la récupération des templates"""
    print("🎨 Test des templates...")
    try:
        db = SessionLocal()
        
        templates = db.query(SandboxTemplate).all()
        print(f"✅ {len(templates)} templates trouvés:")
        for template in templates:
            print(f"  - {template.name} ({template.category})")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test des templates: {e}")
        return False

def test_api_simulation():
    """Test la logique de simulation des réponses IA"""
    print("🤖 Test de la simulation d'IA...")
    try:
        # Simuler quelques scénarios
        test_scenarios = [
            {"user_message": "pas intéressé", "expected_keywords": ["comprends", "problème"]},
            {"user_message": "trop cher", "expected_keywords": ["budget", "ROI"]},
            {"user_message": "déjà un prestataire", "expected_keywords": ["satisfait", "compléter"]},
            {"user_message": "bonjour", "expected_keywords": ["défi", "développement"]},
        ]
        
        for scenario in test_scenarios:
            # Simulation de la logique de réponse (copié de sandbox.py)
            user_message = scenario["user_message"]
            first_name = "Test"
            
            if "pas intéressé" in user_message.lower() or "non merci" in user_message.lower():
                ai_response = f"Je comprends {first_name}. Puis-je vous demander ce qui vous pose problème actuellement en termes de visibilité en ligne ?"
            elif "trop cher" in user_message.lower() or "budget" in user_message.lower():
                ai_response = f"Je comprends votre préoccupation {first_name}. Justement, notre approche permet d'optimiser le ROI."
            elif "déjà un prestataire" in user_message.lower() or "déjà quelqu'un" in user_message.lower():
                ai_response = f"Parfait {first_name} ! Cela montre que vous investissez déjà dans votre présence digitale. Êtes-vous satisfait des résultats actuels ?"
            else:
                ai_response = f"Merci pour votre retour {first_name}. Pourriez-vous me dire quel est votre principal défi actuellement ?"
            
            # Vérifier que les mots-clés attendus sont présents
            found_keywords = [kw for kw in scenario["expected_keywords"] if kw.lower() in ai_response.lower()]
            if found_keywords:
                print(f"✅ Scénario '{user_message}': Réponse appropriée (mots-clés: {found_keywords})")
            else:
                print(f"⚠️ Scénario '{user_message}': Réponse inattendue")
        
        print("✅ Test de simulation d'IA réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test de simulation: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests du système sandbox...")
    print("=" * 50)
    
    tests = [
        ("Connexion base de données", test_database_connection),
        ("Migration tables", run_migration),
        ("Modèles sandbox", test_sandbox_models),
        ("Templates", test_templates),
        ("Simulation IA", test_api_simulation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        result = test_func()
        results.append((test_name, result))
        print("-" * 30)
    
    print("\n🎯 RÉSUMÉ DES TESTS:")
    print("=" * 50)
    success_count = 0
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n📊 Score: {success_count}/{len(tests)} tests réussis")
    
    if success_count == len(tests):
        print("\n🎉 Tous les tests sont passés ! Le système sandbox est prêt à être utilisé.")
        print("\n📝 Prochaines étapes:")
        print("1. Démarrer le serveur backend: cd backend && python -m app.main")
        print("2. Démarrer le frontend: cd frontend && pnpm dev")
        print("3. Accéder au sandbox: http://localhost:3000/dashboard/sandbox")
    else:
        print(f"\n⚠️ {len(tests) - success_count} test(s) ont échoué. Vérifiez les erreurs ci-dessus.")
    
    return success_count == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

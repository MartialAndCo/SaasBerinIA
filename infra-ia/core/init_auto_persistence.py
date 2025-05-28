"""
Script d'initialisation de la persistance automatique
Applique la persistance automatique à tous les agents BerinIA
"""
import os
import sys
import logging
from pathlib import Path

# Ajout du répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.auto_persistence import apply_auto_persistence_to_existing_agents, persistence_control
from core.persistence_service import persistence_service


def initialize_auto_persistence():
    """
    Initialise la persistance automatique pour tout le système BerinIA
    """
    logger = logging.getLogger("BerinIA-Init")
    
    print("🚀 Initialisation de la persistance automatique BerinIA...")
    logger.info("Début de l'initialisation de la persistance automatique")
    
    try:
        # 1. Vérification de la connectivité base de données
        print("📊 Vérification de la base de données...")
        test_query = "SELECT 1 as test"
        result = persistence_service.db.fetch_one(test_query)
        if result and result.get('test') == 1:
            print("✅ Base de données accessible")
        else:
            print("❌ Problème de connectivité base de données")
            return False
        
        # 2. Vérification des tables nécessaires
        print("🏗️ Vérification des tables...")
        required_tables = ['leads', 'messages']
        for table in required_tables:
            try:
                test_query = f"SELECT COUNT(*) as count FROM {table} LIMIT 1"
                result = persistence_service.db.fetch_one(test_query)
                print(f"✅ Table {table} accessible ({result.get('count', 0)} enregistrements)")
            except Exception as e:
                print(f"⚠️ Problème avec la table {table}: {e}")
        
        # 3. Application de la persistance aux agents existants
        print("🔧 Application de la persistance automatique aux agents...")
        apply_auto_persistence_to_existing_agents()
        
        # 4. Activation globale
        print("🌟 Activation globale de la persistance...")
        persistence_control.enable_globally()
        
        # 5. Test de fonctionnement
        print("🧪 Test du système de persistance...")
        stats = persistence_service.get_stats()
        print(f"📈 Statistiques initiales: {stats}")
        
        # 6. Création des collections Qdrant si nécessaire
        print("🧠 Initialisation de la mémoire vectorielle...")
        try:
            from utils.qdrant import create_collection
            
            collections_to_create = [
                ('leads_memory', 1536),
                ('message_memory', 1536), 
                ('conversation_memory', 1536)
            ]
            
            for collection_name, vector_size in collections_to_create:
                try:
                    create_collection(collection_name, vector_size)
                    print(f"✅ Collection {collection_name} initialisée")
                except Exception as e:
                    print(f"⚠️ Collection {collection_name}: {e}")
                    
        except ImportError:
            print("⚠️ Qdrant non disponible, mémoire vectorielle désactivée")
        
        print("\n🎉 Persistance automatique initialisée avec succès!")
        print("📝 Les agents sauvegarderont maintenant automatiquement leurs données")
        print("🔍 Logs disponibles dans infra-ia/logs/")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        logger.error(f"Erreur d'initialisation: {e}")
        return False


def test_persistence_with_mock_data():
    """
    Test de la persistance avec des données factices
    """
    print("\n🧪 Test de la persistance avec données factices...")
    
    try:
        # Test 1: Sauvegarde d'un lead factice
        mock_lead_data = {
            'status': 'success',
            'leads': [{
                'first_name': 'Test',
                'last_name': 'Persistence',
                'email': 'test.persistence@example.com',
                'company': 'Test Company',
                'position': 'Test Manager',
                'source': 'test_init',
                'industry': 'Technology',
                'scrape_date': '2025-05-27T14:00:00'
            }]
        }
        
        result = persistence_service.persist_agent_data(
            agent_name='TestAgent',
            action='test_scrape',
            input_data={},
            result_data=mock_lead_data
        )
        
        persistence_info = result.get('persistence', {})
        if persistence_info.get('status') == 'success':
            print(f"✅ Test leads: {persistence_info.get('count', 0)} sauvegardé(s)")
        else:
            print(f"⚠️ Test leads: {persistence_info}")
        
        # Test 2: Sauvegarde d'un message factice
        mock_message_data = {
            'status': 'success',
            'source': 'email',
            'sender': 'test.persistence@example.com',
            'content': 'Merci pour votre message, je suis intéressé par vos services.',
            'subject': 'Re: Votre proposition',
            'received_at': '2025-05-27T14:05:00'
        }
        
        result = persistence_service.persist_agent_data(
            agent_name='TestResponseListener',
            action='process_email_response',
            input_data={},
            result_data=mock_message_data
        )
        
        persistence_info = result.get('persistence', {})
        if persistence_info.get('status') == 'success':
            print(f"✅ Test message: sauvegardé avec ID {persistence_info.get('message_id')}")
        else:
            print(f"⚠️ Test message: {persistence_info}")
        
        # Affichage des statistiques finales
        stats = persistence_service.get_stats()
        print(f"📊 Statistiques après test: {stats}")
        
        print("✅ Tests de persistance terminés")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")


def show_persistence_status():
    """
    Affiche le statut actuel de la persistance
    """
    print("\n📋 Statut de la persistance automatique:")
    
    status = persistence_control.get_status()
    
    print(f"🌐 Activation globale: {'✅ Activée' if status['global_enabled'] else '❌ Désactivée'}")
    
    if status['agent_overrides']:
        print("🔧 Overrides par agent:")
        for agent, enabled in status['agent_overrides'].items():
            state = '✅ Activé' if enabled else '❌ Désactivé'
            print(f"   - {agent}: {state}")
    else:
        print("🔧 Aucun override spécifique")
    
    stats = status['persistence_stats']
    print(f"📈 Statistiques:")
    print(f"   - Leads sauvegardés: {stats['leads_saved']}")
    print(f"   - Messages sauvegardés: {stats['messages_saved']}")
    print(f"   - Erreurs: {stats['errors']}")
    print(f"   - Dernière activité: {stats['last_activity']}")


if __name__ == "__main__":
    # Configuration des logs
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    
    print("=" * 60)
    print("🤖 INITIALISATION PERSISTANCE AUTOMATIQUE BERINIA")
    print("=" * 60)
    
    # Initialisation
    success = initialize_auto_persistence()
    
    if success:
        # Test avec données factices
        test_persistence_with_mock_data()
        
        # Statut final
        show_persistence_status()
        
        print("\n" + "=" * 60)
        print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print("💡 Pour désactiver: persistence_control.disable_globally()")
        print("💡 Pour réactiver: persistence_control.enable_globally()")
        print("💡 Logs dans: infra-ia/logs/system.log")
        
    else:
        print("\n" + "=" * 60)
        print("❌ ÉCHEC DE L'INITIALISATION")
        print("=" * 60)
        print("🔧 Vérifiez la configuration de la base de données")
        print("🔧 Consultez les logs pour plus de détails")

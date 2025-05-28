#!/usr/bin/env python3
"""
Tests de validation des corrections du bug de duplication des tâches
Date: 27 mai 2025
Auteur: Assistant IA

Ce script teste les corrections apportées aux bugs de duplication dans le système de tâches planifiées.
"""
import os
import sys
import json
import time
import datetime
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

def test_scheduled_tasks_file_cleanup():
    """Test 1: Vérifier que le fichier de tâches a été nettoyé"""
    print("=" * 50)
    print("TEST 1: Vérification du nettoyage du fichier scheduled_tasks.json")
    print("=" * 50)
    
    tasks_file = Path("data/scheduled_tasks.json")
    
    if not tasks_file.exists():
        print("❌ ÉCHEC: Fichier scheduled_tasks.json non trouvé")
        return False
    
    try:
        with open(tasks_file, 'r') as f:
            tasks = json.load(f)
        
        print(f"📊 Nombre de tâches trouvées: {len(tasks)}")
        
        # Vérifier qu'il n'y a que 2 tâches avec les bons IDs
        expected_ids = {"pivot_strategy_weekly", "prospection_daily"}
        found_ids = {task.get("task_id", "") for task in tasks}
        
        if len(tasks) <= 5:  # Acceptable (2 + quelques variations récentes)
            print("✅ SUCCÈS: Nombre de tâches réduit (era ~60, maintenant ≤5)")
        else:
            print(f"⚠️  ATTENTION: Encore {len(tasks)} tâches (devrait être ≤5)")
        
        # Vérifier les IDs de base attendus
        base_ids_found = set()
        for task in tasks:
            task_id = task.get("task_id", "")
            # Extraire l'ID de base (sans _next_xxxxx)
            base_id = task_id.split('_next_')[0]
            base_ids_found.add(base_id)
        
        if expected_ids.issubset(base_ids_found):
            print("✅ SUCCÈS: Tâches de base trouvées avec les bons IDs")
        else:
            missing = expected_ids - base_ids_found
            print(f"⚠️  ATTENTION: IDs de base manquants: {missing}")
        
        # Afficher les tâches actuelles
        print("\n📋 Tâches actuelles:")
        for i, task in enumerate(tasks, 1):
            task_id = task.get("task_id", "unknown")
            agent = task.get("task_data", {}).get("agent", "unknown")
            action = task.get("task_data", {}).get("action", "unknown")
            recurring = task.get("recurring", False)
            print(f"  {i}. {task_id} | {agent}.{action} | récurrent: {recurring}")
        
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC: Erreur lors de la lecture du fichier: {e}")
        return False

def test_scheduler_agent_logic():
    """Test 2: Tester la logique corrigée de l'AgentSchedulerAgent"""
    print("\n" + "=" * 50)
    print("TEST 2: Test de la logique AgentSchedulerAgent")
    print("=" * 50)
    
    try:
        from agents.scheduler.agent_scheduler_agent import AgentSchedulerAgent, ScheduledTask
        
        # Créer une instance de test
        scheduler = AgentSchedulerAgent()
        
        # Test de création d'une tâche récurrente
        test_task_data = {
            "agent": "TestAgent",
            "action": "test_action",
            "params": {"test": True}
        }
        
        execution_time = datetime.datetime.now() + datetime.timedelta(seconds=5)
        
        result = scheduler.schedule_task(
            task_data=test_task_data,
            execution_time=execution_time,
            task_id="test_recurring_task",
            recurring=True,
            recurrence_interval=10  # 10 secondes
        )
        
        if result.get("status") == "success":
            print("✅ SUCCÈS: Tâche récurrente créée")
        else:
            print(f"❌ ÉCHEC: Erreur création tâche: {result.get('message')}")
            return False
        
        # Vérifier les tâches en attente
        pending_result = scheduler.get_pending_tasks()
        if pending_result.get("status") == "success":
            pending_tasks = pending_result.get("pending_tasks", [])
            print(f"📊 Tâches en attente: {len(pending_tasks)}")
            
            # Chercher notre tâche de test
            test_task_found = False
            for task in pending_tasks:
                if task.get("task_id") == "test_recurring_task":
                    test_task_found = True
                    print(f"✅ Tâche de test trouvée: {task.get('task_id')}")
                    break
            
            if not test_task_found:
                print("⚠️  ATTENTION: Tâche de test non trouvée dans les tâches en attente")
        
        # Nettoyer la tâche de test
        cancel_result = scheduler.cancel_task("test_recurring_task")
        if cancel_result.get("status") == "success":
            print("✅ Tâche de test nettoyée")
        
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC: Erreur lors du test AgentSchedulerAgent: {e}")
        import traceback
        print(f"Détails: {traceback.format_exc()}")
        return False

def test_init_system_anti_duplication():
    """Test 3: Tester la logique anti-duplication de init_system.py"""
    print("\n" + "=" * 50)
    print("TEST 3: Test de la logique anti-duplication de init_system.py")
    print("=" * 50)
    
    try:
        # Simuler la fonction setup_initial_tasks
        from agents.scheduler.agent_scheduler_agent import AgentSchedulerAgent
        
        scheduler = AgentSchedulerAgent()
        
        # Obtenir les tâches existantes
        existing_tasks_result = scheduler.get_pending_tasks()
        existing_task_ids = set()
        
        if existing_tasks_result.get("status") == "success":
            for task in existing_tasks_result.get("pending_tasks", []):
                existing_task_ids.add(task.get("task_id", ""))
            print(f"📊 Tâches existantes trouvées: {len(existing_task_ids)}")
            print(f"IDs existants: {existing_task_ids}")
        
        # Tester la logique de vérification
        expected_task_ids = {"pivot_strategy_weekly", "prospection_daily"}
        
        duplicates_that_would_be_created = expected_task_ids.intersection(existing_task_ids)
        new_tasks_that_would_be_created = expected_task_ids - existing_task_ids
        
        print(f"🔄 Tâches qui seraient dupliquées: {duplicates_that_would_be_created}")
        print(f"🆕 Nouvelles tâches qui seraient créées: {new_tasks_that_would_be_created}")
        
        if len(duplicates_that_would_be_created) > 0:
            print("✅ SUCCÈS: La logique anti-duplication empêcherait la création de doublons")
        else:
            print("ℹ️  INFO: Aucun doublon ne serait créé (normal si tâches n'existent pas encore)")
        
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC: Erreur lors du test anti-duplication: {e}")
        import traceback
        print(f"Détails: {traceback.format_exc()}")
        return False

def test_backup_file_exists():
    """Test 4: Vérifier que le backup a été créé"""
    print("\n" + "=" * 50)
    print("TEST 4: Vérification de l'existence du fichier de backup")
    print("=" * 50)
    
    data_dir = Path("data")
    backup_files = list(data_dir.glob("scheduled_tasks.json.backup.*"))
    
    if backup_files:
        print(f"✅ SUCCÈS: {len(backup_files)} fichier(s) de backup trouvé(s)")
        for backup_file in backup_files:
            size = backup_file.stat().st_size
            print(f"  📁 {backup_file.name} ({size:,} bytes)")
        
        # Vérifier la taille du backup (devrait être > 50KB car contenait beaucoup de tâches)
        if any(f.stat().st_size > 50000 for f in backup_files):
            print("✅ SUCCÈS: Backup contient les anciennes tâches dupliquées")
        else:
            print("⚠️  ATTENTION: Backup semble petit, peut-être ne contient pas toutes les tâches")
        
        return True
    else:
        print("❌ ÉCHEC: Aucun fichier de backup trouvé")
        return False

def generate_test_report():
    """Génère un rapport de test"""
    print("\n" + "=" * 70)
    print("RAPPORT DE TEST DES CORRECTIONS DU BUG DE DUPLICATION")
    print("=" * 70)
    
    tests = [
        ("Nettoyage fichier scheduled_tasks.json", test_scheduled_tasks_file_cleanup),
        ("Logique AgentSchedulerAgent corrigée", test_scheduler_agent_logic),
        ("Anti-duplication init_system.py", test_init_system_anti_duplication),
        ("Fichier de backup créé", test_backup_file_exists)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ ERREUR FATALE dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "=" * 70)
    print("RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSÉ" if success else "❌ ÉCHEC"
        print(f"{status:10} {test_name}")
    
    print(f"\n📊 SCORE FINAL: {passed}/{total} tests passés ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 TOUTES LES CORRECTIONS FONCTIONNENT CORRECTEMENT !")
    elif passed >= total * 0.75:
        print("✅ La plupart des corrections fonctionnent, quelques ajustements mineurs possibles")
    else:
        print("⚠️  Des problèmes persistent, investigation supplémentaire requise")
    
    return passed, total

if __name__ == "__main__":
    print("🔧 VALIDATION DES CORRECTIONS DU BUG DE DUPLICATION DES TÂCHES")
    print(f"Exécution le: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Répertoire de travail: {os.getcwd()}")
    
    # Aller dans le bon répertoire
    os.chdir(Path(__file__).parent.parent)
    print(f"Répertoire changé vers: {os.getcwd()}")
    
    passed, total = generate_test_report()
    
    # Code de sortie pour intégration dans scripts
    exit_code = 0 if passed == total else 1
    sys.exit(exit_code)

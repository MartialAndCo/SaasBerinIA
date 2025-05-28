#!/usr/bin/env python3
"""
Tests d'intégration du TaskWatchdogAgent avec le système BerinIA

Ce script teste l'intégration complète du TaskWatchdogAgent dans le système,
en particulier son intégration avec l'AgentSchedulerAgent.
"""

import os
import sys
import json
import time
import datetime
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

def test_normal_task_creation():
    """Test la création d'une tâche normale (doit être autorisée)"""
    print("=" * 60)
    print("TEST 1: Création d'une tâche normale (autorisée)")
    print("=" * 60)
    
    try:
        from agents.scheduler.agent_scheduler_agent import AgentSchedulerAgent
        
        scheduler = AgentSchedulerAgent()
        
        # Tâche normale système
        result = scheduler.schedule_task(
            task_data={
                "agent": "PivotStrategyAgent",
                "action": "recommend_optimizations",
                "params": {
                    "target": "all",
                    "optimization_type": "performance"
                }
            },
            execution_time=datetime.datetime.now() + datetime.timedelta(hours=1),
            task_id="test_normal_task",
            recurring=True,
            recurrence_interval=7*24*3600  # Hebdomadaire
        )
        
        print(f"Résultat: {result}")
        
        if result.get("status") == "success":
            security_analysis = result.get("security_analysis", {})
            threat_level = security_analysis.get("threat_level", "unknown")
            confidence = security_analysis.get("confidence", 0)
            reason = security_analysis.get("reason", "")
            
            print(f"✅ SUCCÈS: Tâche normale créée")
            print(f"   Threat Level: {threat_level}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Reason: {reason}")
            
            # Nettoyage
            scheduler.cancel_task("test_normal_task")
            print("✅ Tâche de test nettoyée")
            return True
        else:
            print(f"❌ ÉCHEC: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_suspicious_task_creation():
    """Test la création d'une tâche suspecte"""
    print("\n" + "=" * 60)
    print("TEST 2: Création d'une tâche suspecte")
    print("=" * 60)
    
    try:
        from agents.scheduler.agent_scheduler_agent import AgentSchedulerAgent
        
        scheduler = AgentSchedulerAgent()
        
        # Tâche suspecte (agent non autorisé avec action suspecte)
        result = scheduler.schedule_task(
            task_data={
                "agent": "UnknownAgent",
                "action": "spam_loop_mass_bulk",
                "params": {
                    "target": "all_users",
                    "count": 99999
                }
            },
            execution_time=datetime.datetime.now() + datetime.timedelta(seconds=10),
            task_id="test_suspicious_task",
            recurring=True,
            recurrence_interval=1  # Toutes les secondes (suspect)
        )
        
        print(f"Résultat: {result}")
        
        # Cette tâche devrait être suspecte ou bloquée
        if result.get("status") == "blocked":
            print("✅ SUCCÈS: Tâche malveillante bloquée par le watchdog")
            return True
        elif result.get("status") == "success":
            security_analysis = result.get("security_analysis", {})
            threat_level = security_analysis.get("threat_level", "unknown")
            
            if threat_level in ["SUSPECT", "CRITICAL"]:
                print(f"✅ SUCCÈS: Tâche détectée comme {threat_level}")
                # Nettoyage
                scheduler.cancel_task("test_suspicious_task")
                return True
            else:
                print(f"⚠️  ATTENTION: Tâche suspecte non détectée (threat_level: {threat_level})")
                # Nettoyage
                scheduler.cancel_task("test_suspicious_task")
                return False
        else:
            print(f"❌ ÉCHEC: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_mass_task_creation():
    """Test la création en masse de tâches (doit être détectée)"""
    print("\n" + "=" * 60)
    print("TEST 3: Création en masse de tâches")
    print("=" * 60)
    
    try:
        from agents.scheduler.agent_scheduler_agent import AgentSchedulerAgent
        
        scheduler = AgentSchedulerAgent()
        
        # Création rapide de plusieurs tâches identiques
        results = []
        task_ids = []
        
        for i in range(5):
            result = scheduler.schedule_task(
                task_data={
                    "agent": "TestAgent",
                    "action": "rapid_execution",
                    "params": {"batch": i}
                },
                execution_time=datetime.datetime.now() + datetime.timedelta(minutes=i+1),
                task_id=f"test_mass_task_{i}",
                recurring=False
            )
            results.append(result)
            if result.get("status") == "success":
                task_ids.append(f"test_mass_task_{i}")
            
            print(f"Tâche {i+1}/5: {result.get('status')} - {result.get('security_analysis', {}).get('threat_level', 'unknown')}")
        
        # Analyser les résultats
        blocked_count = sum(1 for r in results if r.get("status") == "blocked")
        suspect_count = sum(1 for r in results if r.get("security_analysis", {}).get("threat_level") in ["SUSPECT", "CRITICAL"])
        
        print(f"\nRésultats:")
        print(f"  Tâches bloquées: {blocked_count}")
        print(f"  Tâches suspectes: {suspect_count}")
        print(f"  Tâches normales: {5 - blocked_count - suspect_count}")
        
        # Nettoyage
        for task_id in task_ids:
            scheduler.cancel_task(task_id)
        print("✅ Tâches de test nettoyées")
        
        # Le watchdog devrait détecter au moins quelques tâches comme suspectes
        if blocked_count > 0 or suspect_count > 2:
            print("✅ SUCCÈS: Pattern de masse détecté")
            return True
        else:
            print("⚠️  ATTENTION: Pattern de masse non détecté")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_watchdog_direct():
    """Test direct du TaskWatchdogAgent"""
    print("\n" + "=" * 60)
    print("TEST 4: Test direct du TaskWatchdogAgent")
    print("=" * 60)
    
    try:
        from agents.task_watchdog.task_watchdog_agent import TaskWatchdogAgent
        
        watchdog = TaskWatchdogAgent()
        
        # Test d'analyse d'une tâche normale
        normal_analysis = watchdog.run({
            "action": "analyze_new_task",
            "task_id": "test_direct_normal",
            "task_data": {
                "agent": "PivotStrategyAgent",
                "action": "recommend_optimizations"
            },
            "execution_time": "2025-05-27T18:00:00",
            "recurring": True,
            "recurrence_interval": 604800,
            "requesting_agent": "test_system"
        })
        
        print("Analyse tâche normale:")
        analysis = normal_analysis.get("analysis", {})
        print(f"  Threat Level: {analysis.get('threat_level', 'unknown')}")
        print(f"  Confidence: {analysis.get('confidence', 0):.2f}")
        print(f"  Reason: {analysis.get('reason', '')}")
        
        # Test d'analyse d'une tâche malveillante
        malicious_analysis = watchdog.run({
            "action": "analyze_new_task",
            "task_id": "test_direct_malicious",
            "task_data": {
                "agent": "EvilAgent",
                "action": "infinite_loop_spam"
            },
            "execution_time": "2025-05-27T13:00:00",
            "recurring": True,
            "recurrence_interval": 1,  # Toutes les secondes
            "requesting_agent": "unknown_source"
        })
        
        print("\nAnalyse tâche malveillante:")
        analysis = malicious_analysis.get("analysis", {})
        print(f"  Threat Level: {analysis.get('threat_level', 'unknown')}")
        print(f"  Confidence: {analysis.get('confidence', 0):.2f}")
        print(f"  Reason: {analysis.get('reason', '')}")
        
        # Vérifier les statistiques
        stats_result = watchdog.run({"action": "get_stats"})
        if stats_result.get("status") == "success":
            stats = stats_result.get("stats", {})
            print(f"\nStatistiques du watchdog:")
            print(f"  Total analyses: {stats.get('total_analyses', 0)}")
            print(f"  Menaces bloquées: {stats.get('threats_blocked', 0)}")
            print(f"  Patterns appris: {stats.get('patterns_learned', 0)}")
        
        # Valider les résultats
        normal_threat = normal_analysis.get("analysis", {}).get("threat_level", "")
        malicious_threat = malicious_analysis.get("analysis", {}).get("threat_level", "")
        
        if normal_threat == "NORMAL" and malicious_threat in ["SUSPECT", "CRITICAL"]:
            print("✅ SUCCÈS: Watchdog fonctionne correctement")
            return True
        else:
            print(f"❌ ÉCHEC: Résultats inattendus (normal: {normal_threat}, malicious: {malicious_threat})")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_watchdog_report():
    """Test la génération de rapport du watchdog"""
    print("\n" + "=" * 60)
    print("TEST 5: Génération de rapport de menaces")
    print("=" * 60)
    
    try:
        from agents.task_watchdog.task_watchdog_agent import TaskWatchdogAgent
        
        watchdog = TaskWatchdogAgent()
        
        # Génération du rapport
        report_result = watchdog.run({"action": "get_threat_report"})
        
        if report_result.get("status") == "success":
            print("✅ SUCCÈS: Rapport généré")
            print(f"Timestamp: {report_result.get('timestamp', 'unknown')}")
            
            stats = report_result.get("statistics", {})
            print(f"Statistiques:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            
            config = report_result.get("configuration", {})
            print(f"Configuration:")
            for key, value in config.items():
                print(f"  {key}: {value}")
            
            return True
        else:
            print(f"❌ ÉCHEC: {report_result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def run_all_tests():
    """Exécute tous les tests"""
    print("🛡️  TESTS D'INTÉGRATION DU TASKWATCHDOGAGENT")
    print(f"Exécution le: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Répertoire de travail: {os.getcwd()}")
    
    tests = [
        ("Tâche normale autorisée", test_normal_task_creation),
        ("Tâche suspecte détectée", test_suspicious_task_creation),
        ("Création en masse détectée", test_mass_task_creation),
        ("Fonctionnement direct watchdog", test_watchdog_direct),
        ("Génération de rapport", test_watchdog_report)
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
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS D'INTÉGRATION")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSÉ" if success else "❌ ÉCHEC"
        print(f"{status:12} {test_name}")
    
    print(f"\n📊 SCORE FINAL: {passed}/{total} tests passés ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 TASKWATCHDOGAGENT INTÉGRÉ AVEC SUCCÈS !")
        print("🛡️  Le système est maintenant protégé contre les tâches malveillantes")
    elif passed >= total * 0.8:
        print("✅ TaskWatchdogAgent majoritairement fonctionnel")
        print("⚠️  Quelques ajustements peuvent être nécessaires")
    else:
        print("⚠️  Problèmes d'intégration détectés")
        print("🔧 Vérification et correction requises")
    
    return passed, total

if __name__ == "__main__":
    # Aller dans le bon répertoire
    os.chdir(Path(__file__).parent.parent)
    
    passed, total = run_all_tests()
    
    # Code de sortie pour intégration dans scripts
    exit_code = 0 if passed == total else 1
    sys.exit(exit_code)

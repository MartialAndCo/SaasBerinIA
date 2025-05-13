"""
Test de la rotation des fichiers de logs.

Ce script génère un grand nombre de messages de log pour tester
la fonctionnalité de rotation basée sur la taille.
"""
import sys
import os
import time

# Ajouter le répertoire parent au chemin Python pour pouvoir importer utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging_config import setup_logging

def test_log_rotation():
    """Génère des logs pour tester la rotation."""
    # Configurer un logger de test
    logger = setup_logging('test_rotation')
    
    print("Test de rotation des logs en cours...")
    print("Vérifiez le dossier logs/ pour voir les fichiers créés")
    
    # Générer suffisamment de logs pour déclencher plusieurs rotations
    for i in range(5000):  # Devrait générer ~5 fichiers de rotation
        logger.info(f"Message de test {i} : " + "X" * 100)  # Message long pour remplir rapidement
        
        # Afficher la progression
        if i % 500 == 0:
            print(f"Génération de {i} messages...")
            
        # Pause brève pour ne pas surcharger le système
        if i % 100 == 0:
            time.sleep(0.01)
    
    print("Test terminé ! Vérifiez les fichiers de logs")
    print("Organisation des fichiers attendue:")
    print("- logs/test_rotation.log (fichier actif)")
    print("- logs/archives/test_rotation.log.1 (première rotation)")
    print("- logs/archives/test_rotation.log.2 (deuxième rotation)")
    print("- etc. jusqu'à logs/archives/test_rotation.log.5")

if __name__ == "__main__":
    test_log_rotation()

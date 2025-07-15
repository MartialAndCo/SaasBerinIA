#!/usr/bin/env python3
"""
Script de nettoyage des logs de la base de données BerinIA
Supprime les logs plus anciens que 7 jours de toutes les tables de logs
"""

import psycopg2
import sys
from datetime import datetime, timedelta
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/berinia-db-cleanup.log'),
        logging.StreamHandler()
    ]
)

def cleanup_database_logs():
    """Nettoie les logs anciens de la base de données"""
    try:
        # Connexion à la base de données
        conn = psycopg2.connect('postgresql://berinia_user:berinia_pass@localhost/berinia')
        cur = conn.cursor()
        
        # Date limite (7 jours)
        cutoff_date = datetime.now() - timedelta(days=7)
        logging.info(f"Suppression des logs antérieurs à {cutoff_date}")
        
        # Tables de logs à nettoyer
        log_tables = [
            ('system_logs', 'timestamp'),
            ('agent_logs', 'timestamp'), 
            ('logs', 'timestamp')
        ]
        
        total_deleted = 0
        
        for table_name, timestamp_column in log_tables:
            try:
                # Vérifier le nombre de logs avant suppression
                cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {timestamp_column} < %s", (cutoff_date,))
                count_to_delete = cur.fetchone()[0]
                
                if count_to_delete > 0:
                    # Supprimer les logs anciens
                    cur.execute(f"DELETE FROM {table_name} WHERE {timestamp_column} < %s", (cutoff_date,))
                    deleted = cur.rowcount
                    total_deleted += deleted
                    
                    logging.info(f"Table {table_name}: {deleted} logs supprimés")
                else:
                    logging.info(f"Table {table_name}: aucun log ancien à supprimer")
                    
                # Vérifier le nombre restant
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                remaining = cur.fetchone()[0]
                logging.info(f"Table {table_name}: {remaining} logs restants")
                
            except Exception as e:
                logging.error(f"Erreur lors du nettoyage de {table_name}: {e}")
                conn.rollback()
                continue
        
        # Valider les suppressions
        conn.commit()
        logging.info(f"Nettoyage terminé. Total supprimé: {total_deleted} logs")
        
        cur.close()
        conn.close()
        
        # Optimiser les tables après suppression (nouvelle connexion pour VACUUM)
        if total_deleted > 0:
            try:
                conn = psycopg2.connect('postgresql://berinia_user:berinia_pass@localhost/berinia')
                conn.autocommit = True  # VACUUM nécessite autocommit
                cur = conn.cursor()
                
                for table_name, _ in log_tables:
                    try:
                        cur.execute(f"VACUUM ANALYZE {table_name}")
                        logging.info(f"Table {table_name} optimisée")
                    except Exception as e:
                        logging.warning(f"Impossible d'optimiser {table_name}: {e}")
                
                cur.close()
                conn.close()
                
            except Exception as e:
                logging.warning(f"Erreur lors de l'optimisation: {e}")
        
        return total_deleted
        
    except Exception as e:
        logging.error(f"Erreur lors du nettoyage de la base de données: {e}")
        return -1

def main():
    """Fonction principale"""
    logging.info("=== Début du nettoyage des logs de la base de données ===")
    
    result = cleanup_database_logs()
    
    if result >= 0:
        logging.info(f"=== Nettoyage terminé avec succès. {result} logs supprimés ===")
        sys.exit(0)
    else:
        logging.error("=== Nettoyage échoué ===")
        sys.exit(1)

if __name__ == "__main__":
    main()

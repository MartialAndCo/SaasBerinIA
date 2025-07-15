#!/usr/bin/env python3
"""
Script d'optimisation et nettoyage intelligent des logs BerinIA
- Reclassifie les erreurs mal étiquetées
- Supprime les messages répétitifs/spam
- Applique un nettoyage plus agressif
"""

import psycopg2
import sys
from datetime import datetime, timedelta
import logging
import re

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/berinia-logs-optimization.log'),
        logging.StreamHandler()
    ]
)

def reclassify_misclassified_logs():
    """Reclassifie les logs INFO qui sont en réalité des erreurs"""
    try:
        conn = psycopg2.connect('postgresql://berinia_user:berinia_pass@localhost/berinia')
        cur = conn.cursor()
        
        # Patterns d'erreurs à reclassifier
        error_patterns = [
            "erreur", "error", "échec", "failed", "exception", 
            "404", "500", "timeout", "connection refused",
            "impossible de", "cannot", "not found"
        ]
        
        total_reclassified = 0
        
        for pattern in error_patterns:
            # Reclassifier les logs INFO contenant des erreurs
            cur.execute("""
                UPDATE system_logs 
                SET level = 'ERROR' 
                WHERE level = 'INFO' 
                AND (message ILIKE %s OR details::text ILIKE %s)
                AND level != 'ERROR'
            """, (f'%{pattern}%', f'%{pattern}%'))
            
            reclassified = cur.rowcount
            total_reclassified += reclassified
            
            if reclassified > 0:
                logging.info(f"Reclassifié {reclassified} logs contenant '{pattern}'")
        
        conn.commit()
        logging.info(f"Total reclassifié: {total_reclassified} logs")
        
        cur.close()
        conn.close()
        
        return total_reclassified
        
    except Exception as e:
        logging.error(f"Erreur lors de la reclassification: {e}")
        return -1

def remove_spam_logs():
    """Supprime les logs répétitifs/spam"""
    try:
        conn = psycopg2.connect('postgresql://berinia_user:berinia_pass@localhost/berinia')
        cur = conn.cursor()
        
        # Patterns de messages spam à supprimer
        spam_patterns = [
            "Configuration de personnalité chargée",
            "Configuration globale chargée",
            "Configuration Twilio:",
            "Client Instantly.ai initialisé",
            "MessagingAgent configuré en mode",
            "surveillance automatique des leads activée"
        ]
        
        total_removed = 0
        
        for pattern in spam_patterns:
            # Garder seulement 1 occurrence par jour de ces messages
            cur.execute("""
                DELETE FROM system_logs 
                WHERE id NOT IN (
                    SELECT DISTINCT ON (DATE(timestamp)) id
                    FROM system_logs 
                    WHERE message ILIKE %s
                    ORDER BY DATE(timestamp), timestamp ASC
                )
                AND message ILIKE %s
            """, (f'%{pattern}%', f'%{pattern}%'))
            
            removed = cur.rowcount
            total_removed += removed
            
            if removed > 0:
                logging.info(f"Supprimé {removed} logs spam: '{pattern}'")
        
        # Supprimer les doublons exacts (même message, même agent, même minute)
        cur.execute("""
            DELETE FROM system_logs 
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM system_logs 
                GROUP BY agent_name, message, DATE_TRUNC('minute', timestamp)
            )
        """)
        
        duplicates_removed = cur.rowcount
        total_removed += duplicates_removed
        
        if duplicates_removed > 0:
            logging.info(f"Supprimé {duplicates_removed} doublons exacts")
        
        conn.commit()
        logging.info(f"Total supprimé: {total_removed} logs spam/doublons")
        
        cur.close()
        conn.close()
        
        return total_removed
        
    except Exception as e:
        logging.error(f"Erreur lors de la suppression du spam: {e}")
        return -1

def aggressive_cleanup():
    """Nettoyage agressif selon des critères intelligents"""
    try:
        conn = psycopg2.connect('postgresql://berinia_user:berinia_pass@localhost/berinia')
        cur = conn.cursor()
        
        total_removed = 0
        
        # Supprimer les logs INFO de plus de 3 jours (au lieu de 7)
        cur.execute("""
            DELETE FROM system_logs 
            WHERE level = 'INFO' 
            AND timestamp < NOW() - INTERVAL '3 days'
        """)
        
        info_removed = cur.rowcount
        total_removed += info_removed
        logging.info(f"Supprimé {info_removed} logs INFO de plus de 3 jours")
        
        # Garder seulement les ERROR de moins de 2 semaines
        cur.execute("""
            DELETE FROM system_logs 
            WHERE level = 'ERROR' 
            AND timestamp < NOW() - INTERVAL '2 weeks'
        """)
        
        error_removed = cur.rowcount
        total_removed += error_removed
        logging.info(f"Supprimé {error_removed} logs ERROR de plus de 2 semaines")
        
        # Supprimer les logs de debug/verbeux des agents trop bavards
        verbose_patterns = [
            "Configuration chargée",
            "Client initialisé", 
            "Mode de fonctionnement",
            "Surveillance activée",
            "État de l'agent"
        ]
        
        for pattern in verbose_patterns:
            # Garder seulement les 10 plus récents par agent
            cur.execute("""
                DELETE FROM system_logs 
                WHERE id NOT IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (
                            PARTITION BY agent_name 
                            ORDER BY timestamp DESC
                        ) as rn
                        FROM system_logs 
                        WHERE message ILIKE %s
                    ) ranked 
                    WHERE ranked.rn <= 10
                )
                AND message ILIKE %s
            """, (f'%{pattern}%', f'%{pattern}%'))
            
            verbose_removed = cur.rowcount
            total_removed += verbose_removed
            
            if verbose_removed > 0:
                logging.info(f"Supprimé {verbose_removed} logs verbeux: '{pattern}'")
        
        conn.commit()
        logging.info(f"Nettoyage agressif terminé: {total_removed} logs supprimés")
        
        cur.close()
        conn.close()
        
        return total_removed
        
    except Exception as e:
        logging.error(f"Erreur lors du nettoyage agressif: {e}")
        return -1

def get_logs_summary():
    """Affiche un résumé des logs après optimisation"""
    try:
        conn = psycopg2.connect('postgresql://berinia_user:berinia_pass@localhost/berinia')
        cur = conn.cursor()
        
        # Total par niveau
        cur.execute("SELECT level, COUNT(*) FROM system_logs GROUP BY level ORDER BY COUNT(*) DESC")
        levels = cur.fetchall()
        
        logging.info("=== RÉSUMÉ APRÈS OPTIMISATION ===")
        total = sum(count for _, count in levels)
        logging.info(f"Total des logs: {total}")
        
        for level, count in levels:
            percentage = (count / total * 100) if total > 0 else 0
            logging.info(f"  {level}: {count} ({percentage:.1f}%)")
        
        # Top agents
        cur.execute("""
            SELECT agent_name, COUNT(*) 
            FROM system_logs 
            GROUP BY agent_name 
            ORDER BY COUNT(*) DESC 
            LIMIT 5
        """)
        top_agents = cur.fetchall()
        
        logging.info("Top 5 agents:")
        for agent, count in top_agents:
            logging.info(f"  {agent}: {count} logs")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logging.error(f"Erreur lors du résumé: {e}")

def main():
    """Fonction principale d'optimisation"""
    logging.info("=== DÉBUT DE L'OPTIMISATION DES LOGS ===")
    
    # 1. Reclassifier les erreurs
    reclassified = reclassify_misclassified_logs()
    
    # 2. Supprimer le spam
    spam_removed = remove_spam_logs()
    
    # 3. Nettoyage agressif
    aggressive_removed = aggressive_cleanup()
    
    # 4. Résumé
    get_logs_summary()
    
    total_changes = (reclassified if reclassified > 0 else 0) + \
                   (spam_removed if spam_removed > 0 else 0) + \
                   (aggressive_removed if aggressive_removed > 0 else 0)
    
    logging.info(f"=== OPTIMISATION TERMINÉE: {total_changes} modifications ===")
    
    if total_changes > 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

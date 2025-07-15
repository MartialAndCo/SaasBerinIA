#!/bin/bash

# Script de nettoyage automatique des logs système BerinIA
# À exécuter régulièrement via cron

LOG_FILE="/var/log/berinia-cleanup.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Début du nettoyage des logs" >> "$LOG_FILE"

# Nettoyage des logs journald plus anciens que 7 jours
echo "[$DATE] Nettoyage des logs journald..." >> "$LOG_FILE"
CLEANED=$(sudo journalctl --vacuum-time=7d 2>&1)
echo "[$DATE] Résultat: $CLEANED" >> "$LOG_FILE"

# Vérification de l'espace disque utilisé par les logs
echo "[$DATE] Vérification de l'espace disque..." >> "$LOG_FILE"
DISK_USAGE=$(journalctl --disk-usage 2>&1)
echo "[$DATE] Usage actuel: $DISK_USAGE" >> "$LOG_FILE"

# Nettoyage des logs applicatifs BerinIA si ils existent
if [ -d "/root/berinia/logs" ]; then
    echo "[$DATE] Nettoyage des logs applicatifs BerinIA..." >> "$LOG_FILE"
    find /root/berinia/logs -name "*.log" -mtime +7 -delete 2>&1 >> "$LOG_FILE"
fi

# Nettoyage des logs de l'infra-ia si ils existent
if [ -d "/root/berinia/infra-ia/logs" ]; then
    echo "[$DATE] Nettoyage des logs infra-ia..." >> "$LOG_FILE"
    find /root/berinia/infra-ia/logs -name "*.log" -mtime +7 -delete 2>&1 >> "$LOG_FILE"
fi

# Nettoyage et optimisation des logs de la base de données PostgreSQL
echo "[$DATE] Nettoyage des logs de la base de données..." >> "$LOG_FILE"
cd /root/berinia/backend && source venv/bin/activate && python cleanup_database_logs.py >> "$LOG_FILE" 2>&1
DB_CLEANUP_STATUS=$?
if [ $DB_CLEANUP_STATUS -eq 0 ]; then
    echo "[$DATE] Nettoyage de la base de données terminé avec succès" >> "$LOG_FILE"
else
    echo "[$DATE] ERREUR lors du nettoyage de la base de données (code: $DB_CLEANUP_STATUS)" >> "$LOG_FILE"
fi

# Optimisation intelligente des logs (reclassification + suppression spam)
echo "[$DATE] Optimisation intelligente des logs..." >> "$LOG_FILE"
cd /root/berinia/backend && source venv/bin/activate && python optimize_logs.py >> "$LOG_FILE" 2>&1
OPT_STATUS=$?
if [ $OPT_STATUS -eq 0 ]; then
    echo "[$DATE] Optimisation des logs terminée avec succès" >> "$LOG_FILE"
else
    echo "[$DATE] ERREUR lors de l'optimisation des logs (code: $OPT_STATUS)" >> "$LOG_FILE"
fi

echo "[$DATE] Fin du nettoyage des logs" >> "$LOG_FILE"
echo "[$DATE] =====================================" >> "$LOG_FILE"

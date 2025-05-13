#!/bin/bash
# Script pour appliquer la migration d'analyse visuelle à la base de données BerinIA

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== APPLICATION DE LA MIGRATION D'ANALYSE VISUELLE ===${NC}"

# Vérification que l'utilisateur a les droits sudo
if [ "$(id -u)" != "0" ]; then
   echo -e "${RED}Ce script doit être exécuté avec les droits sudo${NC}" 1>&2
   exit 1
fi

# Exécution du script SQL de migration
echo -e "${YELLOW}Exécution de la migration pour ajouter les champs d'analyse visuelle...${NC}"
# Créer une copie dans /tmp pour résoudre les problèmes de permission
cp "$(dirname "$0")/migrations/add_visual_analysis_fields.sql" /tmp/add_visual_analysis_fields.sql
chmod 777 /tmp/add_visual_analysis_fields.sql
sudo -u postgres psql -d berinia -f /tmp/add_visual_analysis_fields.sql

# Attribution des droits sur les nouvelles colonnes
echo -e "${YELLOW}Attribution des droits sur les nouvelles colonnes...${NC}"
sudo -u postgres psql -d berinia -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO berinia_user;"
sudo -u postgres psql -d berinia -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO berinia_user;"

echo -e "${GREEN}=== MIGRATION D'ANALYSE VISUELLE APPLIQUÉE AVEC SUCCÈS ===${NC}"
echo -e "${GREEN}La table 'leads' a été mise à jour avec les champs d'analyse visuelle${NC}"

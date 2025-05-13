#!/bin/bash
# Script pour recréer entièrement la base de données BerinIA
# Ce script supprime et recrée la base de données et exécute le script SQL d'initialisation

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== RECRÉATION DE LA BASE DE DONNÉES BERINIA ===${NC}"

# Vérification que l'utilisateur a les droits sudo
if [ "$(id -u)" != "0" ]; then
   echo -e "${RED}Ce script doit être exécuté avec les droits sudo${NC}" 1>&2
   exit 1
fi

# 1. Suppression des connexions actives à la base de données
echo -e "${YELLOW}Suppression des connexions actives à la base de données...${NC}"
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='berinia';"

# 2. Suppression de la base de données existante
echo -e "${YELLOW}Suppression de la base de données 'berinia' si elle existe...${NC}"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS berinia;"

# 3. Recréation de la base de données
echo -e "${YELLOW}Création d'une nouvelle base de données 'berinia'...${NC}"
sudo -u postgres psql -c "CREATE DATABASE berinia;"

# 4. Gestion des utilisateurs de la base de données
echo -e "${YELLOW}Vérification de l'existence de l'utilisateur 'berinia_user'...${NC}"
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='berinia_user'")

if [ "$USER_EXISTS" != "1" ]; then
    echo -e "${YELLOW}Création de l'utilisateur 'berinia_user'...${NC}"
    sudo -u postgres psql -c "CREATE USER berinia_user WITH PASSWORD 'berinia_pass';"
else
    echo -e "${YELLOW}L'utilisateur 'berinia_user' existe déjà${NC}"
fi

# 5. Attribution des droits sur la base de données
echo -e "${YELLOW}Attribution des droits à l'utilisateur 'berinia_user'...${NC}"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE berinia TO berinia_user;"
sudo -u postgres psql -c "ALTER USER berinia_user WITH SUPERUSER;"

# 6. Exécution du script SQL d'initialisation
echo -e "${YELLOW}Exécution du script SQL d'initialisation...${NC}"
# Créer une copie dans /tmp pour résoudre les problèmes de permission
cp "$(dirname "$0")/migrations/create_berinia_db.sql" /tmp/create_berinia_db.sql
chmod 777 /tmp/create_berinia_db.sql
sudo -u postgres psql -d berinia -f /tmp/create_berinia_db.sql

# 7. Attribution des droits sur les tables
echo -e "${YELLOW}Attribution des droits sur les tables...${NC}"
sudo -u postgres psql -d berinia -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO berinia_user;"
sudo -u postgres psql -d berinia -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO berinia_user;"

echo -e "${GREEN}=== BASE DE DONNÉES BERINIA RECRÉÉE AVEC SUCCÈS ===${NC}"
echo -e "${GREEN}La base 'berinia' est prête à être utilisée avec le système BerinIA${NC}"

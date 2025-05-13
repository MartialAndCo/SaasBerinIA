#!/bin/bash
# Script de configuration de l'environnement virtuel pour BerinIA

# Couleurs pour le terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Fonction pour afficher des bannières
print_banner() {
    echo -e "\n${BLUE}${BOLD}$1${NC}\n"
    echo -e "${BLUE}${BOLD}$(printf '=%.0s' {1..50})${NC}\n"
}

# Fonction pour afficher les étapes
print_step() {
    echo -e "${YELLOW}${BOLD}[ÉTAPE]${NC} $1"
}

# Fonction pour afficher les succès
print_success() {
    echo -e "${GREEN}${BOLD}[OK]${NC} $1"
}

# Fonction pour afficher les erreurs
print_error() {
    echo -e "${RED}${BOLD}[ERREUR]${NC} $1"
}

# Bannière de début
print_banner "Configuration de l'environnement BerinIA"
echo -e "Ce script va configurer l'environnement virtuel pour BerinIA\n"

# Vérification de Python
print_step "Vérification de Python..."
PYTHON_VERSION=$(python3 --version 2>&1)

if [ $? -ne 0 ]; then
    print_error "Python 3 n'est pas installé ou n'est pas disponible via la commande 'python3'"
    echo -e "${BOLD}Veuillez installer Python 3.8 ou supérieur${NC}"
    exit 1
fi

echo -e "Version détectée: ${BLUE}$PYTHON_VERSION${NC}"

# Vérification de la version minimale (3.8)
PYTHON_VERSION_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_VERSION_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_VERSION_MAJOR" -lt 3 ] || ([ "$PYTHON_VERSION_MAJOR" -eq 3 ] && [ "$PYTHON_VERSION_MINOR" -lt 8 ]); then
    print_error "BerinIA nécessite Python 3.8 ou supérieur"
    echo -e "Votre version: ${RED}Python $PYTHON_VERSION_MAJOR.$PYTHON_VERSION_MINOR${NC}"
    exit 1
fi

print_success "Python $PYTHON_VERSION_MAJOR.$PYTHON_VERSION_MINOR détecté"

# Création de l'environnement virtuel
print_step "Création de l'environnement virtuel..."

# Vérification si .venv existe déjà
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Un environnement virtuel existe déjà (.venv)${NC}"
    read -p "Voulez-vous le supprimer et en créer un nouveau ? (o/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        print_step "Suppression de l'environnement virtuel existant..."
        rm -rf .venv
    else
        print_step "Utilisation de l'environnement virtuel existant..."
    fi
fi

# Création d'un nouvel environnement si nécessaire
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        print_error "Impossible de créer l'environnement virtuel"
        echo -e "Essayez d'installer venv: ${BOLD}pip install virtualenv${NC}"
        exit 1
    fi
    print_success "Environnement virtuel créé dans .venv"
fi

# Activation de l'environnement virtuel
print_step "Activation de l'environnement virtuel..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    print_error "Impossible d'activer l'environnement virtuel"
    exit 1
fi
print_success "Environnement virtuel activé"

# Installation des dépendances
print_step "Installation des dépendances..."
if [ ! -f "requirements.txt" ]; then
    print_error "Le fichier requirements.txt n'a pas été trouvé"
    exit 1
fi

pip install --upgrade pip
print_success "Pip mis à jour"

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Impossible d'installer les dépendances"
    echo -e "Consultez les erreurs ci-dessus pour plus de détails"
    exit 1
fi
print_success "Dépendances installées avec succès"

# Création des répertoires nécessaires
print_step "Création des répertoires nécessaires..."
mkdir -p logs data db
print_success "Répertoires créés"

# Vérification du fichier .env
print_step "Vérification du fichier .env..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Le fichier .env n'existe pas${NC}"
    echo -e "Création d'un exemple de fichier .env..."
    
    cat > .env.example << 'EOL'
# Fichier de configuration BerinIA - Copiez ce fichier vers .env et personnalisez-le

# Configuration OpenAI (REQUIS)
OPENAI_API_KEY=sk-votrecleopenai

# Configuration Qdrant (OPTIONNEL)
QDRANT_URL=http://localhost:6333

# Configuration Mailgun (OPTIONNEL)
MAILGUN_API_KEY=key-votreclémailgun
MAILGUN_DOMAIN=mail.berinia.ai

# Configuration Twilio (OPTIONNEL)
TWILIO_SID=votre_sid_twilio
TWILIO_TOKEN=votre_token_twilio
TWILIO_PHONE=+33600000000

# Configuration de la base de données (OPTIONNEL)
DATABASE_URL=sqlite:///db/berinia.db

# Autres configurations
LOG_LEVEL=INFO
DEBUG=false
EOL
    
    echo -e "${YELLOW}Un exemple de fichier .env a été créé sous le nom .env.example${NC}"
    echo -e "Veuillez copier ce fichier vers .env et le configurer avec vos propres clés API :"
    echo -e "${BOLD}cp .env.example .env${NC}"
else
    print_success "Fichier .env trouvé"
    
    # Vérification de la clé OpenAI
    if ! grep -q "OPENAI_API_KEY" .env; then
        print_error "La clé OPENAI_API_KEY n'est pas définie dans le fichier .env"
        echo -e "Ajoutez la ligne ${BOLD}OPENAI_API_KEY=sk-votrecleopenai${NC} au fichier .env"
    else
        print_success "Configuration OPENAI_API_KEY trouvée"
    fi
fi

# Rendre les scripts exécutables
print_step "Préparation des scripts..."
chmod +x init_system.py interact.py webhook/run_webhook.py verify_installation.py

# Invitation à vérifier l'installation
print_banner "Installation terminée avec succès"
echo -e "Pour vérifier l'installation :"
echo -e "${BOLD}python verify_installation.py${NC}"
echo
echo -e "Pour démarrer BerinIA en mode interactif :"
echo -e "${BOLD}python interact.py${NC}"
echo
echo -e "Pour démarrer le serveur webhook :"
echo -e "${BOLD}python webhook/run_webhook.py${NC}"
echo
echo -e "${YELLOW}${BOLD}IMPORTANT :${NC} N'oubliez pas de configurer le fichier .env avec vos clés API"
echo -e "Pour réactiver l'environnement dans une nouvelle session :"
echo -e "${BOLD}source .venv/bin/activate${NC}"

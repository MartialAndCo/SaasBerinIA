#!/bin/bash
# Script d'installation pour l'intégration WhatsApp BerinIA

# Fonction pour afficher les messages avec couleur
print_message() {
  echo -e "\e[1;34m>> $1\e[0m"
}

print_error() {
  echo -e "\e[1;31m>> ERREUR: $1\e[0m"
}

print_success() {
  echo -e "\e[1;32m>> SUCCÈS: $1\e[0m"
}

# Vérification des prérequis
print_message "Vérification des prérequis..."

# Vérifier que Node.js est installé
if ! command -v node &> /dev/null; then
  print_error "Node.js n'est pas installé. Veuillez l'installer avant de continuer."
  exit 1
fi

NODE_VERSION=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
if [ "$NODE_VERSION" -lt 14 ]; then
  print_error "Node.js v14 ou supérieur est requis. Version détectée: $(node -v)"
  exit 1
fi

print_success "Node.js v$(node -v) détecté"

# Créer le répertoire de logs
print_message "Création du répertoire de logs..."
mkdir -p /root/berinia/whatsapp-bot/logs
print_success "Répertoire de logs créé"

# Installation des dépendances avec pnpm
print_message "Installation des dépendances Node.js avec pnpm..."
cd /root/berinia/whatsapp-bot
pnpm install

if [ $? -ne 0 ]; then
  print_error "Échec de l'installation des dépendances"
  exit 1
fi

print_success "Dépendances installées avec succès"

# Configuration du service systemd
print_message "Configuration du service systemd..."

if [ -f /etc/systemd/system/berinia-whatsapp.service ]; then
  print_message "Le service systemd existe déjà, arrêt du service..."
  systemctl stop berinia-whatsapp.service
fi

cp /root/berinia/whatsapp-bot/berinia-whatsapp.service /etc/systemd/system/

if [ $? -ne 0 ]; then
  print_error "Échec de la copie du fichier de service"
  exit 1
fi

print_success "Fichier de service copié"

# Actualisation de systemd
print_message "Actualisation de systemd..."
systemctl daemon-reload

# Activation du service
print_message "Activation du service au démarrage..."
systemctl enable berinia-whatsapp.service

if [ $? -ne 0 ]; then
  print_error "Échec de l'activation du service"
  exit 1
fi

print_success "Service activé avec succès"

# Démarrage du service
print_message "Démarrage du service..."
systemctl start berinia-whatsapp.service

if [ $? -ne 0 ]; then
  print_error "Échec du démarrage du service"
  exit 1
fi

print_success "Service démarré avec succès"

# Affichage des logs pour permettre de scanner le QR code
print_message "Le service est maintenant démarré!"
print_message "Pour voir le QR code à scanner, exécutez:"
echo "    sudo journalctl -f -u berinia-whatsapp.service"
print_message "Instructions après avoir scanné le QR code:"
echo "1. Créez une communauté WhatsApp nommée 'BerinIA'"
echo "2. Créez les groupes spécifiés dans le README.md dans cette communauté"
echo "3. Redémarrez le service: sudo systemctl restart berinia-whatsapp.service"
echo ""
print_success "Installation terminée!"

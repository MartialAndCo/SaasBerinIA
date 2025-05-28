#!/usr/bin/env python3
"""
Script pour appliquer les correctifs à l'API principale de BerinIA.
Ce script modifie la façon dont l'API se connecte à la base de données
pour résoudre les problèmes d'authentification.
"""
import os
import sys
import shutil
import datetime
import time
from pathlib import Path
from dotenv import load_dotenv

# Chemin du backend
BACKEND_DIR = Path("/root/berinia/backend")

# Chemins des fichiers à modifier
APP_MAIN_PATH = BACKEND_DIR / "app" / "main.py"
DATABASE_SESSION_PATH = BACKEND_DIR / "app" / "database" / "session.py"
API_SERVICE_PATH = BACKEND_DIR / "berinia.service"

# Charger les variables d'environnement
load_dotenv(BACKEND_DIR / ".env")

# Configuration de la base de données
db_user = os.getenv("DB_USER", "berinia_user")
db_password = os.getenv("DB_PASSWORD", "berinia_pass")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "berinia")

# URL de connexion SQLAlchemy
DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def backup_file(file_path):
    """Créer une sauvegarde du fichier."""
    if file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + f".bak.{int(time.time())}")
        shutil.copy2(file_path, backup_path)
        print(f"✅ Sauvegarde créée: {backup_path}")
        return True
    else:
        print(f"❌ Le fichier {file_path} n'existe pas. Impossible de créer une sauvegarde.")
        return False

def fix_database_session():
    """
    Modifier le fichier session.py pour utiliser la bonne URL de connexion.
    """
    if not DATABASE_SESSION_PATH.exists():
        print(f"❌ Le fichier {DATABASE_SESSION_PATH} n'existe pas.")
        return False
    
    # Créer une sauvegarde
    if not backup_file(DATABASE_SESSION_PATH):
        return False
    
    # Lire le contenu actuel du fichier
    with open(DATABASE_SESSION_PATH, 'r') as f:
        content = f.read()
    
    # Remplacer l'URL de connexion dans le fichier
    new_content = f"""from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Use the settings from config.py instead of hardcoded values
# Mais on s'assure que l'URL est bien construite avec les bonnes valeurs
SQLALCHEMY_DATABASE_URL = "{DATABASE_URL}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""
    
    # Écrire le nouveau contenu
    with open(DATABASE_SESSION_PATH, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Fichier {DATABASE_SESSION_PATH} modifié avec succès.")
    return True

def ensure_service_file():
    """
    S'assurer que le fichier de service systemd existe et est correctement configuré.
    """
    service_content = f"""[Unit]
Description=BerinIA API Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
User=root
Group=root
WorkingDirectory={BACKEND_DIR}
ExecStart={BACKEND_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10
Environment="PATH={BACKEND_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="DATABASE_URL={DATABASE_URL}"
Environment="PYTHONPATH={BACKEND_DIR}"

[Install]
WantedBy=multi-user.target
"""
    
    # Créer une sauvegarde si le fichier existe
    if API_SERVICE_PATH.exists():
        backup_file(API_SERVICE_PATH)
    
    # Écrire le nouveau contenu
    with open(API_SERVICE_PATH, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Fichier de service {API_SERVICE_PATH} créé/mis à jour.")
    return True

def install_service_file():
    """
    Installer le fichier de service dans systemd.
    """
    # Copier le fichier de service vers /etc/systemd/system/
    try:
        shutil.copy2(API_SERVICE_PATH, "/etc/systemd/system/berinia-api.service")
        print(f"✅ Fichier de service copié vers /etc/systemd/system/berinia-api.service")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la copie du fichier de service: {str(e)}")
        print("⚠️ Vous devez exécuter ce script avec sudo pour installer le service.")
        return False

def main():
    """
    Fonction principale qui exécute tous les correctifs.
    """
    print("=== Application des correctifs à l'API BerinIA ===\n")
    
    # Vérifier que le script est exécuté en tant que root
    if os.geteuid() != 0:
        print("⚠️ Ce script doit être exécuté avec des privilèges root (sudo).")
        print("⚠️ Certaines opérations peuvent échouer.")
    
    # Modifier le fichier session.py
    if not fix_database_session():
        print("❌ Échec de la modification du fichier session.py")
        return False
    
    # Créer le fichier de service
    if not ensure_service_file():
        print("❌ Échec de la création du fichier de service")
        return False
    
    # Installer le fichier de service
    if os.geteuid() == 0:  # Seulement si on est root
        if not install_service_file():
            print("❌ Échec de l'installation du fichier de service")
            return False
        
        # Recharger les services systemd
        os.system("systemctl daemon-reload")
        print("✅ Services systemd rechargés")
        
        # Activer le service
        os.system("systemctl enable berinia-api.service")
        print("✅ Service berinia-api activé")
    else:
        print("\n⚠️ Pour installer le service, exécutez les commandes suivantes avec sudo:")
        print(f"   sudo cp {API_SERVICE_PATH} /etc/systemd/system/berinia-api.service")
        print("   sudo systemctl daemon-reload")
        print("   sudo systemctl enable berinia-api.service")
    
    print("\n✅ Tous les correctifs ont été appliqués avec succès!")
    print("🚀 Vous pouvez maintenant démarrer les services:")
    print("   sudo systemctl start berinia-api.service")
    print("   sudo systemctl start berinia-agents.service")
    print("   sudo systemctl start berinia-scheduler.service")
    print("\n📋 Pour vérifier leur statut:")
    print("   sudo systemctl status berinia-api.service")
    print("   sudo systemctl status berinia-agents.service")
    print("   sudo systemctl status berinia-scheduler.service")
    
    return True

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script pour réinitialiser et tester le mot de passe de la base de données.
"""
import os
import sys
import subprocess
import time
from dotenv import load_dotenv

# Chemin absolu du répertoire actuel (backend)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Charger les variables d'environnement
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

# Obtenir les paramètres de la base de données depuis les variables d'environnement
db_user = os.getenv("DB_USER", "berinia_user")
db_password = os.getenv("DB_PASSWORD", "berinia_pass")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "berinia")

print(f"Configuration actuelle:")
print(f"- User: {db_user}")
print(f"- Password: {'*****' + db_password[-2:] if db_password else 'Non défini'}")
print(f"- Host: {db_host}")
print(f"- Port: {db_port}")
print(f"- Database: {db_name}")
print("\n")

# Réinitialiser le mot de passe PostgreSQL
def reset_postgres_password():
    print("Réinitialisation du mot de passe PostgreSQL...")
    try:
        # Modifier le mot de passe avec psql
        cmd = f"sudo -u postgres psql -c \"ALTER USER {db_user} WITH PASSWORD '{db_password}';\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Mot de passe PostgreSQL réinitialisé avec succès pour l'utilisateur {db_user}")
        else:
            print(f"❌ Erreur lors de la réinitialisation du mot de passe PostgreSQL: {result.stderr}")
            return False
            
        # Vérifier la connexion avec psql
        cmd = f"PGPASSWORD={db_password} psql -h {db_host} -U {db_user} -d {db_name} -c \"SELECT 1 AS test;\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Test de connexion psql réussi")
        else:
            print(f"❌ Échec du test de connexion psql: {result.stderr}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la réinitialisation du mot de passe: {str(e)}")
        return False

# Tester la connexion à la base de données avec psycopg2 directement
def test_psycopg2_connection():
    try:
        import psycopg2
        print("Test de connexion avec psycopg2...")
        
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS test")
        row = cursor.fetchone()
        
        if row and row[0] == 1:
            print(f"✅ Connexion psycopg2 réussie")
            return True
        else:
            print(f"❌ Connexion psycopg2 échouée: pas de données retournées")
            return False
            
    except ImportError:
        print("❌ Module psycopg2 non trouvé. Installation en cours...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], check=True)
        print("📦 Module psycopg2-binary installé. Relancez le script.")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la connexion avec psycopg2: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# Tester la connexion avec SQLAlchemy
def test_sqlalchemy_connection():
    try:
        from sqlalchemy import create_engine, text
        print("Test de connexion avec SQLAlchemy...")
        
        # Construire l'URL de connexion
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Créer l'engine
        engine = create_engine(db_url)
        
        # Tester la connexion
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 AS test"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                print(f"✅ Connexion SQLAlchemy réussie")
                print(f"🔑 URL de connexion utilisée: {db_url.replace(db_password, '*****')}")
                return True
            else:
                print(f"❌ Connexion SQLAlchemy échouée: pas de données retournées")
                return False
                
    except ImportError:
        print("❌ Module SQLAlchemy non trouvé")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la connexion avec SQLAlchemy: {str(e)}")
        return False

# Mettre à jour le fichier .env si nécessaire
def update_env_file():
    env_path = os.path.join(BACKEND_DIR, '.env')
    
    # Vérifier si les variables DATABASE_URL existe déjà dans .env
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Modifier le contenu si nécessaire
    if 'DATABASE_URL=' not in content:
        print("⚙️ Ajout de la variable DATABASE_URL dans le fichier .env")
        # Insérer DATABASE_URL après la section base de données
        content = content.replace(
            f"DB_NAME={db_name}",
            f"DB_NAME={db_name}\nDATABASE_URL=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
        
        # Écrire le nouveau contenu
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("✅ Fichier .env mis à jour")
        return True
    else:
        print("✅ La variable DATABASE_URL existe déjà dans le fichier .env")
        return False

# Fonction principale
def main():
    print("=== Réinitialisation et test de la base de données ===\n")
    
    # Réinitialiser le mot de passe PostgreSQL
    if not reset_postgres_password():
        print("❌ Échec de la réinitialisation du mot de passe PostgreSQL")
        return False
    
    # Vérifier/mettre à jour .env
    update_env_file()
    
    # Tester la connexion avec psycopg2
    if not test_psycopg2_connection():
        print("❌ Échec du test avec psycopg2")
        return False
    
    # Tester la connexion avec SQLAlchemy
    if not test_sqlalchemy_connection():
        print("❌ Échec du test avec SQLAlchemy")
        return False
    
    print("\n✅ Tous les tests de connexion ont réussi!")
    print("🚀 Vous pouvez maintenant démarrer l'API.")
    return True

if __name__ == "__main__":
    main()

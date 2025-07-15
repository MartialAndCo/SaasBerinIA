#!/usr/bin/env python3

import os
import sys
sys.path.append('/root/berinia/backend')

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv('/root/berinia/infra-ia/.env')

# Configuration de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://berinia_user:berinia_pass@localhost/berinia")

print("🔍 NETTOYAGE DES DONNÉES - VILLE OBLIGATOIRE")
print("=" * 50)

# Créer l'engine
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("✅ Connexion réussie à la base de données")
        
        # 1. Identifier les entrées sans ville
        print("\n📊 ÉTAT ACTUEL DES DONNÉES :")
        
        # Campagnes sans ville
        result = connection.execute(text("SELECT id, name FROM campaigns WHERE ville IS NULL"))
        campaigns_without_city = result.fetchall()
        
        # Niches sans ville
        result = connection.execute(text("SELECT id, name FROM niches WHERE ville IS NULL"))
        niches_without_city = result.fetchall()
        
        print(f"❌ Campagnes sans ville : {len(campaigns_without_city)}")
        for id, name in campaigns_without_city:
            print(f"   - ID {id}: {name}")
        
        print(f"❌ Niches sans ville : {len(niches_without_city)}")
        for id, name in niches_without_city:
            print(f"   - ID {id}: {name}")
        
        if not campaigns_without_city and not niches_without_city:
            print("🎉 Toutes les données ont déjà une ville !")
            exit(0)
        
        # 2. Options de nettoyage
        print("\n🧹 OPTIONS DE NETTOYAGE :")
        print("1. Assigner 'Paris' par défaut aux entrées sans ville")
        print("2. Supprimer les entrées sans ville")
        print("3. Annuler")
        
        choice = input("\nChoix (1/2/3) : ").strip()
        
        if choice == "1":
            # Assigner Paris par défaut
            print("\n🏷️ ASSIGNATION DE PARIS PAR DÉFAUT...")
            
            if campaigns_without_city:
                connection.execute(text("UPDATE campaigns SET ville = 'Paris' WHERE ville IS NULL"))
                print(f"✅ {len(campaigns_without_city)} campagnes assignées à Paris")
            
            if niches_without_city:
                connection.execute(text("UPDATE niches SET ville = 'Paris' WHERE ville IS NULL"))
                print(f"✅ {len(niches_without_city)} niches assignées à Paris")
            
            connection.commit()
            
        elif choice == "2":
            # Supprimer les entrées sans ville
            print("\n🗑️ SUPPRESSION DES ENTRÉES SANS VILLE...")
            
            if campaigns_without_city:
                connection.execute(text("DELETE FROM campaigns WHERE ville IS NULL"))
                print(f"✅ {len(campaigns_without_city)} campagnes supprimées")
            
            if niches_without_city:
                connection.execute(text("DELETE FROM niches WHERE ville IS NULL"))
                print(f"✅ {len(niches_without_city)} niches supprimées")
            
            connection.commit()
            
        elif choice == "3":
            print("❌ Opération annulée")
            exit(0)
        else:
            print("❌ Choix invalide")
            exit(1)
        
        # 3. Vérification finale
        print("\n📊 VÉRIFICATION FINALE :")
        
        result = connection.execute(text("SELECT COUNT(*) FROM campaigns WHERE ville IS NULL"))
        campaigns_null = result.fetchone()[0]
        
        result = connection.execute(text("SELECT COUNT(*) FROM niches WHERE ville IS NULL"))
        niches_null = result.fetchone()[0]
        
        if campaigns_null == 0 and niches_null == 0:
            print("🎉 PARFAIT ! Toutes les données ont maintenant une ville !")
            
            # Statistiques finales
            result = connection.execute(text("SELECT COUNT(*), ville FROM campaigns GROUP BY ville ORDER BY ville"))
            campaigns_by_city = result.fetchall()
            
            result = connection.execute(text("SELECT COUNT(*), ville FROM niches GROUP BY ville ORDER BY ville"))
            niches_by_city = result.fetchall()
            
            print("\n📈 RÉPARTITION PAR VILLE :")
            print("CAMPAGNES :")
            for count, ville in campaigns_by_city:
                print(f"   - {ville}: {count} campagnes")
            
            print("NICHES :")
            for count, ville in niches_by_city:
                print(f"   - {ville}: {count} niches")
        else:
            print(f"⚠️ Il reste encore {campaigns_null} campagnes et {niches_null} niches sans ville !")

except Exception as e:
    print(f"❌ Erreur : {e}")
    sys.exit(1)

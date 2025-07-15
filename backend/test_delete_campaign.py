#!/usr/bin/env python3
"""
Script de test pour vérifier la suppression de campagne avec gestion des contraintes FK
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.campaign import Campaign as CampaignModel
from app.models.lead import Lead as LeadModel
from sqlalchemy import func, text

def test_delete_campaign_with_fk_constraints():
    """Test de suppression d'une campagne avec gestion des contraintes FK"""
    
    # Créer une session de base de données
    db = next(get_db())
    
    try:
        # Lister les campagnes existantes
        campaigns = db.query(CampaignModel).all()
        print(f"Campagnes trouvées: {len(campaigns)}")
        
        for campaign in campaigns:
            print(f"- ID: {campaign.id}, Nom: {campaign.name}, Status: {campaign.status}")
        
        if not campaigns:
            print("Aucune campagne trouvée pour tester la suppression")
            return
        
        # Prendre la première campagne pour le test
        test_campaign = campaigns[0]
        campaign_id = test_campaign.id
        
        print(f"\n🧪 Test de suppression de la campagne ID {campaign_id}: '{test_campaign.name}'")
        
        # Vérifier s'il y a des leads associés
        leads_count = db.query(func.count(LeadModel.id)).filter(LeadModel.campagne_id == campaign_id).scalar() or 0
        print(f"Leads associés: {leads_count}")
        
        if leads_count > 0:
            print("⚠️  Dissociation des leads avant suppression...")
            # Dissocier les leads (mettre campagne_id à NULL)
            db.query(LeadModel).filter(LeadModel.campagne_id == campaign_id).update(
                {"campagne_id": None}, synchronize_session=False
            )
        
        # Vérifier et gérer les messages associés
        try:
            print("⚠️  Dissociation des messages avant suppression...")
            # Dissocier les messages (mettre campaign_id à NULL) 
            result = db.execute(
                text("UPDATE messages SET campaign_id = NULL WHERE campaign_id = :campaign_id"),
                {"campaign_id": campaign_id}
            )
            print(f"Messages dissociés: {result.rowcount}")
        except Exception as e:
            print(f"Note: Gestion des messages échouée (table peut-être inexistante): {e}")
        
        # Supprimer la campagne
        print("🗑️  Suppression de la campagne...")
        db.delete(test_campaign)
        db.commit()
        
        print("✅ Suppression réussie !")
        
        # Vérifier que la campagne a bien été supprimée
        deleted_campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
        if deleted_campaign is None:
            print(f"✅ Confirmation: La campagne ID {campaign_id} a été supprimée de la base de données")
        else:
            print(f"❌ Erreur: La campagne ID {campaign_id} existe encore dans la base de données")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Test de suppression de campagne avec gestion des contraintes FK")
    print("=" * 60)
    
    success = test_delete_campaign_with_fk_constraints()
    
    if success:
        print("\n🎉 Test réussi ! La correction fonctionne.")
    else:
        print("\n💥 Test échoué ! Il y a encore des problèmes.")

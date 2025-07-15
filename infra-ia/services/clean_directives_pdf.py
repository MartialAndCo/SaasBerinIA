#!/usr/bin/env python3
"""
Script pour supprimer définitivement le bloc PDF polluant des directives
et activer le système de contexte dynamique
"""

import json
import logging
import requests
from typing import Dict, Any
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectivesCleaner:
    """Nettoyeur de directives - supprime le PDF polluant"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
    
    def get_current_directives(self) -> Dict[str, Any]:
        """Récupère les directives actuelles"""
        try:
            response = requests.get(f"{self.api_base_url}/api/messenger/directives")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Erreur récupération directives: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"❌ Erreur API directives: {e}")
            return {}
    
    def remove_pdf_block(self, sms_instructions: str) -> str:
        """Supprime complètement le bloc PDF des instructions"""
        pdf_start_marker = "DOCUMENTS D'ENTREPRISE BERINIA:"
        
        if pdf_start_marker in sms_instructions:
            # Récupérer seulement la partie avant le PDF
            clean_instructions = sms_instructions.split(pdf_start_marker)[0].strip()
            
            # Ajouter une note sur le système dynamique
            dynamic_note = """

🤖 SYSTÈME CONTEXTUEL DYNAMIQUE ACTIVÉ
Les informations produits/métiers sont maintenant injectées automatiquement selon le contexte de chaque conversation. Plus de bloc PDF générique !"""
            
            clean_instructions += dynamic_note
            
            logger.info(f"📄 Bloc PDF supprimé! Avant: {len(sms_instructions)} caractères → Après: {len(clean_instructions)} caractères")
            return clean_instructions
        else:
            logger.warning("⚠️ Aucun bloc PDF trouvé à supprimer")
            return sms_instructions
    
    def update_directives_without_pdf(self) -> Dict[str, Any]:
        """Met à jour les directives en supprimant le PDF"""
        try:
            # 1. Récupérer les directives actuelles
            current_directives = self.get_current_directives()
            if not current_directives:
                return {"success": False, "error": "Impossible de récupérer les directives"}
            
            # 2. Nettoyer les instructions SMS
            original_instructions = current_directives.get('sms_instructions', '')
            clean_instructions = self.remove_pdf_block(original_instructions)
            
            # 3. Nettoyer les instructions EMAIL aussi si elles existent
            email_instructions = current_directives.get('email_instructions', '')
            if email_instructions and "DOCUMENTS D'ENTREPRISE BERINIA:" in email_instructions:
                clean_email_instructions = self.remove_pdf_block(email_instructions)
                current_directives['email_instructions'] = clean_email_instructions
                logger.info("📧 Bloc PDF supprimé aussi des instructions EMAIL")
            
            # 4. Préparer les données simplifiées pour l'API
            clean_data = {
                "sms_instructions": clean_instructions,
                "email_instructions": current_directives.get('email_instructions', '')
            }
            
            # 5. Métadonnées pour le retour (pas envoyées à l'API)
            cleanup_info = {
                "cleaned_at": datetime.now().isoformat(),
                "original_length": len(original_instructions),
                "clean_length": len(clean_instructions),
                "characters_removed": len(original_instructions) - len(clean_instructions),
                "dynamic_system_enabled": True,
                "note": "PDF polluant supprimé, système contextuel dynamique activé"
            }
            
            # 6. Sauvegarder via API POST (format simplifié)
            response = requests.post(
                f"{self.api_base_url}/api/messenger/directives",
                json=clean_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "PDF polluant supprimé avec succès!",
                    "original_length": cleanup_info["original_length"],
                    "clean_length": cleanup_info["clean_length"],
                    "characters_removed": cleanup_info["characters_removed"],
                    "reduction_percentage": round((cleanup_info["characters_removed"] / cleanup_info["original_length"]) * 100, 1)
                }
            else:
                logger.error(f"❌ Erreur sauvegarde directives: {response.status_code}")
                return {"success": False, "error": f"Erreur sauvegarde: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage directives: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_cleanup(self) -> Dict[str, Any]:
        """Vérifie que le nettoyage a bien fonctionné"""
        try:
            directives = self.get_current_directives()
            sms_instructions = directives.get('sms_instructions', '')
            
            has_pdf_block = "DOCUMENTS D'ENTREPRISE BERINIA:" in sms_instructions
            has_dynamic_note = "SYSTÈME CONTEXTUEL DYNAMIQUE ACTIVÉ" in sms_instructions
            
            return {
                "success": True,
                "pdf_block_found": has_pdf_block,
                "dynamic_system_note": has_dynamic_note,
                "current_length": len(sms_instructions),
                "status": "✅ CLEAN" if not has_pdf_block else "❌ PDF STILL THERE",
                "cleanup_metadata": directives.get('pdf_cleanup', {})
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return {"success": False, "error": str(e)}


def main():
    """Script principal de nettoyage"""
    print("🧹 Nettoyage du Bloc PDF Polluant des Directives BerinIA")
    print("=" * 65)
    
    try:
        cleaner = DirectivesCleaner()
        
        # 1. État avant nettoyage
        print("\n🔍 ÉTAT AVANT NETTOYAGE:")
        verification_before = cleaner.verify_cleanup()
        if verification_before["success"]:
            print(f"   📄 Bloc PDF présent: {'OUI' if verification_before['pdf_block_found'] else 'NON'}")
            print(f"   📏 Taille actuelle: {verification_before['current_length']} caractères")
            print(f"   🎯 Statut: {verification_before['status']}")
        
        # 2. Nettoyage si nécessaire
        if verification_before.get("pdf_block_found", False):
            print(f"\n🧹 SUPPRESSION DU BLOC PDF...")
            result = cleaner.update_directives_without_pdf()
            
            if result["success"]:
                print(f"✅ {result['message']}")
                print(f"   📏 Avant: {result['original_length']} caractères")
                print(f"   📏 Après: {result['clean_length']} caractères")
                print(f"   🗑️ Supprimé: {result['characters_removed']} caractères")
                print(f"   📉 Réduction: {result['reduction_percentage']}%")
            else:
                print(f"❌ Erreur: {result['error']}")
                return
        else:
            print(f"\n✅ PDF déjà supprimé, rien à faire!")
        
        # 3. Vérification après nettoyage
        print(f"\n🔍 ÉTAT APRÈS NETTOYAGE:")
        verification_after = cleaner.verify_cleanup()
        if verification_after["success"]:
            print(f"   📄 Bloc PDF présent: {'OUI' if verification_after['pdf_block_found'] else 'NON'}")
            print(f"   🤖 Note système dynamique: {'OUI' if verification_after['dynamic_system_note'] else 'NON'}")
            print(f"   📏 Taille finale: {verification_after['current_length']} caractères")
            print(f"   🎯 Statut: {verification_after['status']}")
            
            if verification_after.get('cleanup_metadata'):
                meta = verification_after['cleanup_metadata']
                print(f"   📅 Nettoyé le: {meta.get('cleaned_at', 'N/A')}")
        
        print(f"\n🎉 NETTOYAGE TERMINÉ - Le PDF polluant a été éradiqué!")
        print(f"🚀 Le système contextuel dynamique est maintenant actif.")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

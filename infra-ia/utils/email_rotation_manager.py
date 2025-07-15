"""
Gestionnaire de rotation des emails Instantly.ai
Gère la sélection intelligente des emails selon leur statut (test/warmup/actif)
"""

import os
import json
import random
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

class EmailRotationManager:
    """
    Gestionnaire intelligent de rotation des emails Instantly.ai
    
    Fonctionnalités:
    - Rotation aléatoire des emails actifs (évite les warmup)
    - Mapping email utilisé → conversation pour les réponses
    - Mode test avec email dédié
    - Évitement des emails shadowban/désactivés
    """
    
    def __init__(self, instantly_client, test_mode: bool = False):
        """
        Initialisation du gestionnaire
        
        Args:
            instantly_client: Instance du client Instantly.ai
            test_mode: Si True, utilise uniquement l'email de test
        """
        self.instantly_client = instantly_client
        self.test_mode = test_mode
        self.accounts_cache = None
        self.cache_timestamp = None
        self.conversation_email_mapping = self._load_mapping()
        
        # Configuration des emails
        self.email_config = {
            "test_emails": ["test@beriniacontact.com"],
            "warmup_keywords": ["warmup"],
            "cache_duration_minutes": 30
        }
    
    def _load_mapping(self) -> Dict[str, str]:
        """
        Charge le mapping conversation → email utilisé
        
        Returns:
            Dictionnaire {lead_id: email_utilisé}
        """
        mapping_file = Path(__file__).parent.parent / "data" / "email_mapping.json"
        
        try:
            if mapping_file.exists():
                with open(mapping_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def _save_mapping(self) -> None:
        """
        Sauvegarde le mapping conversation → email
        """
        mapping_file = Path(__file__).parent.parent / "data" / "email_mapping.json"
        
        try:
            # Créer le dossier data s'il n'existe pas
            mapping_file.parent.mkdir(exist_ok=True)
            
            with open(mapping_file, 'w') as f:
                json.dump(self.conversation_email_mapping, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde mapping: {e}")
    
    def get_available_accounts(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Récupère les comptes disponibles avec cache
        
        Args:
            force_refresh: Force le rechargement depuis l'API
            
        Returns:
            Liste des comptes avec leurs statuts
        """
        # Vérifier le cache
        if not force_refresh and self.accounts_cache and self.cache_timestamp:
            cache_age = (datetime.now() - self.cache_timestamp).total_seconds() / 60
            if cache_age < self.email_config["cache_duration_minutes"]:
                return self.accounts_cache
        
        try:
            # Récupérer depuis l'API
            accounts_response = self.instantly_client.list_accounts(limit=20)
            
            if accounts_response and accounts_response.get("items"):
                # Enrichir avec le statut déterminé
                enriched_accounts = []
                for account in accounts_response["items"]:
                    account_copy = account.copy()
                    account_copy["determined_status"] = self._determine_account_status(account)
                    enriched_accounts.append(account_copy)
                
                self.accounts_cache = enriched_accounts
                self.cache_timestamp = datetime.now()
                return enriched_accounts
            
            return []
            
        except Exception as e:
            print(f"Erreur récupération comptes: {e}")
            return self.accounts_cache or []
    
    def _determine_account_status(self, account: Dict[str, Any]) -> str:
        """
        Détermine le statut réel d'un compte
        
        Args:
            account: Données du compte Instantly
            
        Returns:
            Statut: "test", "warmup", "active", "disabled"
        """
        email = account.get("email", "").lower()
        status = account.get("status", 0)
        warmup_status = account.get("warmup_status", 0)
        
        # Email de test
        if any(test_email in email for test_email in self.email_config["test_emails"]):
            return "test"
        
        # Compte désactivé
        if status != 1:  # 1 = actif dans Instantly
            return "disabled"
        
        # Compte en warmup
        if warmup_status == 1:
            return "warmup"
        
        # Compte actif
        return "active"
    
    def select_email_for_new_conversation(self, lead_id: str, campaign_type: str = "general") -> Optional[str]:
        """
        Sélectionne un email pour une nouvelle conversation
        
        Args:
            lead_id: ID du lead
            campaign_type: Type de campagne (influence la sélection)
            
        Returns:
            Email sélectionné ou None si aucun disponible
        """
        accounts = self.get_available_accounts()
        
        if self.test_mode:
            # Mode test : utiliser uniquement les emails de test
            test_accounts = [acc for acc in accounts if acc["determined_status"] == "test"]
            if test_accounts:
                selected_email = test_accounts[0]["email"]
                print(f"🧪 [MODE TEST] Email sélectionné: {selected_email}")
            else:
                print("❌ Aucun email de test disponible")
                return None
        else:
            # Mode production : utiliser les emails actifs (pas warmup)
            active_accounts = [acc for acc in accounts if acc["determined_status"] == "active"]
            
            if active_accounts:
                # Sélection aléatoire pour répartir la charge
                selected_account = random.choice(active_accounts)
                selected_email = selected_account["email"]
                print(f"🔄 Email sélectionné (rotation): {selected_email}")
            else:
                print("⚠️ Aucun email actif disponible (tous en warmup?)")
                # Fallback: utiliser l'email de test si disponible
                test_accounts = [acc for acc in accounts if acc["determined_status"] == "test"]
                if test_accounts:
                    selected_email = test_accounts[0]["email"]
                    print(f"🧪 [FALLBACK] Utilisation email de test: {selected_email}")
                else:
                    return None
        
        # Sauvegarder le mapping
        self.conversation_email_mapping[str(lead_id)] = selected_email
        self._save_mapping()
        
        return selected_email
    
    def get_email_for_reply(self, lead_id: str) -> Optional[str]:
        """
        Récupère l'email à utiliser pour répondre à un lead
        
        Args:
            lead_id: ID du lead
            
        Returns:
            Email utilisé pour la conversation initiale
        """
        stored_email = self.conversation_email_mapping.get(str(lead_id))
        
        if stored_email:
            print(f"📧 Email pour réponse (conversation existante): {stored_email}")
            return stored_email
        else:
            print(f"⚠️ Aucun email trouvé pour lead {lead_id}, sélection d'un nouvel email")
            # Nouvelle conversation
            return self.select_email_for_new_conversation(lead_id)
    
    def get_accounts_summary(self) -> Dict[str, Any]:
        """
        Résumé des comptes disponibles par statut
        
        Returns:
            Résumé des comptes
        """
        accounts = self.get_available_accounts()
        
        summary = {
            "total": len(accounts),
            "by_status": {},
            "details": []
        }
        
        for account in accounts:
            email = account["email"]
            status = account["determined_status"]
            
            # Compter par statut
            if status not in summary["by_status"]:
                summary["by_status"][status] = 0
            summary["by_status"][status] += 1
            
            # Détails
            summary["details"].append({
                "email": email,
                "status": status,
                "instantly_status": account.get("status"),
                "warmup_status": account.get("warmup_status")
            })
        
        return summary
    
    def cleanup_old_mappings(self, days_old: int = 30) -> None:
        """
        Nettoie les anciens mappings (optionnel)
        
        Args:
            days_old: Supprimer les mappings plus anciens que X jours
        """
        # Pour une version future avec timestamps
        pass

# Fonction utilitaire pour tester
def test_email_rotation():
    """
    Test du gestionnaire de rotation des emails
    """
    print("🧪 Test du gestionnaire de rotation")
    print("=" * 40)
    
    try:
        # Charger les variables d'environnement
        from pathlib import Path
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        # Importer et initialiser  
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from utils.api_clients.instantly_client import InstantlyClient
        
        client = InstantlyClient()
        manager = EmailRotationManager(client, test_mode=True)
        
        # Test 1: Résumé des comptes
        print("📊 Résumé des comptes:")
        summary = manager.get_accounts_summary()
        for status, count in summary["by_status"].items():
            print(f"  {status}: {count} comptes")
        
        # Test 2: Sélection pour nouvelle conversation
        print(f"\n🔄 Test sélection nouvel email:")
        test_lead_id = "test_lead_123"
        selected_email = manager.select_email_for_new_conversation(test_lead_id)
        print(f"Email sélectionné: {selected_email}")
        
        # Test 3: Récupération pour réponse
        print(f"\n📧 Test récupération email pour réponse:")
        reply_email = manager.get_email_for_reply(test_lead_id)
        print(f"Email pour réponse: {reply_email}")
        
        print("\n✅ Tests terminés avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email_rotation()

"""
Gestionnaire de rotation des comptes SMTP Mailcheap
Gère la sélection intelligente des comptes email et la mémoire des conversations
"""

import os
import json
import random
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

class SMTPRotationManager:
    """
    Gestionnaire intelligent de rotation des comptes SMTP
    
    Fonctionnalités:
    - Rotation aléatoire des comptes SMTP actifs
    - Mapping email utilisé → conversation pour les réponses
    - Mode test avec compte dédié
    - Gestion des variables d'environnement
    """
    
    def __init__(self, smtp_configs: List[Dict[str, Any]], test_mode: bool = False):
        """
        Initialisation du gestionnaire
        
        Args:
            smtp_configs: Liste des configurations SMTP
            test_mode: Si True, utilise uniquement le premier compte
        """
        self.smtp_configs = smtp_configs
        self.test_mode = test_mode
        self.conversation_email_mapping = self._load_mapping()
        
        # Résoudre les variables d'environnement
        self.resolved_configs = self._resolve_env_vars()
        
        # Configuration
        self.config = {
            "mapping_file": Path(__file__).parent / "data" / "smtp_email_mapping.json",
            "test_account_index": 0  # Premier compte pour les tests
        }
        
        # Créer le dossier data s'il n'existe pas
        self.config["mapping_file"].parent.mkdir(exist_ok=True)
    
    def _resolve_env_vars(self) -> List[Dict[str, str]]:
        """
        Résout les variables d'environnement dans les configs SMTP
        
        Returns:
            Liste des configurations avec valeurs résolues
        """
        resolved = []
        
        for config in self.smtp_configs:
            resolved_config = {}
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("MAILCHEAP_"):
                    # Résoudre la variable d'environnement
                    env_value = os.getenv(value)
                    if env_value:
                        resolved_config[key] = env_value
                    else:
                        print(f"⚠️ Variable d'environnement manquante: {value}")
                        resolved_config[key] = ""
                else:
                    resolved_config[key] = value
            
            # Vérifier que la config est valide
            if all(resolved_config.get(k) for k in ["host", "user", "password", "from_email"]):
                resolved.append(resolved_config)
            else:
                print(f"⚠️ Configuration SMTP invalide ignorée: {resolved_config}")
        
        return resolved
    
    def _load_mapping(self) -> Dict[str, str]:
        """
        Charge le mapping conversation → email utilisé
        
        Returns:
            Dictionnaire de mapping
        """
        mapping_file = Path(__file__).parent / "data" / "smtp_email_mapping.json"
        
        try:
            if mapping_file.exists():
                with open(mapping_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur chargement mapping: {e}")
        
        return {}
    
    def _save_mapping(self):
        """
        Sauvegarde le mapping conversation → email utilisé
        """
        mapping_file = self.config["mapping_file"]
        
        try:
            with open(mapping_file, "w", encoding="utf-8") as f:
                json.dump(self.conversation_email_mapping, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde mapping: {e}")
    
    def get_available_accounts(self) -> List[Dict[str, str]]:
        """
        Récupère les comptes SMTP disponibles
        
        Returns:
            Liste des comptes SMTP actifs
        """
        available = []
        
        for config in self.resolved_configs:
            if config.get("status") == "active" and config.get("host") and config.get("user"):
                available.append(config)
        
        return available
    
    def select_smtp_config_for_campaign(self, lead_id: str, campaign_type: str = "default") -> Optional[Dict[str, str]]:
        """
        Sélectionne un compte SMTP pour une campagne
        
        Args:
            lead_id: ID du lead
            campaign_type: Type de campagne (influence la sélection)
            
        Returns:
            Configuration SMTP sélectionnée ou None si aucune disponible
        """
        available_accounts = self.get_available_accounts()
        
        if not available_accounts:
            print("❌ Aucun compte SMTP disponible")
            return None
        
        if self.test_mode:
            # Mode test : utiliser le premier compte
            selected_config = available_accounts[0]
            print(f"🧪 [MODE TEST] Compte sélectionné: {selected_config['from_email']}")
        else:
            # Mode production : rotation aléatoire
            selected_config = random.choice(available_accounts)
            print(f"🔄 Compte sélectionné (rotation): {selected_config['from_email']}")
        
        # Sauvegarder le mapping pour les réponses
        self.conversation_email_mapping[str(lead_id)] = selected_config["from_email"]
        self._save_mapping()
        
        return selected_config
    
    def get_smtp_config_for_reply(self, lead_id: str) -> Optional[Dict[str, str]]:
        """
        Récupère la configuration SMTP à utiliser pour répondre à un lead
        
        Args:
            lead_id: ID du lead
            
        Returns:
            Configuration SMTP utilisée pour l'envoi initial ou None
        """
        original_email = self.conversation_email_mapping.get(str(lead_id))
        
        if not original_email:
            print(f"⚠️ Aucun email original trouvé pour lead {lead_id}")
            return None
        
        # Trouver la config correspondante
        for config in self.resolved_configs:
            if config.get("from_email") == original_email:
                print(f"✅ Réponse avec même email: {original_email}")
                return config
        
        print(f"❌ Configuration introuvable pour email: {original_email}")
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du gestionnaire
        
        Returns:
            Statistiques d'utilisation
        """
        available_accounts = self.get_available_accounts()
        
        # Compter l'utilisation de chaque compte
        usage_counts = {}
        for lead_id, email in self.conversation_email_mapping.items():
            usage_counts[email] = usage_counts.get(email, 0) + 1
        
        return {
            "available_accounts": len(available_accounts),
            "total_conversations": len(self.conversation_email_mapping),
            "usage_distribution": usage_counts,
            "test_mode": self.test_mode,
            "accounts_list": [acc["from_email"] for acc in available_accounts]
        }
    
    def clear_conversation_mapping(self, lead_id: str = None):
        """
        Efface le mapping des conversations
        
        Args:
            lead_id: ID spécifique à effacer (ou None pour tout effacer)
        """
        if lead_id:
            self.conversation_email_mapping.pop(str(lead_id), None)
            print(f"Mapping effacé pour lead {lead_id}")
        else:
            self.conversation_email_mapping.clear()
            print("Tous les mappings effacés")
        
        self._save_mapping()

# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration exemple
    configs = [
        {
            "host": "serveur1.mymailcheap.com",
            "port": 587,
            "user": "email1@domain.com",
            "password": "password1",
            "from_email": "email1@domain.com",
            "status": "active"
        },
        {
            "host": "serveur2.mymailcheap.com", 
            "port": 587,
            "user": "email2@domain.com",
            "password": "password2",
            "from_email": "email2@domain.com",
            "status": "active"
        }
    ]
    
    manager = SMTPRotationManager(configs, test_mode=True)
    
    # Test de sélection
    config = manager.select_smtp_config_for_campaign("123", "test")
    print(f"Config sélectionnée: {config}")
    
    # Test de réponse
    reply_config = manager.get_smtp_config_for_reply("123")
    print(f"Config pour réponse: {reply_config}")
    
    # Statistiques
    stats = manager.get_stats()
    print(f"Statistiques: {stats}")
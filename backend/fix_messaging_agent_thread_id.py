#!/usr/bin/env python3
"""
Patch pour corriger le MessagingAgent afin qu'il gère automatiquement les thread_id
"""

import os
import shutil
import hashlib
from datetime import datetime

def generate_thread_id(lead_email, lead_name):
    """Génère un thread_id unique basé sur le lead"""
    base = (lead_email or lead_name or "unknown").lower()
    return "thread_" + hashlib.md5(base.encode()).hexdigest()[:8]

def patch_messaging_agent():
    """Applique le patch au MessagingAgent pour gérer les thread_id"""
    
    print("🔧 Application du patch MessagingAgent pour thread_id...")
    print("=" * 60)
    
    # Chemin vers le fichier MessagingAgent
    agent_path = "/root/berinia/infra-ia/agents/messaging/messaging_agent.py"
    backup_path = f"{agent_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Créer une sauvegarde
    try:
        shutil.copy2(agent_path, backup_path)
        print(f"✅ Sauvegarde créée: {backup_path}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False
    
    # Lire le contenu actuel
    try:
        with open(agent_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        return False
    
    # Vérifier si le patch est déjà appliqué
    if "def _get_or_create_thread_id" in content:
        print("✅ Le patch thread_id est déjà appliqué !")
        return True
    
    # 1. Ajouter la méthode de génération de thread_id
    thread_id_method = '''
    def _get_or_create_thread_id(self, lead: Dict[str, Any]) -> str:
        """
        Récupère ou crée un thread_id pour un lead
        
        Args:
            lead: Le lead à contacter
            
        Returns:
            thread_id unique pour ce lead
        """
        lead_email = lead.get("email", "")
        lead_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
        
        # Vérifier s'il existe déjà des messages pour ce lead
        if lead.get("lead_id"):
            try:
                # Chercher un thread_id existant pour ce lead
                existing_thread = self.db.fetch_one(
                    "SELECT DISTINCT thread_id FROM messages WHERE lead_id = %s AND thread_id IS NOT NULL LIMIT 1",
                    (lead["lead_id"],)
                )
                
                if existing_thread and existing_thread.get("thread_id"):
                    return existing_thread["thread_id"]
            except Exception as e:
                self.speak(f"Erreur lors de la recherche de thread_id existant: {str(e)}", target="ProspectionSupervisor")
        
        # Générer un nouveau thread_id basé sur l'email ou le nom
        base = (lead_email or lead_name or "unknown").lower()
        thread_id = "thread_" + hashlib.md5(base.encode()).hexdigest()[:8]
        
        self.speak(f"Nouveau thread_id généré: {thread_id} pour {lead_name} ({lead_email})", target="ProspectionSupervisor")
        return thread_id
'''
    
    # 2. Modifier la méthode _save_message_to_db pour inclure thread_id
    old_save_method = '''    def _save_message_to_db(self, lead: Dict[str, Any], message_data: Dict[str, Any], campaign_id: str, channel: str) -> str:
        """
        Enregistre un message envoyé dans la base de données
        
        Args:
            lead: Le lead contacté
            message_data: Les données du message
            campaign_id: L'ID de la campagne
            channel: Le canal utilisé (email, sms, etc.)
            
        Returns:
            ID du message enregistré
        """
        message_id = str(uuid.uuid4())
        
        try:
            # Insertion dans la base de données
            message_record = {
                "id": message_id,
                "lead_id": lead.get("lead_id", ""),
                "campaign_id": campaign_id,
                "template_id": message_data.get("template_id", ""),
                "channel": channel,
                "subject": message_data.get("subject", ""),
                "content": message_data.get("content", ""),
                "sent_at": datetime.datetime.now().isoformat(),
                "status": "sent"
            }
            
            # Selon le mode de fonctionnement (test ou production)
            if not self.config.get("test_mode", True):
                self.db.insert("messages", message_record)
            
            return message_id
            
        except Exception as e:
            self.speak(f"Erreur lors de l'enregistrement du message: {str(e)}", target="ProspectionSupervisor")
            return message_id  # On retourne quand même l'ID généré'''
    
    new_save_method = '''    def _save_message_to_db(self, lead: Dict[str, Any], message_data: Dict[str, Any], campaign_id: str, channel: str) -> str:
        """
        Enregistre un message envoyé dans la base de données
        
        Args:
            lead: Le lead contacté
            message_data: Les données du message
            campaign_id: L'ID de la campagne
            channel: Le canal utilisé (email, sms, etc.)
            
        Returns:
            ID du message enregistré
        """
        message_id = str(uuid.uuid4())
        
        try:
            # Génération ou récupération du thread_id
            thread_id = self._get_or_create_thread_id(lead)
            
            # Préparation des données pour l'insertion SQL directe
            now = datetime.datetime.now()
            lead_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
            
            # Insertion directe avec SQL pour avoir un contrôle total sur les colonnes
            insert_query = """
                INSERT INTO messages (
                    lead_id, lead_name, lead_email, campaign_id, campaign_name,
                    subject, content, status, type, sent_date, created_at, updated_at,
                    direction, sender_type, thread_id, message_type, sender_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                lead.get("lead_id", ""),                           # lead_id
                lead_name,                                         # lead_name
                lead.get("email", ""),                            # lead_email
                campaign_id,                                       # campaign_id
                f"Campagne {lead.get('industry', 'Générale')}",   # campaign_name
                message_data.get("subject", ""),                   # subject
                message_data.get("content", ""),                   # content
                "sent",                                            # status
                channel,                                           # type
                now,                                               # sent_date
                now,                                               # created_at
                now,                                               # updated_at
                "outbound",                                        # direction
                "ai",                                              # sender_type
                thread_id,                                         # thread_id
                channel,                                           # message_type
                "Louise BerinIA"                                   # sender_name
            )
            
            # Selon le mode de fonctionnement (test ou production)
            if not self.config.get("test_mode", True):
                # Exécution de la requête SQL directe
                self.db.execute_query(insert_query, values)
                self.speak(f"Message enregistré avec thread_id: {thread_id}", target="ProspectionSupervisor")
            else:
                self.speak(f"[MODE TEST] Message avec thread_id: {thread_id}", target="ProspectionSupervisor")
            
            return message_id
            
        except Exception as e:
            self.speak(f"Erreur lors de l'enregistrement du message: {str(e)}", target="ProspectionSupervisor")
            return message_id  # On retourne quand même l'ID généré'''
    
    # 3. Ajouter l'import hashlib si nécessaire
    if "import hashlib" not in content:
        content = content.replace("import uuid", "import uuid\nimport hashlib")
    
    # 4. Appliquer les modifications
    # Ajouter la méthode _get_or_create_thread_id avant _save_message_to_db
    if "_save_message_to_db" in content:
        content = content.replace("    def _save_message_to_db", thread_id_method + "\n    def _save_message_to_db")
    
    # Remplacer la méthode _save_message_to_db
    if old_save_method in content:
        content = content.replace(old_save_method, new_save_method)
    
    # Écrire le fichier modifié
    try:
        with open(agent_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Patch appliqué avec succès !")
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture: {e}")
        # Restaurer la sauvegarde
        try:
            shutil.copy2(backup_path, agent_path)
            print("🔄 Sauvegarde restaurée")
        except:
            pass
        return False
    
    # 5. Vérification du patch
    try:
        with open(agent_path, 'r', encoding='utf-8') as f:
            patched_content = f.read()
        
        if "_get_or_create_thread_id" in patched_content and "thread_id = self._get_or_create_thread_id(lead)" in patched_content:
            print("✅ Vérification du patch : SUCCÈS")
            print("\n📋 Fonctionnalités ajoutées :")
            print("   - Génération automatique de thread_id pour chaque lead")
            print("   - Réutilisation des thread_id existants")
            print("   - Thread_id basé sur email/nom du lead pour cohérence")
            print("   - Logging des thread_id créés")
            return True
        else:
            print("❌ Vérification du patch : ÉCHEC")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Patch MessagingAgent pour gestion automatique des thread_id")
    print("=" * 60)
    
    success = patch_messaging_agent()
    
    if success:
        print("\n🎯 PATCH APPLIQUÉ AVEC SUCCÈS !")
        print("Le MessagingAgent gère maintenant automatiquement les thread_id.")
        print("Chaque conversation avec un lead aura un thread_id unique et persistent.")
    else:
        print("\n❌ ÉCHEC DU PATCH")
        print("Vérifiez les erreurs ci-dessus et réessayez.")

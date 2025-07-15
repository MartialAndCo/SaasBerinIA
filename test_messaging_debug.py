#!/usr/bin/env python3
"""
Test pour debug le MessagingAgent et voir quelle version de _save_message_to_db est appelée
"""
import sys
import os

# Ajouter le chemin des modules
sys.path.append('/root/berinia/infra-ia')

def test_messaging_agent_save():
    """Test de la méthode _save_message_to_db"""
    try:
        # Import direct du module pour inspecter
        import importlib.util
        import inspect
        
        spec = importlib.util.spec_from_file_location("messaging_agent", "/root/berinia/infra-ia/agents/messaging/messaging_agent.py")
        module = importlib.util.module_from_spec(spec)
        
        print("🔍 Inspection du fichier messaging_agent.py...")
        
        # Lire le source du fichier directement
        with open("/root/berinia/infra-ia/agents/messaging/messaging_agent.py", "r") as f:
            source = f.read()
        
        # Chercher les définitions de _save_message_to_db
        import re
        
        # Trouver toutes les définitions de la méthode
        method_matches = list(re.finditer(r'def _save_message_to_db.*?(?=def |\Z)', source, re.DOTALL))
        
        print(f"Nombre de définitions de _save_message_to_db trouvées: {len(method_matches)}")
        
        for i, match in enumerate(method_matches):
            method_source = match.group(0)
            print(f"\n--- Définition {i+1} ---")
            
            # Vérifier le contenu de la méthode
            has_template_id = 'template_id' in method_source
            has_channel = '"channel"' in method_source
            has_sent_at = '"sent_at"' in method_source
            has_nouvelle_version = 'NOUVELLE VERSION' in method_source
            
            print(f"Contient 'template_id': {has_template_id}")
            print(f"Contient '\"channel\"': {has_channel}")
            print(f"Contient '\"sent_at\"': {has_sent_at}")
            print(f"Contient 'NOUVELLE VERSION': {has_nouvelle_version}")
            
            # Montrer les premières lignes
            lines = method_source.split('\n')[:10]
            print("Premières lignes:")
            for j, line in enumerate(lines):
                print(f"  {j+1}: {line}")
            
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_messaging_agent_save()
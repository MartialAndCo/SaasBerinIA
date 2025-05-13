#!/usr/bin/env python3
"""
Script de diagnostic du système de webhook sans modification des fichiers existants.
Ce script analyse la configuration du système et tente de diagnostiquer les problèmes
de réception de SMS sans altérer les fichiers existants.
"""
import os
import sys
import json
import logging
import subprocess
import requests
import importlib.util
from datetime import datetime

# Configuration du logging
log_dir = "/root/berinia/infra-ia/tests/temp_webhook_test"
log_file = f"{log_dir}/diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("Webhook-Diagnostic")

def check_file_exists(path):
    """Vérifie si un fichier existe sans le modifier"""
    exists = os.path.exists(path)
    logger.info(f"Vérification du fichier {path}: {'Existe' if exists else 'N\'existe pas'}")
    return exists

def log_directory_contents(path):
    """Liste le contenu d'un répertoire sans le modifier"""
    logger.info(f"Contenu du répertoire {path}:")
    if not os.path.exists(path):
        logger.info("  Le répertoire n'existe pas")
        return
        
    try:
        files = os.listdir(path)
        for file in files:
            full_path = os.path.join(path, file)
            file_type = "Répertoire" if os.path.isdir(full_path) else "Fichier"
            size = os.path.getsize(full_path) if os.path.isfile(full_path) else "-"
            logger.info(f"  {file_type}: {file} - Taille: {size} octets")
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du répertoire {path}: {str(e)}")

def check_webhook_service():
    """Vérifie l'état du service webhook"""
    logger.info("Vérification du service webhook...")
    try:
        result = subprocess.run(
            ["systemctl", "status", "berinia-webhook.service"], 
            capture_output=True, 
            text=True
        )
        logger.info(f"Statut du service: {result.stdout}")
        
        is_active = "active (running)" in result.stdout
        logger.info(f"Le service est {'actif' if is_active else 'inactif'}")
        return is_active
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du service: {str(e)}")
        return False

def check_webhook_urls():
    """Vérifie la connectivité aux différentes URLs du webhook"""
    base_url = "http://127.0.0.1:8001"
    urls = [
        "",
        "/health",
        "/webhook"
    ]
    
    logger.info("Test des URLs du webhook:")
    for url_path in urls:
        full_url = base_url + url_path
        logger.info(f"Test de l'URL: {full_url}")
        
        try:
            response = requests.get(full_url, timeout=5)
            logger.info(f"  Statut: {response.status_code}")
            logger.info(f"  Réponse: {response.text[:200]}" + 
                       ("..." if len(response.text) > 200 else ""))
        except Exception as e:
            logger.error(f"  Erreur: {str(e)}")

def check_required_agents():
    """Vérifie la présence des agents requis"""
    required_agents = [
        "ResponseListenerAgent",
        "ResponseInterpreterAgent"
    ]
    
    logger.info("Vérification des agents requis:")
    
    # Chemins possibles pour les agents
    base_dirs = [
        "/root/berinia/infra-ia/agents",
    ]
    
    for agent_name in required_agents:
        logger.info(f"Recherche de l'agent: {agent_name}")
        found = False
        
        # Vérification des formats possibles (snake_case vs camelCase)
        snake_case = ''.join(['_' + c.lower() if c.isupper() else c.lower() for c in agent_name]).lstrip('_')
        snake_case = snake_case.replace("_agent", "")
        
        for base_dir in base_dirs:
            # Format agent/agent_name
            agent_dir = os.path.join(base_dir, snake_case)
            agent_file = os.path.join(agent_dir, f"{snake_case}_agent.py")
            
            if check_file_exists(agent_dir):
                logger.info(f"  Répertoire trouvé: {agent_dir}")
                log_directory_contents(agent_dir)
                found = True
            
            if check_file_exists(agent_file):
                logger.info(f"  Fichier d'agent trouvé: {agent_file}")
                found = True
                
            # Format agent/agentname
            camel_dir = os.path.join(base_dir, agent_name.lower())
            camel_file = os.path.join(camel_dir, f"{agent_name.lower()}.py")
            
            if check_file_exists(camel_dir):
                logger.info(f"  Répertoire trouvé: {camel_dir}")
                log_directory_contents(camel_dir)
                found = True
            
            if check_file_exists(camel_file):
                logger.info(f"  Fichier d'agent trouvé: {camel_file}")
                found = True
        
        if not found:
            logger.warning(f"⚠️ L'agent {agent_name} n'a pas été trouvé")

def run_test_sms_request():
    """Teste l'envoi d'une requête SMS au webhook"""
    webhook_url = "http://127.0.0.1:8001/webhook/sms-response"
    
    logger.info(f"Test d'envoi d'une requête POST au webhook SMS: {webhook_url}")
    
    # Données de test (simulant une requête Twilio)
    payload = {
        "From": "+33695472227",
        "To": "+33757594999",
        "Body": "Ceci est un test de diagnostic SMS",
        "MessageSid": "DIAG12345"
    }
    
    # En-têtes de la requête (avec signature obligatoire)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Twilio-Signature": "dummy_signature"
    }
    
    try:
        logger.info("Envoi de la requête...")
        response = requests.post(webhook_url, data=payload, headers=headers, timeout=10)
        
        logger.info(f"Code de statut: {response.status_code}")
        logger.info(f"Réponse: {response.text}")
        
        if response.status_code >= 400:
            logger.error(f"⚠️ La requête a échoué avec le code {response.status_code}")
            
            # Tentative de parse du corps de la réponse comme JSON
            try:
                error_data = response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                pass
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la requête: {str(e)}")

def check_imports_in_webhook():
    """Vérifie les imports dans le fichier run_webhook.py"""
    webhook_file = "/root/berinia/infra-ia/webhook/run_webhook.py"
    
    logger.info(f"Analyse des imports dans {webhook_file}:")
    
    if not os.path.exists(webhook_file):
        logger.error(f"Le fichier {webhook_file} n'existe pas")
        return
    
    try:
        with open(webhook_file, 'r') as f:
            content = f.read()
            
        # Recherche des imports clés
        imports_to_check = [
            "RequestValidator",
            "ResponseListenerAgent",
            "ResponseInterpreterAgent"
        ]
        
        for imp in imports_to_check:
            if imp in content:
                logger.info(f"  Import trouvé: {imp}")
            else:
                logger.warning(f"⚠️ Import non trouvé: {imp}")
                
        # Vérification de l'import de RequestValidator
        if "from twilio.request_validator import RequestValidator" in content:
            logger.info("  Import correct: from twilio.request_validator import RequestValidator")
        else:
            logger.warning("⚠️ Import de RequestValidator incorrect ou manquant")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du fichier: {str(e)}")

def main():
    """Fonction principale de diagnostic"""
    logger.info("=== DÉMARRAGE DU DIAGNOSTIC DU WEBHOOK BERINIA ===")
    
    # Vérification du service webhook
    service_active = check_webhook_service()
    
    # Vérification des URLs du webhook
    check_webhook_urls()
    
    # Vérification des agents requis
    check_required_agents()
    
    # Vérification des imports dans le webhook
    check_imports_in_webhook()
    
    # Test d'une requête SMS
    if service_active:
        run_test_sms_request()
    
    logger.info("=== FIN DU DIAGNOSTIC ===")
    logger.info(f"Un rapport complet est disponible dans le fichier: {log_file}")
    
    return True

if __name__ == "__main__":
    success = main()
    print(f"\n📊 DIAGNOSTIC TERMINÉ\nLog: {log_file}")
    sys.exit(0 if success else 1)

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import os
import re
import logging
import subprocess
from app.api import deps

router = APIRouter()
logger = logging.getLogger(__name__)

def read_dotenv_file(file_path: str) -> Dict[str, str]:
    """
    Lit un fichier .env et retourne un dictionnaire des variables et leurs valeurs
    """
    if not os.path.exists(file_path):
        logger.error(f"Fichier .env introuvable: {file_path}")
        return {}
    
    env_vars = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Ignorer les lignes vides et les commentaires
                if not line or line.startswith('#'):
                    continue
                
                # Rechercher les définitions de variables
                if match := re.match(r'^([A-Za-z0-9_]+)=(.*)$', line):
                    key, value = match.groups()
                    # Supprimer les guillemets si présents
                    if value and (
                        (value.startswith('"') and value.endswith('"')) or 
                        (value.startswith("'") and value.endswith("'"))
                    ):
                        value = value[1:-1]
                    env_vars[key] = value
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier .env: {str(e)}")
    
    return env_vars

def write_dotenv_file(file_path: str, env_vars: Dict[str, str]) -> bool:
    """
    Écrit les variables d'environnement dans un fichier .env en préservant les commentaires
    et l'ordre des variables existantes
    """
    if not os.path.exists(file_path):
        logger.error(f"Fichier .env introuvable: {file_path}")
        return False
    
    try:
        # Lire le fichier pour préserver les commentaires et la structure
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Mettre à jour les lignes avec les nouvelles valeurs
        updated_lines = []
        for line in lines:
            strip_line = line.strip()
            # Garder les lignes vides et les commentaires tels quels
            if not strip_line or strip_line.startswith('#'):
                updated_lines.append(line)
                continue
            
            # Mettre à jour les variables d'environnement
            if match := re.match(r'^([A-Za-z0-9_]+)=.*$', strip_line):
                key = match.group(1)
                if key in env_vars:
                    # Préserver l'indentation originale
                    indent = re.match(r'^(\s*)', line).group(1)
                    value = env_vars[key]
                    # Ajouter des guillemets si la valeur contient des espaces
                    if ' ' in value or '\t' in value or '\n' in value:
                        value = f'"{value}"'
                    updated_lines.append(f"{indent}{key}={value}\n")
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Écrire les lignes mises à jour dans le fichier
        with open(file_path, 'w') as f:
            f.writelines(updated_lines)
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'écriture du fichier .env: {str(e)}")
        return False

@router.get("/env-variables")
def get_env_variables():
    """
    Récupère les variables d'environnement du fichier .env
    """
    env_file_path = "/root/berinia/infra-ia/.env"
    variables = read_dotenv_file(env_file_path)
    
    # Filtrer pour ne retourner que les variables pertinentes
    allowed_vars = {
        'OPENAI_API_KEY': variables.get('OPENAI_API_KEY', ''),
        'INSTANTLY_API_KEY': variables.get('INSTANTLY_API_KEY', ''),
        'TWILIO_SID': variables.get('TWILIO_SID', ''),
        'TWILIO_TOKEN': variables.get('TWILIO_TOKEN', ''),
        'TWILIO_PHONE': variables.get('TWILIO_PHONE', ''),
        'APIFY_API_KEY': variables.get('APIFY_API_KEY', ''),
        'APOLLO_API_KEY': variables.get('APOLLO_API_KEY', '')
    }
    
    return {"status": "success", "data": allowed_vars}

@router.post("/env-variables")
def update_env_variables(data: Dict[str, str]):
    """
    Met à jour les variables d'environnement dans le fichier .env
    """
    env_file_path = "/root/berinia/infra-ia/.env"
    
    # Valider les variables autorisées
    allowed_keys = ['OPENAI_API_KEY', 'INSTANTLY_API_KEY', 'TWILIO_SID', 
                   'TWILIO_TOKEN', 'TWILIO_PHONE', 'APIFY_API_KEY', 'APOLLO_API_KEY']
    
    # Filtrer les données pour ne garder que les clés autorisées
    filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
    
    # Lire le fichier actuel
    current_vars = read_dotenv_file(env_file_path)
    
    # Mettre à jour les variables
    for key, value in filtered_data.items():
        current_vars[key] = value
    
    # Écrire les nouvelles variables
    success = write_dotenv_file(env_file_path, current_vars)
    
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Erreur lors de la mise à jour du fichier .env"
        )
    
    # Redémarrer les services qui utilisent ces variables
    try:
        subprocess.run(["sudo", "systemctl", "restart", "berinia-agents.service"], 
                      check=True, capture_output=True)
        logger.info("Service berinia-agents.service redémarré avec succès")
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors du redémarrage du service: {str(e)}")
        logger.error(f"Stdout: {e.stdout.decode() if e.stdout else 'N/A'}")
        logger.error(f"Stderr: {e.stderr.decode() if e.stderr else 'N/A'}")
        # On continue malgré l'erreur
    
    # Renvoyer les valeurs mises à jour
    updated_vars = {
        'OPENAI_API_KEY': current_vars.get('OPENAI_API_KEY', ''),
        'INSTANTLY_API_KEY': current_vars.get('INSTANTLY_API_KEY', ''),
        'TWILIO_SID': current_vars.get('TWILIO_SID', ''),
        'TWILIO_TOKEN': current_vars.get('TWILIO_TOKEN', ''),
        'TWILIO_PHONE': current_vars.get('TWILIO_PHONE', ''),
        'APIFY_API_KEY': current_vars.get('APIFY_API_KEY', ''),
        'APOLLO_API_KEY': current_vars.get('APOLLO_API_KEY', '')
    }
    
    return {"status": "success", "data": updated_vars}

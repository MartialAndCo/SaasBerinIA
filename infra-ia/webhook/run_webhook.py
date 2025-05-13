#!/usr/bin/env python3
"""
Point d'entrée pour le serveur webhook de BerinIA.

Ce script lance un serveur FastAPI qui écoute sur le port 8000
et traite les webhooks entrants de différentes sources (WhatsApp, etc.)
"""
import os
import sys
import json
import asyncio
import argparse
import uvicorn
import datetime
from fastapi import FastAPI, Request, HTTPException, Header, Depends, Response
from fastapi.middleware.cors import CORSMiddleware

# Ajout du répertoire parent au path pour les imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import de logging pour les messages d'erreur initiaux
import logging

# Charger les variables d'environnement depuis le fichier .env
try:
    from dotenv import load_dotenv
    
    # Charger le fichier .env dans le répertoire parent (infra-ia)
    env_path = os.path.join(parent_dir, '.env')
    logger_temp = logging.getLogger("BerinIA.webhook.setup")
    
    if os.path.exists(env_path):
        logger_temp.info(f"Chargement des variables d'environnement depuis {env_path}")
        load_dotenv(env_path)
        
        # Vérifier si TWILIO_TOKEN est défini
        if os.getenv("TWILIO_TOKEN"):
            logger_temp.info("TWILIO_TOKEN bien chargé depuis le fichier .env")
        else:
            logger_temp.error(f"TWILIO_TOKEN absent après chargement de {env_path}")
    else:
        logger_temp.error(f"Fichier .env introuvable: {env_path}")
except Exception as e:
    logging.error(f"Erreur lors du chargement des variables d'environnement: {str(e)}")
    import traceback
    logging.error(traceback.format_exc())

# Import de la nouvelle configuration de logging
from utils.logging_config import get_logger, setup_logging

# Initialiser le logger principal pour le webhook
logger = setup_logging("webhook")

# Import des gestionnaires de webhook spécifiques
from webhook.whatsapp_webhook import handle_whatsapp_webhook
from twilio.request_validator import RequestValidator

# Création de l'application FastAPI
app = FastAPI(title="BerinIA Webhook", description="Serveur webhook pour BerinIA")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_twilio_signature(
    x_twilio_signature: str = Header(...),
    request: Request = None,
):
    """Vérifie la signature Twilio pour sécuriser les webhooks."""
    # Récupérer le token depuis les variables d'environnement déjà chargées
    auth_token = os.getenv("TWILIO_TOKEN")
    
    if not auth_token:
        logger.error(f"ERREUR: TWILIO_TOKEN non défini dans {env_path}")
        return True
    
    validator = RequestValidator(auth_token)
    url = str(request.url)
    
    # Obtenir les données du formulaire de manière asynchrone
    form_data = await request.form()
    params = dict(form_data)
    
    # Log pour débogage
    logger.info(f"Vérification de signature Twilio pour URL: {url}")
    logger.info(f"Signature: {x_twilio_signature}")
    
    try:
        is_valid = validator.validate(url, params, x_twilio_signature)
        
        if not is_valid:
            logger.warning(f"ALERTE: Signature Twilio invalide pour {url}")
    except Exception as e:
        logger.error(f"Erreur lors de la validation de signature Twilio: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return True
        
    return True  # En développement; en production, retourner `is_valid`

@app.get("/")
async def root():
    """
    Point d'entrée racine pour vérifier que le serveur fonctionne
    """
    logger.info("Requête GET sur /")
    return {"status": "ok", "message": "BerinIA Webhook Server"}

@app.get("/health")
async def health_check():
    """
    Endpoint de vérification de santé du service
    """
    logger.info("Vérification de santé du webhook")
    return {"status": "healthy"}

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Endpoint pour le webhook WhatsApp
    """
    try:
        data = await request.json()
        logger.info("Requête webhook WhatsApp reçue")
        
        # Log des données reçues pour debugging
        logger.debug(f"Données reçues: {json.dumps(data)}")
        
        # Traitement par le gestionnaire WhatsApp
        response = await handle_whatsapp_webhook(data)
        
        logger.info("Réponse au webhook WhatsApp envoyée")
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook WhatsApp: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/sms-response")
async def receive_sms_response(
    request: Request,
    auth: bool = Depends(verify_twilio_signature)
):
    """
    Endpoint pour recevoir les réponses SMS via Twilio.
    """
    try:
        # Récupération du corps de la requête
        payload = await request.form()
        data = dict(payload)
        
        logger.info(f"Notification de réponse SMS reçue: {data.get('From')}")
        
        # Vérification des champs requis
        required_fields = ["From", "To", "Body"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            error_msg = f"Champs manquants: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Traitement du SMS
        logger.info(f"SMS de {data['From']} à {data['To']}: {data['Body']}")
        
        # Transmettre les données au ResponseListenerAgent pour traitement
        # Import dynamique pour éviter les dépendances circulaires
        try:
            # Import du registre d'agents
            from agents.registry import registry
            
            # Formatage des données pour le ResponseListenerAgent
            sms_data = {
                "sender": data['From'],
                "recipient": data['To'],
                "body": data['Body'],
                "timestamp": datetime.datetime.now().isoformat(),
                "message_sid": data.get('MessageSid', ''),
                "raw_data": data
            }
            
            # Obtenir ou créer l'instance de ResponseListenerAgent
            listener_agent = registry.get_or_create("ResponseListenerAgent")
            
            if listener_agent:
                logger.info(f"Transmission du SMS de {data['From']} au ResponseListenerAgent")
                
                # Appel du ResponseListenerAgent
                result = listener_agent.run({
                    "action": "process_sms_response",
                    "data": sms_data
                })
                
                logger.info(f"Résultat du traitement par ResponseListenerAgent: {result.get('status', 'unknown')}")
            else:
                logger.error("Impossible de charger le ResponseListenerAgent")
        except Exception as e:
            logger.error(f"Erreur lors de la transmission au ResponseListenerAgent: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Création d'une réponse TwiML vide (pas de réponse automatique)
        response_text = """<?xml version="1.0" encoding="UTF-8"?><Response></Response>"""
        
        return Response(content=response_text, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook SMS: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webhook/logs")
async def get_logs(lines: int = 50):
    """
    Endpoint pour récupérer les dernières lignes des logs
    
    Args:
        lines: Nombre de lignes à récupérer
        
    Returns:
        Liste des dernières lignes de logs
    """
    from utils.logging_config import WEBHOOK_LOG
    
    logger.info(f"Récupération des {lines} dernières lignes de logs")
    
    try:
        with open(WEBHOOK_LOG, "r") as f:
            log_lines = f.readlines()
            return {
                "logs": log_lines[-lines:] if len(log_lines) > lines else log_lines
            }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des logs: {str(e)}")
        return {"error": str(e)}

def run_server():
    """
    Lance le serveur webhook
    """
    try:
        # Analyse des arguments de ligne de commande
        parser = argparse.ArgumentParser(description="Serveur webhook BerinIA")
        parser.add_argument("--host", type=str, default="0.0.0.0", help="Adresse d'écoute (par défaut: 0.0.0.0)")
        parser.add_argument("--port", type=int, default=8001, help="Port d'écoute (par défaut: 8001)")
        args = parser.parse_args()
        
        logger.info(f"Démarrage du serveur webhook BerinIA sur {args.host}:{args.port}...")
        uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run_server()

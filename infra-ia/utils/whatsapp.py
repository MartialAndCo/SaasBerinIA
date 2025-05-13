"""
Utilitaires pour l'intégration WhatsApp dans BerinIA
Ce module permet d'envoyer des messages WhatsApp depuis les agents Python
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Union, List

logger = logging.getLogger(__name__)

# Configuration de l'API WhatsApp
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:3030")

# Mapping des noms de groupe logiques vers les noms réels
GROUP_MAPPING = {
    "ANNOUNCEMENTS": "📣 Annonces officielles",
    "STATS": "📊 Performances & Stats",
    "LOGS": "🛠️ Logs techniques",
    "SUPPORT": "🤖 Support IA / Chatbot",
    "STRATEGY": "🧠 Tactiques & Tests",
    "GENERAL": "💬 Discussion libre"
}

def send_whatsapp_message(
    group: str, 
    message: str, 
    api_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Envoie un message à un groupe WhatsApp spécifique
    
    Args:
        group: Nom ou identifiant logique du groupe (ex: "LOGS" ou "🛠️ Logs techniques")
        message: Contenu du message à envoyer
        api_url: URL de l'API WhatsApp (par défaut http://localhost:3000)
    
    Returns:
        Dict contenant la réponse de l'API
    
    Raises:
        ConnectionError: Si la connexion à l'API WhatsApp échoue
        ValueError: Si le groupe spécifié n'est pas reconnu
    """
    # Utiliser l'URL par défaut si non spécifiée
    if api_url is None:
        api_url = WHATSAPP_API_URL
    
    # Déterminer le nom du groupe réel si un identifiant logique est fourni
    group_name = GROUP_MAPPING.get(group, group)
    
    endpoint = f"{api_url}/send"
    payload = {
        "group": group_name,
        "message": message
    }
    
    logger.info(f"Envoi d'un message WhatsApp au groupe '{group_name}'")
    logger.debug(f"Contenu du message: {message[:50]}..." if len(message) > 50 else message)
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10  # Timeout de 10 secondes pour éviter les blocages
        )
        
        response.raise_for_status()  # Lever une exception si le code de statut est 4XX/5XX
        result = response.json()
        
        logger.info(f"Message WhatsApp envoyé avec succès: {result.get('message', 'OK')}")
        return result
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de l'envoi du message WhatsApp: {str(e)}")
        # Relancer l'exception pour que l'appelant puisse la gérer
        raise ConnectionError(f"Impossible de se connecter à l'API WhatsApp: {str(e)}")

def send_log_message(message: str) -> Dict[str, Any]:
    """Envoie un message au groupe de logs techniques"""
    return send_whatsapp_message("LOGS", message)

def send_announcement(message: str) -> Dict[str, Any]:
    """Envoie une annonce officielle"""
    return send_whatsapp_message("ANNOUNCEMENTS", message)

def send_stats(message: str) -> Dict[str, Any]:
    """Envoie des statistiques ou performances"""
    return send_whatsapp_message("STATS", message)

def format_error_message(
    agent_name: str, 
    error_message: str, 
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Formate un message d'erreur pour l'envoyer au groupe de logs
    
    Args:
        agent_name: Nom de l'agent qui a rencontré l'erreur
        error_message: Message d'erreur
        context: Contexte supplémentaire (optionnel)
    
    Returns:
        Message formaté prêt à être envoyé
    """
    formatted_message = f"⚠️ *ERREUR dans {agent_name}*\n\n"
    formatted_message += f"```\n{error_message}\n```\n\n"
    
    if context:
        formatted_message += "*Contexte:*\n"
        for key, value in context.items():
            formatted_message += f"- {key}: {value}\n"
    
    return formatted_message

def format_stats_message(
    title: str,
    stats: Dict[str, Union[str, int, float]],
    comparison: Optional[Dict[str, Union[str, int, float]]] = None
) -> str:
    """
    Formate un message de statistiques pour l'envoyer au groupe de stats
    
    Args:
        title: Titre du rapport de statistiques
        stats: Dictionnaire de statistiques à afficher
        comparison: Statistiques de comparaison (optionnel)
    
    Returns:
        Message formaté prêt à être envoyé
    """
    formatted_message = f"📊 *{title}*\n\n"
    
    for key, value in stats.items():
        formatted_message += f"*{key}:* {value}"
        
        # Ajouter la comparaison si disponible
        if comparison and key in comparison:
            diff = None
            comp_value = comparison[key]
            
            if isinstance(value, (int, float)) and isinstance(comp_value, (int, float)):
                diff = value - comp_value
                if diff > 0:
                    formatted_message += f" (+{diff}) ⬆️"
                elif diff < 0:
                    formatted_message += f" ({diff}) ⬇️"
                else:
                    formatted_message += " (=)"
        
        formatted_message += "\n"
    
    return formatted_message

# Exemple d'utilisation dans la documentation
if __name__ == "__main__":
    # Ces exemples ne s'exécutent que si le fichier est lancé directement
    logging.basicConfig(level=logging.INFO)
    
    # Exemple d'envoi de message
    try:
        result = send_whatsapp_message("LOGS", "Ceci est un message de test")
        print(f"Résultat: {result}")
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Exemple de formatage d'erreur
    error_msg = format_error_message(
        "ScraperAgent",
        "Impossible de se connecter à la source de données",
        {"url": "https://example.com", "attempt": 3}
    )
    print(f"Message d'erreur formaté:\n{error_msg}")
    
    # Exemple de formatage de statistiques
    stats_msg = format_stats_message(
        "Statistiques journalières - 07/05/2025",
        {
            "Leads générés": 145,
            "Taux de réponse": "23.5%",
            "Score moyen": 78.2
        },
        {
            "Leads générés": 130,
            "Taux de réponse": "21.0%",
            "Score moyen": 75.8
        }
    )
    print(f"Message de statistiques formaté:\n{stats_msg}")

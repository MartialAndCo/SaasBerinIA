"""
Utilitaires pour la gestion de la mémoire de connaissances du système

Ce module fournit des fonctions pour interroger la base de connaissances
vectorielle (Qdrant) et enrichir les contextes des agents avec des
informations pertinentes.
"""
import logging
from typing import List, Dict, Any, Optional

from utils.qdrant import create_embedding, search_knowledge

# Configuration du logging
logger = logging.getLogger(__name__)

def get_relevant_knowledge(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Récupère les connaissances pertinentes pour une requête donnée
    
    Args:
        query: La requête ou question posée
        limit: Nombre maximum de résultats à retourner
        
    Returns:
        Liste des résultats avec leur score et contenu
    """
    try:
        # Recherche des connaissances similaires
        results = search_knowledge(query, limit)
        
        # Filtrer les résultats dont le score est trop bas
        filtered_results = [r for r in results if r.get("score", 0) > 0.75]
        
        if not filtered_results:
            logger.info(f"Aucune connaissance pertinente trouvée pour: '{query}'")
            return []
            
        logger.info(f"Trouvé {len(filtered_results)} connaissances pertinentes pour: '{query}'")
        return filtered_results
        
    except Exception as e:
        logger.warning(f"Erreur lors de la recherche de connaissances: {str(e)}")
        return []

def enrich_context_with_knowledge(query: str, original_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrichit un contexte avec des connaissances pertinentes de la base Qdrant
    
    Args:
        query: La requête ou question posée
        original_context: Le contexte original
        
    Returns:
        Contexte enrichi avec les connaissances pertinentes
    """
    # Copier le contexte original pour ne pas le modifier
    enriched_context = original_context.copy()
    
    # Récupérer les connaissances pertinentes
    relevant_knowledge = get_relevant_knowledge(query)
    
    if not relevant_knowledge:
        return original_context
    
    # Formater les connaissances pour le contexte
    knowledge_text = []
    for i, item in enumerate(relevant_knowledge):
        content = item.get("content", "")
        source = item.get("metadata", {}).get("source", "inconnu")
        knowledge_text.append(f"--- Information {i+1} (source: {source}) ---\n{content}")
    
    # Ajouter les connaissances au contexte
    enriched_context["system_knowledge"] = "\n\n".join(knowledge_text)
    
    return enriched_context

def format_knowledge_for_prompt(knowledge_items: List[Dict[str, Any]]) -> str:
    """
    Formate les connaissances pour inclusion dans un prompt
    
    Args:
        knowledge_items: Liste des connaissances à formater
        
    Returns:
        Texte formaté pour inclusion dans un prompt
    """
    if not knowledge_items:
        return ""
        
    formatted_text = "INFORMATIONS CONTEXTUELLES PERTINENTES:\n\n"
    
    for i, item in enumerate(knowledge_items):
        content = item.get("content", "")
        source = item.get("metadata", {}).get("source", "inconnu")
        formatted_text += f"[Bloc {i+1} - {source}]\n{content}\n\n"
    
    return formatted_text

def enrich_prompt_with_knowledge(query: str, original_prompt: str) -> str:
    """
    Enrichit un prompt avec des connaissances pertinentes
    
    Args:
        query: La requête ou question posée
        original_prompt: Le prompt original
        
    Returns:
        Prompt enrichi avec les connaissances pertinentes
    """
    # Récupérer les connaissances pertinentes
    relevant_knowledge = get_relevant_knowledge(query)
    
    if not relevant_knowledge:
        return original_prompt
    
    # Formater les connaissances
    knowledge_text = format_knowledge_for_prompt(relevant_knowledge)
    
    # Insérer les connaissances dans le prompt, juste après l'introduction
    # ou avant la demande principale
    
    # Chercher un bon point d'insertion
    insertion_markers = [
        "\n\nDEMANDE:", 
        "\n\nQuestion:", 
        "\n\nRequête:",
        "\n\nTâche:"
    ]
    
    for marker in insertion_markers:
        if marker in original_prompt:
            parts = original_prompt.split(marker, 1)
            return parts[0] + "\n\n" + knowledge_text + marker + parts[1]
    
    # Si aucun marqueur n'est trouvé, ajouter après le premier paragraphe
    paragraphs = original_prompt.split("\n\n", 1)
    if len(paragraphs) > 1:
        return paragraphs[0] + "\n\n" + knowledge_text + "\n\n" + paragraphs[1]
    
    # Sinon, simplement ajouter après le prompt
    return original_prompt + "\n\n" + knowledge_text

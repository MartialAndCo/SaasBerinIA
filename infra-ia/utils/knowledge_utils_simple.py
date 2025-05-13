"""
Utilitaires pour la gestion de la mémoire de connaissances du système - Version simplifiée

Ce module fournit des fonctions pour accéder à la base de connaissances
et enrichir les contextes des agents avec des informations pertinentes,
sans dépendre de Qdrant.
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import random

# Configuration du logging
logger = logging.getLogger(__name__)

# Cache global pour les chunks de connaissances
_knowledge_cache = []

def load_knowledge(knowledge_dir: str = "data/knowledge") -> None:
    """
    Charge les connaissances à partir des fichiers markdown

    Args:
        knowledge_dir: Répertoire contenant les fichiers de connaissances
    """
    global _knowledge_cache
    
    try:
        # Chemin absolu vers le répertoire de connaissances
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        knowledge_path = os.path.join(base_dir, knowledge_dir)
        
        logger.info(f"Chargement des connaissances depuis {knowledge_path}")
        
        # Vérifier que le répertoire existe
        if not os.path.exists(knowledge_path) or not os.path.isdir(knowledge_path):
            logger.warning(f"Répertoire de connaissances {knowledge_path} non trouvé")
            return
        
        # Trouver tous les fichiers markdown
        markdown_files = []
        for root, dirs, files in os.walk(knowledge_path):
            for file in files:
                if file.endswith(".md"):
                    markdown_files.append(os.path.join(root, file))
        
        if not markdown_files:
            logger.warning(f"Aucun fichier markdown trouvé dans {knowledge_path}")
            return
        
        logger.info(f"Trouvé {len(markdown_files)} fichiers markdown à traiter")
        
        # Traiter chaque fichier
        for file_path in markdown_files:
            chunks = _process_markdown_file(file_path)
            file_name = os.path.basename(file_path)
            category = os.path.basename(os.path.dirname(file_path))
            
            for i, chunk in enumerate(chunks):
                _knowledge_cache.append({
                    "content": chunk,
                    "metadata": {
                        "source": file_name,
                        "category": category if category != "knowledge" else "system",
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                })
        
        logger.info(f"Chargement terminé: {len(_knowledge_cache)} chunks chargés")
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des connaissances: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def _read_markdown_file(file_path: str) -> str:
    """
    Lit un fichier markdown et renvoie son contenu
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        Contenu du fichier
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def _split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Découpe le texte en chunks pour le traitement.
    Les coupures sont faites de préférence aux sauts de ligne ou points.
    
    Args:
        text: Texte à découper
        chunk_size: Taille maximale des chunks
        overlap: Chevauchement entre chunks
        
    Returns:
        Liste des chunks
    """
    # Séparation par sections (titres markdown)
    sections = re.split(r'(#{1,6}\s+[^\n]+\n)', text)
    chunks = []
    current_chunk = ""
    current_title = ""
    
    for section in sections:
        # Si c'est un titre, garder pour le prochain chunk
        if re.match(r'^#{1,6}\s+', section):
            current_title = section
            continue
            
        # Si c'est du contenu
        if current_title:
            # Ajouter le titre au début du contenu
            section = current_title + section
            current_title = ""
            
        # Découper en segments intelligents (paragraphes, listes, etc.)
        segments = re.split(r'(\n\n|\n(?=\s*[-*+]\s)|(?<=\.)\s+)', section)
        
        for segment in segments:
            if not segment.strip():
                continue
                
            # Si ajouter ce segment dépasse la taille max
            if len(current_chunk) + len(segment) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    
                    # Conserver une partie pour l'overlap
                    overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                    current_chunk = overlap_text + segment
                else:
                    # Cas où un seul segment dépasse la taille max
                    chunks.append(segment[:chunk_size].strip())
                    current_chunk = segment[chunk_size-overlap:] if overlap > 0 else ""
            else:
                current_chunk += segment
    
    # Ajouter le dernier chunk s'il reste du contenu
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def _process_markdown_file(file_path: str) -> List[str]:
    """
    Traite un fichier markdown en le découpant en chunks
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        Liste des chunks
    """
    logger.info(f"Traitement du fichier : {file_path}")
    
    # Lire le contenu du fichier
    content = _read_markdown_file(file_path)
    
    # Découper en chunks
    chunks = _split_text_into_chunks(content)
    logger.info(f"Fichier découpé en {len(chunks)} chunks")
    
    return chunks

def _calculate_similarity(query: str, content: str) -> float:
    """
    Calcule une similarité simplifiée entre une requête et un contenu
    
    Args:
        query: La requête
        content: Le contenu à comparer
        
    Returns:
        Score de similarité (0-1)
    """
    # Version simplifiée: comptage des mots en commun
    query_words = set(re.findall(r'\b\w+\b', query.lower()))
    content_words = set(re.findall(r'\b\w+\b', content.lower()))
    
    if not query_words or not content_words:
        return 0.0
    
    # Mots en commun
    common_words = query_words.intersection(content_words)
    
    # Score basé sur le nombre de mots en commun divisé par le nombre total de mots uniques de la requête
    score = len(common_words) / len(query_words)
    
    # Bonus si des phrases précises de la requête sont trouvées
    query_phrases = [phrase.strip() for phrase in query.lower().split('.') if phrase.strip()]
    for phrase in query_phrases:
        if phrase and len(phrase.split()) > 2 and phrase in content.lower():
            score += 0.2  # Bonus pour une correspondance de phrase
    
    return min(score, 1.0)  # Plafonner à 1.0

def get_relevant_knowledge(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Récupère les connaissances pertinentes pour une requête donnée
    
    Args:
        query: La requête ou question posée
        limit: Nombre maximum de résultats à retourner
        
    Returns:
        Liste des résultats avec leur score et contenu
    """
    global _knowledge_cache
    
    try:
        # S'assurer que la base de connaissances est chargée
        if not _knowledge_cache:
            logger.info("Chargement initial de la base de connaissances")
            load_knowledge()
        
        # Si toujours vide, c'est qu'il y a un problème
        if not _knowledge_cache:
            logger.warning("Base de connaissances vide, impossible de trouver des informations pertinentes")
            return []
        
        # Calcul des scores pour chaque chunk
        scored_chunks = []
        for chunk in _knowledge_cache:
            content = chunk["content"]
            score = _calculate_similarity(query, content)
            
            if score > 0.1:  # Seuil minimal de pertinence
                scored_chunks.append({
                    "score": score,
                    "content": content,
                    "metadata": chunk["metadata"]
                })
        
        # Trier par score décroissant
        sorted_chunks = sorted(scored_chunks, key=lambda x: x["score"], reverse=True)
        
        # Prendre les meilleurs résultats
        top_results = sorted_chunks[:limit]
        
        # Filtrer les résultats dont le score est trop bas
        filtered_results = [r for r in top_results if r["score"] > 0.2]
        
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
    Enrichit un contexte avec des connaissances pertinentes
    
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

# Précharger les connaissances au démarrage
load_knowledge()

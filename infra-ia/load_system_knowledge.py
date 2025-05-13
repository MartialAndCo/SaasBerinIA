#!/usr/bin/env python3
"""
Script pour charger la base de connaissances système dans Qdrant

Ce script découpe le fichier de documentation en chunks, génère des embeddings
pour chaque chunk et les stocke dans la base de données vectorielle Qdrant.
"""
import os
import re
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Importer le module Qdrant
from utils.qdrant import create_collection, add_to_collection, get_collection_info

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

# Configuration
KNOWLEDGE_COLLECTION = "knowledge"
VECTOR_SIZE = 1536  # Taille des vecteurs d'embedding OpenAI
KNOWLEDGE_DIR = Path("data/knowledge")
CHUNK_SIZE = 1000  # Caractères par chunk
CHUNK_OVERLAP = 200  # Chevauchement entre chunks

def read_markdown_file(file_path: Path) -> str:
    """
    Lit un fichier markdown et renvoie son contenu
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        Contenu du fichier
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Découpe le texte en chunks pour l'embedding.
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

def process_markdown_file(file_path: Path, collection_name: str) -> int:
    """
    Traite un fichier markdown : découpe en chunks, génère embeddings, stocke dans Qdrant
    
    Args:
        file_path: Chemin vers le fichier
        collection_name: Nom de la collection Qdrant
        
    Returns:
        Nombre de chunks chargés
    """
    logger.info(f"Traitement du fichier : {file_path}")
    
    # Lire le contenu du fichier
    content = read_markdown_file(file_path)
    
    # Découper en chunks
    chunks = split_text_into_chunks(content)
    logger.info(f"Fichier découpé en {len(chunks)} chunks")
    
    # Extraire les métadonnées du fichier
    filename = file_path.name
    category = file_path.parent.name if file_path.parent.name != "knowledge" else "system"
    
    # Pour chaque chunk, générer l'embedding et stocker dans Qdrant
    for i, chunk in enumerate(chunks):
        # Métadonnées pour ce chunk
        metadata = {
            "source": filename,
            "category": category,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "created_at": time.time()
        }
        
        # Ajouter à Qdrant
        add_to_collection(collection_name, chunk, metadata)
        logger.info(f"Chunk {i+1}/{len(chunks)} ajouté à Qdrant")
        
    return len(chunks)

def main():
    """
    Fonction principale : traite tous les fichiers de la base de connaissances
    """
    logger.info("=== Chargement de la base de connaissances système dans Qdrant ===")
    
    # Vérifier que la collection existe, sinon la créer
    try:
        collection_info = get_collection_info(KNOWLEDGE_COLLECTION)
        logger.info(f"Collection '{KNOWLEDGE_COLLECTION}' existe déjà avec {collection_info.get('vectors_count', 0)} vecteurs")
    except:
        logger.info(f"Création de la collection '{KNOWLEDGE_COLLECTION}'")
        create_collection(KNOWLEDGE_COLLECTION, VECTOR_SIZE)
    
    # Chemin absolu vers le répertoire de connaissances
    knowledge_path = Path(os.path.dirname(os.path.abspath(__file__))) / KNOWLEDGE_DIR
    
    # Trouver tous les fichiers markdown
    markdown_files = list(knowledge_path.glob("**/*.md"))
    if not markdown_files:
        logger.warning(f"Aucun fichier markdown trouvé dans {knowledge_path}")
        return
    
    logger.info(f"Trouvé {len(markdown_files)} fichiers markdown à traiter")
    
    # Traiter chaque fichier
    total_chunks = 0
    for file_path in markdown_files:
        chunks_processed = process_markdown_file(file_path, KNOWLEDGE_COLLECTION)
        total_chunks += chunks_processed
    
    logger.info(f"=== Traitement terminé : {total_chunks} chunks chargés ===")
    
    # Afficher les informations sur la collection mise à jour
    collection_info = get_collection_info(KNOWLEDGE_COLLECTION)
    logger.info(f"Collection '{KNOWLEDGE_COLLECTION}' contient maintenant {collection_info.get('vectors_count', 0)} vecteurs")

if __name__ == "__main__":
    main()

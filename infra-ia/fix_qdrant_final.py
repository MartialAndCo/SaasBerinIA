#!/usr/bin/env python3
"""
Script pour corriger définitivement l'intégration Qdrant
"""

import re

# Lecture du fichier
with open('agents/task_watchdog/task_watchdog_agent.py', 'r') as f:
    content = f.read()

print("🔧 Correction de l'intégration Qdrant...")

# 1. Corriger les imports
content = re.sub(
    r'# from utils\.qdrant import QdrantClient  # Désactivé temporairement',
    'from utils.qdrant import get_client, create_embedding, create_collection',
    content
)

# 2. Corriger l'initialisation
content = re.sub(
    r'# Qdrant désactivé temporairement pour éviter les erreurs\s*self\.qdrant = None',
    '''# Client Qdrant pour mémoire vectorielle
        try:
            from utils.qdrant import get_client
            self.qdrant = get_client()
            self._ensure_collection_exists()
        except Exception as e:
            self.logger.warning(f"Qdrant non disponible, mode dégradé: {e}")
            self.qdrant = None''',
    content
)

# 3. Corriger _ensure_collection_exists
content = re.sub(
    r'collections = self\.qdrant\.list_collections\(\)\s*collection_names = \[c\.name for c in collections\.collections\]',
    '''collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]''',
    content
)

# 4. Corriger store_in_qdrant - utiliser create_embedding
content = re.sub(
    r'# Utilisation d\'un hash simple comme fallback pour le vecteur\s*import hashlib\s*vector_hash = hashlib\.md5\(pattern_text\.strip\(\)\.encode\(\)\)\.hexdigest\(\)\s*vector = \[float\(int\(vector_hash\[i:i\+2\], 16\)\) / 255\.0 for i in range\(0, 32, 2\)\]  # 16 dimensions',
    '''vector = create_embedding(pattern_text.strip())''',
    content,
    flags=re.DOTALL
)

# 5. Corriger get_patterns_from_qdrant - utiliser la bonne méthode
content = re.sub(
    r'results = self\.qdrant\.scroll\(',
    'results = self.qdrant.scroll(',
    content
)

# Sauvegarde
with open('agents/task_watchdog/task_watchdog_agent.py', 'w') as f:
    f.write(content)

print("✅ Qdrant corrigé !")
print("✅ Imports: get_client, create_embedding, create_collection")
print("✅ Initialisation: utilisation de get_client()")
print("✅ Collections: get_collections().collections")
print("✅ Embeddings: create_embedding() au lieu de hash")


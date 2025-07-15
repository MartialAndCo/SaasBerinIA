#!/usr/bin/env python3
"""
Service de vectorisation des connaissances BerinIA
Découpe les PDFs par métier et les vectorise dans Qdrant
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    import qdrant_client
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, VectorParams, Distance
    import requests
except ImportError as e:
    print(f"Dépendances manquantes: {e}")
    print("Installez avec: pip install sentence-transformers qdrant-client requests")
    exit(1)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeVectorizer:
    """Service de vectorisation des connaissances par métier"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialise le service avec la configuration"""
        self.config = self._load_config(config_path)
        self.qdrant_client = self._init_qdrant()
        self.embedding_model = self._init_embedding_model()
        self.collection_name = "berinia_knowledge"
        
        # Créer la collection si elle n'existe pas
        self._ensure_collection_exists()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Charge la configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            return {}
    
    def _init_qdrant(self) -> QdrantClient:
        """Initialise la connexion Qdrant"""
        qdrant_config = self.config.get("qdrant", {})
        host = qdrant_config.get("host", "localhost")
        port = qdrant_config.get("port", 6333)
        
        try:
            client = QdrantClient(host=host, port=port)
            # Test de connexion
            client.get_collections()
            logger.info(f"✅ Connexion Qdrant établie ({host}:{port})")
            return client
        except Exception as e:
            logger.error(f"❌ Impossible de se connecter à Qdrant: {e}")
            raise
    
    def _init_embedding_model(self) -> SentenceTransformer:
        """Initialise le modèle d'embedding"""
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        try:
            model = SentenceTransformer(model_name)
            logger.info(f"✅ Modèle d'embedding chargé: {model_name}")
            return model
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            raise
    
    def _ensure_collection_exists(self):
        """S'assure que la collection existe"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Créer la collection
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # Taille des vecteurs pour all-MiniLM-L6-v2
                        distance=Distance.COSINE
                    )
                )
                
                # Créer des index pour les métadonnées
                self.qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="metier",
                    field_schema="keyword"
                )
                
                self.qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="type",
                    field_schema="keyword"
                )
                
                logger.info(f"✅ Collection '{self.collection_name}' créée")
            else:
                logger.info(f"✅ Collection '{self.collection_name}' existe déjà")
                
        except Exception as e:
            logger.error(f"❌ Erreur création collection: {e}")
            raise
    
    def get_documents_from_api(self) -> List[Dict[str, Any]]:
        """Récupère les documents depuis l'API backend"""
        try:
            response = requests.get("http://localhost:8000/api/messenger/documents")
            if response.status_code == 200:
                data = response.json()
                return data.get('documents', [])
            else:
                logger.error(f"❌ Erreur API documents: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Erreur récupération documents: {e}")
            return []
    
    def get_document_content_direct(self, document_id: int) -> str:
        """Récupère le contenu pur d'un document directement depuis la base"""
        try:
            # Accès direct à la base via SQL pour récupérer le contenu pur
            import psycopg2
            
            # Configuration de la base depuis config.json
            db_config = self.config.get("db", {})
            conn = psycopg2.connect(
                host=db_config.get("host", "localhost"),
                database=db_config.get("database", "berinia"),
                user=db_config.get("user", "berinia_user"),
                password=db_config.get("password", "berinia_pass"),
                port=db_config.get("port", 5432)
            )
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT extracted_content, original_name 
                FROM messenger_documents 
                WHERE id = %s AND is_active = true
            """, (document_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                content, filename = result
                logger.info(f"✅ Contenu récupéré pour {filename}: {len(content)} caractères")
                return content
            else:
                logger.warning(f"⚠️ Aucun document trouvé avec l'ID {document_id}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération directe document {document_id}: {e}")
            return ""
    
    def get_all_documents_content_direct(self) -> List[Dict[str, Any]]:
        """Récupère le contenu pur de TOUS les documents actifs"""
        try:
            import psycopg2
            
            db_config = self.config.get("db", {})
            conn = psycopg2.connect(
                host=db_config.get("host", "localhost"),
                database=db_config.get("database", "berinia"),
                user=db_config.get("user", "berinia_user"),
                password=db_config.get("password", "berinia_pass"),
                port=db_config.get("port", 5432)
            )
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, extracted_content, original_name, file_size
                FROM messenger_documents 
                WHERE is_active = true AND extracted_content IS NOT NULL
                ORDER BY upload_date DESC
            """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            documents = []
            for doc_id, content, filename, file_size in results:
                documents.append({
                    "id": doc_id,
                    "content": content,
                    "filename": filename,
                    "file_size": file_size,
                    "content_length": len(content) if content else 0
                })
            
            logger.info(f"✅ {len(documents)} documents récupérés directement de la base")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération directe de tous les documents: {e}")
            return []
    
    def parse_content_by_metier(self, content: str, document_name: str = "unknown") -> List[Dict[str, Any]]:
        """Découpe le contenu par métier/secteur d'activité de manière intelligente"""
        chunks = []
        
        # 1. Découper d'abord par sections principales
        sections = self._split_into_sections(content)
        
        # 2. Traiter chaque section
        for section in sections:
            section_chunks = self._process_section(section, document_name)
            chunks.extend(section_chunks)
        
        logger.info(f"✅ {len(chunks)} chunks créés à partir du contenu")
        return chunks
    
    def _split_into_sections(self, content: str) -> List[Dict[str, Any]]:
        """Divise le contenu en sections logiques"""
        sections = []
        lines = content.split('\n')
        
        current_section = {
            "title": "",
            "content": "",
            "type": "general"
        }
        
        in_table = False
        table_headers_seen = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Détecter les titres de section
            if self._is_section_title(line):
                # Sauvegarder la section précédente si elle a du contenu
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Commencer une nouvelle section
                current_section = {
                    "title": line,
                    "content": "",
                    "type": self._classify_section_type(line)
                }
            
            # Détecter le début du tableau des métiers
            elif "Catégorie" in line and "Corps de métier" in line:
                # Sauvegarder la section précédente
                if current_section["content"].strip():
                    sections.append(current_section)
                
                current_section = {
                    "title": "Tableau des métiers",
                    "content": "",
                    "type": "tableau_metiers"
                }
                in_table = True
                table_headers_seen = True
                continue
            
            # Si on est dans le tableau, traiter ligne par ligne
            elif in_table and table_headers_seen:
                # Chaque ligne du tableau devient plusieurs sections métier
                if self._is_table_row(line):
                    # Sauvegarder la section précédente du tableau
                    if current_section["content"].strip():
                        sections.append(current_section)
                    
                    # Parser la ligne du tableau - récupère TOUS les métiers
                    metiers_info = self._parse_table_row(line)
                    
                    # Créer une section pour chaque métier trouvé
                    for i, metier_info in enumerate(metiers_info):
                        if i == 0:
                            # Premier métier remplace la section courante
                            current_section = {
                                "title": f"Métier: {metier_info['metier']}",
                                "content": metier_info["full_text"],
                                "type": "metier_specifique",
                                "metier": metier_info["metier"],
                                "categorie": metier_info["categorie"]
                            }
                        else:
                            # Métiers suivants sont ajoutés directement
                            sections.append({
                                "title": f"Métier: {metier_info['metier']}",
                                "content": metier_info["full_text"],
                                "type": "metier_specifique",
                                "metier": metier_info["metier"],
                                "categorie": metier_info["categorie"]
                            })
                else:
                    # Ligne de continuation du tableau
                    current_section["content"] += " " + line
            else:
                # Contenu normal de section
                current_section["content"] += line + "\n"
        
        # Ajouter la dernière section
        if current_section["content"].strip():
            sections.append(current_section)
        
        logger.info(f"📋 {len(sections)} sections identifiées")
        return sections
    
    def _is_section_title(self, line: str) -> bool:
        """Détermine si une ligne est un titre de section"""
        titles = [
            "Qui sommes-nous ?",
            "Ce que nous apportons à nos clients",
            "Notre méthode de déploiement",
            "En cas de doute : démonstration gratuite",
            "Pourquoi travailler avec nous ?"
        ]
        return line in titles or (line.endswith("?") and len(line) < 50)
    
    def _classify_section_type(self, title: str) -> str:
        """Classifie le type de section selon son titre"""
        if "apportons" in title.lower() or "solutions" in title.lower():
            return "produits"
        elif "méthode" in title.lower() or "déploiement" in title.lower():
            return "processus"
        elif "démonstration" in title.lower():
            return "demo"
        elif "pourquoi" in title.lower():
            return "avantages"
        else:
            return "general"
    
    def _is_table_row(self, line: str) -> bool:
        """Détermine si une ligne fait partie du tableau des métiers"""
        # Chercher des patterns typiques des lignes du tableau
        categories = ["Services", "Commerce", "Artisans", "Immobilier", "Bien-être", 
                     "Santé", "Restauration", "Formation", "Entreprises", "Logistique"]
        
        for cat in categories:
            if cat in line:
                return True
        
        # Ou si la ligne contient des métiers spécifiques
        metiers = ["Avocats", "Comptables", "Boutiques", "Plombiers", "Coiffeurs", 
                  "Restaurants", "Formateurs", "Infirmiers"]
        
        for metier in metiers:
            if metier in line:
                return True
        
        return False
    
    def _parse_table_row(self, line: str) -> List[Dict[str, Any]]:
        """Parse une ligne du tableau pour extraire TOUS les métiers de cette ligne"""
        results = []
        
        if len(line.strip()) < 10:
            return results
        
        text_lower = line.lower()
        
        # Identifier la catégorie
        categories_map = {
            "services": "Services professionnels",
            "commerce": "Commerce & E-commerce", 
            "artisans": "Artisans & BTP",
            "immobilier": "Immobilier & habitat",
            "bien-être": "Bien-être & beauté",
            "beauté": "Bien-être & beauté",
            "santé": "Santé & paramédical",
            "restauration": "Restauration & hôtellerie",
            "formation": "Formation & Éducation",
            "entreprises": "Entreprises de services",
            "logistique": "Logistique & terrain"
        }
        
        categorie = ""
        for key, cat in categories_map.items():
            if key in text_lower:
                categorie = cat
                break
        
        # Définir TOUS les métiers possibles avec leurs variantes
        all_metiers_map = {
            # Services professionnels
            "avocats": ["avocat", "avocats", "cabinet d'avocat", "juridique"],
            "comptables": ["comptable", "comptables", "expertise comptable", "expert comptable"],
            "notaires": ["notaire", "notaires", "office notarial"],
            "consultants": ["consultant", "consultants", "conseil", "conseiller"],
            
            # Commerce & E-commerce
            "boutiques": ["boutique", "boutiques", "magasin", "magasins"],
            "e-commerces": ["e-commerce", "ecommerce", "commerce en ligne", "boutique en ligne"],
            "magasins": ["magasin", "magasins", "commerce", "spécialisé"],
            
            # Artisans & BTP
            "plombiers": ["plombier", "plombiers", "plomberie"],
            "électriciens": ["électricien", "électriciens", "électricité"],
            "couvreurs": ["couvreur", "couvreurs", "couverture", "toiture"],
            "maçons": ["maçon", "maçons", "maçonnerie"],
            "menuisiers": ["menuisier", "menuisiers", "menuiserie"],
            "chauffagistes": ["chauffagiste", "chauffagistes", "chauffage"],
            
            # Immobilier & habitat
            "agences_immobilier": ["agence", "agences", "immobilier", "agence immobilière"],
            "conciergeries": ["conciergerie", "conciergeries", "concierge"],
            "syndics": ["syndic", "syndics", "copropriété"],
            
            # Bien-être & beauté
            "coiffeurs": ["coiffeur", "coiffeurs", "salon de coiffure", "coiffure"],
            "esthéticiennes": ["esthéticienne", "esthéticiennes", "esthétique", "beauté"],
            "spas": ["spa", "spas", "institut de beauté", "bien-être"],
            
            # Santé & paramédical
            "médecins": ["médecin", "médecins", "docteur", "cabinet médical"],
            "infirmiers": ["infirmier", "infirmiers", "infirmière", "soins"],
            "kinés": ["kiné", "kinés", "kinésithérapeute", "kinésithérapie"],
            "ostéos": ["ostéo", "ostéos", "ostéopathe", "ostéopathie"],
            "sages-femmes": ["sage-femme", "sages-femmes", "maternité"],
            
            # Restauration & hôtellerie
            "restaurants": ["restaurant", "restaurants", "restauration", "resto"],
            "hôtels": ["hôtel", "hôtels", "hôtellerie", "hébergement"],
            "traiteurs": ["traiteur", "traiteurs", "événementiel"],
            
            # Formation & Éducation
            "formateurs": ["formateur", "formateurs", "formation", "enseignement"],
            "cfa": ["cfa", "centre de formation", "apprentissage"],
            "auto-écoles": ["auto-école", "auto-écoles", "permis", "conduite"],
            
            # Entreprises de services
            "startups": ["startup", "startups", "start-up"],
            "freelances": ["freelance", "freelances", "indépendant", "travailleur indépendant"],
            "agences_com": ["agence", "communication", "marketing", "publicité"],
            
            # Logistique & terrain
            "livreurs": ["livreur", "livreurs", "livraison", "coursier"],
            "nettoyeurs": ["nettoyeur", "nettoyeurs", "nettoyage", "entretien"],
            "agents_terrain": ["agent", "terrain", "commercial", "technicien"]
        }
        
        # Chercher tous les métiers présents dans cette ligne
        detected_metiers = []
        for metier_key, variants in all_metiers_map.items():
            for variant in variants:
                if variant.lower() in text_lower:
                    detected_metiers.append(metier_key)
                    break  # Une seule détection par métier
        
        # Extraire les gains (pourcentages et bénéfices)
        gains_found = re.findall(r'[+\-]\d+%|\d+%', line)
        
        # Si aucun métier spécifique détecté mais on a une catégorie, créer un chunk générique
        if not detected_metiers and categorie:
            detected_metiers = [categorie.lower().replace(" ", "_")]
        
        # Créer un chunk pour chaque métier détecté
        for metier in detected_metiers:
            formatted_text = f"""Secteur: {categorie}
Métier spécifique: {metier}
Solutions BerinIA: {line.strip()}"""
            
            if gains_found:
                formatted_text += f"\nGains mesurés: {', '.join(gains_found)}"
            
            results.append({
                "metier": metier,
                "categorie": categorie,
                "metiers_specifiques": detected_metiers,
                "gains": gains_found,
                "full_text": formatted_text.strip()
            })
        
        return results
    
    def _process_section(self, section: Dict[str, Any], document_name: str) -> List[Dict[str, Any]]:
        """Traite une section et crée des chunks appropriés"""
        chunks = []
        
        content = section["content"].strip()
        if len(content) < 30:  # Ignorer les sections trop courtes
            return chunks
        
        # Déterminer le métier et le type selon la section
        if section["type"] == "metier_specifique":
            metier = section.get("metier", "général")
            content_type = "metier_detaille"
        else:
            metier = self._detect_metier_in_content(content)
            content_type = section["type"]
        
        # Créer le chunk
        chunk = {
            "content": content,
            "metier": metier,
            "type": content_type,
            "length": len(content),
            "source": document_name,
            "document_name": document_name,
            "section_title": section["title"]
        }
        
        # Ajouter les métadonnées spécifiques aux métiers
        if section["type"] == "metier_specifique":
            chunk["categorie"] = section.get("categorie", "")
            chunk["metiers_specifiques"] = section.get("metiers_specifiques", [])
        
        chunks.append(chunk)
        
        return chunks
    
    def _detect_metier_in_content(self, content: str) -> str:
        """Détecte le métier principal dans un contenu"""
        content_lower = content.lower()
        
        # Mapping plus précis des métiers
        metier_patterns = {
            "restaurant": ["restaurant", "restauration", "resto", "cuisine", "menu"],
            "coiffure": ["coiffeur", "coiffure", "cheveux", "salon", "coupe"],
            "garage": ["garage", "mécanique", "auto", "réparation", "voiture"],
            "sante": ["médecin", "santé", "patient", "soin", "cabinet"],
            "commerce": ["boutique", "magasin", "commerce", "vente"],
            "artisan": ["artisan", "plombier", "électricien", "btp"],
            "avocat": ["avocat", "juridique", "droit", "conseil"],
            "comptable": ["comptable", "comptabilité", "expert"],
            "immobilier": ["immobilier", "agence", "bien", "location"]
        }
        
        for metier, keywords in metier_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                return metier
        
        return "général"
    
    def _classify_content_type(self, content: str) -> str:
        """Classifie le type de contenu"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["produit", "solution", "outil", "logiciel"]):
            return "produits"
        elif any(word in content_lower for word in ["usage", "utilisation", "cas d'usage", "exemple"]):
            return "usages"
        elif any(word in content_lower for word in ["%", "gain", "économie", "bénéfice", "amélioration"]):
            return "gains"
        elif any(word in content_lower for word in ["prix", "tarif", "coût", "abonnement"]):
            return "tarification"
        else:
            return "général"
    
    def vectorize_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Vectorise les chunks avec le modèle d'embedding"""
        vectorized_chunks = []
        
        for i, chunk in enumerate(chunks):
            try:
                # Créer un texte enrichi pour l'embedding
                enriched_text = f"Métier: {chunk['metier']}. Type: {chunk['type']}. {chunk['content']}"
                
                # Générer l'embedding
                embedding = self.embedding_model.encode(enriched_text)
                
                # Créer l'ID unique
                chunk_id = hashlib.md5(chunk['content'].encode()).hexdigest()
                
                vectorized_chunk = {
                    "id": chunk_id,
                    "vector": embedding.tolist(),
                    "payload": {
                        "content": chunk['content'],
                        "metier": chunk['metier'],
                        "type": chunk['type'],
                        "length": chunk['length'],
                        "source": chunk['source'],
                        "created_at": datetime.now().isoformat()
                    }
                }
                
                vectorized_chunks.append(vectorized_chunk)
                
            except Exception as e:
                logger.error(f"❌ Erreur vectorisation chunk {i}: {e}")
        
        logger.info(f"✅ {len(vectorized_chunks)} chunks vectorisés")
        return vectorized_chunks
    
    def store_in_qdrant(self, vectorized_chunks: List[Dict[str, Any]]) -> bool:
        """Stocke les chunks vectorisés dans Qdrant"""
        try:
            points = []
            for chunk in vectorized_chunks:
                point = PointStruct(
                    id=chunk["id"],
                    vector=chunk["vector"],
                    payload=chunk["payload"]
                )
                points.append(point)
            
            # Insérer en batch
            operation_info = self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✅ {len(points)} chunks stockés dans Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur stockage Qdrant: {e}")
            return False
    
    def process_all_documents(self) -> Dict[str, Any]:
        """Traite tous les documents disponibles"""
        logger.info("🚀 Début du traitement des documents")
        
        # Récupérer la liste des documents
        documents = self.get_documents_from_api()
        
        if not documents:
            logger.warning("⚠️ Aucun document trouvé")
            return {"success": False, "message": "Aucun document disponible"}
        
        logger.info(f"📄 {len(documents)} documents trouvés")
        
        all_chunks = []
        
        # Récupérer le contenu pur de tous les documents
        documents = self.get_all_documents_content_direct()
        
        for doc in documents:
            content = doc["content"]
            if content and content.strip():
                logger.info(f"📄 Traitement de {doc['filename']} ({doc['content_length']} caractères)")
                
                # Découper ce document par métier
                chunks = self.parse_content_by_metier(content, doc["filename"])
                
                # Ajouter les métadonnées du document
                for chunk in chunks:
                    chunk["document_id"] = doc["id"]
                    chunk["document_name"] = doc["filename"]
                
                all_chunks.extend(chunks)
                logger.info(f"  ✅ {len(chunks)} chunks créés pour {doc['filename']}")
        
        if not all_chunks:
            return {"success": False, "message": "Aucun contenu exploitable trouvé"}
        
        # Vectoriser
        vectorized_chunks = self.vectorize_chunks(all_chunks)
        
        # Stocker dans Qdrant
        success = self.store_in_qdrant(vectorized_chunks)
        
        if success:
            return {
                "success": True,
                "message": f"Traitement terminé avec succès",
                "total_chunks": len(vectorized_chunks),
                "metiers_detected": list(set([c['metier'] for c in all_chunks])),
                "types_content": list(set([c['type'] for c in all_chunks]))
            }
        else:
            return {"success": False, "message": "Erreur lors du stockage"}
    
    def search_relevant_chunks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche les chunks les plus pertinents pour une requête"""
        try:
            # Vectoriser la requête
            query_embedding = self.embedding_model.encode(query)
            
            # Rechercher dans Qdrant
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                with_payload=True
            )
            
            # Formatter les résultats
            results = []
            for hit in search_result:
                result = {
                    "content": hit.payload.get("content", ""),
                    "metier": hit.payload.get("metier", ""),
                    "type": hit.payload.get("type", ""),
                    "score": hit.score,
                    "id": hit.id
                }
                results.append(result)
            
            logger.info(f"✅ {len(results)} chunks trouvés pour: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return []


def main():
    """Test du service de vectorisation"""
    print("🧪 Test du service de vectorisation BerinIA")
    print("=" * 50)
    
    try:
        # Initialiser le service
        vectorizer = KnowledgeVectorizer()
        
        # Traiter tous les documents
        result = vectorizer.process_all_documents()
        
        print(f"\n📊 Résultat du traitement:")
        print(f"   Succès: {result['success']}")
        print(f"   Message: {result['message']}")
        
        if result['success']:
            print(f"   Total chunks: {result['total_chunks']}")
            print(f"   Métiers détectés: {result['metiers_detected']}")
            print(f"   Types de contenu: {result['types_content']}")
            
            # Test de recherche
            print(f"\n🔍 Test de recherche sémantique:")
            test_queries = [
                "Je suis coiffeuse, que pouvez-vous m'apporter ?",
                "Restaurant automatisation",
                "Gains bénéfices amélioration"
            ]
            
            for query in test_queries:
                print(f"\n   Query: '{query}'")
                results = vectorizer.search_relevant_chunks(query, limit=3)
                for i, result in enumerate(results):
                    print(f"   {i+1}. [{result['metier']}|{result['type']}] Score: {result['score']:.3f}")
                    print(f"      {result['content'][:100]}...")
        
        print("\n✅ Test terminé")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

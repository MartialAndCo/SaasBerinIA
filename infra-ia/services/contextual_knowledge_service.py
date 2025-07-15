#!/usr/bin/env python3
"""
Service de récupération contextuelle des connaissances BerinIA
Analyse les messages utilisateur et récupère le contexte le plus pertinent
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from .knowledge_vectorizer import KnowledgeVectorizer
except ImportError:
    # Import direct si exécuté en standalone
    from knowledge_vectorizer import KnowledgeVectorizer

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextualKnowledgeService:
    """Service de récupération contextuelle des connaissances"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialise le service contextuel"""
        self.vectorizer = KnowledgeVectorizer(config_path)
        self.metiers_mapping = self._load_metiers_mapping()
    
    def _load_metiers_mapping(self) -> Dict[str, List[str]]:
        """Mapping des métiers avec mots-clés pour améliorer la détection"""
        return {
            "coiffeurs": ["coiffeur", "coiffure", "salon", "cheveux", "coupe", "coloration", "brushing"],
            "restaurants": ["restaurant", "resto", "cuisine", "chef", "serveur", "cuisinier", "brasserie", "bistrot", "pizzeria"],
            "avocats": ["avocat", "juridique", "droit", "cabinet", "conseil", "procédure", "notaire"],
            "comptables": ["comptable", "expertise", "comptabilité", "fiscal", "déclaration", "tva", "expert"],
            "plombiers": ["plombier", "plomberie", "artisan", "électricien", "chauffagiste", "btp"],
            "médecins": ["médecin", "docteur", "cabinet", "santé", "patient", "consultation", "clinique"],
            "infirmiers": ["infirmier", "kiné", "ostéo", "sage-femme", "paramédical", "soin"],
            "boutiques": ["boutique", "magasin", "commerce", "vente", "e-commerce", "en ligne"],
            "agences_immobilier": ["immobilier", "agence", "bien", "vente", "location", "appartement", "maison"],
            "formateurs": ["formation", "formateur", "enseignement", "cfa", "auto-école", "éducation"],
            "startups": ["startup", "entreprise", "freelance", "indépendant", "services"],
            "livreurs": ["livraison", "livreur", "logistique", "transport", "coursier"]
        }
    
    def detect_metier_from_context(self, message: str, lead_context: Dict[str, Any] = None) -> str:
        """Détecte le métier à partir du message et du contexte lead"""
        message_lower = message.lower()
        
        # 1. Vérifier d'abord le contexte lead (industry, company, etc.)
        if lead_context:
            industry = lead_context.get('industry', '').lower()
            company = lead_context.get('company', '').lower()
            position = lead_context.get('position', '').lower()
            
            # Rechercher dans les données du lead
            context_text = f"{industry} {company} {position}".lower()
            for metier, keywords in self.metiers_mapping.items():
                if any(keyword in context_text for keyword in keywords):
                    logger.info(f"🎯 Métier détecté via contexte lead: {metier}")
                    return metier
        
        # 2. Analyser le message directement
        for metier, keywords in self.metiers_mapping.items():
            if any(keyword in message_lower for keyword in keywords):
                logger.info(f"🎯 Métier détecté via message: {metier}")
                return metier
        
        # 3. Détection par patterns plus complexes
        patterns = {
            "restaurants": r"(je suis|mon|notre).*(restaurant|resto|cuisine|chef)",
            "coiffeurs": r"(salon|coiffeur|cheveux|coupe)",
            "avocats": r"(cabinet|avocat|juridique|droit)",
            "comptables": r"(comptable|expert|comptabilité)",
            "médecins": r"(médecin|docteur|cabinet|santé)",
            "boutiques": r"(boutique|magasin|commerce|vente)",
            "plombiers": r"(plombier|artisan|électricien|btp)"
        }
        
        for metier, pattern in patterns.items():
            if re.search(pattern, message_lower):
                logger.info(f"🎯 Métier détecté via pattern: {metier}")
                return metier
        
        return "général"
    
    def get_contextual_knowledge(self, message: str, lead_context: Dict[str, Any] = None, limit: int = 3) -> Dict[str, Any]:
        """Récupère le contexte le plus pertinent pour un message"""
        try:
            # 1. Détecter le métier
            detected_metier = self.detect_metier_from_context(message, lead_context)
            
            # 2. Construire une requête enrichie
            enhanced_query = self._build_enhanced_query(message, detected_metier, lead_context)
            
            # 3. Rechercher les chunks pertinents
            relevant_chunks = self.vectorizer.search_relevant_chunks(enhanced_query, limit=limit)
            
            # 4. Filtrer et optimiser les résultats
            optimized_chunks = self._optimize_chunks(relevant_chunks, detected_metier)
            
            # 5. Formater le contexte final
            formatted_context = self._format_context_for_louise(optimized_chunks, detected_metier)
            
            return {
                "success": True,
                "detected_metier": detected_metier,
                "enhanced_query": enhanced_query,
                "chunks_found": len(optimized_chunks),
                "formatted_context": formatted_context,
                "raw_chunks": optimized_chunks
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération contexte: {e}")
            return {
                "success": False,
                "error": str(e),
                "formatted_context": ""
            }
    
    def _build_enhanced_query(self, message: str, detected_metier: str, lead_context: Dict[str, Any] = None) -> str:
        """Construit une requête enrichie pour améliorer la recherche"""
        base_query = message
        
        # Ajouter le métier détecté
        if detected_metier != "général":
            base_query = f"{detected_metier} {base_query}"
        
        # Ajouter des mots-clés du contexte lead si disponible
        if lead_context:
            industry = lead_context.get('industry', '')
            if industry:
                base_query = f"{industry} {base_query}"
        
        # Ajouter des synonymes selon le type de question
        query_lower = message.lower()
        
        if any(word in query_lower for word in ["prix", "coût", "tarif", "combien"]):
            base_query += " tarification prix"
        elif any(word in query_lower for word in ["gain", "bénéfice", "amélioration", "résultat"]):
            base_query += " gains bénéfices pourcentage"
        elif any(word in query_lower for word in ["comment", "fonctionne", "utilise"]):
            base_query += " fonctionnement usage utilisation"
        elif any(word in query_lower for word in ["produit", "solution", "outil"]):
            base_query += " produits solutions outils"
        
        logger.info(f"🔍 Requête enrichie: '{base_query}'")
        return base_query
    
    def _optimize_chunks(self, chunks: List[Dict[str, Any]], detected_metier: str) -> List[Dict[str, Any]]:
        """Optimise les chunks trouvés selon le métier détecté"""
        if not chunks:
            return chunks
        
        # 1. Prioriser les chunks du métier spécifique
        metier_chunks = [c for c in chunks if c.get('metier') == detected_metier]
        other_chunks = [c for c in chunks if c.get('metier') != detected_metier]
        
        # 2. Prioriser les chunks "metier_detaille"
        detailed_chunks = [c for c in metier_chunks if c.get('type') == 'metier_detaille']
        general_chunks = [c for c in metier_chunks if c.get('type') != 'metier_detaille']
        
        # 3. Réorganiser par pertinence
        optimized = detailed_chunks + general_chunks + other_chunks[:2]  # Max 2 chunks autres métiers
        
        # 4. Éliminer les doublons de contenu
        seen_content = set()
        final_chunks = []
        
        for chunk in optimized:
            content_key = chunk.get('content', '')[:100]  # Premier 100 caractères
            if content_key not in seen_content:
                seen_content.add(content_key)
                final_chunks.append(chunk)
        
        logger.info(f"✅ {len(final_chunks)} chunks optimisés pour {detected_metier}")
        return final_chunks
    
    def _format_context_for_louise(self, chunks: List[Dict[str, Any]], detected_metier: str) -> str:
        """Formate le contexte pour injection dans le prompt de Louise"""
        if not chunks:
            return ""
        
        context_parts = []
        
        # En-tête avec métier détecté
        if detected_metier != "général":
            context_parts.append(f"🎯 CONTEXTE MÉTIER DÉTECTÉ: {detected_metier.upper()}")
        
        # Formater chaque chunk
        for i, chunk in enumerate(chunks, 1):
            metier = chunk.get('metier', 'général')
            content_type = chunk.get('type', 'général')
            content = chunk.get('content', '')
            
            # Nettoyer et raccourcir le contenu si nécessaire
            clean_content = self._clean_content(content)
            
            chunk_header = f"[{metier}|{content_type}]"
            context_parts.append(f"{i}. {chunk_header} {clean_content}")
        
        formatted_context = "\n".join(context_parts)
        
        # Ajouter des instructions spécifiques selon le métier
        if detected_metier != "général":
            instructions = self._get_metier_instructions(detected_metier)
            if instructions:
                formatted_context += f"\n\n💡 FOCUS {detected_metier.upper()}: {instructions}"
        
        logger.info(f"📝 Contexte formaté: {len(formatted_context)} caractères")
        return formatted_context
    
    def _clean_content(self, content: str) -> str:
        """Nettoie et optimise le contenu"""
        # Supprimer les retours à la ligne multiples
        content = re.sub(r'\n+', ' ', content)
        
        # Limiter la longueur si trop long
        if len(content) > 400:
            content = content[:400] + "..."
        
        return content.strip()
    
    def _get_metier_instructions(self, metier: str) -> str:
        """Retourne des instructions spécifiques selon le métier"""
        instructions_map = {
            "coiffeurs": "Mets en avant les solutions de réservation automatique et de rappels clients",
            "restaurants": "Insiste sur l'automatisation des réservations et la gestion des commandes",
            "avocats": "Souligne la prise de RDV automatique et le tri intelligent des appels",
            "comptables": "Met l'accent sur la gestion documentaire et l'automatisation administrative",
            "plombiers": "Privilégie les appels d'urgence et la qualification automatique des demandes",
            "médecins": "Focus sur la prise de RDV médicaux et le tri selon l'urgence",
            "boutiques": "Insiste sur le support client 24/7 et la gestion des commandes",
            "agences_immobilier": "Met en avant la qualification des prospects et les visites virtuelles"
        }
        
        return instructions_map.get(metier, "")
    
    def generate_contextual_prompt_injection(self, message: str, lead_context: Dict[str, Any] = None) -> str:
        """Génère l'injection de prompt contextuelle pour remplacer le PDF statique"""
        try:
            # Récupérer le contexte
            context_data = self.get_contextual_knowledge(message, lead_context, limit=3)
            
            if not context_data["success"]:
                logger.warning("⚠️ Échec récupération contexte, retour au mode générique")
                return "CONTEXTE: Solutions d'automatisation BerinIA adaptées à tous secteurs"
            
            # Formater pour injection
            injection = f"""CONTEXTE DYNAMIQUE BERINIA:
{context_data['formatted_context']}

☝️ Utilise UNIQUEMENT ces informations ciblées pour répondre de manière spécifique et pertinente."""
            
            logger.info(f"✅ Injection contextuelle générée: {len(injection)} caractères")
            return injection
            
        except Exception as e:
            logger.error(f"❌ Erreur génération injection: {e}")
            return "CONTEXTE: Solutions d'automatisation BerinIA"


def main():
    """Test du service contextuel"""
    print("🧪 Test du Service de Récupération Contextuelle BerinIA")
    print("=" * 60)
    
    try:
        # Initialiser le service
        service = ContextualKnowledgeService()
        
        # Test de différents messages
        test_cases = [
            {
                "message": "Je suis coiffeuse, ça m'apporte quoi concrètement ?",
                "lead_context": {"industry": "Beauté", "company": "Salon Marie"}
            },
            {
                "message": "Restaurant, je veux automatiser les réservations",
                "lead_context": {"position": "Gérant restaurant"}
            },
            {
                "message": "Cabinet d'avocat, quels sont les gains ?",
                "lead_context": None
            },
            {
                "message": "Combien ça coûte pour un garage ?",
                "lead_context": {"company": "Garage Auto Plus"}
            },
            {
                "message": "Je suis en e-commerce, ça marche comment ?",
                "lead_context": None
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n🔍 TEST {i}: {test['message']}")
            print(f"📊 Lead context: {test['lead_context']}")
            
            # Récupérer le contexte
            result = service.get_contextual_knowledge(
                test['message'], 
                test['lead_context']
            )
            
            if result['success']:
                print(f"✅ Métier détecté: {result['detected_metier']}")
                print(f"📄 {result['chunks_found']} chunks trouvés")
                print(f"📝 Contexte formaté:")
                print(result['formatted_context'])
                
                # Tester l'injection pour prompt
                injection = service.generate_contextual_prompt_injection(
                    test['message'], 
                    test['lead_context']
                )
                print(f"\n💉 Injection pour Louise:")
                print(injection[:300] + "..." if len(injection) > 300 else injection)
            else:
                print(f"❌ Erreur: {result['error']}")
            
            print("-" * 60)
        
        print("\n✅ Tests terminés")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

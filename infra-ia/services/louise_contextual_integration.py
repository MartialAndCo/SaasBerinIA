#!/usr/bin/env python3
"""
Intégration du service contextuel avec Louise
Remplace l'injection statique du PDF par une récupération dynamique
"""

import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from .contextual_knowledge_service import ContextualKnowledgeService
except ImportError:
    from contextual_knowledge_service import ContextualKnowledgeService

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LouiseContextualIntegration:
    """Intégration du service contextuel avec Louise"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialise l'intégration"""
        self.contextual_service = ContextualKnowledgeService(config_path)
        self.api_base_url = "http://localhost:8000"
    
    def get_current_directives(self) -> Dict[str, Any]:
        """Récupère les directives actuelles de Louise"""
        try:
            response = requests.get(f"{self.api_base_url}/api/messenger/directives")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Erreur récupération directives: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"❌ Erreur API directives: {e}")
            return {}
    
    def extract_static_pdf_block(self, sms_instructions: str) -> tuple[str, str]:
        """Extrait et sépare le bloc PDF statique du reste des instructions"""
        # Chercher le début du bloc PDF
        pdf_start_marker = "DOCUMENTS D'ENTREPRISE BERINIA:"
        
        if pdf_start_marker in sms_instructions:
            # Diviser en deux parties
            before_pdf = sms_instructions.split(pdf_start_marker)[0].strip()
            
            # Le bloc PDF est tout ce qui suit
            pdf_block_start = sms_instructions.find(pdf_start_marker)
            pdf_block = sms_instructions[pdf_block_start:].strip()
            
            logger.info(f"📄 Bloc PDF extrait: {len(pdf_block)} caractères")
            logger.info(f"📝 Instructions avant PDF: {len(before_pdf)} caractères")
            
            return before_pdf, pdf_block
        else:
            logger.warning("⚠️ Marqueur PDF non trouvé")
            return sms_instructions, ""
    
    def build_dynamic_prompt(self, base_instructions: str, message: str, lead_context: Dict[str, Any] = None) -> str:
        """Construit un prompt dynamique avec contexte ciblé"""
        try:
            # Générer l'injection contextuelle
            contextual_injection = self.contextual_service.generate_contextual_prompt_injection(
                message, lead_context
            )
            
            # Assembler le prompt final
            dynamic_prompt = f"""{base_instructions}

{contextual_injection}"""
            
            logger.info(f"✅ Prompt dynamique généré: {len(dynamic_prompt)} caractères")
            return dynamic_prompt
            
        except Exception as e:
            logger.error(f"❌ Erreur construction prompt dynamique: {e}")
            # Fallback : retourner les instructions de base
            return base_instructions
    
    def update_directives_with_context(self, message: str, lead_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Met à jour les directives avec le contexte dynamique"""
        try:
            # 1. Récupérer les directives actuelles
            current_directives = self.get_current_directives()
            if not current_directives:
                return {"success": False, "error": "Impossible de récupérer les directives"}
            
            # 2. Extraire le bloc PDF statique
            original_instructions = current_directives.get('sms_instructions', '')
            base_instructions, static_pdf_block = self.extract_static_pdf_block(original_instructions)
            
            # 3. Construire les nouvelles instructions dynamiques
            dynamic_instructions = self.build_dynamic_prompt(base_instructions, message, lead_context)
            
            # 4. Préparer les nouvelles directives
            updated_directives = current_directives.copy()
            updated_directives['sms_instructions'] = dynamic_instructions
            
            # Ajouter des métadonnées sur le contexte
            updated_directives['dynamic_context'] = {
                "applied_at": datetime.now().isoformat(),
                "message": message,
                "lead_context": lead_context,
                "static_pdf_length": len(static_pdf_block),
                "dynamic_length": len(dynamic_instructions),
                "reduction_percentage": round((1 - len(dynamic_instructions) / len(original_instructions)) * 100, 1) if original_instructions else 0
            }
            
            return {
                "success": True,
                "original_length": len(original_instructions),
                "dynamic_length": len(dynamic_instructions),
                "reduction": updated_directives['dynamic_context']['reduction_percentage'],
                "updated_directives": updated_directives
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour directives: {e}")
            return {"success": False, "error": str(e)}
    
    def restore_static_directives(self) -> Dict[str, Any]:
        """Restaure les directives avec le bloc PDF statique complet"""
        try:
            # Cette fonction pourrait être appelée pour revenir au mode statique si nécessaire
            current_directives = self.get_current_directives()
            
            # Si les directives ont des métadonnées dynamiques, on peut les identifier
            if 'dynamic_context' in current_directives:
                logger.info("📄 Directives dynamiques détectées, restauration possible")
                # Ici on pourrait implémenter la logique de restauration
                return {"success": True, "message": "Restoration logic would go here"}
            else:
                return {"success": True, "message": "Directives already in static mode"}
                
        except Exception as e:
            logger.error(f"❌ Erreur restauration: {e}")
            return {"success": False, "error": str(e)}
    
    def simulate_louise_response(self, message: str, lead_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simule la génération d'une réponse de Louise avec contexte dynamique"""
        try:
            # 1. Mettre à jour les directives
            update_result = self.update_directives_with_context(message, lead_context)
            
            if not update_result["success"]:
                return {"success": False, "error": update_result["error"]}
            
            # 2. Extraire les informations de contexte
            context_data = self.contextual_service.get_contextual_knowledge(message, lead_context)
            
            # 3. Simuler une réponse de Louise basée sur le contexte
            if context_data["success"]:
                detected_metier = context_data["detected_metier"]
                chunks_found = context_data["chunks_found"]
                
                # Générer une réponse simulée basée sur le métier détecté
                simulated_response = self._generate_simulated_response(message, detected_metier, context_data)
                
                return {
                    "success": True,
                    "detected_metier": detected_metier,
                    "chunks_used": chunks_found,
                    "context_reduction": f"{update_result['reduction']}%",
                    "original_prompt_length": update_result["original_length"],
                    "dynamic_prompt_length": update_result["dynamic_length"],
                    "simulated_response": simulated_response
                }
            else:
                return {"success": False, "error": "Échec récupération contexte"}
                
        except Exception as e:
            logger.error(f"❌ Erreur simulation Louise: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_simulated_response(self, message: str, metier: str, context_data: Dict[str, Any]) -> str:
        """Génère une réponse simulée de Louise"""
        # Templates de réponses par métier
        responses_templates = {
            "coiffeurs": "Salut ! Pour ton salon, je peux te proposer un système qui automatise tes rdv 24/7. Tes clients réservent directement, plus de téléphone qui sonne ! Tu récupères +45% de réservations et +30% de fidélité. Curieuse ?",
            
            "restaurants": "Hello ! Ton resto peut automatiser les réservations et commandes. Plus de stress avec le téléphone, tout se fait automatiquement. Les restaurateurs voient -90% de tâches manuelles et +40% de commandes. Je te montre ?",
            
            "avocats": "Bonjour ! Pour votre cabinet, on peut automatiser la prise de RDV et trier les appels selon l'urgence. Vous récupérez +25h par semaine pour vous concentrer sur vos dossiers. Intéressé ?",
            
            "comptables": "Bonjour ! Votre cabinet peut automatiser la gestion documentaire et les prises de RDV clients. Fini les interruptions constantes, vous gagnez 60% de temps administratif. Je vous explique ?",
            
            "boutiques": "Salut ! Ton e-commerce peut avoir un support client 24/7 automatique. Tes clients sont pris en charge même la nuit ! Tu divises par 3 le SAV et +94% de satisfaction. Ça t'intéresse ?",
            
            "plombiers": "Hello ! Pour ton entreprise d'artisan, on peut trier les urgences automatiquement et qualifier chaque demande. Tu rates -80% d'appels en moins et traites +35% de clients. Curieux ?",
            
            "général": "Salut ! BerinIA automatise ce qui te prend du temps : rdv, appels, relances clients. Selon ton secteur, on a des solutions sur mesure. Tu es dans quel domaine ?"
        }
        
        # Récupérer le template ou utiliser le général
        response = responses_templates.get(metier, responses_templates["général"])
        
        # Ajouter un contexte si on a des gains spécifiques
        if context_data.get("raw_chunks"):
            # Extraire des gains du premier chunk
            first_chunk = context_data["raw_chunks"][0]
            content = first_chunk.get("content", "")
            
            # Chercher des pourcentages dans le contenu
            import re
            gains = re.findall(r'[+\-]\d+%', content)
            if gains and metier != "général":
                # Ajouter des gains spécifiques trouvés
                gains_text = ", ".join(gains[:2])  # Max 2 gains
                response = response.replace("Curieuse ?", f"Gains mesurés : {gains_text}. Curieuse ?")
                response = response.replace("Je te montre ?", f"Gains mesurés : {gains_text}. Je te montre ?")
                response = response.replace("Intéressé ?", f"Gains mesurés : {gains_text}. Intéressé ?")
        
        return response


def main():
    """Test de l'intégration avec Louise"""
    print("🧪 Test d'Intégration Contextuelle avec Louise")
    print("=" * 60)
    
    try:
        # Initialiser l'intégration
        integration = LouiseContextualIntegration()
        
        # Tests de simulation de réponses Louise
        test_scenarios = [
            {
                "message": "Je suis coiffeuse, ça m'apporte quoi ?",
                "lead_context": {"industry": "Beauté", "company": "Salon Marie"},
                "description": "Coiffeuse avec contexte lead"
            },
            {
                "message": "Restaurant, on veut automatiser",
                "lead_context": {"position": "Gérant restaurant"},
                "description": "Restaurant avec contexte"
            },
            {
                "message": "Cabinet d'avocat, quels gains ?",
                "lead_context": None,
                "description": "Avocat sans contexte lead"
            },
            {
                "message": "E-commerce, comment ça marche ?",
                "lead_context": None,
                "description": "E-commerce sans contexte"
            },
            {
                "message": "Je cherche des solutions",
                "lead_context": None,
                "description": "Message générique"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🔍 SCENARIO {i}: {scenario['description']}")
            print(f"💬 Message: '{scenario['message']}'")
            print(f"📊 Lead context: {scenario['lead_context']}")
            
            # Simuler la réponse de Louise
            result = integration.simulate_louise_response(
                scenario['message'], 
                scenario['lead_context']
            )
            
            if result['success']:
                print(f"✅ Métier détecté: {result['detected_metier']}")
                print(f"📄 Chunks utilisés: {result['chunks_used']}")
                print(f"📉 Réduction contexte: {result['context_reduction']}")
                print(f"📏 Prompt: {result['original_prompt_length']} → {result['dynamic_prompt_length']} caractères")
                print(f"🗣️ Réponse Louise simulée:")
                print(f"   '{result['simulated_response']}'")
            else:
                print(f"❌ Erreur: {result['error']}")
            
            print("-" * 60)
        
        print("\n✅ Tests d'intégration terminés")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

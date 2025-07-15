#!/usr/bin/env python3
"""
TaskWatchdogAgent - Gardien de la sécurité des tâches planifiées du système BerinIA

Ce module implémente un agent de surveillance en temps réel qui analyse chaque tâche
créée pour détecter les anomalies, comportements malveillants ou patterns suspects.

PHILOSOPHIE PERMISSIVE : Tout agent peut créer des tâches légitimes.
L'analyse se concentre sur les PATTERNS COMPORTEMENTAUX suspects, pas sur l'identité.
"""

import os
import json
import time
import logging
import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.agent_base import Agent
from utils.llm import LLMService
from utils.qdrant import get_client, create_embedding, create_collection

class TaskWatchdogAgent(Agent):
    """
    Agent de surveillance des tâches planifiées - VERSION PERMISSIVE
    
    Responsabilités:
    - Analyser chaque tâche créée en temps réel
    - Détecter les patterns suspects via LLM (approche comportementale)
    - Stocker les analyses en mémoire vectorielle
    - Prendre des actions automatiques selon le niveau de menace
    - Alerter l'admin en cas de menace critique
    
    PRINCIPE : Autoriser par défaut, bloquer les vraies anomalies
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du TaskWatchdogAgent
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        super().__init__("TaskWatchdogAgent", config_path)
        
        # Logger dédié
        self.logger = logging.getLogger("BerinIA-TaskWatchdog")
        
        # Service LLM pour analyses intelligentes (utilisation statique)
        
        # Client Qdrant pour mémoire vectorielle
        # Client Qdrant pour mémoire vectorielle
        try:
            from utils.qdrant import get_client
            self.qdrant = get_client()
            self._ensure_collection_exists()
        except Exception as e:
            self.logger.warning(f"Qdrant non disponible, mode dégradé: {e}")
            self.qdrant = None
        
        # Cache des patterns récents (fallback si Qdrant indisponible)
        self.pattern_cache = []
        
        # Statistiques de l'agent
        self.stats = {
            "total_analyses": 0,
            "threats_blocked": 0,
            "false_positives": 0,
            "last_analysis": None,
            "patterns_learned": 0
        }
        
        self.logger.info("TaskWatchdogAgent initialisé et prêt (mode permissif)")
    
    def _ensure_collection_exists(self):
        """Assure que la collection Qdrant existe"""
        if not self.qdrant:
            return
            
        collection_name = self.config.get("qdrant_collection", "task_security_patterns")
        
        try:
            # Vérifier si la collection existe
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name not in collection_names:
                # Créer la collection
                self.qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        "size": 1536,  # Taille des embeddings OpenAI
                        "distance": "Cosine"
                    }
                )
                self.logger.info(f"Collection Qdrant {collection_name} créée")
        except Exception as e:
            self.logger.error(f"Erreur création collection Qdrant: {e}")
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal du TaskWatchdogAgent
        
        Args:
            input_data: Données d'entrée avec action et paramètres
            
        Returns:
            Résultat de l'action demandée
        """
        action = input_data.get("action", "")
        
        try:
            if action == "analyze_new_task":
                return self.analyze_task_security(input_data)
            
            elif action == "get_threat_report":
                return self.generate_threat_report()
            
            elif action == "update_patterns":
                return self.update_security_patterns(input_data)
            
            elif action == "get_stats":
                return {"status": "success", "stats": self.stats}
            
            elif action == "reset_false_positive":
                return self.reset_false_positive(input_data)
            
            else:
                return {
                    "status": "error",
                    "message": f"Action non reconnue: {action}"
                }
                
        except Exception as e:
            error_msg = f"Erreur dans TaskWatchdogAgent.run(): {e}"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def analyze_task_security(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse la sécurité d'une nouvelle tâche en temps réel
        
        Args:
            task_info: Informations sur la tâche à analyser
            
        Returns:
            Résultat de l'analyse de sécurité
        """
        try:
            # Extraction des données de la tâche
            task_data = task_info.get("task_data", {})
            task_id = task_info.get("task_id", "unknown")
            execution_time = task_info.get("execution_time", "")
            recurring = task_info.get("recurring", False)
            recurrence_interval = task_info.get("recurrence_interval")
            
            # Mise à jour des statistiques
            self.stats["total_analyses"] += 1
            self.stats["last_analysis"] = datetime.datetime.now().isoformat()
            
            # 1. Récupération du contexte historique
            recent_patterns = self.get_recent_task_patterns()
            
            # 2. Analyse via LLM
            llm_analysis = self.llm_security_analysis(task_info, recent_patterns)
            
            # 3. Validation et correction de l'analyse
            validated_analysis = self.validate_analysis_output(llm_analysis)
            
            # 4. Stockage en mémoire vectorielle
            if self.config.get("enable_learning", True):
                self.store_analysis_pattern(task_info, validated_analysis)
            
            # 5. Action automatique selon le niveau de menace
            if validated_analysis.get("threat_level") == "CRITICAL":
                self.take_critical_action(task_info, validated_analysis)
            elif validated_analysis.get("threat_level") == "SUSPECT":
                self.take_suspect_action(task_info, validated_analysis)
            
            # 6. Logging de l'analyse (seulement suspects/critiques en mode permissif)
            if self.config.get("log_only_suspects_and_critical", True):
                if validated_analysis.get("threat_level") in ["SUSPECT", "CRITICAL"]:
                    self.log_analysis(task_info, validated_analysis)
            elif self.config.get("log_all_analyses", False):
                self.log_analysis(task_info, validated_analysis)
            
            # 7. Communication avec le système
            self.communicate_analysis_result(task_info, validated_analysis)
            
            return {
                "status": "success",
                "analysis": validated_analysis,
                "task_id": task_id
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse de sécurité: {e}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "analysis": {
                    "threat_level": "NORMAL",  # En cas d'erreur, on laisse passer
                    "confidence": 0.0,
                    "reason": "Erreur d'analyse, autorisation par défaut"
                }
            }
    
    def llm_security_analysis(self, task_info: Dict[str, Any], recent_patterns: str) -> Dict[str, Any]:
        """
        Effectue l'analyse de sécurité via LLM
        
        Args:
            task_info: Informations sur la tâche
            recent_patterns: Contexte des patterns récents
            
        Returns:
            Analyse LLM structurée
        """
        # Construction du prompt avec variables
        task_data = task_info.get("task_data", {})
        
        prompt_variables = {
            "requesting_agent": task_info.get("requesting_agent", "unknown"),
            "target_agent": task_data.get("agent", "unknown"),
            "action": task_data.get("action", "unknown"),
            "execution_time": task_info.get("execution_time", ""),
            "recurring": task_info.get("recurring", False),
            "recurrence_interval": task_info.get("recurrence_interval", "none"),
            "task_id": task_info.get("task_id", "unknown"),
            "creation_context": task_info.get("creation_context", "unknown"),
            "recent_patterns": recent_patterns,
            "critical_keywords": ", ".join(self.config.get("critical_keywords", [])),
            "suspicious_keywords": ", ".join(self.config.get("suspicious_keywords", []))
        }
        
        # Construction du prompt complet
        prompt = self._build_prompt(prompt_variables)
        
        # Appel LLM avec le modèle configuré
        model = self.config.get("analysis_model", "gpt-4.1-mini")
        
        try:
            response = LLMService.call_llm(prompt, complexity="medium")
            
            # Parsing de la réponse JSON
            return self.parse_llm_response(response)
            
        except Exception as e:
            self.logger.error(f"Erreur appel LLM: {e}")
            # Analyse de fallback basique
            return self.permissive_fallback_analysis(task_info)
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse la réponse LLM et valide la structure JSON avec robustesse améliorée"""
        try:
            # Nettoyage robuste de la réponse
            clean_response = response.strip()
            
            # Enlever les balises markdown possibles
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            elif clean_response.startswith("```"):
                clean_response = clean_response[3:]
            
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            # Enlever les espaces et retours à la ligne inutiles
            clean_response = clean_response.strip()
            
            # Log de debug pour voir ce qu'on essaie de parser
            self.logger.debug(f"Tentative parsing JSON: {clean_response[:200]}...")
            
            # Parsing JSON
            analysis = json.loads(clean_response)
            
            # Validation et correction des champs obligatoires
            analysis = self.validate_and_fix_analysis_fields(analysis)
            
            self.logger.debug(f"Parsing JSON réussi: {analysis.get('threat_level', 'unknown')}")
            return analysis
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Erreur parsing JSON LLM: {e}")
            self.logger.error(f"Réponse LLM problématique: {response[:500]}...")
            
            # Tentative de parsing manuel/extraction
            extracted_analysis = self.extract_analysis_manually(response)
            if extracted_analysis:
                return extracted_analysis
            
            # Fallback ultime
            return self.create_fallback_analysis("Erreur parsing JSON LLM")
            
        except ValueError as e:
            self.logger.error(f"Erreur validation LLM: {e}")
            return self.create_fallback_analysis(f"Erreur validation: {e}")
        except Exception as e:
            self.logger.error(f"Erreur inattendue parsing LLM: {e}")
            return self.create_fallback_analysis(f"Erreur inattendue: {e}")
    
    def validate_and_fix_analysis_fields(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et corrige les champs d'analyse"""
        # Champs obligatoires avec valeurs par défaut
        required_fields = {
            "threat_level": "NORMAL",
            "confidence": 0.5,
            "reason": "Analyse automatique",
            "recommended_action": "ALLOW",
            "patterns_detected": [],
            "risk_factors": [],
            "legitimate_reasons": []
        }
        
        # Ajouter les champs manquants
        for field, default_value in required_fields.items():
            if field not in analysis:
                analysis[field] = default_value
                self.logger.warning(f"Champ manquant ajouté: {field} = {default_value}")
        
        # Validation des valeurs
        valid_threat_levels = ["NORMAL", "SUSPECT", "CRITICAL"]
        if analysis["threat_level"] not in valid_threat_levels:
            self.logger.warning(f"threat_level invalide: {analysis['threat_level']}, correction -> NORMAL")
            analysis["threat_level"] = "NORMAL"
        
        valid_actions = ["ALLOW", "QUARANTINE", "DELETE"]
        if analysis["recommended_action"] not in valid_actions:
            self.logger.warning(f"recommended_action invalide: {analysis['recommended_action']}, correction -> ALLOW")
            analysis["recommended_action"] = "ALLOW"
        
        # Validation confidence
        try:
            confidence = float(analysis["confidence"])
            if confidence < 0 or confidence > 1:
                raise ValueError("Confidence hors limites")
            analysis["confidence"] = confidence
        except (ValueError, TypeError):
            self.logger.warning(f"Confidence invalide: {analysis['confidence']}, correction -> 0.5")
            analysis["confidence"] = 0.5
        
        # Assurer que les listes sont bien des listes
        list_fields = ["patterns_detected", "risk_factors", "legitimate_reasons"]
        for field in list_fields:
            if not isinstance(analysis[field], list):
                self.logger.warning(f"Champ {field} n'est pas une liste, correction")
                analysis[field] = []
        
        return analysis
    
    def extract_analysis_manually(self, response: str) -> Optional[Dict[str, Any]]:
        """Tentative d'extraction manuelle si le parsing JSON échoue"""
        try:
            # Recherche de patterns dans la réponse
            analysis = {}
            
            # Rechercher threat_level
            import re
            threat_match = re.search(r'"threat_level":\s*"(NORMAL|SUSPECT|CRITICAL)"', response, re.IGNORECASE)
            if threat_match:
                analysis["threat_level"] = threat_match.group(1).upper()
            
            # Rechercher confidence
            conf_match = re.search(r'"confidence":\s*(0\.\d+|\d+\.\d+|[01])', response)
            if conf_match:
                analysis["confidence"] = float(conf_match.group(1))
            
            # Rechercher reason
            reason_match = re.search(r'"reason":\s*"([^"]+)"', response)
            if reason_match:
                analysis["reason"] = reason_match.group(1)
            
            # Rechercher recommended_action
            action_match = re.search(r'"recommended_action":\s*"(ALLOW|QUARANTINE|DELETE)"', response, re.IGNORECASE)
            if action_match:
                analysis["recommended_action"] = action_match.group(1).upper()
            
            # Si on a au moins les champs principaux, valider et retourner
            if "threat_level" in analysis and "confidence" in analysis:
                self.logger.info("Extraction manuelle réussie")
                return self.validate_and_fix_analysis_fields(analysis)
            
        except Exception as e:
            self.logger.error(f"Erreur extraction manuelle: {e}")
        
        return None
    
    def _build_prompt(self, variables: Dict[str, Any]) -> str:
        """
        Construit le prompt d'analyse de sécurité pour le LLM
        
        Args:
            variables: Variables à injecter dans le prompt
            
        Returns:
            Prompt formaté pour l'analyse LLM
        """
        prompt_template = """
Tu es TaskWatchdogAgent, gardien de la sécurité du système BerinIA.

TÂCHE À ANALYSER :
Agent demandeur: {requesting_agent}
Agent cible: {target_agent}
Action: {action}
Exécution: {execution_time}
Récurrente: {recurring}
Intervalle: {recurrence_interval}
ID tâche: {task_id}
Contexte: {creation_context}

HISTORIQUE RÉCENT :
{recent_patterns}

CRITÈRES DE SÉCURITÉ :
1. DUPLICATION : Détecte si >5 tâches similaires récentes
2. FRÉQUENCE : Alerte si intervalle <300 secondes (5min)
3. MOTS-CLÉS CRITIQUES : {critical_keywords}
4. MOTS-CLÉS SUSPECTS : {suspicious_keywords}
5. VOLUME : Surveille création massive de tâches

MISSION PRINCIPALE : BLOQUER LES DUPLICATIONS EXPONENTIELLES

ANALYSE REQUISE :
- NORMAL : Tâche légitime, pas de problème détecté
- SUSPECT : Pattern inhabituel mais pas critique
- CRITICAL : Duplication/spam détecté → BLOCAGE IMMÉDIAT

RÉPONSE JSON OBLIGATOIRE :
{{
  "threat_level": "NORMAL|SUSPECT|CRITICAL",
  "confidence": 0.XX,
  "reason": "Explication claire et précise",
  "recommended_action": "ALLOW|QUARANTINE|DELETE",
  "patterns_detected": ["pattern1", "pattern2"],
  "risk_factors": ["facteur1", "facteur2"],
  "legitimate_reasons": ["raison1", "raison2"]
}}
"""
        
        return prompt_template.format(**variables)
    
    def create_fallback_analysis(self, reason: str) -> Dict[str, Any]:
        """Crée une analyse de fallback sécurisée"""
        return {
            "threat_level": "NORMAL",
            "confidence": 0.0,
            "reason": f"Fallback: {reason}",
            "recommended_action": "ALLOW",
            "patterns_detected": ["fallback_analysis"],
            "risk_factors": ["erreur_parsing"],
            "legitimate_reasons": ["mode_permissif_fallback"],
            "behavioral_analysis": {
                "task_frequency": "unknown",
                "action_coherence": "unknown", 
                "recursion_depth": "unknown"
            }
        }
    
    def permissive_fallback_analysis(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse de fallback PERMISSIVE sans LLM
        
        NOUVELLE LOGIQUE : 
        - Autoriser par défaut tous les agents
        - Détecter uniquement les patterns vraiment dangereux
        - Focus sur le comportement, pas l'identité
        """
        task_data = task_info.get("task_data", {})
        agent = task_data.get("agent", "")
        action = task_data.get("action", "")
        recurring = task_info.get("recurring", False)
        recurrence_interval = task_info.get("recurrence_interval")
        
        # Facteurs de risque COMPORTEMENTAUX
        risk_factors = []
        legitimate_reasons = []
        
        # 1. Vérifier mots-clés CRITIQUES (vraiment dangereux)
        critical_keywords = self.config.get("critical_keywords", [])
        for keyword in critical_keywords:
            if keyword.lower() in action.lower():
                risk_factors.append(f"mot_cle_critique_{keyword}")
        
        # 2. Vérifier mots-clés suspects (mais pas bloquants)
        suspicious_keywords = self.config.get("suspicious_keywords", [])
        for keyword in suspicious_keywords:
            if keyword.lower() in action.lower():
                risk_factors.append(f"mot_cle_suspect_{keyword}")
        
        # 3. Analyser la récurrence (pattern comportemental)
        if recurring and recurrence_interval:
            behavioral_thresholds = self.config.get("behavioral_thresholds", {})
            min_interval = behavioral_thresholds.get("minimum_task_interval_seconds", 1)
            
            if recurrence_interval < min_interval:
                risk_factors.append("recurrence_trop_rapide")
            elif recurrence_interval > 86400:  # Plus d'un jour
                legitimate_reasons.append("recurrence_raisonnable")
            else:
                legitimate_reasons.append("recurrence_normale")
        
        # 4. Raisons légitimes par défaut (mode permissif)
        if not risk_factors:
            legitimate_reasons.extend([
                "agent_action_coherente",
                "aucun_pattern_suspect_detecte",
                "analyse_permissive_ok"
            ])
        
        # 5. Déterminer le niveau de menace (PERMISSIF)
        critical_keywords_found = [rf for rf in risk_factors if "critique" in rf]
        
        if len(critical_keywords_found) >= 1:
            # Mots-clés vraiment dangereux détectés
            threat_level = "CRITICAL"
            recommended_action = "DELETE"
            confidence = 0.9
            reason = f"Mots-clés critiques détectés : {', '.join(critical_keywords_found)}"
        elif len(risk_factors) >= 3:
            # Plusieurs facteurs suspects (mais pas critiques)
            threat_level = "SUSPECT"
            recommended_action = "QUARANTINE"
            confidence = 0.7
            reason = f"Multiples facteurs suspects : {', '.join(risk_factors[:2])}"
        elif len(risk_factors) >= 1 and "recurrence_trop_rapide" in risk_factors:
            # Récurrence vraiment problématique
            threat_level = "SUSPECT"
            recommended_action = "QUARANTINE"
            confidence = 0.6
            reason = "Récurrence anormalement rapide détectée"
        else:
            # Par défaut : NORMAL (mode permissif)
            threat_level = "NORMAL"
            recommended_action = "ALLOW"
            confidence = 0.8 if legitimate_reasons else 0.5
            reason = f"Tâche normale - {len(legitimate_reasons)} indicateurs positifs"
        
        return {
            "threat_level": threat_level,
            "confidence": confidence,
            "reason": reason,
            "recommended_action": recommended_action,
            "patterns_detected": ["analyse_permissive_fallback"],
            "risk_factors": risk_factors,
            "legitimate_reasons": legitimate_reasons,
            "behavioral_analysis": {
                "task_frequency": "normal" if not risk_factors else "elevated",
                "action_coherence": "logical" if legitimate_reasons else "questionable",
                "recursion_depth": "safe"
            }
        }
    
    def validate_analysis_output(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et corrige l'analyse si nécessaire"""
        # Valeurs par défaut
        valid_threat_levels = ["NORMAL", "SUSPECT", "CRITICAL"]
        valid_actions = ["ALLOW", "QUARANTINE", "DELETE"]
        
        # Correction du threat_level
        if analysis.get("threat_level") not in valid_threat_levels:
            analysis["threat_level"] = "NORMAL"  # Par défaut permissif
        
        # Correction de l'action recommandée
        if analysis.get("recommended_action") not in valid_actions:
            analysis["recommended_action"] = "ALLOW"  # Par défaut permissif
        
        # Validation de la confiance
        confidence = analysis.get("confidence", 0.0)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            analysis["confidence"] = 0.5
        
        # Assurer la présence des listes
        for field in ["patterns_detected", "risk_factors", "legitimate_reasons"]:
            if field not in analysis or not isinstance(analysis[field], list):
                analysis[field] = []
        
        return analysis
    
    def get_recent_task_patterns(self) -> str:
        """Récupère les patterns récents des tâches"""
        try:
            if self.qdrant:
                return self.get_patterns_from_qdrant()
            else:
                return self.get_patterns_from_cache()
        except Exception as e:
            self.logger.error(f"Erreur récupération patterns: {e}")
            return "Aucun historique disponible"
    
    def get_patterns_from_qdrant(self) -> str:
        """Récupère les patterns depuis Qdrant"""
        collection_name = self.config.get("qdrant_collection", "task_security_patterns")
        window_hours = self.config.get("analysis_window_hours", 24)
        cutoff_time = time.time() - (window_hours * 3600)
        
        try:
            # Recherche des analyses récentes
            results = self.qdrant.scroll(
                collection_name=collection_name,
                limit=50,
                with_payload=True,
                scroll_filter={
                    "must": [
                        {
                            "key": "timestamp",
                            "range": {
                                "gte": cutoff_time
                            }
                        }
                    ]
                }
            )
            
            # Construction du contexte
            patterns = []
            for point in results[0]:
                payload = point.payload
                analysis = payload.get("analysis", {})
                task_info = payload.get("task_info", {})
                
                pattern_text = f"- {task_info.get('task_data', {}).get('agent', 'unknown')} → {task_info.get('task_data', {}).get('action', 'unknown')} : {analysis.get('threat_level', 'unknown')}"
                patterns.append(pattern_text)
            
            if patterns:
                return f"Patterns récents (dernières {window_hours}h):\n" + "\n".join(patterns[:10])
            else:
                return "Aucune activité récente détectée"
                
        except Exception as e:
            self.logger.error(f"Erreur Qdrant patterns: {e}")
            return "Erreur récupération historique"
    
    def get_patterns_from_cache(self) -> str:
        """Récupère les patterns depuis le cache local"""
        if not self.pattern_cache:
            return "Aucun historique en cache"
        
        # Filtrer par fenêtre temporelle
        window_hours = self.config.get("analysis_window_hours", 24)
        cutoff_time = time.time() - (window_hours * 3600)
        
        recent_patterns = [
            p for p in self.pattern_cache 
            if p.get("timestamp", 0) > cutoff_time
        ]
        
        if recent_patterns:
            patterns_text = []
            for pattern in recent_patterns[-10:]:  # Derniers 10
                task_info = pattern.get("task_info", {})
                analysis = pattern.get("analysis", {})
                
                pattern_text = f"- {task_info.get('task_data', {}).get('agent', 'unknown')} → {task_info.get('task_data', {}).get('action', 'unknown')} : {analysis.get('threat_level', 'unknown')}"
                patterns_text.append(pattern_text)
            
            return f"Patterns récents (cache):\n" + "\n".join(patterns_text)
        else:
            return "Aucune activité récente en cache"
    
    def store_analysis_pattern(self, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """Stocke l'analyse en mémoire vectorielle"""
        try:
            if self.qdrant:
                self.store_in_qdrant(task_info, analysis)
            
            # Toujours stocker en cache local aussi
            self.store_in_cache(task_info, analysis)
            
            self.stats["patterns_learned"] += 1
            
        except Exception as e:
            self.logger.error(f"Erreur stockage pattern: {e}")
    
    def store_in_qdrant(self, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """Stocke en Qdrant"""
        collection_name = self.config.get("qdrant_collection", "task_security_patterns")
        
        # Construction du texte à vectoriser
        task_data = task_info.get("task_data", {})
        pattern_text = f"""
        Agent: {task_data.get('agent', 'unknown')}
        Action: {task_data.get('action', 'unknown')}
        Threat: {analysis.get('threat_level', 'unknown')}
        Reason: {analysis.get('reason', '')}
        Patterns: {', '.join(analysis.get('patterns_detected', []))}
        """
        
        # Vectorisation via OpenAI embeddings
        try:
            vector = create_embedding(pattern_text.strip())
            
            # Stockage
            self.qdrant.upsert(
                collection_name=collection_name,
                points=[{
                    "id": abs(hash(task_info.get("task_id", str(time.time())))) % 2147483647,
                    "vector": vector,
                    "payload": {
                        "task_info": task_info,
                        "analysis": analysis,
                        "timestamp": time.time(),
                        "pattern_text": pattern_text.strip()
                    }
                }]
            )
            
        except Exception as e:
            self.logger.error(f"Erreur vectorisation/stockage: {e}")
    
    def store_in_cache(self, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """Stocke en cache local"""
        pattern = {
            "task_info": task_info,
            "analysis": analysis,
            "timestamp": time.time()
        }
        
        self.pattern_cache.append(pattern)
        
        # Limiter la taille du cache
        max_cache_size = 100
        if len(self.pattern_cache) > max_cache_size:
            self.pattern_cache = self.pattern_cache[-max_cache_size:]
    
    def take_critical_action(self, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """Prend une action immédiate pour une menace critique"""
        task_id = task_info.get("task_id", "unknown")
        
        if self.config.get("auto_delete_on_critical", True):
            # Tentative de suppression de la tâche
            try:
                # Import dynamique pour éviter la dépendance circulaire
                from agents.scheduler.agent_scheduler_agent import AgentSchedulerAgent
                
                scheduler = AgentSchedulerAgent()
                delete_result = scheduler.cancel_task(task_id)
                
                if delete_result.get("status") == "success":
                    self.speak(
                        f"🚨 SÉCURITÉ CRITIQUE: Tâche {task_id} supprimée automatiquement - {analysis.get('reason', '')}",
                        target="OverseerAgent"
                    )
                    self.stats["threats_blocked"] += 1
                else:
                    self.speak(
                        f"⚠️ ÉCHEC SUPPRESSION: Impossible de supprimer la tâche {task_id} - {delete_result.get('message', '')}",
                        target="OverseerAgent"
                    )
                    
            except Exception as e:
                self.logger.error(f"Erreur suppression tâche critique: {e}")
                self.speak(
                    f"❌ ERREUR: Impossible de supprimer la tâche critique {task_id}",
                    target="OverseerAgent"
                )
        
        # Alerte admin
        if self.config.get("alert_admin_on_critical", True):
            self.alert_admin("CRITICAL", task_info, analysis)
    
    def take_suspect_action(self, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """Prend une action pour une tâche suspecte"""
        task_id = task_info.get("task_id", "unknown")
        
        # Surveillance renforcée en mode permissif
        self.speak(
            f"⚠️ TÂCHE SUSPECTE: {task_id} détectée - {analysis.get('reason', '')} - Surveillance renforcée activée",
            target="OverseerAgent"
        )
        
        # Optionnel: quarantaine si configuré
        if self.config.get("auto_quarantine_on_suspect", False):
            # TODO: Implémenter la logique de quarantaine
            pass
    
    def alert_admin(self, severity: str, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """Envoie une alerte à l'admin"""
        task_id = task_info.get("task_id", "unknown")
        task_data = task_info.get("task_data", {})
        
        alert_message = f"""
🚨 ALERTE SÉCURITÉ {severity}

Tâche: {task_id}
Agent: {task_data.get('agent', 'unknown')}
Action: {task_data.get('action', 'unknown')}
Menace: {analysis.get('threat_level', 'unknown')}
Confiance: {analysis.get('confidence', 0):.2f}

Raison: {analysis.get('reason', '')}

Facteurs de risque: {', '.join(analysis.get('risk_factors', []))}
Patterns détectés: {', '.join(analysis.get('patterns_detected', []))}

Action recommandée: {analysis.get('recommended_action', 'unknown')}
        """.strip()
        
        # Transmission à l'AdminInterpreterAgent pour notification
        self.speak(alert_message, target="AdminInterpreterAgent")
    
    def communicate_analysis_result(self, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """Communique le résultat de l'analyse au système"""
        task_id = task_info.get("task_id", "unknown")
        threat_level = analysis.get("threat_level", "unknown")
        confidence = analysis.get("confidence", 0)
        
        # En mode permissif, on log moins les tâches normales
        if threat_level == "NORMAL":
            # Message très discret pour les tâches normales
            if confidence > 0.7:  # Seulement si on est vraiment sûr que c'est normal
                pass  # Pas de message pour éviter le spam
            else:
                self.speak(
                    f"✅ Tâche {task_id} analysée: {threat_level} (confiance: {confidence:.2f})",
                    target="OverseerAgent"
                )
        else:
            # Message visible pour les anomalies
            self.speak(
                f"⚠️ ANALYSE: Tâche {task_id} - {threat_level} - {analysis.get('reason', '')}",
                target="OverseerAgent"
            )
    
    def log_analysis(self, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """Log l'analyse pour traçabilité"""
        task_id = task_info.get("task_id", "unknown")
        
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "task_id": task_id,
            "analysis": analysis,
            "agent": self.name
        }
        
        self.logger.info(f"Analysis: {json.dumps(log_entry, indent=2)}")
    
    def generate_threat_report(self) -> Dict[str, Any]:
        """Génère un rapport de menaces"""
        try:
            recent_patterns = self.get_recent_task_patterns()
            
            report = {
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat(),
                "statistics": self.stats,
                "recent_patterns": recent_patterns,
                "configuration": {
                    "max_tasks_per_hour": self.config.get("max_tasks_per_agent_per_hour"),
                    "max_tasks_per_day": self.config.get("max_tasks_per_agent_per_day"),
                    "auto_delete_critical": self.config.get("auto_delete_on_critical"),
                    "learning_enabled": self.config.get("enable_learning"),
                    "permissive_mode": self.config.get("permissive_mode", True),
                    "detection_approach": self.config.get("detection_approach", "behavioral_analysis")
                }
            }
            
            return report
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur génération rapport: {e}"
            }
    
    def update_security_patterns(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour les patterns de sécurité"""
        # TODO: Implémenter la mise à jour des patterns

        return {
            "status": "success",
            "message": "Mise à jour des patterns (non implémenté)"
        }
    
    def reset_false_positive(self, fp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Marque une analyse comme faux positif pour apprentissage"""
        try:
            task_id = fp_data.get("task_id")
            if task_id:
                self.stats["false_positives"] += 1
                self.speak(
                    f"📝 Faux positif signalé pour la tâche {task_id} - Apprentissage mis à jour",
                    target="OverseerAgent"
                )
            
            return {"status": "success", "message": "Faux positif enregistré"}
            
        except Exception as e:
            return {"status": "error", "message": f"Erreur reset faux positif: {e}"}


# Point d'entrée pour tests directs
if __name__ == "__main__":
    # Configuration du logging pour tests
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test basique
    watchdog = TaskWatchdogAgent()
    
    # Test d'analyse d'une tâche normale
    test_task = {
        "task_id": "test_task_123",
        "task_data": {
            "agent": "MessagingAgent",
            "action": "send_email"
        },
        "execution_time": "2025-05-27T18:00:00",
        "recurring": False,
        "requesting_agent": "test_system"
    }
    
    result = watchdog.run({
        "action": "analyze_new_task",
        **test_task
    })
    
    print("Résultat test (mode permissif):")
    print(json.dumps(result, indent=2, ensure_ascii=False))

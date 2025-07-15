"""
Module du PivotStrategyAgent - Optimisation et analyse stratégique du système BerinIA
"""
import os
import json
import logging
import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
from collections import defaultdict
import statistics

from core.agent_base import Agent
from utils.llm import LLMService
from utils.qdrant import query_knowledge, store_knowledge

class PivotStrategyAgent(Agent):
    """
    PivotStrategyAgent - Agent responsable de l'analyse des performances et de l'optimisation stratégique
    
    Cet agent est responsable de:
    - Analyser les performances des campagnes et des niches
    - Identifier les points d'amélioration dans les stratégies de prospection
    - Recommander des ajustements stratégiques
    - Stocker les connaissances acquises pour optimisation future
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du PivotStrategyAgent
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("PivotStrategyAgent", config_path)
        
        # Logger dédié
        self.logger = logging.getLogger("BerinIA-PivotStrategy")
        
        # Métriques utilisées pour l'analyse
        self.performance_metrics = [
            "open_rate",           # Taux d'ouverture des emails
            "response_rate",       # Taux de réponse
            "positive_rate",       # Taux de réponses positives
            "conversion_rate",     # Taux de conversion
            "bounce_rate",         # Taux de rebond
            "unsubscribe_rate"     # Taux de désabonnement
        ]
        
        # Seuils de performance par défaut (peuvent être modifiés via config)
        self.performance_thresholds = self.config.get("performance_thresholds", {
            "open_rate": {
                "excellent": 0.5,  # 50%+
                "good": 0.3,       # 30-50%
                "average": 0.2,    # 20-30%
                "poor": 0.1        # <10%
            },
            "response_rate": {
                "excellent": 0.2,  # 20%+
                "good": 0.1,       # 10-20%
                "average": 0.05,   # 5-10%
                "poor": 0.02       # <2%
            },
            "positive_rate": {
                "excellent": 0.5,  # 50%+
                "good": 0.3,       # 30-50%
                "average": 0.15,   # 15-30%
                "poor": 0.05       # <5%
            },
            "conversion_rate": {
                "excellent": 0.1,  # 10%+
                "good": 0.05,      # 5-10%
                "average": 0.02,   # 2-5%
                "poor": 0.01       # <1%
            }
        })
        
        # Seuils d'alertes
        self.alert_thresholds = self.config.get("alert_thresholds", {
            "bounce_rate": 0.1,    # 10%+ de bounces → alerte
            "unsubscribe_rate": 0.05  # 5%+ de désabonnements → alerte
        })
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal du PivotStrategyAgent
        
        Args:
            input_data: Données d'entrée avec l'action à effectuer
            
        Returns:
            Résultat de l'action demandée
        """
        action = input_data.get("action", "")
        
        if action == "analyze_and_recommend":
            return self.analyze_and_recommend(input_data)
        elif action == "contact_niche_explorer":
            return self._contact_niche_explorer(input_data)
        elif action == "analyze_performance":
            return {"status": "success", "analysis": self._analyze_performance(input_data)}
        elif action == "analyze_campaign":
            return self.analyze_campaign(
                input_data.get("campaign_id", ""),
                input_data.get("detail_level", "full")
            )
        elif action == "analyze_niche":
            return self.analyze_niche(
                input_data.get("niche", ""),
                input_data.get("time_period", "all")
            )
        elif action == "recommend_optimizations":
            return self.recommend_optimizations(
                input_data.get("target", "all"),
                input_data.get("optimization_type", "all")
            )
        elif action == "get_insights":
            return self.get_insights(
                input_data.get("keywords", []),
                input_data.get("context", "prospection")
            )
        elif action == "store_learning":
            return self.store_learning(
                input_data.get("learning_data", {}),
                input_data.get("category", "general")
            )
        elif action == "get_stats":
            return {
                "status": "success",
                "agent_type": "PivotStrategyAgent",
                "available_actions": [
                    "analyze_and_recommend",
                    "contact_niche_explorer",
                    "analyze_performance",
                    "analyze_campaign",
                    "analyze_niche",
                    "recommend_optimizations",
                    "get_insights",
                    "store_learning"
                ]
            }
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}",
                "available_actions": [
                    "analyze_and_recommend",
                    "contact_niche_explorer",
                    "analyze_performance",
                    "analyze_campaign",
                    "analyze_niche",
                    "recommend_optimizations",
                    "get_insights",
                    "store_learning",
                    "get_stats"
                ]
            }
    
    def analyze_campaign(self, campaign_id: str, detail_level: str = "full") -> Dict[str, Any]:
        """
        Analyse les performances d'une campagne spécifique
        
        Args:
            campaign_id: Identifiant de la campagne
            detail_level: Niveau de détail de l'analyse (basic, full, metrics_only)
            
        Returns:
            Résultats de l'analyse
        """
        if not campaign_id:
            return {
                "status": "error",
                "message": "Identifiant de campagne manquant"
            }
        
        try:
            # Récupération des données de la campagne depuis la base de données
            from core.db import get_campaign_metrics, get_campaign_responses
            
            # Récupération des métriques brutes
            metrics = get_campaign_metrics(campaign_id)
            
            # Récupération des réponses pour analyse
            responses = get_campaign_responses(campaign_id)
            
            # Calcul des métriques dérivées
            derived_metrics = self._calculate_derived_metrics(metrics, responses)
            
            # Évaluation des performances
            performance_evaluation = self._evaluate_performance(derived_metrics)
            
            # Détection des problèmes
            issues = self._detect_issues(derived_metrics, performance_evaluation)
            
            # Recommandations spécifiques à la campagne
            recommendations = self._generate_recommendations(
                derived_metrics, 
                performance_evaluation, 
                issues, 
                campaign_id=campaign_id
            )
            
            # Construction du résultat selon le niveau de détail demandé
            if detail_level == "metrics_only":
                result = {
                    "campaign_id": campaign_id,
                    "metrics": derived_metrics
                }
            elif detail_level == "basic":
                result = {
                    "campaign_id": campaign_id,
                    "metrics": derived_metrics,
                    "performance": performance_evaluation,
                    "issues_count": len(issues)
                }
            else:  # full
                result = {
                    "campaign_id": campaign_id,
                    "metrics": derived_metrics,
                    "performance": performance_evaluation,
                    "issues": issues,
                    "recommendations": recommendations
                }
            
            # Stockage de l'analyse comme connaissance pour référence future
            if self.config.get("store_analysis_in_qdrant", True):
                store_knowledge(
                    content=json.dumps(result),
                    metadata={
                        "type": "campaign_analysis",
                        "campaign_id": campaign_id,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "performance_summary": performance_evaluation.get("overall", "unknown")
                    },
                    collection_name="knowledge"
                )
            
            # Formatage du message pour l'OverseerAgent
            overall_performance = performance_evaluation.get("overall", "inconnu")
            self.speak(
                f"Analyse de la campagne {campaign_id} terminée. "
                f"Performance globale: {overall_performance}. "
                f"Problèmes détectés: {len(issues)}.",
                target="OverseerAgent"
            )
            
            return {
                "status": "success",
                "analysis": result
            }
            
        except Exception as e:
            error_message = f"Erreur lors de l'analyse de la campagne {campaign_id}: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def analyze_niche(self, niche: str, time_period: str = "all") -> Dict[str, Any]:
        """
        Analyse les performances d'une niche spécifique
        
        Args:
            niche: Niche à analyser
            time_period: Période d'analyse (all, last_month, last_week, etc.)
            
        Returns:
            Résultats de l'analyse
        """
        if not niche:
            return {
                "status": "error",
                "message": "Niche non spécifiée"
            }
        
        try:
            # Récupération des données de la niche depuis la base de données
            from core.db import get_niche_campaigns, get_campaign_metrics
            
            # Récupération des campagnes associées à la niche
            campaigns = get_niche_campaigns(niche, time_period)
            
            if not campaigns:
                return {
                    "status": "warning",
                    "message": f"Aucune campagne trouvée pour la niche {niche} sur la période spécifiée"
                }
            
            # Agrégation des métriques de toutes les campagnes
            all_metrics = []
            for campaign_id in campaigns:
                metrics = get_campaign_metrics(campaign_id)
                all_metrics.append(metrics)
            
            # Calcul des métriques agrégées
            aggregated_metrics = self._aggregate_metrics(all_metrics)
            
            # Évaluation des performances
            performance_evaluation = self._evaluate_performance(aggregated_metrics)
            
            # Tendances au fil du temps
            trends = self._analyze_trends(all_metrics, campaigns)
            
            # Comparaison avec d'autres niches
            from core.db import get_all_niches
            all_niches = get_all_niches()
            niche_comparison = self._compare_to_other_niches(niche, all_niches)
            
            # Recommandations spécifiques à la niche
            recommendations = self._generate_recommendations(
                aggregated_metrics, 
                performance_evaluation, 
                [], 
                niche=niche, 
                trends=trends
            )
            
            # Construction du résultat
            result = {
                "niche": niche,
                "time_period": time_period,
                "campaigns_count": len(campaigns),
                "metrics": aggregated_metrics,
                "performance": performance_evaluation,
                "trends": trends,
                "comparison": niche_comparison,
                "recommendations": recommendations
            }
            
            # Stockage de l'analyse comme connaissance pour référence future
            if self.config.get("store_analysis_in_qdrant", True):
                store_knowledge(
                    content=json.dumps(result),
                    metadata={
                        "type": "niche_analysis",
                        "niche": niche,
                        "time_period": time_period,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "performance_summary": performance_evaluation.get("overall", "unknown")
                    },
                    collection_name="knowledge"
                )
            
            # Formatage du message pour l'OverseerAgent
            overall_performance = performance_evaluation.get("overall", "inconnu")
            self.speak(
                f"Analyse de la niche {niche} terminée. "
                f"Performance globale: {overall_performance}. "
                f"Campagnes analysées: {len(campaigns)}.",
                target="OverseerAgent"
            )
            
            return {
                "status": "success",
                "analysis": result
            }
            
        except Exception as e:
            error_message = f"Erreur lors de l'analyse de la niche {niche}: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def recommend_optimizations(self, target: str = "all", optimization_type: str = "all") -> Dict[str, Any]:
        """
        Recommande des optimisations basées sur l'analyse des données
        
        Args:
            target: Cible de l'optimisation (all, campaign_id, niche)
            optimization_type: Type d'optimisation (all, messaging, targeting, timing)
            
        Returns:
            Recommandations d'optimisation
        """
        try:
            # Construction du prompt pour le LLM avec contexte
            prompt_data = {
                "target": target,
                "optimization_type": optimization_type
            }
            
            # Récupération des connaissances pertinentes depuis Qdrant
            if target != "all" and target != "":
                # Contexte spécifique à une campagne ou une niche
                relevant_knowledge = query_knowledge(
                    query=f"optimization recommendations for {target}",
                    limit=5,
                    collection_name="knowledge"
                )
                prompt_data["relevant_knowledge"] = relevant_knowledge
            
            # Ajout du contexte général des performances
            if target == "all":
                # Récupération des métriques globales du système
                from core.db import get_global_metrics
                global_metrics = get_global_metrics()
                prompt_data["global_metrics"] = global_metrics
            
            # Construction du prompt
            prompt = self.build_prompt(prompt_data)
            
            # Appel au LLM pour générer les recommandations
            llm_response = LLMService.call_llm(prompt, complexity="high")
            
            try:
                # Parsing du résultat JSON
                recommendations = json.loads(llm_response)
                
                # Structuration des recommandations
                structured_recommendations = {
                    "target": target,
                    "optimization_type": optimization_type,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "recommendations": recommendations
                }
                
                # Stockage des recommandations comme connaissance
                if self.config.get("store_recommendations_in_qdrant", True):
                    store_knowledge(
                        content=json.dumps(structured_recommendations),
                        metadata={
                            "type": "optimization_recommendations",
                            "target": target,
                            "optimization_type": optimization_type,
                            "timestamp": datetime.datetime.now().isoformat()
                        },
                        collection_name="knowledge"
                    )
                
                # Formatage du message pour l'OverseerAgent
                self.speak(
                    f"Recommandations d'optimisation générées pour {target or 'tout le système'}.",
                    target="OverseerAgent"
                )
                
                return {
                    "status": "success",
                    "recommendations": structured_recommendations
                }
                
            except json.JSONDecodeError:
                # Si le résultat n'est pas un JSON valide
                return {
                    "status": "error",
                    "message": "Impossible de parser les recommandations",
                    "raw_response": llm_response
                }
            
        except Exception as e:
            error_message = f"Erreur lors de la génération des recommandations: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def store_learning(self, learning_data: Dict[str, Any], category: str = "general") -> Dict[str, Any]:
        """
        Stocke un apprentissage pour référence future
        
        Args:
            learning_data: Données d'apprentissage
            category: Catégorie de l'apprentissage
            
        Returns:
            Statut du stockage
        """
        if not learning_data:
            return {
                "status": "error",
                "message": "Données d'apprentissage manquantes"
            }
        
        try:
            # Ajout des métadonnées
            metadata = {
                "type": "learning",
                "category": category,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Stockage dans Qdrant
            store_knowledge(
                content=json.dumps(learning_data),
                metadata=metadata,
                collection_name="knowledge"
            )
            
            self.speak(
                f"Nouvel apprentissage stocké dans la catégorie '{category}'",
                target="OverseerAgent"
            )
            
            return {
                "status": "success",
                "message": f"Apprentissage stocké dans la catégorie '{category}'"
            }
            
        except Exception as e:
            error_message = f"Erreur lors du stockage de l'apprentissage: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def get_insights(self, keywords: List[str], context: str = "prospection") -> Dict[str, Any]:
        """
        Récupère des insights basés sur des mots-clés et un contexte
        
        Args:
            keywords: Liste de mots-clés
            context: Contexte de la recherche
            
        Returns:
            Insights récupérés
        """
        if not keywords:
            return {
                "status": "error",
                "message": "Mots-clés manquants"
            }
        
        try:
            # Construction de la requête
            query = " ".join(keywords)
            if context:
                query = f"{context} {query}"
            
            # Récupération des connaissances
            knowledge_results = query_knowledge(
                query=query,
                limit=10,
                collection_name="knowledge"
            )
            
            if not knowledge_results:
                return {
                    "status": "warning",
                    "message": "Aucun insight trouvé pour ces mots-clés"
                }
            
            # Structuration des résultats
            insights = []
            for item in knowledge_results:
                try:
                    # La clé est "document" et non "content" dans query_knowledge
                    document_content = item.get("document", "")
                    metadata = item.get("metadata", {})
                    score = item.get("score", 0)
                    
                    # Essayer de parser le contenu JSON
                    try:
                        if document_content and isinstance(document_content, str):
                            parsed_content = json.loads(document_content)
                            insights.append({
                                "content": parsed_content,
                                "metadata": metadata,
                                "score": score
                            })
                        else:
                            insights.append({
                                "content": document_content,
                                "metadata": metadata,
                                "score": score
                            })
                    except json.JSONDecodeError:
                        insights.append({
                            "content": document_content,
                            "metadata": metadata,
                            "score": score
                        })
                except Exception as e:
                    # Log de l'erreur pour debug
                    print(f"Erreur traitement insight: {e}")
                    continue
            
            self.speak(
                f"Récupération de {len(insights)} insights pour les mots-clés: {', '.join(keywords)}",
                target="OverseerAgent"
            )
            
            return {
                "status": "success",
                "insights": insights,
                "query": query
            }
            
        except Exception as e:
            error_message = f"Erreur lors de la récupération des insights: {str(e)}"
            self.speak(error_message, target="OverseerAgent")
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def _calculate_derived_metrics(self, raw_metrics: Dict[str, Any], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les métriques dérivées à partir des métriques brutes
        
        Args:
            raw_metrics: Métriques brutes
            responses: Réponses reçues
            
        Returns:
            Métriques dérivées
        """
        derived_metrics = {}
        
        # Métriques de base
        sent_count = raw_metrics.get("sent_count", 0)
        delivered_count = raw_metrics.get("delivered_count", 0)
        open_count = raw_metrics.get("open_count", 0)
        click_count = raw_metrics.get("click_count", 0)
        response_count = len(responses)
        
        # Calcul des taux
        if sent_count > 0:
            derived_metrics["delivery_rate"] = delivered_count / sent_count
            derived_metrics["bounce_rate"] = 1 - (delivered_count / sent_count)
        else:
            derived_metrics["delivery_rate"] = 0
            derived_metrics["bounce_rate"] = 0
        
        if delivered_count > 0:
            derived_metrics["open_rate"] = open_count / delivered_count
            derived_metrics["response_rate"] = response_count / delivered_count
        else:
            derived_metrics["open_rate"] = 0
            derived_metrics["response_rate"] = 0
        
        if open_count > 0:
            derived_metrics["click_to_open_rate"] = click_count / open_count
        else:
            derived_metrics["click_to_open_rate"] = 0
        
        # Analyse des sentiments dans les réponses
        if response_count > 0:
            sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
            
            for response in responses:
                sentiment = response.get("sentiment", "neutral")
                sentiment_counts[sentiment] += 1
            
            derived_metrics["positive_rate"] = sentiment_counts["positive"] / response_count
            derived_metrics["neutral_rate"] = sentiment_counts["neutral"] / response_count
            derived_metrics["negative_rate"] = sentiment_counts["negative"] / response_count
        else:
            derived_metrics["positive_rate"] = 0
            derived_metrics["neutral_rate"] = 0
            derived_metrics["negative_rate"] = 0
        
        # Autres métriques
        derived_metrics["unsubscribe_rate"] = raw_metrics.get("unsubscribe_count", 0) / max(delivered_count, 1)
        derived_metrics["conversion_rate"] = raw_metrics.get("conversion_count", 0) / max(delivered_count, 1)
        
        # Agrégation des données brutes
        derived_metrics.update({
            "sent_count": sent_count,
            "delivered_count": delivered_count,
            "open_count": open_count,
            "click_count": click_count,
            "response_count": response_count,
            "unsubscribe_count": raw_metrics.get("unsubscribe_count", 0),
            "conversion_count": raw_metrics.get("conversion_count", 0)
        })
        
        return derived_metrics
    
    def _evaluate_performance(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """
        Évalue les performances selon les métriques et les seuils configurés
        
        Args:
            metrics: Métriques calculées
            
        Returns:
            Évaluation des performances
        """
        performance = {}
        
        # Évaluation des métriques individuelles
        for metric in self.performance_metrics:
            if metric in metrics and metric in self.performance_thresholds:
                value = metrics[metric]
                thresholds = self.performance_thresholds[metric]
                
                if value >= thresholds["excellent"]:
                    performance[metric] = "excellent"
                elif value >= thresholds["good"]:
                    performance[metric] = "good"
                elif value >= thresholds["average"]:
                    performance[metric] = "average"
                else:
                    performance[metric] = "poor"
        
        # Calcul de la performance globale (moyenne pondérée)
        score_map = {
            "excellent": 4,
            "good": 3,
            "average": 2,
            "poor": 1
        }
        
        # Poids des métriques
        weights = {
            "open_rate": 1,
            "response_rate": 2,
            "positive_rate": 3,
            "conversion_rate": 4,
            "bounce_rate": 2,
            "unsubscribe_rate": 2
        }
        
        # Calcul du score global
        total_score = 0
        total_weight = 0
        
        for metric, rating in performance.items():
            if metric in weights:
                weight = weights[metric]
                total_score += score_map[rating] * weight
                total_weight += weight
        
        # Détermination de la performance globale
        if total_weight > 0:
            average_score = total_score / total_weight
            
            if average_score >= 3.5:
                performance["overall"] = "excellent"
            elif average_score >= 2.5:
                performance["overall"] = "good"
            elif average_score >= 1.5:
                performance["overall"] = "average"
            else:
                performance["overall"] = "poor"
        else:
            performance["overall"] = "unknown"
        
        return performance
    
    def _detect_issues(self, metrics: Dict[str, Any], performance: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Détecte les problèmes potentiels dans les métriques
        
        Args:
            metrics: Métriques calculées
            performance: Évaluation des performances
            
        Returns:
            Liste des problèmes détectés
        """
        issues = []
        
        # Vérification des mauvaises performances
        for metric, rating in performance.items():
            if metric != "overall" and rating == "poor":
                issues.append({
                    "type": "poor_performance",
                    "metric": metric,
                    "value": metrics.get(metric, 0),
                    "severity": "high",
                    "description": f"Performance faible pour {metric}"
                })
        
        # Vérification des alertes
        for metric, threshold in self.alert_thresholds.items():
            if metric in metrics and metrics[metric] >= threshold:
                issues.append({
                    "type": "threshold_exceeded",
                    "metric": metric,
                    "value": metrics[metric],
                    "threshold": threshold,
                    "severity": "high",
                    "description": f"Seuil d'alerte dépassé pour {metric}"
                })
        
        # Détection des anomalies statistiques
        # Exemple: taux de réponse très différent du taux d'ouverture
        if "open_rate" in metrics and "response_rate" in metrics:
            if metrics["open_rate"] > 0.4 and metrics["response_rate"] < 0.05:
                issues.append({
                    "type": "anomaly",
                    "metric": "response_to_open_ratio",
                    "value": metrics["response_rate"] / max(metrics["open_rate"], 0.001),
                    "severity": "medium",
                    "description": "Taux de réponse faible malgré un bon taux d'ouverture"
                })
        
        return issues
    
    def _generate_recommendations(self, metrics: Dict[str, Any], performance: Dict[str, str], 
                                 issues: List[Dict[str, Any]], campaign_id: Optional[str] = None, 
                                 niche: Optional[str] = None, trends: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Génère des recommandations basées sur l'analyse
        
        Args:
            metrics: Métriques calculées
            performance: Évaluation des performances
            issues: Problèmes détectés
            campaign_id: Identifiant de la campagne (si applicable)
            niche: Niche concernée (si applicable)
            trends: Tendances observées (si applicable)
            
        Returns:
            Liste des recommandations
        """
        # Construction du prompt pour le LLM
        prompt_data = {
            "metrics": metrics,
            "performance": performance,
            "issues": issues,
            "campaign_id": campaign_id,
            "niche": niche,
            "trends": trends
        }
        
        # Récupération de connaissances pertinentes depuis Qdrant
        query_terms = []
        if campaign_id:
            query_terms.append(campaign_id)
        if niche:
            query_terms.append(niche)
        
        # Ajout des métriques problématiques aux termes de recherche
        for issue in issues:
            query_terms.append(issue["metric"])
        
        if query_terms:
            query = " ".join(query_terms)
            relevant_knowledge = query_knowledge(
                query=query,
                limit=3,
                collection_name="knowledge"
            )
            prompt_data["relevant_knowledge"] = relevant_knowledge
        
        # Construction du prompt
        prompt = self.build_prompt(prompt_data)
        
        # Appel au LLM pour générer les recommandations
        try:
            llm_response = LLMService.call_llm(prompt, complexity="high")
            recommendations = json.loads(llm_response)
            
            return recommendations if isinstance(recommendations, list) else [recommendations]
            
        except Exception as e:
            # Fallback: recommandations basiques basées sur les problèmes détectés
            fallback_recommendations = []
            
            for issue in issues:
                if issue["metric"] == "open_rate" and issue["type"] == "poor_performance":
                    fallback_recommendations.append({
                        "type": "subject_line",
                        "priority": "high",
                        "recommendation": "Améliorer les lignes d'objet pour augmenter le taux d'ouverture",
                        "reason": "Taux d'ouverture faible détecté"
                    })
                
                elif issue["metric"] == "response_rate" and issue["type"] == "poor_performance":
                    fallback_recommendations.append({
                        "type": "content",
                        "priority": "high", 
                        "recommendation": "Revoir le contenu des messages pour inciter plus de réponses",
                        "reason": "Taux de réponse faible"
                    })
            
            return fallback_recommendations
    
    def _contact_niche_explorer(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Communique avec le NicheExplorerAgent pour obtenir des insights
        
        Args:
            input_data: Données d'entrée pour la communication
            
        Returns:
            Résultats de la communication avec NicheExplorerAgent
        """
        try:
            from agents.overseer.overseer_agent import OverseerAgent
            overseer = OverseerAgent()
            
            # Communication avec NicheExplorerAgent
            result = overseer.execute_agent("NicheExplorerAgent", {
                "action": "strategic_recommendations",
                "current_niches": input_data.get("current_niches", []),
                "context": "performance_analysis"
            })
            
            return {
                "status": "success",
                "niche_explorer_response": result,
                "message": "Communication avec NicheExplorerAgent réussie"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur communication NicheExplorerAgent: {str(e)}"
            }
    
    def _analyze_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse les données de performance et fournit des insights
        
        Args:
            performance_data: Données de performance à analyser
            
        Returns:
            Analyse des performances
        """
        try:
            conversion_rate = performance_data.get("conversion_rate", 0)
            response_rate = performance_data.get("response_rate", 0)
            status = performance_data.get("status", "unknown")
            
            # Classification des performances
            if conversion_rate >= 0.1:  # 10%+
                performance_level = "excellent"
                recommendation = "Maintenir la stratégie actuelle"
            elif conversion_rate >= 0.05:  # 5-10%
                performance_level = "good"
                recommendation = "Optimiser pour atteindre l'excellence"
            elif conversion_rate >= 0.02:  # 2-5%
                performance_level = "average"
                recommendation = "Améliorer le ciblage et les messages"
            else:  # <2%
                performance_level = "poor"
                recommendation = "Revoir complètement la stratégie"
            
            # Analyse du taux de réponse
            response_analysis = ""
            if response_rate >= 0.15:  # 15%+
                response_analysis = "Excellent engagement"
            elif response_rate >= 0.08:  # 8-15%
                response_analysis = "Bon engagement"
            elif response_rate >= 0.03:  # 3-8%
                response_analysis = "Engagement moyen"
            else:  # <3%
                response_analysis = "Faible engagement"
            
            return {
                "performance_level": performance_level,
                "recommendation": recommendation,
                "response_analysis": response_analysis,
                "conversion_rate": conversion_rate,
                "response_rate": response_rate,
                "detailed_analysis": {
                    "strengths": self._identify_strengths(performance_data),
                    "weaknesses": self._identify_weaknesses(performance_data),
                    "opportunities": self._identify_opportunities(performance_data)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur analyse performance: {str(e)}"
            }
    
    def _should_trigger_analysis(self, scenario: Dict[str, Any]) -> bool:
        """
        Détermine si une analyse doit être déclenchée selon le scénario
        
        Args:
            scenario: Scénario à évaluer
            
        Returns:
            True si l'analyse doit être déclenchée
        """
        scenario_type = scenario.get("type", "")
        threshold = scenario.get("threshold", 0)
        
        # Règles de déclenchement
        trigger_rules = {
            "low_conversion": lambda t: t < 0.03,  # <3% conversion
            "high_bounce": lambda t: t > 0.15,    # >15% bounce
            "good_performance": lambda t: t > 0.08, # >8% conversion (pas besoin d'analyse urgente)
            "poor_response": lambda t: t < 0.05,   # <5% réponse
            "urgent_issue": lambda t: True,        # Toujours déclencher
        }
        
        if scenario_type in trigger_rules:
            rule = trigger_rules[scenario_type]
            should_trigger = rule(threshold)
            
            # Cas spéciaux
            if scenario_type == "good_performance":
                return not should_trigger  # Inverse pour good_performance
            
            return should_trigger
        
        # Par défaut, ne pas déclencher pour types inconnus
        return False
    
    def _identify_strengths(self, performance_data: Dict[str, Any]) -> List[str]:
        """Identifie les points forts"""
        strengths = []
        
        if performance_data.get("open_rate", 0) > 0.3:
            strengths.append("Bon taux d'ouverture")
        if performance_data.get("response_rate", 0) > 0.1:
            strengths.append("Bon taux de réponse")
        if performance_data.get("conversion_rate", 0) > 0.05:
            strengths.append("Bon taux de conversion")
        
        return strengths if strengths else ["Aucun point fort identifié"]
    
    def _identify_weaknesses(self, performance_data: Dict[str, Any]) -> List[str]:
        """Identifie les points faibles"""
        weaknesses = []
        
        if performance_data.get("bounce_rate", 0) > 0.1:
            weaknesses.append("Taux de rebond élevé")
        if performance_data.get("unsubscribe_rate", 0) > 0.05:
            weaknesses.append("Taux de désabonnement élevé")
        if performance_data.get("response_rate", 0) < 0.03:
            weaknesses.append("Faible taux de réponse")
        
        return weaknesses if weaknesses else ["Aucun point faible majeur"]
    
    def _identify_opportunities(self, performance_data: Dict[str, Any]) -> List[str]:
        """Identifie les opportunités d'amélioration"""
        opportunities = []
        
        open_rate = performance_data.get("open_rate", 0)
        response_rate = performance_data.get("response_rate", 0)
        
        if open_rate > 0.3 and response_rate < 0.1:
            opportunities.append("Améliorer le contenu pour convertir les ouvertures en réponses")
        
        if performance_data.get("click_rate", 0) > 0.1 and performance_data.get("conversion_rate", 0) < 0.05:
            opportunities.append("Optimiser le landing page pour convertir les clics")
        
        return opportunities if opportunities else ["Optimisation générale recommandée"]
    
    def analyze_and_recommend(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse complète et recommandations pour les campagnes actuelles
        
        Args:
            input_data: Données d'entrée avec campagnes et données de performance
            
        Returns:
            Analyse complète avec recommandations
        """
        try:
            current_campaigns = input_data.get("current_campaigns", [])
            performance_data = input_data.get("performance_data", {})
            
            # Analyse de chaque campagne
            campaign_analyses = []
            overall_recommendations = []
            
            for campaign in current_campaigns:
                # Analyser les performances de la campagne
                campaign_perf = performance_data.get(campaign, {})
                analysis = self._analyze_performance(campaign_perf)
                
                campaign_analyses.append({
                    "campaign": campaign,
                    "analysis": analysis
                })
                
                # Ajouter des recommandations spécifiques
                if analysis.get("performance_level") == "poor":
                    overall_recommendations.append({
                        "type": "campaign_optimization",
                        "campaign": campaign,
                        "priority": "urgente",
                        "recommendation": f"Optimiser ou arrêter la campagne {campaign}",
                        "reason": "Performance en dessous des attentes"
                    })
            
            # Recommandations stratégiques globales
            strategic_recommendations = [
                {
                    "type": "targeting",
                    "priority": "haute",
                    "recommendation": "Affiner le ciblage TPE/PME",
                    "reason": "Améliorer la pertinence des contacts"
                },
                {
                    "type": "content",
                    "priority": "moyenne",
                    "recommendation": "Personnaliser davantage les messages",
                    "reason": "Augmenter l'engagement"
                },
                {
                    "type": "timing",
                    "priority": "moyenne",
                    "recommendation": "Optimiser les horaires d'envoi",
                    "reason": "Maximiser les taux d'ouverture"
                }
            ]
            
            # Communication avec NicheExplorerAgent pour insights supplémentaires
            niche_insights = self._contact_niche_explorer({
                "current_niches": [campaign.split("_")[0] for campaign in current_campaigns if "_" in campaign],
                "action": "analyze_opportunities"
            })
            
            return {
                "status": "success",
                "campaign_analyses": campaign_analyses,
                "overall_recommendations": overall_recommendations + strategic_recommendations,
                "niche_insights": niche_insights,
                "summary": {
                    "campaigns_analyzed": len(current_campaigns),
                    "poor_performers": len([c for c in campaign_analyses if c["analysis"].get("performance_level") == "poor"]),
                    "good_performers": len([c for c in campaign_analyses if c["analysis"].get("performance_level") in ["good", "excellent"]])
                },
                "analysis_date": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur analyse et recommandations: {str(e)}"
            }
    
    def _aggregate_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Agrège les métriques de plusieurs campagnes
        
        Args:
            metrics_list: Liste des métriques à agréger
            
        Returns:
            Métriques agrégées
        """
        if not metrics_list:
            return {}
        
        aggregated = defaultdict(list)
        
        # Collecte de toutes les valeurs
        for metrics in metrics_list:
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    aggregated[key].append(value)
        
        # Calcul des moyennes et totaux
        result = {}
        for key, values in aggregated.items():
            if key.endswith('_count'):
                # Pour les compteurs, on fait la somme
                result[key] = sum(values)
            else:
                # Pour les taux, on fait la moyenne
                result[key] = statistics.mean(values) if values else 0
        
        return result
    
    def _analyze_trends(self, metrics_list: List[Dict[str, Any]], campaigns: List[str]) -> Dict[str, Any]:
        """
        Analyse les tendances dans les métriques au fil du temps
        
        Args:
            metrics_list: Liste des métriques chronologiques
            campaigns: Liste des campagnes correspondantes
            
        Returns:
            Analyse des tendances
        """
        if len(metrics_list) < 2:
            return {"trend": "insufficient_data", "message": "Données insuffisantes pour analyser les tendances"}
        
        trends = {}
        
        # Analyse de la tendance pour chaque métrique
        for metric in ['open_rate', 'response_rate', 'conversion_rate']:
            values = [m.get(metric, 0) for m in metrics_list if metric in m]
            
            if len(values) >= 2:
                # Calcul de la tendance (simple régression linéaire)
                x_values = list(range(len(values)))
                if len(set(values)) > 1:  # Si les valeurs ne sont pas toutes identiques
                    # Calcul du coefficient de corrélation comme approximation de tendance
                    mean_x = statistics.mean(x_values)
                    mean_y = statistics.mean(values)
                    
                    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, values))
                    denominator_x = sum((x - mean_x) ** 2 for x in x_values)
                    
                    if denominator_x > 0:
                        slope = numerator / denominator_x
                        
                        if slope > 0.01:
                            trends[metric] = "increasing"
                        elif slope < -0.01:
                            trends[metric] = "decreasing"
                        else:
                            trends[metric] = "stable"
                    else:
                        trends[metric] = "stable"
                else:
                    trends[metric] = "stable"
        
        return trends
    
    def _compare_to_other_niches(self, niche: str, all_niches: List[str]) -> Dict[str, Any]:
        """
        Compare les performances d'une niche aux autres
        
        Args:
            niche: Niche à comparer
            all_niches: Liste de toutes les niches
            
        Returns:
            Comparaison avec les autres niches
        """
        try:
            from core.db import get_niche_performance_summary
            
            # Récupération des performances de la niche actuelle
            current_performance = get_niche_performance_summary(niche)
            
            # Récupération des performances des autres niches
            other_performances = []
            for other_niche in all_niches:
                if other_niche != niche:
                    perf = get_niche_performance_summary(other_niche)
                    if perf:
                        other_performances.append(perf)
            
            if not other_performances:
                return {"comparison": "no_data", "message": "Aucune autre niche pour comparaison"}
            
            # Calcul des moyennes des autres niches
            avg_others = {}
            for metric in ['conversion_rate', 'response_rate', 'open_rate']:
                values = [perf.get(metric, 0) for perf in other_performances if metric in perf]
                if values:
                    avg_others[metric] = statistics.mean(values)
            
            # Comparaison
            comparison = {}
            for metric in avg_others:
                current_value = current_performance.get(metric, 0)
                other_avg = avg_others[metric]
                
                if current_value > other_avg * 1.2:  # 20% de mieux
                    comparison[metric] = "above_average"
                elif current_value < other_avg * 0.8:  # 20% de moins
                    comparison[metric] = "below_average"
                else:
                    comparison[metric] = "average"
            
            return {
                "comparison": comparison,
                "current_performance": current_performance,
                "market_averages": avg_others
            }
            
        except Exception as e:
            return {
                "comparison": "error",
                "message": f"Erreur lors de la comparaison: {str(e)}"
            }


# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du PivotStrategyAgent
    agent = PivotStrategyAgent()
    
    # Test de l'agent
    result = agent.run({
        "action": "analyze_campaign",
        "campaign_id": "test_campaign_001",
        "detail_level": "full"
    })
    
    print(json.dumps(result, indent=2))

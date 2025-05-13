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
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "")
        
        # Traitement selon l'action demandée
        if action == "analyze_campaign":
            # Analyse d'une campagne spécifique
            return self.analyze_campaign(
                input_data.get("campaign_id"),
                input_data.get("detail_level", "full")
            )
        
        elif action == "analyze_niche":
            # Analyse d'une niche spécifique
            return self.analyze_niche(
                input_data.get("niche"),
                input_data.get("time_period", "all")
            )
        
        elif action == "recommend_optimizations":
            # Recommandation d'optimisations basées sur les données
            return self.recommend_optimizations(
                input_data.get("target", "all"),
                input_data.get("optimization_type", "all")
            )
        
        elif action == "store_learning":
            # Stockage d'un apprentissage pour référence future
            return self.store_learning(
                input_data.get("learning_data", {}),
                input_data.get("category", "general")
            )
        
        elif action == "get_insights":
            # Récupération d'insights basés sur des mots-clés
            return self.get_insights(
                input_data.get("keywords", []),
                input_data.get("context", "prospection")
            )
        
        else:
            # Action non reconnue
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
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
                    content = json.loads(item["content"])
                    insights.append({
                        "content": content,
                        "metadata": item["metadata"],
                        "score": item.get("score", 0)
                    })
                except:
                    # Si le contenu n'est pas un JSON valide
                    insights.append({
                        "content": item["content"],
                        "metadata": item["metadata"],
                        "score": item.get("score", 0)
                    })
            
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

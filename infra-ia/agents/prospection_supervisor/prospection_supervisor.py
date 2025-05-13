"""
Module du ProspectionSupervisor - Superviseur des agents de prospection
"""
import os
import json
from typing import Dict, Any, Optional, List
import datetime

from core.agent_base import Agent
from utils.llm import LLMService

class ProspectionSupervisor(Agent):
    """
    ProspectionSupervisor - Superviseur des agents de communication avec les leads
    
    Ce superviseur est responsable de:
    - Coordonner les agents de messages et de relances
    - Superviser les communications et les séquences de messages
    - Interpréter les réponses reçues
    - Adapter les stratégies de communication
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisation du ProspectionSupervisor
        
        Args:
            config_path: Chemin optionnel vers le fichier de configuration
        """
        super().__init__("ProspectionSupervisor", config_path)
        
        # État du superviseur
        self.prospection_stats = {
            "total_leads_contacted": 0,
            "messages_sent": 0,
            "positive_responses": 0,
            "negative_responses": 0,
            "neutral_responses": 0,
            "conversion_rate": 0.0
        }
        
        # Chargement des campagnes actives
        self.active_campaigns = self.config.get("active_campaigns", [])
        
        # Chargement des paramètres de messagerie
        self.messaging_params = self.config.get("messaging_params", {
            "daily_limit": 100,
            "batch_size": 20,
            "time_between_batches_hours": 1,
            "max_follow_ups": 3
        })
    
    def coordinate_messaging(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordonne l'envoi de messages aux leads qualifiés
        
        Args:
            input_data: Données d'entrée avec les leads à contacter
            
        Returns:
            Résultat de l'envoi des messages
        """
        leads = input_data.get("leads", [])
        campaign_id = input_data.get("campaign_id", "")
        template_id = input_data.get("template_id", "")
        
        if not leads:
            return {
                "status": "error",
                "message": "Aucun lead à contacter",
                "leads": []
            }
        
        if not campaign_id:
            return {
                "status": "error",
                "message": "ID de campagne requis",
                "leads": []
            }
        
        if not template_id:
            return {
                "status": "error",
                "message": "ID de template requis",
                "leads": []
            }
        
        self.speak(f"Envoi de messages à {len(leads)} leads pour la campagne '{campaign_id}'", target="OverseerAgent")
        
        # Appel au MessagingAgent pour envoyer les messages
        from agents.overseer.overseer_agent import OverseerAgent
        overseer = OverseerAgent()
        
        messaging_result = overseer.execute_agent("MessagingAgent", {
            "action": "send_messages",
            "leads": leads,
            "campaign_id": campaign_id,
            "template_id": template_id
        })
        
        if messaging_result.get("status") != "success":
            self.speak(f"Erreur lors de l'envoi des messages: {messaging_result.get('message')}", target="OverseerAgent")
            return messaging_result
        
        # Récupération des résultats d'envoi
        sent_messages = messaging_result.get("sent_messages", [])
        failed_messages = messaging_result.get("failed_messages", [])
        
        # Mise à jour des statistiques
        self.prospection_stats["total_leads_contacted"] += len(sent_messages)
        self.prospection_stats["messages_sent"] += len(sent_messages)
        
        # Mise à jour des taux de conversion si des données sont disponibles
        if self.prospection_stats["total_leads_contacted"] > 0:
            conversion_rate = (self.prospection_stats["positive_responses"] / self.prospection_stats["total_leads_contacted"]) * 100
            self.prospection_stats["conversion_rate"] = round(conversion_rate, 2)
        
        # Log des résultats
        self.speak(
            f"Messages envoyés: {len(sent_messages)} succès, {len(failed_messages)} échecs",
            target="OverseerAgent"
        )
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "template_id": template_id,
            "sent_messages": sent_messages,
            "failed_messages": failed_messages,
            "stats": {
                "total": len(leads),
                "sent": len(sent_messages),
                "failed": len(failed_messages)
            }
        }
    
    def coordinate_follow_ups(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordonne l'envoi de relances aux leads déjà contactés
        
        Args:
            input_data: Données d'entrée avec les paramètres de relance
            
        Returns:
            Résultat de l'envoi des relances
        """
        campaign_id = input_data.get("campaign_id", "")
        template_id = input_data.get("template_id", "")
        days_since_last = input_data.get("days_since_last", 7)
        max_follow_ups = input_data.get("max_follow_ups", self.messaging_params.get("max_follow_ups", 3))
        
        if not campaign_id:
            return {
                "status": "error",
                "message": "ID de campagne requis"
            }
        
        if not template_id:
            return {
                "status": "error",
                "message": "ID de template de relance requis"
            }
        
        self.speak(f"Coordination des relances pour la campagne '{campaign_id}'", target="OverseerAgent")
        
        # Appel au FollowUpAgent pour gérer les relances
        from agents.overseer.overseer_agent import OverseerAgent
        overseer = OverseerAgent()
        
        follow_up_result = overseer.execute_agent("FollowUpAgent", {
            "action": "send_follow_ups",
            "campaign_id": campaign_id,
            "template_id": template_id,
            "days_since_last": days_since_last,
            "max_follow_ups": max_follow_ups
        })
        
        if follow_up_result.get("status") != "success":
            self.speak(f"Erreur lors des relances: {follow_up_result.get('message')}", target="OverseerAgent")
            return follow_up_result
        
        # Récupération des résultats d'envoi
        sent_follow_ups = follow_up_result.get("sent_follow_ups", [])
        skipped_follow_ups = follow_up_result.get("skipped_follow_ups", [])
        
        # Mise à jour des statistiques
        self.prospection_stats["messages_sent"] += len(sent_follow_ups)
        
        # Log des résultats
        self.speak(
            f"Relances envoyées: {len(sent_follow_ups)} succès, {len(skipped_follow_ups)} ignorées",
            target="OverseerAgent"
        )
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "template_id": template_id,
            "sent_follow_ups": sent_follow_ups,
            "skipped_follow_ups": skipped_follow_ups,
            "stats": {
                "sent": len(sent_follow_ups),
                "skipped": len(skipped_follow_ups)
            }
        }
    
    def handle_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère une réponse reçue d'un lead
        
        Args:
            input_data: Données d'entrée avec la réponse à traiter
            
        Returns:
            Résultat de l'interprétation de la réponse
        """
        response_data = input_data.get("response_data", {})
        campaign_id = input_data.get("campaign_id", "")
        
        if not response_data:
            return {
                "status": "error",
                "message": "Données de réponse manquantes"
            }
        
        self.speak(f"Traitement d'une réponse pour la campagne '{campaign_id}'", target="OverseerAgent")
        
        # Appel au ResponseInterpreterAgent pour analyser la réponse
        from agents.overseer.overseer_agent import OverseerAgent
        overseer = OverseerAgent()
        
        interpretation_result = overseer.execute_agent("ResponseInterpreterAgent", {
            "action": "interpret",
            "response_data": response_data,
            "campaign_id": campaign_id
        })
        
        if interpretation_result.get("status") != "success":
            self.speak(f"Erreur lors de l'interprétation: {interpretation_result.get('message')}", target="OverseerAgent")
            return interpretation_result
        
        # Récupération de l'interprétation
        interpretation = interpretation_result.get("interpretation", {})
        sentiment = interpretation.get("sentiment", "neutral")
        action = interpretation.get("action", "none")
        
        # Mise à jour des statistiques selon le sentiment
        if sentiment == "positive":
            self.prospection_stats["positive_responses"] += 1
        elif sentiment == "negative":
            self.prospection_stats["negative_responses"] += 1
        else:
            self.prospection_stats["neutral_responses"] += 1
        
        # Mise à jour des taux de conversion
        if self.prospection_stats["total_leads_contacted"] > 0:
            conversion_rate = (self.prospection_stats["positive_responses"] / self.prospection_stats["total_leads_contacted"]) * 100
            self.prospection_stats["conversion_rate"] = round(conversion_rate, 2)
        
        # Exécution de l'action recommandée
        action_result = {}
        
        if action == "transfer_to_crm":
            # Transfert au CRM
            self.speak(f"Transfert au CRM recommandé pour la réponse", target="OverseerAgent")
            # Implémentation du transfert au CRM à ajouter ici
            
        elif action == "send_follow_up":
            # Envoi d'une relance spécifique
            follow_up_template = interpretation.get("follow_up_template", "")
            if follow_up_template:
                self.speak(f"Envoi d'une relance spécifique recommandé", target="OverseerAgent")
                
                # Appel au FollowUpAgent pour une relance spécifique
                action_result = overseer.execute_agent("FollowUpAgent", {
                    "action": "send_custom_follow_up",
                    "lead_id": response_data.get("lead_id", ""),
                    "campaign_id": campaign_id,
                    "template_id": follow_up_template
                })
        
        # Log du résultat final
        self.speak(
            f"Réponse interprétée: sentiment {sentiment}, action {action}",
            target="OverseerAgent"
        )
        
        return {
            "status": "success",
            "campaign_id": campaign_id,
            "interpretation": interpretation,
            "action_taken": action,
            "action_result": action_result
        }
    
    def manage_campaigns(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gère les campagnes de prospection
        
        Args:
            input_data: Données d'entrée pour la gestion des campagnes
            
        Returns:
            Résultat de l'opération sur les campagnes
        """
        action = input_data.get("action", "list")
        
        if action == "list":
            # Liste des campagnes actives
            return {
                "status": "success",
                "active_campaigns": self.active_campaigns
            }
        
        elif action == "add":
            # Ajout d'une nouvelle campagne
            campaign_data = input_data.get("campaign_data", {})
            
            if not campaign_data or not campaign_data.get("id"):
                return {
                    "status": "error",
                    "message": "Données de campagne incorrectes ou ID manquant"
                }
            
            # Vérification que la campagne n'existe pas déjà
            campaign_id = campaign_data.get("id")
            for campaign in self.active_campaigns:
                if campaign.get("id") == campaign_id:
                    return {
                        "status": "error",
                        "message": f"La campagne {campaign_id} existe déjà"
                    }
            
            # Ajout de la campagne
            self.active_campaigns.append(campaign_data)
            
            # Sauvegarde dans la configuration
            self.update_config("active_campaigns", self.active_campaigns)
            
            self.speak(f"Nouvelle campagne ajoutée: {campaign_id}", target="OverseerAgent")
            
            return {
                "status": "success",
                "message": f"Campagne {campaign_id} ajoutée",
                "active_campaigns": self.active_campaigns
            }
        
        elif action == "update":
            # Mise à jour d'une campagne existante
            campaign_data = input_data.get("campaign_data", {})
            
            if not campaign_data or not campaign_data.get("id"):
                return {
                    "status": "error",
                    "message": "Données de campagne incorrectes ou ID manquant"
                }
            
            # Recherche de la campagne à mettre à jour
            campaign_id = campaign_data.get("id")
            campaign_found = False
            
            for i, campaign in enumerate(self.active_campaigns):
                if campaign.get("id") == campaign_id:
                    # Mise à jour de la campagne
                    self.active_campaigns[i] = campaign_data
                    campaign_found = True
                    break
            
            if not campaign_found:
                return {
                    "status": "error",
                    "message": f"Campagne {campaign_id} non trouvée"
                }
            
            # Sauvegarde dans la configuration
            self.update_config("active_campaigns", self.active_campaigns)
            
            self.speak(f"Campagne mise à jour: {campaign_id}", target="OverseerAgent")
            
            return {
                "status": "success",
                "message": f"Campagne {campaign_id} mise à jour",
                "active_campaigns": self.active_campaigns
            }
        
        elif action == "pause" or action == "stop":
            # Mise en pause d'une campagne
            campaign_id = input_data.get("campaign_id", "")
            
            if not campaign_id:
                return {
                    "status": "error",
                    "message": "ID de campagne requis"
                }
            
            # Recherche de la campagne à mettre en pause
            campaign_found = False
            
            for i, campaign in enumerate(self.active_campaigns):
                if campaign.get("id") == campaign_id:
                    # Mise à jour du statut de la campagne
                    self.active_campaigns[i]["status"] = "paused"
                    campaign_found = True
                    break
            
            if not campaign_found:
                return {
                    "status": "error",
                    "message": f"Campagne {campaign_id} non trouvée"
                }
            
            # Sauvegarde dans la configuration
            self.update_config("active_campaigns", self.active_campaigns)
            
            self.speak(f"Campagne mise en pause: {campaign_id}", target="OverseerAgent")
            
            return {
                "status": "success",
                "message": f"Campagne {campaign_id} mise en pause",
                "active_campaigns": self.active_campaigns
            }
        
        elif action == "resume" or action == "start":
            # Reprise d'une campagne
            campaign_id = input_data.get("campaign_id", "")
            
            if not campaign_id:
                return {
                    "status": "error",
                    "message": "ID de campagne requis"
                }
            
            # Recherche de la campagne à reprendre
            campaign_found = False
            
            for i, campaign in enumerate(self.active_campaigns):
                if campaign.get("id") == campaign_id:
                    # Mise à jour du statut de la campagne
                    self.active_campaigns[i]["status"] = "active"
                    campaign_found = True
                    break
            
            if not campaign_found:
                return {
                    "status": "error",
                    "message": f"Campagne {campaign_id} non trouvée"
                }
            
            # Sauvegarde dans la configuration
            self.update_config("active_campaigns", self.active_campaigns)
            
            self.speak(f"Campagne reprise: {campaign_id}", target="OverseerAgent")
            
            return {
                "status": "success",
                "message": f"Campagne {campaign_id} reprise",
                "active_campaigns": self.active_campaigns
            }
        
        elif action == "delete" or action == "remove":
            # Suppression d'une campagne
            campaign_id = input_data.get("campaign_id", "")
            
            if not campaign_id:
                return {
                    "status": "error",
                    "message": "ID de campagne requis"
                }
            
            # Recherche de la campagne à supprimer
            campaign_found = False
            new_campaigns = []
            
            for campaign in self.active_campaigns:
                if campaign.get("id") == campaign_id:
                    campaign_found = True
                else:
                    new_campaigns.append(campaign)
            
            if not campaign_found:
                return {
                    "status": "error",
                    "message": f"Campagne {campaign_id} non trouvée"
                }
            
            # Mise à jour de la liste
            self.active_campaigns = new_campaigns
            
            # Sauvegarde dans la configuration
            self.update_config("active_campaigns", self.active_campaigns)
            
            self.speak(f"Campagne supprimée: {campaign_id}", target="OverseerAgent")
            
            return {
                "status": "success",
                "message": f"Campagne {campaign_id} supprimée",
                "active_campaigns": self.active_campaigns
            }
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }
    
    def get_prospection_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de prospection
        
        Returns:
            Statistiques de prospection
        """
        return {
            "status": "success",
            "stats": self.prospection_stats,
            "active_campaigns": len(self.active_campaigns)
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implémentation de la méthode run() principale
        
        Args:
            input_data: Les données d'entrée
            
        Returns:
            Les données de sortie
        """
        action = input_data.get("action", "")
        
        if action == "send_messages" or action == "message":
            return self.coordinate_messaging(input_data)
        
        elif action == "follow_up" or action == "send_follow_ups":
            return self.coordinate_follow_ups(input_data)
        
        elif action == "handle_response":
            return self.handle_response(input_data)
        
        elif action == "manage_campaigns":
            return self.manage_campaigns(input_data)
        
        elif action == "get_stats":
            return self.get_prospection_stats()
        
        else:
            return {
                "status": "error",
                "message": f"Action non reconnue: {action}"
            }

# Si ce script est exécuté directement
if __name__ == "__main__":
    # Création d'une instance du ProspectionSupervisor
    supervisor = ProspectionSupervisor()
    
    # Test de l'agent
    result = supervisor.run({
        "action": "get_stats"
    })
    
    print(json.dumps(result, indent=2))

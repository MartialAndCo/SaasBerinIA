"""Client API pour communiquer avec l'API BerinIA"""
import requests
import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from config.settings import API_BASE_URL, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

class BeriniaAPIClient:
    """Client pour l'API BerinIA"""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.timeout = REQUEST_TIMEOUT
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        """Effectue une requête à l'API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API {method} {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue {method} {endpoint}: {e}")
            return None
    
    def _extract_list_from_response(self, result: Any, key: str) -> List[Dict]:
        """Extrait une liste depuis une réponse API qui peut être un dict ou une liste directe"""
        if not result:
            return []
        
        # Si c'est déjà une liste, on la retourne directement
        if isinstance(result, list):
            return result
        
        # Si c'est un dictionnaire, on essaie d'extraire la clé
        if isinstance(result, dict):
            return result.get(key, [])
        
        # Cas non prévu, on retourne une liste vide
        logger.warning(f"Format de réponse inattendu pour {key}: {type(result)}")
        return []
    
    # === STATISTIQUES ===
    def get_dashboard_stats(self) -> Optional[Dict]:
        """Récupère les statistiques du tableau de bord"""
        return self._make_request('GET', '/dashboard')
    
    def get_general_stats(self) -> Optional[Dict]:
        """Récupère les statistiques générales"""
        return self._make_request('GET', '/stats')
    
    # === CAMPAGNES ===
    def get_campaigns(self, status: Optional[str] = None) -> Optional[List[Dict]]:
        """Récupère la liste des campagnes"""
        params = {}
        if status:
            params['status'] = status
        
        result = self._make_request('GET', '/campaigns', params=params)
        return self._extract_list_from_response(result, 'campaigns')
    
    def get_campaign_details(self, campaign_id: str) -> Optional[Dict]:
        """Récupère les détails d'une campagne"""
        return self._make_request('GET', f'/campaigns/{campaign_id}')
    
    def get_campaign_stats(self, campaign_id: str) -> Optional[Dict]:
        """Récupère les statistiques d'une campagne"""
        return self._make_request('GET', f'/campaigns/{campaign_id}/stats')
    
    def start_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Démarre une campagne"""
        data = {"status": "active"}
        return self._make_request('PUT', f'/campaigns/{campaign_id}/status', json=data)
    
    def stop_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Arrête une campagne"""
        data = {"status": "paused"}
        return self._make_request('PUT', f'/campaigns/{campaign_id}/status', json=data)
    
    def export_campaign_data(self, campaign_id: str) -> Optional[Dict]:
        """Exporte les données d'une campagne"""
        return self._make_request('GET', f'/campaigns/{campaign_id}/export')
    
    # === NOUVEAUX ENDPOINTS GESTION CAMPAGNES ===
    def get_active_campaigns(self) -> Optional[List[Dict]]:
        """Récupère les campagnes actives via le nouvel endpoint"""
        result = self._make_request('GET', '/campaigns-management/active')
        return self._extract_list_from_response(result, 'campaigns')
    
    def get_inactive_campaigns(self) -> Optional[List[Dict]]:
        """Récupère les campagnes inactives via le nouvel endpoint"""
        result = self._make_request('GET', '/campaigns-management/inactive')
        return self._extract_list_from_response(result, 'campaigns')
    
    def get_campaign_detailed_stats(self, campaign_id: str) -> Optional[Dict]:
        """Récupère les statistiques détaillées d'une campagne"""
        return self._make_request('GET', f'/campaigns-management/stats/{campaign_id}')
    
    def launch_campaign(self, niche_id: int, city: str, target_leads: int = 100, description: str = None) -> Optional[Dict]:
        """Lance une nouvelle campagne"""
        data = {
            "niche_id": niche_id,
            "city": city,
            "target_leads": target_leads
        }
        if description:
            data["description"] = description
        return self._make_request('POST', '/campaigns-management/launch', json=data)
    
    def stop_campaign_management(self, campaign_id: str) -> Optional[Dict]:
        """Arrête une campagne via le nouvel endpoint"""
        return self._make_request('PUT', f'/campaigns-management/{campaign_id}/stop')
    
    def restart_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Redémarre une campagne"""
        return self._make_request('PUT', f'/campaigns-management/{campaign_id}/restart')
    
    def export_campaign_management(self, campaign_id: str) -> Optional[Dict]:
        """Exporte les données d'une campagne via le nouvel endpoint"""
        return self._make_request('GET', f'/campaigns-management/export/{campaign_id}')
    
    # === NOUVEAUX ENDPOINTS POUR CRÉATION CAMPAGNES ===
    def get_available_niches(self) -> Optional[List[Dict]]:
        """Récupère les niches disponibles pour créer une campagne"""
        result = self._make_request('GET', '/niches/')
        return self._extract_list_from_response(result, 'niches')
    
    def get_available_cities(self) -> Optional[List[str]]:
        """Récupère les villes disponibles"""
        # Pour l'instant on retourne une liste de villes communes
        return ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille"]
    
    def create_new_campaign(self, niche_id: int, niche_name: str, city: str, target_leads: int = 50, description: str = None) -> Optional[Dict]:
        """Crée une nouvelle campagne"""
        data = {
            "niche_id": niche_id,
            "niche_name": niche_name,
            "city": city,
            "target_leads": target_leads,
            "description": description or f"Nouvelle campagne {niche_name} - {city}"
        }
        return self._make_request('POST', '/campaigns-management/launch', json=data)
    
    # === LEADS ===
    def get_leads_count(self) -> Optional[Dict]:
        """Récupère le nombre total de leads"""
        result = self._make_request('GET', '/leads/count')
        return result
    
    def get_leads_stats(self) -> Optional[Dict]:
        """Récupère les statistiques des leads"""
        return self._make_request('GET', '/leads/stats')
    
    def get_leads(self, limit: int = 10, offset: int = 0, status: Optional[str] = None) -> Optional[List[Dict]]:
        """Récupère la liste des leads avec pagination"""
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        
        result = self._make_request('GET', '/leads/', params=params)
        return self._extract_list_from_response(result, 'leads')
    
    def search_leads(self, query: str) -> Optional[List[Dict]]:
        """Recherche des leads"""
        params = {'search': query}
        result = self._make_request('GET', '/leads/search', params=params)
        return self._extract_list_from_response(result, 'leads')
    
    def get_lead_details(self, lead_id: str) -> Optional[Dict]:
        """Récupère les détails d'un lead"""
        return self._make_request('GET', f'/leads/{lead_id}')
    
    def get_lead_compensation(self, lead_id: str) -> Optional[Dict]:
        """Récupère la compensation d'un lead"""
        return self._make_request('GET', f'/leads/{lead_id}/compensation')
    
    # === NICHES ===
    def get_niches(self) -> Optional[List[Dict]]:
        """Récupère la liste des niches"""
        result = self._make_request('GET', '/niches')
        return self._extract_list_from_response(result, 'niches')
    
    def get_niche_details(self, niche_id: str) -> Optional[Dict]:
        """Récupère les détails d'une niche"""
        return self._make_request('GET', f'/niches/{niche_id}')
    
    def get_niche_performance(self, niche_id: str) -> Optional[Dict]:
        """Récupère les performances d'une niche"""
        return self._make_request('GET', f'/niches/{niche_id}/performance')
    
    def stop_niche(self, niche_id: str) -> Optional[Dict]:
        """Arrête une niche"""
        return self._make_request('POST', f'/niches/{niche_id}/stop')
    
    def analyze_niche_viability(self, niche_name: str) -> Optional[Dict]:
        """Analyse la viabilité d'une niche"""
        data = {'niche_name': niche_name}
        return self._make_request('POST', '/niches/analyze', json=data)
    
    def get_niche_campaigns(self, niche_id: str) -> Optional[List[Dict]]:
        """Récupère les campagnes associées à une niche"""
        result = self._make_request('GET', f'/niches/{niche_id}/campaigns')
        return self._extract_list_from_response(result, 'campaigns')
    
    # === AGENTS ===
    def get_agents_status(self) -> Optional[List[Dict]]:
        """Récupère l'état des agents"""
        result = self._make_request('GET', '/agents/')
        return self._extract_list_from_response(result, 'agents')
    
    def get_agent_details(self, agent_name: str) -> Optional[Dict]:
        """Récupère les détails d'un agent"""
        return self._make_request('GET', f'/agents/{agent_name}')
    
    def restart_agent(self, agent_name: str) -> Optional[Dict]:
        """Redémarre un agent"""
        return self._make_request('POST', f'/agents/{agent_name}/restart')
    
    # === SYSTÈME ===
    def get_system_status(self) -> Optional[Dict]:
        """Récupère l'état du système"""
        return self._make_request('GET', '/system/status')
    
    def get_scheduled_tasks(self) -> Optional[List[Dict]]:
        """Récupère les tâches planifiées"""
        result = self._make_request('GET', '/tasks')
        return self._extract_list_from_response(result, 'tasks')
    
    def create_task(self, action: str, agent_id: int, parameters: Dict = None, 
                   priority: int = 3, scheduled_time: str = None, 
                   is_recurring: bool = False, recurrence_interval: int = None) -> Optional[Dict]:
        """Crée une nouvelle tâche planifiée"""
        data = {
            "action": action,
            "agent_id": agent_id,
            "parameters": parameters or {},
            "priority": priority,
            "is_recurring": is_recurring
        }
        if scheduled_time:
            data["scheduled_time"] = scheduled_time
        if recurrence_interval:
            data["recurrence_interval"] = recurrence_interval
        
        return self._make_request('POST', '/tasks', json=data)
    
    def delete_task(self, task_id: str) -> Optional[Dict]:
        """Supprime une tâche planifiée"""
        return self._make_request('DELETE', f'/tasks/{task_id}')
    
    def execute_task_now(self, task_id: str) -> Optional[Dict]:
        """Exécute immédiatement une tâche"""
        return self._make_request('POST', f'/tasks/{task_id}/execute')
    
    def update_task_status(self, task_id: str, status: str) -> Optional[Dict]:
        """Met à jour le statut d'une tâche"""
        data = {"status": status}
        return self._make_request('PUT', f'/tasks/{task_id}', json=data)
    
    def get_task_details(self, task_id: str) -> Optional[Dict]:
        """Récupère les détails d'une tâche"""
        return self._make_request('GET', f'/tasks/{task_id}')
    
    def get_security_logs(self) -> Optional[List[Dict]]:
        """Récupère les logs de sécurité"""
        result = self._make_request('GET', '/system-logs')
        return self._extract_list_from_response(result, 'logs')
    
    def get_system_logs(self, limit: int = 50) -> Optional[List[Dict]]:
        """Récupère les logs système"""
        params = {'limit': limit}
        result = self._make_request('GET', '/logs/recent', params=params)
        return self._extract_list_from_response(result, 'logs')
    
    def restart_system(self) -> Optional[Dict]:
        """Redémarre le système"""
        return self._make_request('POST', '/system/restart')
    
    def get_services_status(self) -> Optional[Dict]:
        """Récupère l'état des services"""
        return self._make_request('GET', '/services/')
    
    def restart_service(self, service_name: str) -> Optional[Dict]:
        """Redémarre un service"""
        return self._make_request('POST', f'/services/{service_name}/restart')
    
    # === NOUVELLES MÉTHODES POUR TÂCHES AVANCÉES ===
    
    def create_advanced_task(self, task_type: str, agent_id: int, action: str, 
                           parameters: Dict = None, priority: int = 3,
                           scheduled_time: str = None, is_recurring: bool = False,
                           recurrence_interval: int = None, end_date: str = None,
                           condition: str = None, max_executions: int = None,
                           auto_cleanup: bool = True, cleanup_after_days: int = 30) -> Optional[Dict]:
        """Crée une tâche avec tous les paramètres avancés selon le type"""
        data = {
            "action": action,
            "agent_id": agent_id,
            "parameters": parameters or {},
            "priority": priority,
            "is_recurring": is_recurring
        }
        
        # Paramètres temporels
        if scheduled_time:
            data["scheduled_time"] = scheduled_time
        if recurrence_interval:
            data["recurrence_interval"] = recurrence_interval
        
        # Paramètres avancés selon le type de tâche
        task_behavior = {
            "task_type": task_type,
            "auto_cleanup": auto_cleanup,
            "cleanup_after_days": cleanup_after_days
        }
        
        if task_type == "system_recurring":
            task_behavior.update({
                "auto_cleanup": False,  # Jamais de nettoyage pour les tâches système
                "cleanup_after_days": None,
                "priority_decay": False
            })
        elif task_type == "business_recurring":
            task_behavior.update({
                "end_date": end_date,
                "priority_decay": True
            })
        elif task_type == "one_time":
            task_behavior.update({
                "max_executions": 1,
                "cleanup_after_days": 1
            })
        elif task_type == "conditional":
            task_behavior.update({
                "condition": condition,
                "cleanup_after_days": 7
            })
        
        # Ajouter le comportement aux paramètres
        data["parameters"]["task_behavior"] = task_behavior
        
        return self._make_request('POST', '/tasks', json=data)
    
    def get_leads_for_selection(self, status: str = None, campaign_id: str = None, 
                               niche_id: str = None, min_score: int = None) -> Optional[List[Dict]]:
        """Récupère des leads selon des critères spécifiques pour sélection"""
        params = {}
        if status:
            params['status'] = status
        if campaign_id:
            params['campaign_id'] = campaign_id
        if niche_id:
            params['niche_id'] = niche_id
        if min_score:
            params['min_score'] = min_score
        
        result = self._make_request('GET', '/leads/', params=params)
        return self._extract_list_from_response(result, 'leads')
    
    def get_campaigns_for_selection(self, status: str = None, niche_id: str = None) -> Optional[List[Dict]]:
        """Récupère des campagnes pour sélection dans les tâches"""
        params = {}
        if status:
            params['status'] = status
        if niche_id:
            params['niche_id'] = niche_id
        
        result = self._make_request('GET', '/campaigns', params=params)
        return self._extract_list_from_response(result, 'campaigns')
    
    def get_niches_for_selection(self, status: str = 'active') -> Optional[List[Dict]]:
        """Récupère les niches disponibles pour sélection"""
        params = {}
        if status:
            params['status'] = status
        
        result = self._make_request('GET', '/niches', params=params)
        return self._extract_list_from_response(result, 'niches')
    
    # === RENDEZ-VOUS (MEETINGS) ===
    
    def get_meetings_stats(self, start_date: str = None, end_date: str = None) -> Optional[Dict]:
        """Récupère les statistiques des rendez-vous"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return self._make_request('GET', '/meetings/stats', params=params)
    
    def get_meetings(self, lead_id: int = None, status: str = None, 
                    start_date: str = None, end_date: str = None,
                    include_lead: bool = True, limit: int = 20, offset: int = 0) -> Optional[Dict]:
        """Récupère la liste des rendez-vous avec pagination"""
        params = {
            'include_lead': include_lead,
            'limit': limit,
            'offset': offset
        }
        if lead_id:
            params['lead_id'] = lead_id
        if status:
            params['status'] = status
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return self._make_request('GET', '/meetings/', params=params)
    
    def get_upcoming_meetings(self, days: int = 7, include_lead: bool = True) -> Optional[Dict]:
        """Récupère les rendez-vous à venir"""
        params = {
            'days': days,
            'include_lead': include_lead
        }
        return self._make_request('GET', '/meetings/upcoming', params=params)
    
    def get_meetings_by_period(self, period: str = "today", include_lead: bool = True) -> Optional[Dict]:
        """Récupère les rendez-vous par période (today, week, month)"""
        params = {
            'period': period,
            'include_lead': include_lead
        }
        return self._make_request('GET', '/meetings/by-period', params=params)
    
    def get_meeting_details(self, meeting_id: int) -> Optional[Dict]:
        """Récupère les détails d'un rendez-vous spécifique"""
        return self._make_request('GET', f'/meetings/{meeting_id}')
    
    def update_meeting_status(self, meeting_id: int, status: str, notes: str = None) -> Optional[Dict]:
        """Met à jour le statut d'un rendez-vous"""
        data = {'status': status}
        if notes:
            data['notes'] = notes
        
        return self._make_request('PATCH', f'/meetings/{meeting_id}/status', json=data)
    
    def reschedule_meeting(self, meeting_id: int, new_start_time: str, 
                          new_duration: int = None, reason: str = None,
                          notify_client: bool = True) -> Optional[Dict]:
        """Reporte un rendez-vous"""
        data = {
            'action': 'reschedule',
            'new_start_time': new_start_time,
            'notify_client': notify_client
        }
        if new_duration:
            data['new_duration'] = new_duration
        if reason:
            data['reason'] = reason
        
        return self._make_request('POST', f'/meetings/{meeting_id}/action', json=data)
    
    def cancel_meeting(self, meeting_id: int, reason: str = None, notify_client: bool = True) -> Optional[Dict]:
        """Annule un rendez-vous"""
        data = {
            'action': 'cancel',
            'notify_client': notify_client
        }
        if reason:
            data['reason'] = reason
        
        return self._make_request('POST', f'/meetings/{meeting_id}/action', json=data)
    
    def create_meeting(self, client_name: str, client_email: str, start_time: str,
                      end_time: str, duration_minutes: int = 30, description: str = None,
                      lead_id: int = None, meeting_link: str = None) -> Optional[Dict]:
        """Crée un nouveau rendez-vous"""
        data = {
            'client_name': client_name,
            'client_email': client_email,
            'start_time': start_time,
            'end_time': end_time,
            'duration_minutes': duration_minutes
        }
        if description:
            data['description'] = description
        if lead_id:
            data['lead_id'] = lead_id
        if meeting_link:
            data['meeting_link'] = meeting_link
        
        return self._make_request('POST', '/meetings/', json=data)
    
    # === CONVERSATIONS ET RÉSUMÉS ===
    
    def get_conversations(self, lead_id: int = None, limit: int = 50) -> Optional[Dict]:
        """Récupère la liste des conversations"""
        params = {'limit': limit}
        if lead_id:
            params['lead_id'] = lead_id
        
        return self._make_request('GET', '/conversations/conversations', params=params)
    
    def get_conversation_details(self, thread_id: str) -> Optional[Dict]:
        """Récupère les détails d'une conversation"""
        return self._make_request('GET', f'/conversations/conversations/{thread_id}')
    
    def get_conversation_summary(self, thread_id: str) -> Optional[Dict]:
        """Récupère le résumé d'une conversation"""
        return self._make_request('GET', f'/conversations/conversations/{thread_id}/summary')
    
    def get_lead_conversation_summary(self, lead_id: int) -> Optional[Dict]:
        """Récupère le résumé de toutes les conversations d'un lead"""
        return self._make_request('GET', f'/conversations/leads/{lead_id}/conversation-summary')
    
    # === CONVERSIONS DE RENDEZ-VOUS ===
    
    def get_services(self) -> Optional[Dict]:
        """Récupère la liste des services disponibles"""
        return self._make_request('GET', '/conversions/services/')
    
    def convert_meeting(self, meeting_id: int, outcome_type: str, **kwargs) -> Optional[Dict]:
        """Enregistre le résultat d'un rendez-vous"""
        data = {
            'outcome_type': outcome_type
        }
        
        # Ajouter les paramètres optionnels
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value
        
        return self._make_request('POST', f'/conversions/meetings/{meeting_id}/convert', json=data)
    
    def get_meeting_outcome(self, meeting_id: int) -> Optional[Dict]:
        """Récupère le résultat d'un rendez-vous"""
        return self._make_request('GET', f'/conversions/meetings/{meeting_id}/outcome')
    
    def get_conversion_stats(self, start_date: str = None, end_date: str = None) -> Optional[Dict]:
        """Récupère les statistiques de conversion"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return self._make_request('GET', '/conversions/stats/conversions', params=params)
    
    def get_refusal_stats(self) -> Optional[Dict]:
        """Récupère les statistiques des raisons de refus"""
        return self._make_request('GET', '/conversions/stats/refusals')
    
    def get_revenue_stats(self, start_date: str = None, end_date: str = None) -> Optional[Dict]:
        """Récupère les statistiques de revenus"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return self._make_request('GET', '/conversions/stats/revenue', params=params)
    
    def get_sales(self, limit: int = 20, offset: int = 0, payment_status: str = None) -> Optional[Dict]:
        """Récupère la liste des ventes"""
        params = {'limit': limit, 'offset': offset}
        if payment_status:
            params['payment_status'] = payment_status
        
        return self._make_request('GET', '/conversions/sales/', params=params)
    
    def update_sale_payment(self, sale_id: int, payment_status: str, 
                           payment_date: str = None, notes: str = None) -> Optional[Dict]:
        """Met à jour le statut de paiement d'une vente"""
        data = {'payment_status': payment_status}
        if payment_date:
            data['payment_date'] = payment_date
        if notes:
            data['notes'] = notes
        
        return self._make_request('PUT', f'/conversions/sales/{sale_id}/payment', json=data)
    
    def get_follow_ups(self) -> Optional[Dict]:
        """Récupère les prospects à relancer"""
        return self._make_request('GET', '/conversions/follow-ups/')
    
    # === BILLING ===
    
    def get_clients_for_billing(self, limit: int = 50) -> Optional[List[Dict]]:
        """Récupère les clients avec informations de facturation"""
        params = {'limit': limit}
        result = self._make_request('GET', '/leads/', params=params)
        return self._extract_list_from_response(result, 'leads')

    def get_billing_info(self, lead_id: int) -> Optional[Dict]:
        """Récupère les informations de facturation d'un lead"""
        return self._make_request('GET', f'/billing/lead/{lead_id}')

    def update_billing_info(self, lead_id: int, billing_data: Dict) -> Optional[Dict]:
        """Met à jour les informations de facturation d'un lead"""
        return self._make_request('PUT', f'/billing/lead/{lead_id}', json=billing_data)

    def get_available_services(self) -> Optional[List[Dict]]:
        """Récupère les services disponibles pour facturation"""
        result = self._make_request('GET', '/conversions/services/')
        return result if isinstance(result, list) else []

    def create_invoice(self, invoice_data: Dict) -> Optional[Dict]:
        """Crée une facture"""
        return self._make_request('POST', '/billing/create-invoice', json=invoice_data)

    def get_lead_invoices(self, lead_id: int) -> Optional[List[Dict]]:
        """Récupère les factures d'un lead"""
        result = self._make_request('GET', f'/billing/invoices/{lead_id}')
        return result if isinstance(result, list) else []

    def get_invoice_details(self, invoice_id: int) -> Optional[Dict]:
        """Récupère les détails d'une facture"""
        return self._make_request('GET', f'/billing/invoice/{invoice_id}')

    def send_invoice(self, invoice_id: int) -> Optional[Dict]:
        """Envoie une facture par email"""
        return self._make_request('POST', f'/billing/invoice/{invoice_id}/send')

    def get_all_invoices(self, status: str = None, limit: int = 50) -> Optional[List[Dict]]:
        """Récupère toutes les factures"""
        params = {'limit': limit}
        if status:
            params['status'] = status
        result = self._make_request('GET', '/billing/invoices', params=params)
        return result if isinstance(result, list) else []

    def get_invoice_details(self, invoice_id: int) -> Optional[Dict]:
        """Récupère les détails complets d'une facture"""
        return self._make_request('GET', f'/billing/invoice/{invoice_id}/details')

    def get_billing_stats(self, period: str = 'month') -> Optional[Dict]:
        """Récupère les statistiques de facturation"""
        params = {'period': period}
        return self._make_request('GET', '/billing/stats', params=params)

    def get_today_meetings_for_billing(self) -> Optional[Dict]:
        """Récupère les rendez-vous du jour pour facturation"""
        return self._make_request('GET', '/billing/today-meetings')

    def get_stripe_products(self, active: bool = True, limit: int = 100) -> Optional[Dict]:
        """Récupère les produits Stripe avec leurs prix"""
        params = {'active': active, 'limit': limit}
        return self._make_request('GET', '/billing/stripe-products', params=params)

    def sync_stripe_products(self) -> Optional[Dict]:
        """Synchronise les produits Stripe"""
        return self._make_request('POST', '/billing/sync-stripe-products')

    def create_invoice_with_stripe_products(self, invoice_data: Dict) -> Optional[Dict]:
        """Crée une facture avec des produits Stripe"""
        return self._make_request('POST', '/billing/create-invoice-with-stripe-products', json=invoice_data)

    def validate_invoice_items(self, items: List[Dict]) -> Optional[Dict]:
        """Valide les items d'une facture et ajoute automatiquement les abonnements"""
        return self._make_request('POST', '/billing/validate-invoice-items', json=items)

    def create_invoice_with_validation(self, lead_id: int, selected_items: List[Dict], send_email: bool = False) -> Optional[Dict]:
        """Crée une facture avec validation automatique des abonnements"""
        data = {
            "lead_id": lead_id,
            "selected_items": selected_items,
            "send_email": send_email
        }
        return self._make_request('POST', '/billing/create-invoice-with-validation', json=data)


class APIClient:
    """Client API asynchrone pour les notifications de paiement"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def get(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Effectue une requête GET asynchrone"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API request failed: {response.status} - {url}")
                        return None
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None
    
    async def post(self, endpoint: str, json: Dict = None) -> Optional[Dict]:
        """Effectue une requête POST asynchrone"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=json) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        logger.error(f"API request failed: {response.status} - {url}")
                        return None
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None

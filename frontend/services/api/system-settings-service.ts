/**
 * Service pour gérer les paramètres système
 */

import apiService, { ApiResponse } from '../api';

// Types pour les paramètres système
export interface SystemIntegrations {
  // Twilio
  twilio_account_sid?: string;
  twilio_auth_token?: string;
  twilio_integration_active?: boolean;
  
  // Instantly.ai
  instantly_api_key?: string;
  instantly_integration_active?: boolean;
  
  // WhatsApp
  whatsapp_integration_active?: boolean;
  whatsapp_notification_group?: string;
  service_active?: boolean;
}

export interface SystemScheduling {
  agent_frequency?: string;
  agent_execution_time?: string;
  agent_active?: boolean;
  custom_hours_interval?: number;
  max_execution_duration?: number;
  leads_per_campaign?: number;
  max_simultaneous_campaigns?: number;
  daily_report_active?: boolean;
  daily_report_time?: string;
  report_channel_email?: boolean;
  report_channel_slack?: boolean;
  report_channel_dashboard?: boolean;
  report_channel_whatsapp?: boolean;
  knowledge_trigger_frequency?: string;
  max_learning_delay?: number;
}

export interface ServiceStatus {
  name: string;
  status: 'active' | 'inactive' | 'error';
  uptime?: string;
}

class SystemSettingsService {
  /**
   * Récupère tous les paramètres d'intégration
   */
  async getIntegrations(): Promise<SystemIntegrations> {
    try {
      // Le préfixe '/api/' est nécessaire pour les URL
      const response = await apiService.get<ApiResponse<SystemIntegrations>>('/api/system/integrations');
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la récupération des paramètres d\'intégration:', error);
      throw error;
    }
  }

  /**
   * Met à jour les paramètres d'intégration
   */
  async updateIntegrations(data: Partial<SystemIntegrations>): Promise<SystemIntegrations> {
    try {
      const response = await apiService.post<ApiResponse<SystemIntegrations>>('/api/system/integrations', data);
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la mise à jour des paramètres d\'intégration:', error);
      throw error;
    }
  }

  /**
   * Récupère les paramètres spécifiques à Instantly.ai
   */
  async getInstantlySettings(): Promise<Partial<SystemIntegrations>> {
    try {
      const response = await apiService.get<ApiResponse<Partial<SystemIntegrations>>>('/api/system/integrations/instantly');
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la récupération des paramètres Instantly.ai:', error);
      throw error;
    }
  }

  /**
   * Met à jour les paramètres spécifiques à Instantly.ai
   */
  async updateInstantlySettings(data: Partial<SystemIntegrations>): Promise<Partial<SystemIntegrations>> {
    try {
      const response = await apiService.post<ApiResponse<Partial<SystemIntegrations>>>('/api/system/integrations/instantly', data);
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la mise à jour des paramètres Instantly.ai:', error);
      throw error;
    }
  }

  /**
   * Récupère les paramètres spécifiques à WhatsApp
   */
  async getWhatsAppSettings(): Promise<Partial<SystemIntegrations>> {
    try {
      const response = await apiService.get<ApiResponse<Partial<SystemIntegrations>>>('/api/system/integrations/whatsapp');
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la récupération des paramètres WhatsApp:', error);
      throw error;
    }
  }

  /**
   * Met à jour les paramètres spécifiques à WhatsApp
   */
  async updateWhatsAppSettings(data: Partial<SystemIntegrations>): Promise<Partial<SystemIntegrations>> {
    try {
      const response = await apiService.post<ApiResponse<Partial<SystemIntegrations>>>('/api/system/integrations/whatsapp', data);
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la mise à jour des paramètres WhatsApp:', error);
      throw error;
    }
  }

  /**
   * Récupère tous les paramètres de planification
   */
  async getScheduling(): Promise<SystemScheduling> {
    try {
      const response = await apiService.get<ApiResponse<SystemScheduling>>('/api/system/scheduling');
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la récupération des paramètres de planification:', error);
      throw error;
    }
  }

  /**
   * Met à jour les paramètres de planification
   */
  async updateScheduling(data: Partial<SystemScheduling>): Promise<SystemScheduling> {
    try {
      const response = await apiService.post<ApiResponse<SystemScheduling>>('/api/system/scheduling', data);
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la mise à jour des paramètres de planification:', error);
      throw error;
    }
  }

  /**
   * Récupère le statut des services système
   */
  async getServicesStatus(): Promise<ServiceStatus[]> {
    try {
      // Maintenant nous appelons une API réelle au lieu des données simulées
      console.log("Appel de l'API pour récupérer les services");
      const response = await apiService.get<ApiResponse<ServiceStatus[]>>('/api/system/services');
      console.log("Réponse de l'API services:", response.data);
      
      // Vérification correcte de la présence de données
      if (response.data && (response.data as any).status === 'success' && Array.isArray((response.data as any).data)) {
        console.log("Utilisation des données réelles de l'API:", (response.data as any).data);
        return (response.data as any).data;
      } else {
        console.warn("Format de réponse API inattendu, utilisation du fallback");
        return this.getFallbackServiceStatus();
      }
    } catch (error) {
      console.error('Erreur lors de la récupération du statut des services:', error);
      // En cas d'erreur, retourner les données simulées comme fallback
      console.warn("Utilisation des données de secours (fallback)");
      return this.getFallbackServiceStatus();
    }
  }

  /**
   * Données de statut de service de secours (fallback) en cas d'échec de l'API
   */
  private getFallbackServiceStatus(): ServiceStatus[] {
    console.warn("Utilisation de données simulées pour le statut des services");
    return [
      {
        name: 'berinia-api.service',
        status: 'active',
        uptime: 'N/A (simulé)'
      },
      {
        name: 'berinia-next.service',
        status: 'active',
        uptime: 'N/A (simulé)'
      },
      {
        name: 'berinia-webhook.service',
        status: 'active',
        uptime: 'N/A (simulé)'
      },
      {
        name: 'berinia-whatsapp.service',
        status: 'active',
        uptime: 'N/A (simulé)'
      },
      {
        name: 'berinia-qdrant.service',
        status: 'active',
        uptime: 'N/A (simulé)'
      },
      {
        name: 'berinia-agents.service',
        status: 'active',
        uptime: 'N/A (simulé)'
      },
      {
        name: 'berinia-scheduler.service',
        status: 'active',
        uptime: 'N/A (simulé)'
      }
    ];
  }

  /**
   * Contrôle un service système (démarrer/arrêter/redémarrer)
   */
  async controlService(serviceName: string, action: 'start' | 'stop' | 'restart'): Promise<boolean> {
    try {
      const response = await apiService.post<ApiResponse<{ success: boolean }>>('/api/system/service-control', {
        service: serviceName,
        action: action
      });
      return response.data.data?.success || false;
    } catch (error) {
      console.error(`Erreur lors de l'action ${action} sur le service ${serviceName}:`, error);
      throw error;
    }
  }
}

// Exporter une instance unique du service
const systemSettingsService = new SystemSettingsService();
export default systemSettingsService;

import apiService, { ApiResponse } from '../api';

/**
 * Interface pour les variables d'environnement
 */
export interface EnvVariables {
  OPENAI_API_KEY: string;
  INSTANTLY_API_KEY: string;
  TWILIO_SID: string;
  TWILIO_TOKEN: string;
  TWILIO_PHONE: string;
  APIFY_API_KEY: string;
  APOLLO_API_KEY: string;
  [key: string]: string;  // Pour permettre l'accès dynamique aux propriétés
}

/**
 * Service pour gérer les variables d'environnement
 */
class EnvVariablesService {
  /**
   * Récupère les variables d'environnement
   */
  async getVariables(): Promise<EnvVariables> {
    try {
      const response = await apiService.get<ApiResponse<EnvVariables>>('/api/system/env-variables');
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la récupération des variables d\'environnement:', error);
      throw error;
    }
  }

  /**
   * Met à jour les variables d'environnement
   */
  async updateVariables(data: Partial<EnvVariables>): Promise<EnvVariables> {
    try {
      const response = await apiService.post<ApiResponse<EnvVariables>>('/api/system/env-variables', data);
      return response.data.data || {};
    } catch (error) {
      console.error('Erreur lors de la mise à jour des variables d\'environnement:', error);
      throw error;
    }
  }

  /**
   * Masque partiellement une clé API pour l'affichage
   */
  maskApiKey(key: string): string {
    if (!key) return '';
    if (key.length <= 8) return '••••••••'; // Si trop courte, masquer complètement
    
    // Montrer les premiers et derniers caractères
    const firstPart = key.substring(0, 4);
    const lastPart = key.substring(key.length - 4);
    return `${firstPart}••••••••••••${lastPart}`;
  }
}

// Exporter une instance unique du service
const envVariablesService = new EnvVariablesService();
export default envVariablesService;

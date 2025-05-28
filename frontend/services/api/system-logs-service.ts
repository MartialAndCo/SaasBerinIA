import { apiRequest } from '../api-interceptor';

export interface SystemLog {
  id: number;
  timestamp: string;
  level: string;
  source: string;
  agent_name: string | null;
  module: string | null;
  message: string;
  details: Record<string, any> | null;
  context_id: string | null;
  created_at: string;
}

export interface SystemLogResponse {
  logs: SystemLog[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface SystemLogStats {
  total_logs: number;
  by_level: Record<string, number>;
  by_source: Record<string, number>;
  by_agent: Record<string, number>;
  recent_hour: number;
}

export interface SystemLogFilters {
  page?: number;
  per_page?: number;
  level?: string;
  source?: string;
  agent_name?: string;
  module?: string;
  context_id?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
}

class SystemLogsService {
  
  /**
   * Récupérer les logs système avec pagination et filtres
   */
  async getLogs(filters: SystemLogFilters = {}): Promise<SystemLogResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value));
      }
    });
    
    const url = `/api/system-logs/?${params.toString()}`;
    const response = await apiRequest(url);
    return response as SystemLogResponse;
  }

  /**
   * Obtenir les statistiques des logs système
   */
  async getStats(): Promise<SystemLogStats> {
    const response = await apiRequest('/api/system-logs/stats');
    return response as SystemLogStats;
  }

  /**
   * Récupérer les erreurs récentes
   */
  async getRecentErrors(limit: number = 50): Promise<SystemLog[]> {
    const response = await apiRequest(`/api/system-logs/errors?limit=${limit}`);
    return response as SystemLog[];
  }

  /**
   * Récupérer les logs d'un agent spécifique
   */
  async getAgentLogs(agentName: string, limit: number = 100, level?: string): Promise<SystemLog[]> {
    let url = `/api/system-logs/agents/${encodeURIComponent(agentName)}?limit=${limit}`;
    if (level) {
      url += `&level=${level}`;
    }
    
    const response = await apiRequest(url);
    return response as SystemLog[];
  }

  /**
   * Obtenir les niveaux de logs disponibles
   */
  async getAvailableLevels(): Promise<string[]> {
    const response = await apiRequest('/api/system-logs/levels');
    return (response as {levels: string[]}).levels;
  }

  /**
   * Obtenir les sources disponibles
   */
  async getAvailableSources(): Promise<string[]> {
    const response = await apiRequest('/api/system-logs/sources');
    return (response as {sources: string[]}).sources;
  }

  /**
   * Obtenir les agents qui ont des logs
   */
  async getAvailableAgents(): Promise<string[]> {
    const response = await apiRequest('/api/system-logs/agents');
    return (response as {agents: string[]}).agents;
  }

  /**
   * Nettoyer les anciens logs
   */
  async cleanupOldLogs(daysToKeep: number = 30): Promise<{message: string, deleted_logs: number, days_kept: number}> {
    const response = await apiRequest(
      `/api/system-logs/cleanup?days_to_keep=${daysToKeep}`,
      {
        method: 'DELETE'
      }
    );
    return response as {message: string, deleted_logs: number, days_kept: number};
  }

  /**
   * Créer un nouveau log système (pour test)
   */
  async createLog(log: {
    level: string;
    source: string;
    message: string;
    agent_name?: string;
    module?: string;
    details?: Record<string, any>;
    context_id?: string;
  }): Promise<SystemLog> {
    const response = await apiRequest('/api/system-logs/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(log)
    });
    return response as SystemLog;
  }

  /**
   * Formater le timestamp pour l'affichage
   */
  formatTimestamp(timestamp: string): string {
    try {
      return new Date(timestamp).toLocaleString('fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return timestamp;
    }
  }

  /**
   * Obtenir la couleur selon le niveau de log
   */
  getLevelColor(level: string): string {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return 'text-red-600 bg-red-50';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50';
      case 'INFO':
        return 'text-blue-600 bg-blue-50';
      case 'DEBUG':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  }

  /**
   * Obtenir l'icône selon le niveau de log
   */
  getLevelIcon(level: string): string {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return '🔴';
      case 'WARNING':
        return '🟡';
      case 'INFO':
        return '🔵';
      case 'DEBUG':
        return '⚫';
      default:
        return '⚪';
    }
  }

  /**
   * Obtenir l'icône selon la source
   */
  getSourceIcon(source: string): string {
    switch (source.toLowerCase()) {
      case 'agent':
        return '🤖';
      case 'system':
        return '⚙️';
      case 'api':
        return '🔌';
      case 'webhook':
        return '🔗';
      case 'database':
        return '💾';
      default:
        return '📝';
    }
  }
}

// Instance unique du service
export const systemLogsService = new SystemLogsService();
export default systemLogsService;

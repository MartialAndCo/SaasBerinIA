/**
 * Service de gestion des logs des agents et du système - VERSION VRAIES DONNÉES
 *
 * Ce service récupère les logs du système via l'API RÉELLE et les formate pour l'affichage
 * dans l'interface d'administration. AUCUNE donnée fictive.
 */

import { apiRequest } from "../api-interceptor"

// Types
export interface LogEntry {
  id: string | number
  timestamp: string
  level: "info" | "success" | "warning" | "error"
  source: "agent" | "system" | "cron" | "api"
  agent_id?: number
  agent_name?: string
  module?: string
  action?: string
  status?: string
  message: string
  details?: any
}

export interface LogStats {
  system: {
    total: number
    errors: number
    warnings: number
    recent_hour: number
  }
  agents: {
    total: number
    errors: number
    warnings: number
    recent_hour: number
  }
  totals: {
    all_logs: number
    all_errors: number
    all_warnings: number
    recent_hour: number
  }
}

/**
 * Service de gestion des logs des agents et du système - VRAIES DONNÉES UNIQUEMENT
 */
class RealLogsService {
  /**
   * Récupère tous les logs (système + agents) depuis l'API réelle
   */
  async getAllLogs(limit: number = 100, level?: string, source?: string): Promise<{ data: LogEntry[], status: number }> {
    try {
      let url = `/api/logs-extended/all?limit=${limit}`
      
      if (level && level !== "all") {
        url += `&level=${level}`
      }
      
      if (source && source !== "all") {
        url += `&source=${source}`
      }
      
      const logs = await apiRequest(url)
      
      // Formater les logs pour le frontend
      const formattedLogs = Array.isArray(logs) ? logs.map((log: any) => ({
        id: log.id,
        timestamp: log.timestamp,
        level: log.level,
        source: log.source,
        agent_id: log.agent_id,
        agent_name: log.agent_name,
        module: log.module,
        action: log.action,
        status: log.status,
        message: log.message,
        details: log.details
      })) : []

      return {
        data: formattedLogs,
        status: 200
      }
    } catch (error) {
      console.error("Error fetching all logs:", error)
      
      // Retourner un tableau vide en cas d'erreur, pas de données fictives
      return {
        data: [],
        status: 500
      }
    }
  }

  /**
   * Récupère les logs système depuis l'API réelle
   */
  async getSystemLogs(limit: number = 50, level?: string): Promise<{ data: LogEntry[], status: number }> {
    try {
      let url = `/api/logs-extended/system?limit=${limit}`
      
      if (level && level !== "all") {
        url += `&level=${level}`
      }
      
      const logs = await apiRequest(url)
      
      // Formater les logs pour le frontend
      const formattedLogs = Array.isArray(logs) ? logs.map((log: any) => ({
        id: log.id,
        timestamp: log.timestamp,
        level: log.level,
        source: "system" as const,
        module: log.module,
        message: log.message,
        details: log.details
      })) : []

      return {
        data: formattedLogs,
        status: 200
      }
    } catch (error) {
      console.error("Error fetching system logs:", error)
      
      return {
        data: [],
        status: 500
      }
    }
  }

  /**
   * Récupère les logs d'agents depuis l'API réelle
   */
  async getAgentLogs(limit: number = 50, agentId?: number, status?: string): Promise<{ data: LogEntry[], status: number }> {
    try {
      let url = `/api/logs-extended/agents?limit=${limit}`
      
      if (agentId) {
        url += `&agent_id=${agentId}`
      }
      
      if (status && status !== "all") {
        url += `&status=${status}`
      }
      
      const logs = await apiRequest(url)
      
      // Formater les logs pour le frontend
      const formattedLogs = Array.isArray(logs) ? logs.map((log: any) => ({
        id: log.id,
        timestamp: log.timestamp,
        level: log.level,
        source: "agent" as const,
        agent_id: log.agent_id,
        agent_name: log.agent_name,
        action: log.action,
        status: log.status,
        message: log.message,
        details: log.details
      })) : []

      return {
        data: formattedLogs,
        status: 200
      }
    } catch (error) {
      console.error("Error fetching agent logs:", error)
      
      return {
        data: [],
        status: 500
      }
    }
  }

  /**
   * Récupère uniquement les logs d'erreur depuis l'API réelle
   */
  async getErrorLogs(limit: number = 50): Promise<{ data: LogEntry[], status: number }> {
    try {
      const logs = await apiRequest(`/api/logs-extended/errors?limit=${limit}`)
      
      // Formater les logs pour le frontend
      const formattedLogs = Array.isArray(logs) ? logs.map((log: any) => ({
        id: log.id,
        timestamp: log.timestamp,
        level: "error" as const,
        source: log.source,
        agent_id: log.agent_id,
        agent_name: log.agent_name,
        module: log.module,
        action: log.action,
        message: log.message,
        details: log.details
      })) : []

      return {
        data: formattedLogs,
        status: 200
      }
    } catch (error) {
      console.error("Error fetching error logs:", error)
      
      return {
        data: [],
        status: 500
      }
    }
  }

  /**
   * Récupère les logs pour un agent spécifique
   */
  async getLogsForAgent(agentId: number, limit: number = 50): Promise<{ data: LogEntry[], status: number }> {
    return this.getAgentLogs(limit, agentId)
  }

  /**
   * Récupère les statistiques des logs depuis l'API réelle
   */
  async getLogsStats(): Promise<{ data: LogStats, status: number }> {
    try {
      const stats = await apiRequest('/api/logs-extended/stats')
      
      return {
        data: stats,
        status: 200
      }
    } catch (error) {
      console.error("Error fetching logs stats:", error)
      
      // Retourner des stats vides en cas d'erreur, pas de données fictives
      return {
        data: {
          system: { total: 0, errors: 0, warnings: 0, recent_hour: 0 },
          agents: { total: 0, errors: 0, warnings: 0, recent_hour: 0 },
          totals: { all_logs: 0, all_errors: 0, all_warnings: 0, recent_hour: 0 }
        },
        status: 500
      }
    }
  }

  /**
   * Convertit le niveau de log en texte explicite pour l'UI
   */
  getLevelText(level: string): string {
    switch (level) {
      case "info": return "INFO"
      case "success": return "SUCCÈS"
      case "warning": return "AVERTISSEMENT"
      case "error": return "ERREUR"
      default: return "INFO"
    }
  }

  /**
   * Convertit le type de source en texte explicite pour l'UI
   */
  getSourceText(source: string): string {
    switch (source) {
      case "agent": return "AGENT"
      case "system": return "SYSTÈME"
      case "cron": return "CRON"
      case "api": return "API"
      default: return "SYSTÈME"
    }
  }

  /**
   * Méthode pour rafraîchir/actualiser les logs
   */
  async refreshLogs(): Promise<boolean> {
    try {
      // Relancer une requête pour forcer le rafraîchissement
      await this.getAllLogs(1)
      return true
    } catch (error) {
      console.error("Error refreshing logs:", error)
      return false
    }
  }
}

export const realLogsService = new RealLogsService()

// Exporter aussi comme default pour compatibilité
export default realLogsService

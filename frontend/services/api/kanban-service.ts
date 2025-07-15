/**
 * Service de gestion du kanban CRM
 *
 * Service dédié au tableau kanban pour le suivi des leads.
 * Utilise uniquement des données réelles via l'API backend - ZÉRO mock.
 */

import { api, type ApiResponse } from "../api-interceptor"
import type { Lead } from "./leads-service"

// Types spécifiques au kanban
export interface LeadsByStatus {
  new: Lead[]
  qualification: Lead[]
  presentation: Lead[]
  negotiation: Lead[]
  evaluation: Lead[]
  won: Lead[]
  lost: Lead[]
}

export interface KanbanStats {
  total: number
  by_status: Record<string, number>
  by_campaign: Record<string, number>
}

export interface KanbanFilters {
  campagne_id?: number
  search?: string
}

export interface StatusUpdateData {
  status: "new" | "qualification" | "presentation" | "negotiation" | "evaluation" | "won" | "lost"
  notes?: string
}

/**
 * Service Kanban - 100% données réelles
 */
class KanbanService {
  /**
   * Récupère les leads groupés par statut pour le kanban
   */
  async getLeadsKanban(filters?: KanbanFilters): Promise<ApiResponse<LeadsByStatus>> {
    const params = new URLSearchParams()
    
    if (filters) {
      if (filters.campagne_id) {
        params.append("campagne_id", filters.campagne_id.toString())
      }
      if (filters.search) {
        params.append("search", filters.search)
      }
    }

    const queryString = params.toString()
    const endpoint = queryString ? `/api/leads/kanban?${queryString}` : "/api/leads/kanban"
    
    return api.get<LeadsByStatus>(endpoint)
  }

  /**
   * Met à jour le statut d'un lead (drag & drop)
   */
  async updateLeadStatus(leadId: number, statusData: StatusUpdateData): Promise<ApiResponse<Lead>> {
    return api.patch<Lead>(`/api/leads/${leadId}/status`, statusData)
  }

  /**
   * Récupère les statistiques pour le kanban
   */
  async getKanbanStats(filters?: KanbanFilters): Promise<ApiResponse<KanbanStats>> {
    const params = new URLSearchParams()
    
    if (filters?.campagne_id) {
      params.append("campagne_id", filters.campagne_id.toString())
    }

    const queryString = params.toString()
    const endpoint = queryString ? `/api/leads/stats?${queryString}` : "/api/leads/stats"
    
    return api.get<KanbanStats>(endpoint)
  }

  /**
   * Récupère les détails d'un lead spécifique
   */
  async getLeadDetails(leadId: number): Promise<ApiResponse<Lead>> {
    return api.get<Lead>(`/api/leads/${leadId}`)
  }

  /**
   * Met à jour un lead complet
   */
  async updateLead(leadId: number, leadData: Partial<Lead>): Promise<ApiResponse<Lead>> {
    return api.put<Lead>(`/api/leads/${leadId}`, leadData)
  }

  /**
   * Supprime un lead
   */
  async deleteLead(leadId: number): Promise<ApiResponse<void>> {
    return api.delete<void>(`/api/leads/${leadId}`)
  }

  /**
   * Récupère la liste des campagnes pour le filtre
   */
  async getCampaigns(): Promise<ApiResponse<Array<{ id: number; nom: string }>>> {
    return api.get<Array<{ id: number; nom: string }>>("/api/campaigns")
  }
}

// Configuration des statuts pour le kanban
export const KANBAN_STATUSES = [
  {
    key: "new" as const,
    label: "Nouveau",
    color: "bg-gray-100 text-gray-800",
    borderColor: "border-gray-300"
  },
  {
    key: "qualification" as const,
    label: "Qualification", 
    color: "bg-blue-100 text-blue-800",
    borderColor: "border-blue-300"
  },
  {
    key: "presentation" as const,
    label: "Présentation",
    color: "bg-yellow-100 text-yellow-800", 
    borderColor: "border-yellow-300"
  },
  {
    key: "negotiation" as const,
    label: "Négociation",
    color: "bg-orange-100 text-orange-800",
    borderColor: "border-orange-300"
  },
  {
    key: "evaluation" as const,
    label: "Évaluation",
    color: "bg-purple-100 text-purple-800",
    borderColor: "border-purple-300"
  },
  {
    key: "won" as const,
    label: "Gagné",
    color: "bg-green-100 text-green-800",
    borderColor: "border-green-300"
  },
  {
    key: "lost" as const,
    label: "Perdu",
    color: "bg-red-100 text-red-800",
    borderColor: "border-red-300"
  }
] as const

export type KanbanStatusKey = typeof KANBAN_STATUSES[number]['key']

export const kanbanService = new KanbanService()

/**
 * Service de gestion des leads
 *
 * Gère toutes les opérations liées aux leads générés par les campagnes.
 * Utilise uniquement des données réelles via l'API backend.
 */

import { api, type ApiResponse, type PaginatedResponse } from "../api-interceptor"

// Types
export interface Lead {
  id: number
  // Noms - Backend utilise first_name/last_name, frontend utilise nom
  nom?: string
  first_name?: string
  last_name?: string
  email: string
  // Téléphone - Backend utilise phone, frontend utilise telephone
  telephone?: string
  phone?: string
  // Entreprise - Backend utilise company, frontend utilise entreprise
  entreprise?: string
  company?: string
  status: string
  statut?: string
  date_creation: string
  created_at?: string
  campagne_id: number
  // Champs supplémentaires
  notes?: string
  position?: string
  linkedin_url?: string
  website?: string
  industry?: string
  niche_id?: number
  source?: string
  score?: number
  score_details?: any
  validation_status?: string
  last_contact?: string
  updated_at?: string
  // Champs d'analyse visuelle
  visual_score?: number
  visual_analysis_data?: any
  has_popup?: boolean
  popup_removed?: boolean
  screenshot_path?: string
  enhanced_screenshot_path?: string
  visual_analysis_date?: string
  site_type?: string
  visual_quality?: number
  website_maturity?: string
  design_strengths?: string[]
  design_weaknesses?: string[]
}

export interface LeadCreate {
  nom: string
  email: string
  telephone?: string
  entreprise?: string
  statut?: string
  campagne_id?: number
}

export interface LeadUpdate {
  nom?: string
  email?: string
  telephone?: string
  entreprise?: string
  statut?: string
  campagne_id?: number
}

export interface LeadStatusUpdateRequest {
  status: "new" | "qualification" | "presentation" | "negotiation" | "evaluation" | "won" | "lost"
  notes?: string
}

export interface LeadFilters {
  status?: string
  campagne_id?: number
  search?: string
  page?: number
  limit?: number
}

/**
 * Service de gestion des leads - 100% API réelle
 */
class LeadsService {
  /**
   * Récupère la liste des leads avec pagination
   */
  async getLeads(page = 1, limit = 10, filters?: LeadFilters): Promise<ApiResponse<PaginatedResponse<Lead>>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    })

    // Ajouter les filtres aux paramètres de requête
    if (filters) {
      if (filters.status && filters.status !== "all") {
        params.append("status", filters.status)
      }
      if (filters.campagne_id) {
        params.append("campagne_id", filters.campagne_id.toString())
      }
      if (filters.search) {
        params.append("search", filters.search)
      }
    }

    return api.get<PaginatedResponse<Lead>>(`/api/leads?${params.toString()}`)
  }

  /**
   * Récupère les détails d'un lead spécifique
   */
  async getLead(id: number): Promise<ApiResponse<Lead>> {
    return api.get<Lead>(`/api/leads/${id}`)
  }

  /**
   * Crée un nouveau lead
   */
  async createLead(leadData: LeadCreate): Promise<ApiResponse<Lead>> {
    return api.post<Lead>("/api/leads", leadData)
  }

  /**
   * Met à jour un lead existant
   */
  async updateLead(id: number, leadData: LeadUpdate): Promise<ApiResponse<Lead>> {
    return api.put<Lead>(`/api/leads/${id}`, leadData)
  }

  /**
   * Met à jour le statut d'un lead
   */
  async updateLeadStatus(id: number, statusData: LeadStatusUpdateRequest): Promise<ApiResponse<Lead>> {
    return api.patch<Lead>(`/api/leads/${id}/status`, statusData)
  }

  /**
   * Supprime un lead
   */
  async deleteLead(id: number): Promise<ApiResponse<void>> {
    return api.delete<void>(`/api/leads/${id}`)
  }

  /**
   * Exporte les leads au format CSV
   */
  async exportLeads(filters?: LeadFilters): Promise<ApiResponse<Blob>> {
    const params = new URLSearchParams()
    
    if (filters) {
      if (filters.status && filters.status !== "all") {
        params.append("status", filters.status)
      }
      if (filters.campagne_id) {
        params.append("campagne_id", filters.campagne_id.toString())
      }
      if (filters.search) {
        params.append("search", filters.search)
      }
    }

    // Appel API réel pour l'export
    const response = await fetch(`/api/leads/export?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`)
    }

    const blob = await response.blob()
    return {
      data: blob,
      status: response.status,
    }
  }

  /**
   * Récupère les statistiques des leads
   */
  async getLeadStats(filters?: LeadFilters): Promise<ApiResponse<{
    total: number
    by_status: Record<string, number>
    by_campaign: Record<string, number>
  }>> {
    const params = new URLSearchParams()
    
    if (filters) {
      if (filters.campagne_id) {
        params.append("campagne_id", filters.campagne_id.toString())
      }
    }

    return api.get<{
      total: number
      by_status: Record<string, number>
      by_campaign: Record<string, number>
    }>(`/api/leads/stats?${params.toString()}`)
  }
}

export const leadsService = new LeadsService()

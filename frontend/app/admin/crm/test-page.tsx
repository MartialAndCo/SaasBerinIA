'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { toast } from 'sonner'

// Version simplifiée pour test SANS authentification
export default function TestKanbanPage() {
  const [leadsData, setLeadsData] = useState<any>({
    new: [],
    qualification: [],
    presentation: [],
    negotiation: [],
    evaluation: [],
    won: [],
    lost: []
  })
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState<any>({})

  // Debug pour tracer les re-renders
  console.log('🔄 TestKanban render', { filters, loading })

  // Stabiliser l'objet filters avec useMemo
  const stableFilters = useMemo(() => {
    console.log('📋 Filters changed:', filters)
    return filters
  }, [JSON.stringify(filters)])

  // Stabiliser la fonction de chargement
  const loadKanbanData = useCallback(async () => {
    console.log('🔍 Loading kanban data with filters:', stableFilters)
    try {
      setLoading(true)
      
      // Appel direct à l'API SANS authentification
      const response = await fetch('/api/leads/kanban')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      setLeadsData(data)
      console.log('✅ Data loaded successfully:', data)
    } catch (error) {
      console.error('❌ Erreur lors du chargement des leads:', error)
      toast.error('Erreur lors du chargement des leads')
    } finally {
      setLoading(false)
    }
  }, [stableFilters])

  // Charger les données initiales
  useEffect(() => {
    console.log('🚀 useEffect triggered - loading data')
    loadKanbanData()
  }, [loadKanbanData])

  const handleFiltersChange = useCallback((newFilters: any) => {
    console.log('🔄 Filters changing to:', newFilters)
    setFilters(newFilters)
  }, [])

  const getTotalLeads = () => {
    return Object.values(leadsData).reduce((total: number, leads: any) => total + leads.length, 0)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="ml-4">Chargement test...</p>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Test Kanban - Sans Auth</h1>
      
      {/* Filtres simplifiés */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h3 className="text-lg font-semibold mb-4">Filtres Test</h3>
        <input
          type="text"
          placeholder="Rechercher..."
          onChange={(e) => {
            console.log('🔍 Search input changed:', e.target.value)
            setTimeout(() => {
              handleFiltersChange({ search: e.target.value })
            }, 300)
          }}
          className="w-full p-2 border rounded"
        />
      </div>

      {/* Statistiques */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h3 className="text-lg font-semibold">
          Total des leads: {getTotalLeads()}
        </h3>
        <div className="grid grid-cols-7 gap-2 mt-2">
          {Object.entries(leadsData).map(([status, leads]: [string, any]) => (
            <div key={status} className="text-center">
              <div className="text-sm font-medium">{status}</div>
              <div className="text-lg">{leads.length}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Colonnes simplifiées */}
      <div className="grid grid-cols-7 gap-4">
        {Object.entries(leadsData).map(([status, leads]: [string, any]) => (
          <div key={status} className="bg-gray-50 rounded-lg p-4 min-h-48">
            <h4 className="font-semibold mb-2 capitalize">{status}</h4>
            <div className="space-y-2">
              {leads.map((lead: any) => (
                <div key={lead.id} className="bg-white p-2 rounded shadow text-sm">
                  <div className="font-medium">
                    {lead.nom || `${lead.first_name || ''} ${lead.last_name || ''}`.trim() || 'Sans nom'}
                  </div>
                  <div className="text-gray-600">{lead.email}</div>
                  <div className="text-gray-500">{lead.entreprise || lead.company}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Debug info */}
      <div className="mt-6 p-4 bg-gray-100 rounded">
        <h4 className="font-bold">Debug Info:</h4>
        <p>Filters: {JSON.stringify(stableFilters)}</p>
        <p>Loading: {loading.toString()}</p>
        <p>Render count: Voir console</p>
      </div>
    </div>
  )
}

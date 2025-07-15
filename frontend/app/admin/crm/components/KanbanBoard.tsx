'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { SortableContext, arrayMove } from '@dnd-kit/sortable'
import { createPortal } from 'react-dom'

import { kanbanService, KANBAN_STATUSES, type LeadsByStatus, type KanbanFilters } from '@/services/api/kanban-service'
import type { Lead } from '@/services/api/leads-service'
import KanbanColumn from './KanbanColumn'
import KanbanFiltersComponent from './KanbanFilters' 
import LeadCard from './LeadCard'
import { toast } from 'sonner'

export default function KanbanBoard() {
  const [leadsData, setLeadsData] = useState<LeadsByStatus>({
    new: [],
    qualification: [],
    presentation: [],
    negotiation: [],
    evaluation: [],
    won: [],
    lost: []
  })
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState<KanbanFilters>({})
  const [activeId, setActiveId] = useState<string | null>(null)
  const [activeLead, setActiveLead] = useState<Lead | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  )

  // Debug pour tracer les re-renders
  console.log('🔄 KanbanBoard render', { filters, loading })

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
      const response = await kanbanService.getLeadsKanban(stableFilters)
      // Corriger la structure de réponse - l'API retourne directement les données
      setLeadsData(response.data || response)
      console.log('✅ Data loaded successfully')
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

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    setActiveId(active.id as string)
    
    // Trouver le lead actif
    const leadId = parseInt(active.id as string)
    const allLeads = Object.values(leadsData).flat()
    const lead = allLeads.find(l => l.id === leadId)
    setActiveLead(lead || null)
  }

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event
    if (!over) return

    const activeId = active.id as string
    const overId = over.id as string

    // Si on survole une colonne
    if (overId.startsWith('column-')) {
      const newStatus = overId.replace('column-', '')
      const leadId = parseInt(activeId)
      
          // Mettre à jour l'état local temporairement
          setLeadsData(prev => {
            const newData = { ...prev }
            const allLeads = Object.values(newData).flat()
            const lead = allLeads.find(l => l.id === leadId)
            
            if (lead && lead.status !== newStatus) {
              // Retirer le lead de sa colonne actuelle
              Object.keys(newData).forEach(status => {
                newData[status as keyof LeadsByStatus] = newData[status as keyof LeadsByStatus].filter(l => l.id !== leadId)
              })
              
              // Ajouter le lead à la nouvelle colonne
              if (newStatus in newData) {
                lead.status = newStatus
                newData[newStatus as keyof LeadsByStatus].push(lead)
              }
            }
            
            return newData
          })
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    setActiveId(null)
    setActiveLead(null)

    if (!over) {
      // Recharger les données si le drop échoue
      await loadKanbanData()
      return
    }

    const activeId = active.id as string
    const overId = over.id as string

    // Si on drop sur une colonne
    if (overId.startsWith('column-')) {
      const newStatus = overId.replace('column-', '') as keyof LeadsByStatus
      const leadId = parseInt(activeId)
      
      try {
        // Mettre à jour via l'API
        await kanbanService.updateLeadStatus(leadId, { 
          status: newStatus as any,
          notes: `Statut changé vers ${KANBAN_STATUSES.find(s => s.key === newStatus)?.label || newStatus}`
        })
        
        toast.success(`Lead déplacé vers ${KANBAN_STATUSES.find(s => s.key === newStatus)?.label || newStatus}`)
        
        // Recharger les données pour s'assurer de la cohérence
        await loadKanbanData()
      } catch (error) {
        console.error('Erreur lors de la mise à jour du statut:', error)
        toast.error('Erreur lors de la mise à jour du statut')
        
        // Recharger les données en cas d'erreur
        await loadKanbanData()
      }
    }
  }

  const handleFiltersChange = useCallback((newFilters: KanbanFilters) => {
    setFilters(newFilters)
  }, [])

  const getTotalLeads = () => {
    return Object.values(leadsData).reduce((total, leads) => total + leads.length, 0)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Filtres */}
      <KanbanFiltersComponent filters={filters} onFiltersChange={handleFiltersChange} />
      
      {/* Statistiques */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Total des leads: {getTotalLeads()}
          </h3>
          <div className="flex space-x-4 text-sm text-gray-600">
            {KANBAN_STATUSES.map(status => (
              <span key={status.key} className={`px-2 py-1 rounded-full ${status.color}`}>
                {status.label}: {leadsData[status.key]?.length || 0}
              </span>
            ))}
          </div>
        </div>
      </div>

        {/* Tableau Kanban - Version moderne avec scroll horizontal */}
        <DndContext
          sensors={sensors}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <div className="relative">
            <div className="flex gap-6 overflow-x-auto pb-4 min-h-[80vh]" style={{ scrollbarWidth: 'thin' }}>
              {KANBAN_STATUSES.map(status => (
                <KanbanColumn
                  key={status.key}
                  status={status}
                  leads={leadsData[status.key] || []}
                  onRefresh={loadKanbanData}
                />
              ))}
            </div>
          </div>

        {/* Overlay pour le drag */}
        {createPortal(
          <DragOverlay>
            {activeId && activeLead ? (
              <LeadCard 
                lead={activeLead} 
                isDragging={true}
                onEdit={() => {}}
                onDelete={() => {}} 
              />
            ) : null}
          </DragOverlay>,
          document.body
        )}
      </DndContext>
    </div>
  )
}

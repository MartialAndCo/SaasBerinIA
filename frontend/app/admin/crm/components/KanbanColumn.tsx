'use client'

import React from 'react'
import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { KANBAN_STATUSES, type KanbanStatusKey } from '@/services/api/kanban-service'
import type { Lead } from '@/services/api/leads-service'
import LeadCard from './LeadCard'

interface KanbanColumnProps {
  status: typeof KANBAN_STATUSES[number]
  leads: Lead[]
  onRefresh: () => void
}

export default function KanbanColumn({ status, leads, onRefresh }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: `column-${status.key}`,
  })

  const handleEdit = (lead: Lead) => {
    // TODO: Ouvrir modal d'édition
    console.log('Edit lead:', lead)
  }

  const handleDelete = async (lead: Lead) => {
    // TODO: Confirmer et supprimer le lead
    console.log('Delete lead:', lead)
    onRefresh()
  }

  return (
    <div
      ref={setNodeRef}
      className={`bg-white rounded-lg shadow-sm border border-gray-200 min-h-[600px] transition-colors ${
        isOver ? 'border-blue-400 bg-blue-50' : ''
      }`}
      style={{ width: '380px', minWidth: '380px', flexShrink: 0 }}
    >
      {/* Bordure colorée en haut */}
      <div className={`h-1 rounded-t-lg ${status.borderColor.replace('border-', 'bg-')}`}></div>
      
      {/* En-tête de colonne */}
      <div className="p-4 pb-3 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 text-base">{status.label}</h3>
          <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-xs font-medium">
            {leads.length}
          </span>
        </div>
        {/* Indicateur de valeur total si nécessaire */}
        <div className="text-xs text-gray-500 mt-1">
          {leads.length} lead{leads.length > 1 ? 's' : ''}
        </div>
      </div>

      {/* Liste des leads */}
      <div className="p-4 pt-3">
        <SortableContext items={leads.map(lead => lead.id.toString())} strategy={verticalListSortingStrategy}>
          <div className="space-y-3">
            {leads.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
                  <svg className="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-gray-500">Aucun lead</p>
                <p className="text-xs text-gray-400 mt-1">Glissez un lead ici</p>
              </div>
            ) : (
              leads.map(lead => (
                <LeadCard
                  key={lead.id}
                  lead={lead}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              ))
            )}
          </div>
        </SortableContext>
      </div>

      {/* Zone de drop visuelle */}
      {isOver && (
        <div className="mt-4 p-4 border-2 border-dashed border-blue-400 rounded-lg bg-blue-50">
          <p className="text-center text-blue-600 font-medium">
            Relâchez pour déplacer le lead vers {status.label}
          </p>
        </div>
      )}
    </div>
  )
}

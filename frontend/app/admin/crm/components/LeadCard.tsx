'use client'

import React from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Mail, Phone, Building, Calendar, Eye, Edit, Trash2 } from 'lucide-react'
import type { Lead } from '@/services/api/leads-service'

interface LeadCardProps {
  lead: Lead
  isDragging?: boolean
  onEdit: (lead: Lead) => void
  onDelete: (lead: Lead) => void
}

export default function LeadCard({ lead, isDragging = false, onEdit, onDelete }: LeadCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: isDnd,
  } = useSortable({
    id: lead.id.toString(),
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  const getScoreBadge = (score?: number) => {
    if (!score) return null
    
    const getScoreColor = (score: number) => {
      if (score >= 80) return 'bg-green-100 text-green-800'
      if (score >= 60) return 'bg-yellow-100 text-yellow-800'
      if (score >= 40) return 'bg-orange-100 text-orange-800'
      return 'bg-red-100 text-red-800'
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(score)}`}>
        Score: {score}
      </span>
    )
  }

  const getInitials = () => {
    const name = lead.nom || `${lead.first_name || ''} ${lead.last_name || ''}`.trim() || 'Sans nom'
    return name.split(' ').map(word => word.charAt(0)).join('').substring(0, 2).toUpperCase()
  }

  const getAvatarColor = () => {
    const colors = [
      'bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-pink-500', 
      'bg-indigo-500', 'bg-red-500', 'bg-yellow-500', 'bg-teal-500'
    ]
    return colors[lead.id % colors.length]
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-all duration-200 cursor-grab ${
        isDnd || isDragging ? 'opacity-50 rotate-2 scale-105 shadow-lg' : ''
      }`}
    >
      {/* En-tête avec avatar et actions */}
      <div className="flex items-start space-x-3 mb-3">
        {/* Avatar avec initiales */}
        <div className={`w-10 h-10 rounded-full ${getAvatarColor()} flex items-center justify-center flex-shrink-0`}>
          <span className="text-white text-sm font-medium">{getInitials()}</span>
        </div>
        
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-gray-900 leading-tight">
            {lead.nom || `${lead.first_name || ''} ${lead.last_name || ''}`.trim() || 'Sans nom'}
          </h4>
          <div className="flex items-center space-x-2 mt-1">
            {getScoreBadge(lead.visual_score)}
          </div>
        </div>
        
        <div className="flex flex-col space-y-1">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onEdit(lead)
            }}
            className="p-1.5 hover:bg-gray-100 rounded text-gray-400 hover:text-blue-600 transition-colors"
            title="Éditer"
          >
            <Edit size={14} />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(lead)
            }}
            className="p-1.5 hover:bg-gray-100 rounded text-gray-400 hover:text-red-600 transition-colors"
            title="Supprimer"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Informations de contact */}
      <div className="space-y-2 text-xs text-gray-600">
        {lead.email && (
          <div className="flex items-center space-x-2">
            <Mail size={12} className="text-gray-400" />
            <span className="truncate">{lead.email}</span>
          </div>
        )}
        
        {(lead.telephone || lead.phone) && (
          <div className="flex items-center space-x-2">
            <Phone size={12} className="text-gray-400" />
            <span>{lead.telephone || lead.phone}</span>
          </div>
        )}
        
        {(lead.entreprise || lead.company) && (
          <div className="flex items-center space-x-2">
            <Building size={12} className="text-gray-400" />
            <span className="truncate">{lead.entreprise || lead.company}</span>
          </div>
        )}
        
        {lead.date_creation && (
          <div className="flex items-center space-x-2">
            <Calendar size={12} className="text-gray-400" />
            <span>{formatDate(lead.date_creation)}</span>
          </div>
        )}
      </div>

      {/* Informations d'analyse visuelle */}
      {lead.website_maturity && (
        <div className="mt-3 pt-2 border-t border-gray-100">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">Maturité site:</span>
            <span className={`px-2 py-1 rounded-full font-medium ${
              lead.website_maturity === 'high' ? 'bg-green-100 text-green-800' :
              lead.website_maturity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {lead.website_maturity === 'high' ? 'Élevée' :
               lead.website_maturity === 'medium' ? 'Moyenne' : 'Faible'}
            </span>
          </div>
        </div>
      )}

      {/* Campagne */}
      {lead.campagne_id && (
        <div className="mt-2 text-xs text-gray-500">
          Campagne #{lead.campagne_id}
        </div>
      )}

      {/* Notes courtes */}
      {lead.notes && (
        <div className="mt-2 text-xs text-gray-600 bg-gray-50 rounded p-2">
          <p className="line-clamp-2">{lead.notes}</p>
        </div>
      )}
    </div>
  )
}

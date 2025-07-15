'use client'

import React, { useState, useEffect } from 'react'
import { Search, Filter, X } from 'lucide-react'
import { type KanbanFilters } from '@/services/api/kanban-service'

interface KanbanFiltersProps {
  filters: KanbanFilters
  onFiltersChange: (filters: KanbanFilters) => void
}

export default function KanbanFilters({ filters, onFiltersChange }: KanbanFiltersProps) {
  const [searchValue, setSearchValue] = useState(filters.search || '')
  const [selectedCampaign, setSelectedCampaign] = useState(filters.campagne_id?.toString() || '')
  const [showFilters, setShowFilters] = useState(false)

  // Debug pour tracer les re-renders
  console.log('🔍 KanbanFilters render', { searchValue, selectedCampaign })

  // Débounce pour la recherche - SANS onFiltersChange en dépendance
  useEffect(() => {
    console.log('⏰ Filter useEffect triggered', { searchValue, selectedCampaign })
    const timeout = setTimeout(() => {
      const newFilters = {
        campagne_id: selectedCampaign ? parseInt(selectedCampaign) : undefined,
        search: searchValue || undefined
      }
      console.log('📤 Calling onFiltersChange with:', newFilters)
      onFiltersChange(newFilters)
    }, 300)

    return () => clearTimeout(timeout)
  }, [searchValue, selectedCampaign]) // Retirer onFiltersChange des dépendances

  const handleCampaignChange = (campaignId: string) => {
    setSelectedCampaign(campaignId)
    // Le useEffect se chargera de mettre à jour les filtres
  }

  const clearFilters = () => {
    setSearchValue('')
    setSelectedCampaign('')
    onFiltersChange({})
  }

  const hasActiveFilters = filters.search || filters.campagne_id

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Filtres</h3>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center space-x-2 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
        >
          <Filter size={16} />
          <span>{showFilters ? 'Masquer' : 'Afficher'} les filtres</span>
        </button>
      </div>

      <div className="space-y-4">
        {/* Barre de recherche */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Rechercher par nom, email, entreprise..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {searchValue && (
            <button
              onClick={() => setSearchValue('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Filtres détaillés */}
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
            {/* Filtre par campagne */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Campagne
              </label>
              <select
                value={selectedCampaign}
                onChange={(e) => handleCampaignChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Toutes les campagnes</option>
                <option value="1">Campagne Immobilier</option>
                <option value="2">Campagne E-commerce</option>
                <option value="3">Campagne Services</option>
                <option value="4">Campagne Santé</option>
                <option value="5">Campagne Vétérinaire</option>
              </select>
            </div>

            {/* Filtre par source */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Source
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled
              >
                <option value="">Toutes les sources</option>
                <option value="scraping">Scraping</option>
                <option value="import">Import</option>
                <option value="manual">Manuel</option>
              </select>
            </div>

            {/* Filtre par score */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Score minimum
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled
              >
                <option value="">Tous les scores</option>
                <option value="80">80+ (Excellent)</option>
                <option value="60">60+ (Bon)</option>
                <option value="40">40+ (Moyen)</option>
                <option value="20">20+ (Faible)</option>
              </select>
            </div>
          </div>
        )}

        {/* Actions */}
        {hasActiveFilters && (
          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <span className="text-sm text-gray-600">
              {filters.search && `Recherche: "${filters.search}"`}
              {filters.search && filters.campagne_id && ' • '}
              {filters.campagne_id && `Campagne #${filters.campagne_id}`}
            </span>
            <button
              onClick={clearFilters}
              className="flex items-center space-x-1 text-sm text-red-600 hover:text-red-800"
            >
              <X size={14} />
              <span>Effacer les filtres</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

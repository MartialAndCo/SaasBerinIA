import { Metadata } from 'next'
import KanbanBoard from './components/KanbanBoard'

export const metadata: Metadata = {
  title: 'CRM - Suivi des Leads | BerinIA',
  description: 'Tableau kanban pour le suivi et la gestion des leads par statut',
}

export default function CRMPage() {
  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">CRM - Suivi des Leads</h1>
        <p className="text-gray-600 mt-2">
          Gérez vos leads par statut avec le tableau kanban
        </p>
      </div>
      
      <KanbanBoard />
    </div>
  )
}

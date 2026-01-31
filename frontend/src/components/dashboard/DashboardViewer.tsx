import { useState } from 'react'
import { Link } from 'react-router-dom'
import FilterBar from './FilterBar'
import CardContainer from './CardContainer'

interface Dashboard {
  dashboard_id: string
  name: string
  layout: {
    cards?: Array<{ cardId: string; x: number; y: number; w: number; h: number }>
  }
  filters: Array<{ name: string; type: string; column: string }>
  permission?: string
}

interface DashboardViewerProps {
  dashboard: Dashboard
  showEditLink?: boolean
}

export default function DashboardViewer({ dashboard, showEditLink = false }: DashboardViewerProps) {
  const [filters, setFilters] = useState<Record<string, any>>({})
  const cards = dashboard.layout?.cards || []

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-2xl font-bold">{dashboard.name}</h2>
        {showEditLink && (dashboard.permission === 'owner' || dashboard.permission === 'editor') && (
          <Link
            to={`/dashboards/${dashboard.dashboard_id}/edit`}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
          >
            編集
          </Link>
        )}
      </div>
      <FilterBar
        filters={dashboard.filters}
        values={filters}
        onChange={setFilters}
      />
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => (
          <CardContainer
            key={card.cardId}
            cardId={card.cardId}
            filters={filters}
          />
        ))}
        {cards.length === 0 && (
          <div className="col-span-full text-center text-gray-500 py-12">
            カードがありません
          </div>
        )}
      </div>
    </div>
  )
}

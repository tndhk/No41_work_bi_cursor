import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import FilterBar from '../components/dashboard/FilterBar'
import CardContainer from '../components/dashboard/CardContainer'

interface Dashboard {
  dashboard_id: string
  name: string
  layout: {
    cards?: Array<{ cardId: string; x: number; y: number; w: number; h: number }>
  }
  filters: Array<{ name: string; type: string; column: string }>
}

export default function DashboardViewPage() {
  const { dashboardId } = useParams<{ dashboardId: string }>()
  const [filters, setFilters] = useState<Record<string, any>>({})

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard', dashboardId],
    queryFn: async () => {
      const response = await api.get(`dashboards/${dashboardId}`).json<{ data: Dashboard }>()
      return response.data
    },
    enabled: !!dashboardId,
  })

  if (isLoading) {
    return <div className="p-6">読み込み中...</div>
  }

  if (!dashboard) {
    return <div className="p-6 text-red-600">ダッシュボードが見つかりません</div>
  }

  const cards = dashboard.layout?.cards || []

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">{dashboard.name}</h2>
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

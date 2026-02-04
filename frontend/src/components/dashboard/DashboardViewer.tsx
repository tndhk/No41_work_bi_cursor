import { useState } from 'react'
import { Link } from 'react-router-dom'
import FilterBar from './FilterBar'
import CardContainer from './CardContainer'
import ChatbotPanel from '../chatbot/ChatbotPanel'
import FilterViewManager from './FilterViewManager'
import DashboardShareDialog from './DashboardShareDialog'

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
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [isShareDialogOpen, setIsShareDialogOpen] = useState(false)
  const cards = dashboard.layout?.cards || []
  const canEdit = dashboard.permission === 'owner' || dashboard.permission === 'editor'
  const canShare = dashboard.permission === 'owner'

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-2xl font-bold">{dashboard.name}</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setIsChatOpen(!isChatOpen)}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm flex items-center gap-2"
            aria-label="チャットを開く"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <span>データを質問</span>
          </button>
          {canShare && (
            <button
              onClick={() => setIsShareDialogOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              共有
            </button>
          )}
          {showEditLink && canEdit && (
            <Link
              to={`/dashboards/${dashboard.dashboard_id}/edit`}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
            >
              編集
            </Link>
          )}
        </div>
      </div>
      <div className="space-y-4">
        <FilterBar
          filters={dashboard.filters}
          values={filters}
          onChange={setFilters}
        />
        <FilterViewManager
          dashboardId={dashboard.dashboard_id}
          currentFilters={filters}
          onApplyFilterView={setFilters}
          canEdit={canEdit}
        />
      </div>
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
      
      <ChatbotPanel
        dashboardId={dashboard.dashboard_id}
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
      
      <DashboardShareDialog
        dashboardId={dashboard.dashboard_id}
        isOpen={isShareDialogOpen}
        onClose={() => setIsShareDialogOpen(false)}
      />
    </div>
  )
}

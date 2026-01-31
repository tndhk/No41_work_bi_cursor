import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import DashboardEditor from '../components/dashboard/DashboardEditor'
import type { DashboardCard } from '../components/dashboard/layout'

interface Dashboard {
  dashboard_id: string
  name: string
  layout: {
    cards?: Array<{ cardId: string; x: number; y: number; w: number; h: number }>
  }
  filters: Array<{ name: string; type: string; column: string }>
  permission?: string
}

type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

export default function DashboardEditPage() {
  const { dashboardId } = useParams<{ dashboardId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard', dashboardId],
    queryFn: async () => {
      const response = await api.get(`dashboards/${dashboardId}`).json<{ data: Dashboard; permission?: string }>()
      return {
        ...response.data,
        permission: response.permission,
      }
    },
    enabled: !!dashboardId,
  })

  const updateMutation = useMutation({
    mutationFn: async (layout: { cards: DashboardCard[] }) => {
      return api.put(`dashboards/${dashboardId}`, {
        json: { layout },
      }).json<{ data: Dashboard }>()
    },
    onMutate: () => {
      setSaveStatus('saving')
    },
    onSuccess: () => {
      setSaveStatus('saved')
      queryClient.invalidateQueries({ queryKey: ['dashboard', dashboardId] })
      setTimeout(() => setSaveStatus('idle'), 2000)
    },
    onError: () => {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3000)
    },
  })

  const handleLayoutCommit = (cards: DashboardCard[]) => {
    updateMutation.mutate({ cards })
  }

  if (isLoading) {
    return <div className="p-6">読み込み中...</div>
  }

  if (!dashboard) {
    return <div className="p-6 text-red-600">ダッシュボードが見つかりません</div>
  }

  // 権限チェック
  if (dashboard.permission !== 'owner' && dashboard.permission !== 'editor') {
    return (
      <div className="p-6 text-red-600">
        このダッシュボードを編集する権限がありません
      </div>
    )
  }

  const cards: DashboardCard[] = dashboard.layout?.cards || []

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-2xl font-bold">{dashboard.name} - 編集</h2>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-600">
            {saveStatus === 'saving' && '保存中...'}
            {saveStatus === 'saved' && '保存しました'}
            {saveStatus === 'error' && '保存に失敗しました'}
          </div>
          <button
            onClick={() => navigate(`/dashboards/${dashboardId}`)}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm"
          >
            閲覧に戻る
          </button>
        </div>
      </div>
      <DashboardEditor cards={cards} onLayoutCommit={handleLayoutCommit} />
    </div>
  )
}

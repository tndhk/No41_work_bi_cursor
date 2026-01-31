import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import DashboardViewer from '../components/dashboard/DashboardViewer'

interface Dashboard {
  dashboard_id: string
  name: string
  layout: {
    cards?: Array<{ cardId: string; x: number; y: number; w: number; h: number }>
  }
  filters: Array<{ name: string; type: string; column: string }>
  permission?: string
}

export default function DashboardViewPage() {
  const { dashboardId } = useParams<{ dashboardId: string }>()

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

  if (isLoading) {
    return <div className="p-6">読み込み中...</div>
  }

  if (!dashboard) {
    return <div className="p-6 text-red-600">ダッシュボードが見つかりません</div>
  }

  return <DashboardViewer dashboard={dashboard} showEditLink={true} />
}

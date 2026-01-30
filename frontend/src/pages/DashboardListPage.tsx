import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

interface Dashboard {
  dashboard_id: string
  name: string
  owner_id: string
  created_at: string
  updated_at: string
}

export default function DashboardListPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboards'],
    queryFn: async () => {
      const response = await api.get('dashboards').json<{ data: Dashboard[] }>()
      return response.data
    },
  })

  if (isLoading) {
    return <div className="p-6">読み込み中...</div>
  }

  if (error) {
    return <div className="p-6 text-red-600">エラーが発生しました</div>
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">ダッシュボード一覧</h2>
        <Link
          to="/dashboards/new"
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          新規作成
        </Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.map((dashboard) => (
          <Link
            key={dashboard.dashboard_id}
            to={`/dashboards/${dashboard.dashboard_id}`}
            className="block p-6 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
          >
            <h3 className="text-lg font-semibold mb-2">{dashboard.name}</h3>
            <p className="text-sm text-gray-500">
              更新日: {new Date(dashboard.updated_at).toLocaleDateString('ja-JP')}
            </p>
          </Link>
        ))}
        {data?.length === 0 && (
          <div className="col-span-full text-center text-gray-500 py-12">
            ダッシュボードがありません
          </div>
        )}
      </div>
    </div>
  )
}

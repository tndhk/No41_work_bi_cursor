import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { filterViewsApi, type FilterView, type FilterViewCreateRequest } from '../../lib/filterViews'

interface FilterViewManagerProps {
  dashboardId: string
  currentFilters: Record<string, any>
  onApplyFilterView: (filterState: Record<string, any>) => void
  canEdit?: boolean
}

export default function FilterViewManager({
  dashboardId,
  currentFilters,
  onApplyFilterView,
  canEdit = false,
}: FilterViewManagerProps) {
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [viewName, setViewName] = useState('')
  const [isShared, setIsShared] = useState(false)
  const [isDefault, setIsDefault] = useState(false)
  const queryClient = useQueryClient()

  const { data: filterViews = [], isLoading } = useQuery({
    queryKey: ['filter-views', dashboardId],
    queryFn: () => filterViewsApi.list(dashboardId),
  })

  const createMutation = useMutation({
    mutationFn: (data: FilterViewCreateRequest) => filterViewsApi.create(dashboardId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-views', dashboardId] })
      setShowSaveDialog(false)
      setViewName('')
      setIsShared(false)
      setIsDefault(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (filterViewId: string) => filterViewsApi.delete(dashboardId, filterViewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-views', dashboardId] })
    },
  })

  const handleSave = () => {
    if (!viewName.trim()) {
      alert('ビュー名を入力してください')
      return
    }
    createMutation.mutate({
      name: viewName,
      filter_state: currentFilters,
      is_shared: isShared,
      is_default: isDefault,
    })
  }

  const handleDelete = (filterViewId: string) => {
    if (confirm('このフィルタビューを削除しますか？')) {
      deleteMutation.mutate(filterViewId)
    }
  }

  const handleApply = (filterView: FilterView) => {
    onApplyFilterView(filterView.filter_state)
  }

  if (isLoading) {
    return <div className="text-sm text-gray-500">読み込み中...</div>
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-semibold text-gray-700">フィルタビュー</h3>
        {canEdit && (
          <button
            onClick={() => setShowSaveDialog(true)}
            className="px-3 py-1 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            保存
          </button>
        )}
      </div>

      {filterViews.length === 0 ? (
        <p className="text-sm text-gray-500">フィルタビューがありません</p>
      ) : (
        <div className="space-y-2">
          {filterViews.map((view) => (
            <div key={view.filter_view_id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
              <div className="flex items-center gap-2 flex-1">
                <button
                  onClick={() => handleApply(view)}
                  className="text-sm text-indigo-600 hover:text-indigo-700 flex-1 text-left"
                >
                  {view.name}
                </button>
                {view.is_default && (
                  <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">デフォルト</span>
                )}
                {view.is_shared && (
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">共有</span>
                )}
              </div>
              {canEdit && (
                <button
                  onClick={() => handleDelete(view.filter_view_id)}
                  className="text-sm text-red-600 hover:text-red-700 ml-2"
                >
                  削除
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {showSaveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">フィルタビューを保存</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ビュー名</label>
                <input
                  type="text"
                  value={viewName}
                  onChange={(e) => setViewName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="例: 2024年1月のデータ"
                />
              </div>
              {canEdit && (
                <>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is-shared"
                      checked={isShared}
                      onChange={(e) => setIsShared(e.target.checked)}
                      className="mr-2"
                    />
                    <label htmlFor="is-shared" className="text-sm text-gray-700">
                      共有する
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is-default"
                      checked={isDefault}
                      onChange={(e) => setIsDefault(e.target.checked)}
                      className="mr-2"
                    />
                    <label htmlFor="is-default" className="text-sm text-gray-700">
                      デフォルトビューにする
                    </label>
                  </div>
                </>
              )}
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowSaveDialog(false)
                  setViewName('')
                  setIsShared(false)
                  setIsDefault(false)
                }}
                className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
              >
                キャンセル
              </button>
              <button
                onClick={handleSave}
                disabled={createMutation.isPending}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {createMutation.isPending ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

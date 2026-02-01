import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { datasetsApi } from '../lib/datasets'
import DatasetPreview from '../components/dataset/DatasetPreview'

export default function DatasetDetailPage() {
  const { datasetId } = useParams<{ datasetId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: dataset, isLoading } = useQuery({
    queryKey: ['dataset', datasetId],
    queryFn: async () => {
      if (!datasetId) throw new Error('Dataset ID is required')
      return datasetsApi.get(datasetId)
    },
    enabled: !!datasetId,
  })

  const reimportMutation = useMutation({
    mutationFn: async () => {
      if (!datasetId) throw new Error('Dataset ID is required')
      return datasetsApi.reimport(datasetId)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['dataset', datasetId] })
      queryClient.invalidateQueries({ queryKey: ['dataset-preview', datasetId] })
      if (result.schema_changed) {
        alert('スキーマが変更されました。データを確認してください。')
      }
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!datasetId) throw new Error('Dataset ID is required')
      await datasetsApi.delete(datasetId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      navigate('/datasets')
    },
  })

  if (isLoading) {
    return <div className="p-6">読み込み中...</div>
  }

  if (!dataset) {
    return <div className="p-6 text-red-600">Datasetが見つかりません</div>
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-2xl font-bold">{dataset.name}</h2>
        <div className="flex gap-2">
          <button
            onClick={() => reimportMutation.mutate()}
            disabled={reimportMutation.isPending}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {reimportMutation.isPending ? '再取り込み中...' : '再取り込み'}
          </button>
          <button
            onClick={() => {
              if (confirm('このDatasetを削除しますか？')) {
                deleteMutation.mutate()
              }
            }}
            disabled={deleteMutation.isPending}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
          >
            削除
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">基本情報</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Dataset ID:</span>
            <span className="ml-2 font-mono">{dataset.dataset_id}</span>
          </div>
          <div>
            <span className="text-gray-600">行数:</span>
            <span className="ml-2">{dataset.row_count.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-gray-600">列数:</span>
            <span className="ml-2">{dataset.column_count}</span>
          </div>
          <div>
            <span className="text-gray-600">ソースタイプ:</span>
            <span className="ml-2">{dataset.source_type}</span>
          </div>
          {dataset.last_import_at && (
            <div>
              <span className="text-gray-600">最終取り込み:</span>
              <span className="ml-2">{new Date(dataset.last_import_at).toLocaleString('ja-JP')}</span>
            </div>
          )}
        </div>
      </div>

      {datasetId && <DatasetPreview dataset_id={datasetId} />}
    </div>
  )
}

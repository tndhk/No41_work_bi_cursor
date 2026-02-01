import { Link } from 'react-router-dom'
import type { Dataset, DatasetListResponse } from '../../lib/datasets'

interface DatasetListProps {
  datasets: Dataset[]
  onDelete: (dataset_id: string) => void
  pagination?: DatasetListResponse['pagination']
  onPageChange: (page: number) => void
}

export default function DatasetList({ datasets, onDelete, pagination, onPageChange }: DatasetListProps) {
  if (datasets.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12 bg-white rounded-lg shadow-sm">
        Datasetがありません
      </div>
    )
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {datasets.map((dataset) => (
          <div
            key={dataset.dataset_id}
            className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-semibold">{dataset.name}</h3>
              <button
                onClick={() => onDelete(dataset.dataset_id)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                削除
              </button>
            </div>
            <div className="text-sm text-gray-600 space-y-1 mb-4">
              <p>行数: {dataset.row_count.toLocaleString()}</p>
              <p>列数: {dataset.column_count}</p>
              <p>ソース: {dataset.source_type}</p>
              {dataset.last_import_at && (
                <p>最終取り込み: {new Date(dataset.last_import_at).toLocaleString('ja-JP')}</p>
              )}
            </div>
            <div className="flex gap-2">
              <Link
                to={`/datasets/${dataset.dataset_id}`}
                className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700"
              >
                詳細
              </Link>
            </div>
          </div>
        ))}
      </div>

      {pagination && pagination.total > pagination.limit && (
        <div className="flex justify-center items-center gap-4">
          <button
            onClick={() => onPageChange(Math.max(0, Math.floor(pagination.offset / pagination.limit) - 1))}
            disabled={pagination.offset === 0}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            前へ
          </button>
          <span className="text-sm text-gray-600">
            {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.total)} /{' '}
            {pagination.total}
          </span>
          <button
            onClick={() => onPageChange(Math.floor(pagination.offset / pagination.limit) + 1)}
            disabled={!pagination.has_next}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            次へ
          </button>
        </div>
      )}
    </div>
  )
}

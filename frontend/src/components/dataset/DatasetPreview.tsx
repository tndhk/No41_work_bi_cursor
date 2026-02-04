import { useQuery } from '@tanstack/react-query'
import { datasetsApi } from '../../lib/datasets'

interface DatasetPreviewProps {
  dataset_id: string
  limit?: number
}

export default function DatasetPreview({ dataset_id, limit = 100 }: DatasetPreviewProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dataset-preview', dataset_id, limit],
    queryFn: async () => {
      return datasetsApi.preview(dataset_id, limit)
    },
  })

  if (isLoading) {
    return <div className="p-4">読み込み中...</div>
  }

  if (error) {
    return <div className="p-4 text-red-600">プレビューの読み込みに失敗しました</div>
  }

  if (!data) {
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold mb-4">プレビュー</h3>
      <div className="mb-4 text-sm text-gray-600">
        <p>総行数: {data.total_rows.toLocaleString()}</p>
        <p>表示行数: {data.rows.length}</p>
      </div>

      {data.columns.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {data.columns.map((colName) => (
                  <th
                    key={colName}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {colName}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  {data.columns.map((colName) => (
                    <td key={colName} className="px-4 py-3 text-sm text-gray-900">
                      {row[colName] !== null && row[colName] !== undefined
                        ? String(row[colName])
                        : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

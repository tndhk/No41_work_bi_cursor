import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { datasetsApi, type Dataset } from '../lib/datasets'
import DatasetList from '../components/dataset/DatasetList'
import DatasetImport from '../components/dataset/DatasetImport'

export default function DatasetListPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(0)
  const [showImport, setShowImport] = useState(false)
  const queryClient = useQueryClient()
  const limit = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['datasets', searchQuery, page],
    queryFn: async () => {
      const response = await datasetsApi.list({
        limit,
        offset: page * limit,
        q: searchQuery || undefined,
      })
      return response
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (dataset_id: string) => {
      await datasetsApi.delete(dataset_id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })

  const handleDelete = async (dataset_id: string) => {
    if (confirm('このDatasetを削除しますか？')) {
      deleteMutation.mutate(dataset_id)
    }
  }

  if (isLoading) {
    return <div className="p-6">読み込み中...</div>
  }

  if (error) {
    return <div className="p-6 text-red-600">エラーが発生しました</div>
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Dataset一覧</h2>
        <button
          onClick={() => setShowImport(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          新規取り込み
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="検索..."
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value)
            setPage(0)
          }}
          className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {showImport && (
        <div className="mb-6">
          <DatasetImport
            onSuccess={() => {
              setShowImport(false)
              queryClient.invalidateQueries({ queryKey: ['datasets'] })
            }}
            onCancel={() => setShowImport(false)}
          />
        </div>
      )}

      <DatasetList
        datasets={data?.data || []}
        onDelete={handleDelete}
        pagination={data?.pagination}
        onPageChange={setPage}
      />
    </div>
  )
}

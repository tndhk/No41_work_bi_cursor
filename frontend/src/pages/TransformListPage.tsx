import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { transformsApi, type Transform } from '../lib/transforms'
import TransformList from '../components/transform/TransformList'
import TransformEditor from '../components/transform/TransformEditor'

export default function TransformListPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(0)
  const [editingTransform, setEditingTransform] = useState<Transform | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const queryClient = useQueryClient()
  const limit = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['transforms', searchQuery, page],
    queryFn: async () => {
      const response = await transformsApi.list({
        limit,
        offset: page * limit,
        q: searchQuery || undefined,
      })
      return response
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (transform_id: string) => {
      await transformsApi.delete(transform_id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transforms'] })
    },
  })

  const handleDelete = async (transform_id: string) => {
    if (confirm('このTransformを削除しますか？')) {
      deleteMutation.mutate(transform_id)
    }
  }

  const handleEdit = (transform: Transform) => {
    setEditingTransform(transform)
    setShowCreate(false)
  }

  const handleCreate = () => {
    setEditingTransform(null)
    setShowCreate(true)
  }

  const handleCloseEditor = () => {
    setEditingTransform(null)
    setShowCreate(false)
  }

  const handleSave = () => {
    queryClient.invalidateQueries({ queryKey: ['transforms'] })
    handleCloseEditor()
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
        <h2 className="text-2xl font-bold">Transform一覧</h2>
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          新規作成
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

      {(showCreate || editingTransform) && (
        <div className="mb-6">
          <TransformEditor
            transform={editingTransform}
            onSave={handleSave}
            onCancel={handleCloseEditor}
          />
        </div>
      )}

      <TransformList
        transforms={data?.data || []}
        onEdit={handleEdit}
        onDelete={handleDelete}
        pagination={data?.pagination}
        onPageChange={setPage}
      />
    </div>
  )
}

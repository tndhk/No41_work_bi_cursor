import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { cardsApi, type Card } from '../lib/cards'
import CardList from '../components/card/CardList'
import CardEditor from '../components/card/CardEditor'

export default function CardListPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(0)
  const [editingCard, setEditingCard] = useState<Card | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const queryClient = useQueryClient()
  const limit = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['cards', searchQuery, page],
    queryFn: async () => {
      const response = await cardsApi.list({
        limit,
        offset: page * limit,
        q: searchQuery || undefined,
      })
      return response
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (card_id: string) => {
      await cardsApi.delete(card_id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] })
    },
  })

  const handleDelete = async (card_id: string) => {
    if (confirm('このCardを削除しますか？')) {
      deleteMutation.mutate(card_id)
    }
  }

  const handleEdit = (card: Card) => {
    setEditingCard(card)
    setShowCreate(false)
  }

  const handleCreate = () => {
    setEditingCard(null)
    setShowCreate(true)
  }

  const handleCloseEditor = () => {
    setEditingCard(null)
    setShowCreate(false)
  }

  const handleSave = () => {
    queryClient.invalidateQueries({ queryKey: ['cards'] })
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
        <h2 className="text-2xl font-bold">Card一覧</h2>
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

      {(showCreate || editingCard) && (
        <div className="mb-6">
          <CardEditor card={editingCard} onSave={handleSave} onCancel={handleCloseEditor} />
        </div>
      )}

      <CardList
        cards={data?.data || []}
        onEdit={handleEdit}
        onDelete={handleDelete}
        pagination={data?.pagination}
        onPageChange={setPage}
      />
    </div>
  )
}

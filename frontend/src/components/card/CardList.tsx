import type { Card, CardListResponse } from '../../lib/cards'

interface CardListProps {
  cards: Card[]
  onEdit: (card: Card) => void
  onDelete: (card_id: string) => void
  pagination?: CardListResponse['pagination']
  onPageChange: (page: number) => void
}

export default function CardList({ cards, onEdit, onDelete, pagination, onPageChange }: CardListProps) {
  if (cards.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12 bg-white rounded-lg shadow-sm">
        Cardがありません
      </div>
    )
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {cards.map((card) => (
          <div
            key={card.card_id}
            className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-semibold">{card.name}</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => onEdit(card)}
                  className="text-indigo-600 hover:text-indigo-800 text-sm"
                >
                  編集
                </button>
                <button
                  onClick={() => onDelete(card.card_id)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  削除
                </button>
              </div>
            </div>
            <div className="text-sm text-gray-600 space-y-1 mb-4">
              <p>Dataset ID: {card.dataset_id}</p>
              {card.filter_applicable.length > 0 && (
                <p>適用フィルタ: {card.filter_applicable.join(', ')}</p>
              )}
              <p>更新日: {new Date(card.updated_at).toLocaleString('ja-JP')}</p>
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

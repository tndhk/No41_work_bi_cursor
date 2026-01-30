import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'

interface CardContainerProps {
  cardId: string
  filters: Record<string, any>
}

export default function CardContainer({ cardId, filters }: CardContainerProps) {
  const { data: card, isLoading } = useQuery({
    queryKey: ['card', cardId],
    queryFn: async () => {
      const response = await api.get(`cards/${cardId}`).json<{ data: any }>()
      return response.data
    },
  })

  const { data: preview, isLoading: isPreviewLoading } = useQuery({
    queryKey: ['card-preview', cardId, filters],
    queryFn: async () => {
      const response = await api
        .post(`cards/${cardId}/preview`, {
          json: { filters, params: {} },
        })
        .json<{ data: { html: string } }>()
      return response.data
    },
    enabled: !!card,
  })

  if (isLoading || isPreviewLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!card || !preview) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <p className="text-gray-500">カードを読み込めませんでした</p>
      </div>
    )
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold mb-4">{card.name}</h3>
      <div
        className="card-content"
        dangerouslySetInnerHTML={{ __html: preview.html }}
      />
    </div>
  )
}

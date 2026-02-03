import { useState, type ChangeEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { cardsApi } from '../../lib/cards'
import SandboxedHtmlFrame from '../common/SandboxedHtmlFrame'

interface CardPreviewProps {
  card_id: string
}

export default function CardPreview({ card_id }: CardPreviewProps): JSX.Element {
  const [filters, setFilters] = useState<Record<string, any>>({})
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const [filterInput, setFilterInput] = useState<string>('{}')
  const [jsonError, setJsonError] = useState<string | null>(null)

  const previewMutation = useMutation({
    mutationFn: async () => {
      if (jsonError) {
        throw new Error('JSON形式が無効です。修正してください。')
      }
      return cardsApi.preview(card_id, { filters })
    },
    onSuccess: (data) => {
      setPreviewHtml(data.html)
    },
  })

  function handlePreview(): void {
    previewMutation.mutate()
  }

  function handleFilterChange(event: ChangeEvent<HTMLTextAreaElement>): void {
    const value = event.target.value
    setFilterInput(value)
    try {
      const parsed = JSON.parse(value)
      setFilters(parsed)
      setJsonError(null)
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : '無効なJSON形式です')
    }
  }

  return (
    <div className="border border-gray-300 rounded-lg p-4">
      <h4 className="text-lg font-semibold mb-4">プレビュー</h4>

      <div className="mb-4 space-y-2">
        <label htmlFor="filter-input" className="block text-sm font-medium text-gray-700">
          フィルタ値 (JSON形式、例: {'{"category": "A", "date": "2024-01-01"}'})
        </label>
        <textarea
          id="filter-input"
          value={filterInput}
          onChange={handleFilterChange}
          className={`w-full px-3 py-2 border rounded-md font-mono text-sm ${
            jsonError ? 'border-red-500' : 'border-gray-300'
          }`}
          rows={4}
          aria-invalid={!!jsonError}
          aria-describedby={jsonError ? 'json-error' : undefined}
        />
        {jsonError && (
          <p id="json-error" className="text-sm text-red-600">
            {jsonError}
          </p>
        )}
      </div>

      <button
        onClick={handlePreview}
        disabled={previewMutation.isPending}
        className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 mb-4"
      >
        {previewMutation.isPending ? '実行中...' : 'プレビュー実行'}
      </button>

      {previewMutation.isError && (
        <div className="text-red-600 text-sm mb-4">
          {previewMutation.error instanceof Error
            ? previewMutation.error.message
            : 'プレビューの実行に失敗しました'}
        </div>
      )}

      {previewHtml && (
        <div className="border border-gray-300 rounded-md p-4 bg-gray-50">
          <SandboxedHtmlFrame
            title={`card-preview-${card_id}`}
            html={previewHtml}
            height="320px"
          />
        </div>
      )}
    </div>
  )
}

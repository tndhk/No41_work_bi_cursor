import { useState, useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import Editor from '@monaco-editor/react'
import { cardsApi, type Card } from '../../lib/cards'
import { datasetsApi } from '../../lib/datasets'
import CardPreview from './CardPreview'

const cardSchema = z.object({
  name: z.string().min(1, '名前は必須です'),
  dataset_id: z.string().min(1, 'Datasetは必須です'),
  code: z.string().min(1, 'コードは必須です'),
  used_columns: z.string().optional(),
  filter_applicable: z.string().optional(),
})

interface CardEditorProps {
  card?: Card | null
  onSave: () => void
  onCancel: () => void
}

export default function CardEditor({ card, onSave, onCancel }: CardEditorProps) {
  const [usedColumns, setUsedColumns] = useState<string[]>(card?.used_columns || [])
  const [filterApplicable, setFilterApplicable] = useState<string[]>(card?.filter_applicable || [])
  const [showPreview, setShowPreview] = useState(false)

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => {
      const response = await datasetsApi.list({ limit: 100 })
      return response.data
    },
  })

  const form = useForm<z.infer<typeof cardSchema>>({
    resolver: zodResolver(cardSchema),
    defaultValues: {
      name: card?.name || '',
      dataset_id: card?.dataset_id || '',
      code: card?.code || '',
      used_columns: card?.used_columns.join(', ') || '',
      filter_applicable: card?.filter_applicable.join(', ') || '',
    },
  })

  useEffect(() => {
    if (card) {
      form.reset({
        name: card.name,
        dataset_id: card.dataset_id,
        code: card.code,
        used_columns: card.used_columns.join(', '),
        filter_applicable: card.filter_applicable.join(', '),
      })
      setUsedColumns(card.used_columns)
      setFilterApplicable(card.filter_applicable)
    }
  }, [card, form])

  const createMutation = useMutation({
    mutationFn: async (payload: {
      formData: z.infer<typeof cardSchema>
      usedColumns: string[]
      filterApplicable: string[]
    }) => {
      return cardsApi.create({
        name: payload.formData.name,
        dataset_id: payload.formData.dataset_id,
        code: payload.formData.code,
        used_columns: payload.usedColumns,
        filter_applicable: payload.filterApplicable,
      })
    },
    onSuccess: () => {
      onSave()
    },
  })

  const updateMutation = useMutation({
    mutationFn: async (payload: {
      formData: z.infer<typeof cardSchema>
      usedColumns: string[]
      filterApplicable: string[]
    }) => {
      if (!card) throw new Error('Card ID is required')
      return cardsApi.update(card.card_id, {
        name: payload.formData.name,
        dataset_id: payload.formData.dataset_id,
        code: payload.formData.code,
        used_columns: payload.usedColumns,
        filter_applicable: payload.filterApplicable,
      })
    },
    onSuccess: () => {
      onSave()
    },
  })

  const onSubmit = (data: z.infer<typeof cardSchema>) => {
    const usedCols = data.used_columns
      ? data.used_columns.split(',').map((s) => s.trim()).filter(Boolean)
      : []
    const filterApps = data.filter_applicable
      ? data.filter_applicable.split(',').map((s) => s.trim()).filter(Boolean)
      : []

    setUsedColumns(usedCols)
    setFilterApplicable(filterApps)

    const payload = {
      formData: data,
      usedColumns: usedCols,
      filterApplicable: filterApps,
    }

    if (card) {
      updateMutation.mutate(payload)
    } else {
      createMutation.mutate(payload)
    }
  }

  const defaultCode = `def render(dataset: "DataFrameLike", filters: dict, params: dict) -> "HTMLResult":
    # フィルタ適用済みデータを受け取る
    # HTMLを生成して返す
    # 例:
    # import pandas as pd
    # html = f"<div>行数: {len(dataset)}</div>"
    # return HTMLResult(
    #     html=html,
    #     used_columns=["col1", "col2"],
    #     filter_applicable=["category", "date"]
    # )
    from app.models.card import HTMLResult
    return HTMLResult(
        html="<div>カードコードを実装してください</div>",
        used_columns=[],
        filter_applicable=[]
    )
`

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold mb-4">{card ? 'Card編集' : 'Card作成'}</h3>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">名前</label>
          <input
            {...form.register('name')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {form.formState.errors.name && (
            <p className="mt-1 text-sm text-red-600">{form.formState.errors.name.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Dataset</label>
          <select
            {...form.register('dataset_id')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">選択してください</option>
            {datasets?.map((dataset) => (
              <option key={dataset.dataset_id} value={dataset.dataset_id}>
                {dataset.name}
              </option>
            ))}
          </select>
          {form.formState.errors.dataset_id && (
            <p className="mt-1 text-sm text-red-600">{form.formState.errors.dataset_id.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Pythonコード</label>
          <div className="border border-gray-300 rounded-md overflow-hidden">
            <Controller
              name="code"
              control={form.control}
              render={({ field }) => (
                <Editor
                  height="400px"
                  defaultLanguage="python"
                  value={field.value || defaultCode}
                  onChange={(value) => field.onChange(value || '')}
                  theme="vs-light"
                  options={{
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                  }}
                />
              )}
            />
          </div>
          {form.formState.errors.code && (
            <p className="mt-1 text-sm text-red-600">{form.formState.errors.code.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            使用カラム (カンマ区切り)
          </label>
          <input
            {...form.register('used_columns')}
            placeholder="例: col1, col2, col3"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            適用可能フィルタ (カンマ区切り)
          </label>
          <input
            {...form.register('filter_applicable')}
            placeholder="例: category, date"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={createMutation.isPending || updateMutation.isPending}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createMutation.isPending || updateMutation.isPending ? '保存中...' : '保存'}
          </button>
          {card && (
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              {showPreview ? 'プレビューを閉じる' : 'プレビュー'}
            </button>
          )}
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
          >
            キャンセル
          </button>
        </div>

        {(createMutation.isError || updateMutation.isError) && (
          <div className="text-red-600 text-sm">
            {createMutation.error instanceof Error
              ? createMutation.error.message
              : updateMutation.error instanceof Error
                ? updateMutation.error.message
                : 'エラーが発生しました'}
          </div>
        )}

        {card && showPreview && (
          <div className="mt-6">
            <CardPreview card_id={card.card_id} />
          </div>
        )}
      </form>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import Editor from '@monaco-editor/react'
import { transformsApi, type Transform } from '../../lib/transforms'
import { datasetsApi } from '../../lib/datasets'

const transformSchema = z.object({
  name: z.string().min(1, '名前は必須です'),
  code: z.string().min(1, 'コードは必須です'),
  input_dataset_ids: z.array(z.string()).min(1, '少なくとも1つの入力Datasetが必要です'),
  schedule: z.string().nullable().optional(),
})

interface TransformEditorProps {
  transform?: Transform | null
  onSave: () => void
  onCancel: () => void
}

export default function TransformEditor({ transform, onSave, onCancel }: TransformEditorProps) {
  const [inputDatasetIds, setInputDatasetIds] = useState<string[]>(transform?.input_dataset_ids || [])

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => {
      const response = await datasetsApi.list({ limit: 100 })
      return response.data
    },
  })

  const form = useForm<z.infer<typeof transformSchema>>({
    resolver: zodResolver(transformSchema),
    defaultValues: {
      name: transform?.name || '',
      code: transform?.code || '',
      input_dataset_ids: transform?.input_dataset_ids || [],
      schedule: transform?.schedule || null,
    },
  })

  useEffect(() => {
    if (transform) {
      const ids = transform.input_dataset_ids
      form.reset({
        name: transform.name,
        code: transform.code,
        input_dataset_ids: ids,
        schedule: transform.schedule,
      })
      setInputDatasetIds(ids)
    }
  }, [transform, form])

  const createMutation = useMutation({
    mutationFn: async (data: z.infer<typeof transformSchema>) => {
      return transformsApi.create({
        name: data.name,
        code: data.code,
        input_dataset_ids: inputDatasetIds,
        schedule: data.schedule || null,
      })
    },
    onSuccess: () => {
      onSave()
    },
  })

  const updateMutation = useMutation({
    mutationFn: async (data: z.infer<typeof transformSchema>) => {
      if (!transform) throw new Error('Transform ID is required')
      return transformsApi.update(transform.transform_id, {
        name: data.name,
        code: data.code,
        input_dataset_ids: inputDatasetIds,
        schedule: data.schedule || null,
      })
    },
    onSuccess: () => {
      onSave()
    },
  })

  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!transform) throw new Error('Transform ID is required')
      return transformsApi.execute(transform.transform_id)
    },
  })

  const onSubmit = (data: z.infer<typeof transformSchema>) => {
    if (transform) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  const defaultCode = `def transform(inputs: dict[str, "DataFrameLike"], params: dict) -> "DataFrameLike":
    # inputs["dataset_name"] のようにDatasetにアクセス
    # 例: result = inputs["sales"].copy()
    # 返り値はDataFrameLike（pandas.DataFrame等）
    return inputs[list(inputs.keys())[0]]
`

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold mb-4">
        {transform ? 'Transform編集' : 'Transform作成'}
      </h3>

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
          <label className="block text-sm font-medium text-gray-700 mb-2">入力Dataset</label>
          <div className="space-y-2">
            {datasets?.map((dataset) => (
              <label key={dataset.dataset_id} className="flex items-center">
                <input
                  type="checkbox"
                  checked={inputDatasetIds.includes(dataset.dataset_id)}
                  onChange={(e) => {
                    const nextIds = e.target.checked
                      ? [...inputDatasetIds, dataset.dataset_id]
                      : inputDatasetIds.filter((id) => id !== dataset.dataset_id)
                    setInputDatasetIds(nextIds)
                    form.setValue('input_dataset_ids', nextIds, { shouldValidate: true })
                  }}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">{dataset.name}</span>
              </label>
            ))}
          </div>
          {form.formState.errors.input_dataset_ids && (
            <p className="mt-1 text-sm text-red-600">
              {form.formState.errors.input_dataset_ids.message}
            </p>
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
            スケジュール (cron形式、例: 0 0 * * *)
          </label>
          <input
            {...form.register('schedule')}
            placeholder="例: 0 0 * * * (毎日0時)"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <p className="mt-1 text-xs text-gray-500">
            空欄の場合は手動実行のみ。cron形式でスケジュールを設定できます。
          </p>
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={createMutation.isPending || updateMutation.isPending}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createMutation.isPending || updateMutation.isPending ? '保存中...' : '保存'}
          </button>
          {transform && (
            <button
              type="button"
              onClick={() => executeMutation.mutate()}
              disabled={executeMutation.isPending}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {executeMutation.isPending ? '実行中...' : '実行'}
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

        {(createMutation.isError || updateMutation.isError || executeMutation.isError) && (
          <div className="text-red-600 text-sm">
            {createMutation.error instanceof Error
              ? createMutation.error.message
              : updateMutation.error instanceof Error
                ? updateMutation.error.message
                : executeMutation.error instanceof Error
                  ? executeMutation.error.message
                  : 'エラーが発生しました'}
          </div>
        )}

        {executeMutation.isSuccess && (
          <div className="text-green-600 text-sm">
            実行が完了しました。実行履歴を確認してください。
          </div>
        )}
      </form>
    </div>
  )
}

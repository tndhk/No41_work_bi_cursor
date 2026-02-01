import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { datasetsApi, type DatasetCreateRequest, type S3ImportRequest } from '../../lib/datasets'

const localCsvSchema = z.object({
  name: z.string().min(1, '名前は必須です'),
  encoding: z.string().default('utf-8'),
  delimiter: z.string().default(','),
  has_header: z.boolean().default(true),
})

const s3ImportSchema = z.object({
  name: z.string().min(1, '名前は必須です'),
  bucket: z.string().min(1, 'バケット名は必須です'),
  key: z.string().min(1, 'キーは必須です'),
  encoding: z.string().default('utf-8'),
  delimiter: z.string().default(','),
  has_header: z.boolean().default(true),
})

interface DatasetImportProps {
  onSuccess: () => void
  onCancel: () => void
}

export default function DatasetImport({ onSuccess, onCancel }: DatasetImportProps) {
  const [importType, setImportType] = useState<'local' | 's3'>('local')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const localForm = useForm<z.infer<typeof localCsvSchema>>({
    resolver: zodResolver(localCsvSchema),
    defaultValues: {
      name: '',
      encoding: 'utf-8',
      delimiter: ',',
      has_header: true,
    },
  })

  const s3Form = useForm<z.infer<typeof s3ImportSchema>>({
    resolver: zodResolver(s3ImportSchema),
    defaultValues: {
      name: '',
      bucket: '',
      key: '',
      encoding: 'utf-8',
      delimiter: ',',
      has_header: true,
    },
  })

  const localMutation = useMutation({
    mutationFn: async (data: z.infer<typeof localCsvSchema>) => {
      if (!selectedFile) throw new Error('ファイルが選択されていません')
      return datasetsApi.create(selectedFile, data)
    },
    onSuccess: () => {
      onSuccess()
    },
  })

  const s3Mutation = useMutation({
    mutationFn: async (data: z.infer<typeof s3ImportSchema>) => {
      return datasetsApi.s3Import(data)
    },
    onSuccess: () => {
      onSuccess()
    },
  })

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h3 className="text-xl font-bold mb-4">Dataset取り込み</h3>
        <div className="flex gap-4 mb-4">
          <button
            onClick={() => setImportType('local')}
            className={`px-4 py-2 rounded-md ${
              importType === 'local'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Local CSV
          </button>
          <button
            onClick={() => setImportType('s3')}
            className={`px-4 py-2 rounded-md ${
              importType === 's3'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            S3 CSV
          </button>
        </div>
      </div>

      {importType === 'local' ? (
        <form
          onSubmit={localForm.handleSubmit((data) => localMutation.mutate(data))}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ファイル</label>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center ${
                dragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300'
              }`}
            >
              {selectedFile ? (
                <div>
                  <p className="text-sm text-gray-600">{selectedFile.name}</p>
                  <button
                    type="button"
                    onClick={() => setSelectedFile(null)}
                    className="mt-2 text-sm text-red-600 hover:text-red-800"
                  >
                    削除
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-sm text-gray-600 mb-2">ファイルをドラッグ&ドロップ</p>
                  <p className="text-xs text-gray-500 mb-2">または</p>
                  <label className="px-4 py-2 bg-indigo-600 text-white rounded-md cursor-pointer hover:bg-indigo-700">
                    ファイルを選択
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </label>
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">名前</label>
            <input
              {...localForm.register('name')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {localForm.formState.errors.name && (
              <p className="mt-1 text-sm text-red-600">{localForm.formState.errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">文字コード</label>
            <select
              {...localForm.register('encoding')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="utf-8">UTF-8</option>
              <option value="shift_jis">Shift-JIS</option>
              <option value="euc-jp">EUC-JP</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">区切り文字</label>
            <input
              {...localForm.register('delimiter')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="flex items-center">
              <input type="checkbox" {...localForm.register('has_header')} className="mr-2" />
              <span className="text-sm text-gray-700">ヘッダー行あり</span>
            </label>
          </div>

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={!selectedFile || localMutation.isPending}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {localMutation.isPending ? '取り込み中...' : '取り込み'}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              キャンセル
            </button>
          </div>

          {localMutation.isError && (
            <div className="text-red-600 text-sm">
              {localMutation.error instanceof Error ? localMutation.error.message : 'エラーが発生しました'}
            </div>
          )}
        </form>
      ) : (
        <form
          onSubmit={s3Form.handleSubmit((data) => s3Mutation.mutate(data))}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">名前</label>
            <input
              {...s3Form.register('name')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {s3Form.formState.errors.name && (
              <p className="mt-1 text-sm text-red-600">{s3Form.formState.errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">S3バケット</label>
            <input
              {...s3Form.register('bucket')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {s3Form.formState.errors.bucket && (
              <p className="mt-1 text-sm text-red-600">{s3Form.formState.errors.bucket.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">S3キー</label>
            <input
              {...s3Form.register('key')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {s3Form.formState.errors.key && (
              <p className="mt-1 text-sm text-red-600">{s3Form.formState.errors.key.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">文字コード</label>
            <select
              {...s3Form.register('encoding')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="utf-8">UTF-8</option>
              <option value="shift_jis">Shift-JIS</option>
              <option value="euc-jp">EUC-JP</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">区切り文字</label>
            <input
              {...s3Form.register('delimiter')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="flex items-center">
              <input type="checkbox" {...s3Form.register('has_header')} className="mr-2" />
              <span className="text-sm text-gray-700">ヘッダー行あり</span>
            </label>
          </div>

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={s3Mutation.isPending}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {s3Mutation.isPending ? '取り込み中...' : '取り込み'}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              キャンセル
            </button>
          </div>

          {s3Mutation.isError && (
            <div className="text-red-600 text-sm">
              {s3Mutation.error instanceof Error ? s3Mutation.error.message : 'エラーが発生しました'}
            </div>
          )}
        </form>
      )}
    </div>
  )
}

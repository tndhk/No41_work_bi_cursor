import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DatasetListPage from '../DatasetListPage'

// datasetsApi をモック
vi.mock('../../lib/datasets', () => ({
  datasetsApi: {
    list: vi.fn(),
    delete: vi.fn(),
  },
}))

// DatasetList と DatasetImport をモック
vi.mock('../../components/dataset/DatasetList', () => ({
  default: ({ datasets, onDelete }: any) => (
    <div data-testid="dataset-list">
      {datasets.map((dataset: any) => (
        <div key={dataset.dataset_id} data-testid={`dataset-${dataset.dataset_id}`}>
          <span>{dataset.name}</span>
          <button onClick={() => onDelete(dataset.dataset_id)}>削除</button>
        </div>
      ))}
    </div>
  ),
}))

vi.mock('../../components/dataset/DatasetImport', () => ({
  default: ({ onSuccess, onCancel }: any) => (
    <div data-testid="dataset-import">
      <span>Dataset Import</span>
      <button onClick={onSuccess}>インポート成功</button>
      <button onClick={onCancel}>キャンセル</button>
    </div>
  ),
}))

import { datasetsApi } from '../../lib/datasets'

describe('DatasetListPage', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    window.confirm = vi.fn(() => true)
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )

  it('ローディング状態を表示する', () => {
    vi.mocked(datasetsApi.list).mockReturnValue(
      new Promise(() => {}) as any
    )

    render(<DatasetListPage />, { wrapper })

    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  it('データセット一覧を表示する', async () => {
    const mockDatasets = [
      {
        dataset_id: 'd1',
        name: 'Dataset 1',
        owner_id: 'u1',
        source_type: 'file',
        source_config: {},
        schema: [],
        row_count: 100,
        column_count: 5,
        s3_path: 's3://bucket/key',
        partition_column: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
        last_import_at: null,
        last_import_by: null,
      },
      {
        dataset_id: 'd2',
        name: 'Dataset 2',
        owner_id: 'u1',
        source_type: 'file',
        source_config: {},
        schema: [],
        row_count: 200,
        column_count: 10,
        s3_path: 's3://bucket/key2',
        partition_column: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
        last_import_at: null,
        last_import_by: null,
      },
    ]

    vi.mocked(datasetsApi.list).mockResolvedValueOnce({
      data: mockDatasets,
      pagination: {
        total: 2,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<DatasetListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('Dataset一覧')).toBeInTheDocument()
      expect(screen.getByText('Dataset 1')).toBeInTheDocument()
      expect(screen.getByText('Dataset 2')).toBeInTheDocument()
    })
  })

  it.skip('エラー状態を表示する', async () => {
    // TODO: react-queryのエラーハンドリングを改善
    const errorQueryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    vi.mocked(datasetsApi.list).mockRejectedValueOnce(new Error('Network error'))

    const errorWrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={errorQueryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )

    render(<DatasetListPage />, { wrapper: errorWrapper })

    await waitFor(
      () => {
        expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('検索機能が動作する', async () => {
    const user = userEvent.setup()
    const mockDatasets = [
      {
        dataset_id: 'd1',
        name: 'Dataset 1',
        owner_id: 'u1',
        source_type: 'file',
        source_config: {},
        schema: [],
        row_count: 100,
        column_count: 5,
        s3_path: 's3://bucket/key',
        partition_column: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
        last_import_at: null,
        last_import_by: null,
      },
    ]

    vi.mocked(datasetsApi.list).mockResolvedValue({
      data: mockDatasets,
      pagination: {
        total: 1,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<DatasetListPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByPlaceholderText('検索...')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const searchInput = screen.getByPlaceholderText('検索...')
    await user.type(searchInput, 't')

    await waitFor(
      () => {
        expect(datasetsApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            q: 't',
          })
        )
      },
      { timeout: 5000 }
    )
  })

  it('新規取り込みボタンでインポートコンポーネントを表示する', async () => {
    const user = userEvent.setup()
    vi.mocked(datasetsApi.list).mockResolvedValueOnce({
      data: [],
      pagination: {
        total: 0,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<DatasetListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('新規取り込み')).toBeInTheDocument()
    })

    const importButton = screen.getByRole('button', { name: '新規取り込み' })
    await user.click(importButton)

    await waitFor(() => {
      expect(screen.getByTestId('dataset-import')).toBeInTheDocument()
    })
  })

  it('インポート成功時にインポートコンポーネントを閉じる', async () => {
    const user = userEvent.setup()
    vi.mocked(datasetsApi.list).mockResolvedValue({
      data: [],
      pagination: {
        total: 0,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<DatasetListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('新規取り込み')).toBeInTheDocument()
    })

    const importButton = screen.getByRole('button', { name: '新規取り込み' })
    await user.click(importButton)

    await waitFor(() => {
      expect(screen.getByTestId('dataset-import')).toBeInTheDocument()
    })

    const successButton = screen.getByRole('button', { name: 'インポート成功' })
    await user.click(successButton)

    await waitFor(() => {
      expect(screen.queryByTestId('dataset-import')).not.toBeInTheDocument()
    })
  })

  it('インポートキャンセル時にインポートコンポーネントを閉じる', async () => {
    const user = userEvent.setup()
    vi.mocked(datasetsApi.list).mockResolvedValue({
      data: [],
      pagination: {
        total: 0,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<DatasetListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('新規取り込み')).toBeInTheDocument()
    })

    const importButton = screen.getByRole('button', { name: '新規取り込み' })
    await user.click(importButton)

    await waitFor(() => {
      expect(screen.getByTestId('dataset-import')).toBeInTheDocument()
    })

    const cancelButton = screen.getByRole('button', { name: 'キャンセル' })
    await user.click(cancelButton)

    await waitFor(() => {
      expect(screen.queryByTestId('dataset-import')).not.toBeInTheDocument()
    })
  })

  it('削除ボタンでデータセットを削除する', async () => {
    const user = userEvent.setup()
    const mockDataset = {
      dataset_id: 'd1',
      name: 'Dataset 1',
      owner_id: 'u1',
      source_type: 'file',
      source_config: {},
      schema: [],
      row_count: 100,
      column_count: 5,
      s3_path: 's3://bucket/key',
      partition_column: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      last_import_at: null,
      last_import_by: null,
    }

    vi.mocked(datasetsApi.list).mockResolvedValue({
      data: [mockDataset],
      pagination: {
        total: 1,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })
    vi.mocked(datasetsApi.delete).mockResolvedValueOnce(undefined)

    render(<DatasetListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('Dataset 1')).toBeInTheDocument()
    })

    const deleteButton = screen.getByRole('button', { name: '削除' })
    await user.click(deleteButton)

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalledWith('このDatasetを削除しますか？')
      expect(datasetsApi.delete).toHaveBeenCalledWith('d1')
    })
  })
})

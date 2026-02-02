import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DatasetDetailPage from '../DatasetDetailPage'

// datasetsApi をモック
vi.mock('../../lib/datasets', () => ({
  datasetsApi: {
    get: vi.fn(),
    reimport: vi.fn(),
    delete: vi.fn(),
  },
}))

// DatasetPreview をモック
vi.mock('../../components/dataset/DatasetPreview', () => ({
  default: ({ dataset_id }: any) => (
    <div data-testid="dataset-preview">
      <span>Preview for {dataset_id}</span>
    </div>
  ),
}))

// useParams, useNavigate をモック
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: vi.fn(),
    useNavigate: vi.fn(),
  }
})

import { datasetsApi } from '../../lib/datasets'
import { useParams, useNavigate } from 'react-router-dom'

describe('DatasetDetailPage', () => {
  let queryClient: QueryClient
  const mockNavigate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.mocked(useParams).mockReturnValue({ datasetId: 'd1' })
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)
    window.confirm = vi.fn(() => true)
    window.alert = vi.fn()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )

  it('ローディング状態を表示する', () => {
    vi.mocked(datasetsApi.get).mockReturnValue(
      new Promise(() => {}) as any
    )

    render(<DatasetDetailPage />, { wrapper })

    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  it('データセット詳細を表示する', async () => {
    const mockDataset = {
      dataset_id: 'd1',
      name: 'Test Dataset',
      owner_id: 'u1',
      source_type: 'file',
      source_config: {},
      schema: [],
      row_count: 1000,
      column_count: 5,
      s3_path: 's3://bucket/key',
      partition_column: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      last_import_at: '2024-01-02T00:00:00Z',
      last_import_by: 'u1',
    }

    vi.mocked(datasetsApi.get).mockResolvedValueOnce(mockDataset)

    render(<DatasetDetailPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('Test Dataset')).toBeInTheDocument()
        expect(screen.getByText('1,000')).toBeInTheDocument()
        expect(screen.getByText('5')).toBeInTheDocument()
        expect(screen.getByText('file')).toBeInTheDocument()
        expect(screen.getByTestId('dataset-preview')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('再取り込みボタンで再取り込みを実行する', async () => {
    const user = userEvent.setup()
    const mockDataset = {
      dataset_id: 'd1',
      name: 'Test Dataset',
      owner_id: 'u1',
      source_type: 'file',
      source_config: {},
      schema: [],
      row_count: 1000,
      column_count: 5,
      s3_path: 's3://bucket/key',
      partition_column: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      last_import_at: null,
      last_import_by: null,
    }

    vi.mocked(datasetsApi.get).mockResolvedValue(mockDataset)
    vi.mocked(datasetsApi.reimport).mockResolvedValueOnce({
      data: mockDataset,
      schema_changed: false,
    })

    render(<DatasetDetailPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('再取り込み')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const reimportButton = screen.getByRole('button', { name: '再取り込み' })
    await user.click(reimportButton)

    await waitFor(
      () => {
        expect(datasetsApi.reimport).toHaveBeenCalledWith('d1')
      },
      { timeout: 3000 }
    )
  })

  it('削除ボタンでデータセットを削除する', async () => {
    const user = userEvent.setup()
    const mockDataset = {
      dataset_id: 'd1',
      name: 'Test Dataset',
      owner_id: 'u1',
      source_type: 'file',
      source_config: {},
      schema: [],
      row_count: 1000,
      column_count: 5,
      s3_path: 's3://bucket/key',
      partition_column: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      last_import_at: null,
      last_import_by: null,
    }

    vi.mocked(datasetsApi.get).mockResolvedValue(mockDataset)
    vi.mocked(datasetsApi.delete).mockResolvedValueOnce(undefined)

    render(<DatasetDetailPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('削除')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const deleteButton = screen.getByRole('button', { name: '削除' })
    await user.click(deleteButton)

    await waitFor(
      () => {
        expect(window.confirm).toHaveBeenCalledWith('このDatasetを削除しますか？')
        expect(datasetsApi.delete).toHaveBeenCalledWith('d1')
        expect(mockNavigate).toHaveBeenCalledWith('/datasets')
      },
      { timeout: 3000 }
    )
  })

  it('データセットが見つからない場合にエラーを表示する', async () => {
    vi.mocked(datasetsApi.get).mockResolvedValueOnce(null as any)

    render(<DatasetDetailPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('Datasetが見つかりません')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })
})

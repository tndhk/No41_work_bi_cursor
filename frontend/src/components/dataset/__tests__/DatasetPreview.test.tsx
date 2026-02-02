import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DatasetPreview from '../DatasetPreview'

// datasetsApi をモック
vi.mock('../../../lib/datasets', () => ({
  datasetsApi: {
    preview: vi.fn(),
  },
}))

import { datasetsApi } from '../../../lib/datasets'

describe('DatasetPreview', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('ローディング状態を表示する', () => {
    vi.mocked(datasetsApi.preview).mockReturnValue(
      new Promise(() => {}) as any
    )

    render(<DatasetPreview dataset_id="d1" />, { wrapper })

    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  it('データプレビューを表示する', async () => {
    const mockPreview = {
      columns: [
        { name: 'col1', dtype: 'string' },
        { name: 'col2', dtype: 'number' },
      ],
      rows: [
        { col1: 'value1', col2: 100 },
        { col1: 'value2', col2: 200 },
      ],
      row_count: 1000,
    }

    vi.mocked(datasetsApi.preview).mockResolvedValueOnce(mockPreview)

    render(<DatasetPreview dataset_id="d1" />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('プレビュー')).toBeInTheDocument()
        expect(screen.getByText(/総行数:/)).toBeInTheDocument()
        expect(screen.getByText(/表示行数:/)).toBeInTheDocument()
        expect(screen.getByText('col1')).toBeInTheDocument()
        expect(screen.getByText('col2')).toBeInTheDocument()
        expect(screen.getByText('value1')).toBeInTheDocument()
        expect(screen.getByText('100')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('エラー状態を表示する', async () => {
    vi.mocked(datasetsApi.preview).mockRejectedValueOnce(new Error('Network error'))

    render(<DatasetPreview dataset_id="d1" />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('プレビューの読み込みに失敗しました')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('limitパラメータを渡す', async () => {
    const mockPreview = {
      columns: [],
      rows: [],
      row_count: 0,
    }

    vi.mocked(datasetsApi.preview).mockResolvedValueOnce(mockPreview)

    render(<DatasetPreview dataset_id="d1" limit={50} />, { wrapper })

    await waitFor(
      () => {
        expect(datasetsApi.preview).toHaveBeenCalledWith('d1', 50)
      },
      { timeout: 3000 }
    )
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TransformListPage from '../TransformListPage'

// transformsApi をモック
vi.mock('../../lib/transforms', () => ({
  transformsApi: {
    list: vi.fn(),
    delete: vi.fn(),
  },
}))

// TransformList と TransformEditor をモック
vi.mock('../../components/transform/TransformList', () => ({
  default: ({ transforms, onEdit, onDelete }: any) => (
    <div data-testid="transform-list">
      {transforms.map((transform: any) => (
        <div key={transform.transform_id} data-testid={`transform-${transform.transform_id}`}>
          <span>{transform.name}</span>
          <button onClick={() => onEdit(transform)}>編集</button>
          <button onClick={() => onDelete(transform.transform_id)}>削除</button>
        </div>
      ))}
    </div>
  ),
}))

vi.mock('../../components/transform/TransformEditor', () => ({
  default: ({ transform, onSave, onCancel }: any) => (
    <div data-testid="transform-editor">
      <span>{transform ? `編集: ${transform.name}` : '新規作成'}</span>
      <button onClick={onSave}>保存</button>
      <button onClick={onCancel}>キャンセル</button>
    </div>
  ),
}))

import { transformsApi } from '../../lib/transforms'

describe('TransformListPage', () => {
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
    vi.mocked(transformsApi.list).mockReturnValue(
      new Promise(() => {}) as any
    )

    render(<TransformListPage />, { wrapper })

    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  it('トランスフォーム一覧を表示する', async () => {
    const mockTransforms = [
      {
        transform_id: 't1',
        name: 'Transform 1',
        owner_id: 'u1',
        code: 'code1',
        input_dataset_ids: ['d1'],
        output_dataset_id: null,
        params: {},
        schedule: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
        last_executed_at: null,
      },
      {
        transform_id: 't2',
        name: 'Transform 2',
        owner_id: 'u1',
        code: 'code2',
        input_dataset_ids: ['d2'],
        output_dataset_id: 'd3',
        params: {},
        schedule: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
        last_executed_at: null,
      },
    ]

    vi.mocked(transformsApi.list).mockResolvedValueOnce({
      data: mockTransforms,
      pagination: {
        total: 2,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<TransformListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('Transform一覧')).toBeInTheDocument()
      expect(screen.getByText('Transform 1')).toBeInTheDocument()
      expect(screen.getByText('Transform 2')).toBeInTheDocument()
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

    vi.mocked(transformsApi.list).mockRejectedValueOnce(new Error('Network error'))

    const errorWrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={errorQueryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )

    render(<TransformListPage />, { wrapper: errorWrapper })

    await waitFor(
      () => {
        expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('検索機能が動作する', async () => {
    const user = userEvent.setup()
    const mockTransforms = [
      {
        transform_id: 't1',
        name: 'Transform 1',
        owner_id: 'u1',
        code: 'code1',
        input_dataset_ids: ['d1'],
        output_dataset_id: null,
        params: {},
        schedule: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
        last_executed_at: null,
      },
    ]

    vi.mocked(transformsApi.list).mockResolvedValue({
      data: mockTransforms,
      pagination: {
        total: 1,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<TransformListPage />, { wrapper })

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
        expect(transformsApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            q: 't',
          })
        )
      },
      { timeout: 5000 }
    )
  })

  it('新規作成ボタンでエディタを表示する', async () => {
    const user = userEvent.setup()
    vi.mocked(transformsApi.list).mockResolvedValue({
      data: [],
      pagination: {
        total: 0,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<TransformListPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByRole('button', { name: '新規作成' })).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const createButton = screen.getByRole('button', { name: '新規作成' })
    await user.click(createButton)

    await waitFor(
      () => {
        expect(screen.getByTestId('transform-editor')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // エディタ内のテキストを確認（エディタ内のspan要素を確認）
    const editor = screen.getByTestId('transform-editor')
    expect(editor).toHaveTextContent('新規作成')
  })

  it('編集ボタンでエディタを表示する', async () => {
    const user = userEvent.setup()
    const mockTransform = {
      transform_id: 't1',
      name: 'Transform 1',
      owner_id: 'u1',
      code: 'code1',
      input_dataset_ids: ['d1'],
      output_dataset_id: null,
      params: {},
      schedule: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      last_executed_at: null,
    }

    vi.mocked(transformsApi.list).mockResolvedValueOnce({
      data: [mockTransform],
      pagination: {
        total: 1,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<TransformListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('Transform 1')).toBeInTheDocument()
    })

    const editButton = screen.getByRole('button', { name: '編集' })
    await user.click(editButton)

    await waitFor(() => {
      expect(screen.getByTestId('transform-editor')).toBeInTheDocument()
      expect(screen.getByText('編集: Transform 1')).toBeInTheDocument()
    })
  })

  it('削除ボタンでトランスフォームを削除する', async () => {
    const user = userEvent.setup()
    const mockTransform = {
      transform_id: 't1',
      name: 'Transform 1',
      owner_id: 'u1',
      code: 'code1',
      input_dataset_ids: ['d1'],
      output_dataset_id: null,
      params: {},
      schedule: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      last_executed_at: null,
    }

    vi.mocked(transformsApi.list).mockResolvedValue({
      data: [mockTransform],
      pagination: {
        total: 1,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })
    vi.mocked(transformsApi.delete).mockResolvedValueOnce(undefined)

    render(<TransformListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('Transform 1')).toBeInTheDocument()
    })

    const deleteButton = screen.getByRole('button', { name: '削除' })
    await user.click(deleteButton)

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalledWith('このTransformを削除しますか？')
      expect(transformsApi.delete).toHaveBeenCalledWith('t1')
    })
  })

  it('エディタのキャンセルボタンでエディタを閉じる', async () => {
    const user = userEvent.setup()
    vi.mocked(transformsApi.list).mockResolvedValueOnce({
      data: [],
      pagination: {
        total: 0,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<TransformListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('新規作成')).toBeInTheDocument()
    })

    const createButton = screen.getByRole('button', { name: '新規作成' })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByTestId('transform-editor')).toBeInTheDocument()
    })

    const cancelButton = screen.getByRole('button', { name: 'キャンセル' })
    await user.click(cancelButton)

    await waitFor(() => {
      expect(screen.queryByTestId('transform-editor')).not.toBeInTheDocument()
    })
  })
})

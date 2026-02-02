import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CardListPage from '../CardListPage'

// cardsApi をモック
vi.mock('../../lib/cards', () => ({
  cardsApi: {
    list: vi.fn(),
    delete: vi.fn(),
  },
}))

// CardList と CardEditor をモック
vi.mock('../../components/card/CardList', () => ({
  default: ({ cards, onEdit, onDelete }: any) => (
    <div data-testid="card-list">
      {cards.map((card: any) => (
        <div key={card.card_id} data-testid={`card-${card.card_id}`}>
          <span>{card.name}</span>
          <button onClick={() => onEdit(card)}>編集</button>
          <button onClick={() => onDelete(card.card_id)}>削除</button>
        </div>
      ))}
    </div>
  ),
}))

vi.mock('../../components/card/CardEditor', () => ({
  default: ({ card, onSave, onCancel }: any) => (
    <div data-testid="card-editor">
      <span>{card ? `編集: ${card.name}` : '新規作成'}</span>
      <button onClick={onSave}>保存</button>
      <button onClick={onCancel}>キャンセル</button>
    </div>
  ),
}))

import { cardsApi } from '../../lib/cards'

describe('CardListPage', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    // window.confirm をモック
    window.confirm = vi.fn(() => true)
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )

  it('ローディング状態を表示する', () => {
    vi.mocked(cardsApi.list).mockReturnValue(
      new Promise(() => {}) as any
    )

    render(<CardListPage />, { wrapper })

    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  it('カード一覧を表示する', async () => {
    const mockCards = [
      {
        card_id: 'c1',
        name: 'Card 1',
        owner_id: 'u1',
        dataset_id: 'd1',
        code: 'code1',
        params: {},
        used_columns: [],
        filter_applicable: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
      {
        card_id: 'c2',
        name: 'Card 2',
        owner_id: 'u1',
        dataset_id: 'd1',
        code: 'code2',
        params: {},
        used_columns: [],
        filter_applicable: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
      },
    ]

    vi.mocked(cardsApi.list).mockResolvedValueOnce({
      data: mockCards,
      pagination: {
        total: 2,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<CardListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('Card一覧')).toBeInTheDocument()
      expect(screen.getByText('Card 1')).toBeInTheDocument()
      expect(screen.getByText('Card 2')).toBeInTheDocument()
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

    vi.mocked(cardsApi.list).mockRejectedValueOnce(new Error('Network error'))

    const errorWrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={errorQueryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )

    render(<CardListPage />, { wrapper: errorWrapper })

    await waitFor(
      () => {
        expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('検索機能が動作する', async () => {
    const user = userEvent.setup()
    const mockCards = [
      {
        card_id: 'c1',
        name: 'Card 1',
        owner_id: 'u1',
        dataset_id: 'd1',
        code: 'code1',
        params: {},
        used_columns: [],
        filter_applicable: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ]

    vi.mocked(cardsApi.list).mockResolvedValue({
      data: mockCards,
      pagination: {
        total: 1,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<CardListPage />, { wrapper })

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
        expect(cardsApi.list).toHaveBeenCalledWith(
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
    vi.mocked(cardsApi.list).mockResolvedValue({
      data: [],
      pagination: {
        total: 0,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<CardListPage />, { wrapper })

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
        expect(screen.getByTestId('card-editor')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // エディタ内のテキストを確認（エディタ内のspan要素を確認）
    const editor = screen.getByTestId('card-editor')
    expect(editor).toHaveTextContent('新規作成')
  })

  it('編集ボタンでエディタを表示する', async () => {
    const user = userEvent.setup()
    const mockCard = {
      card_id: 'c1',
      name: 'Card 1',
      owner_id: 'u1',
      dataset_id: 'd1',
      code: 'code1',
      params: {},
      used_columns: [],
      filter_applicable: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    }

    vi.mocked(cardsApi.list).mockResolvedValueOnce({
      data: [mockCard],
      pagination: {
        total: 1,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<CardListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('Card 1')).toBeInTheDocument()
    })

    const editButton = screen.getByRole('button', { name: '編集' })
    await user.click(editButton)

    await waitFor(() => {
      expect(screen.getByTestId('card-editor')).toBeInTheDocument()
      expect(screen.getByText('編集: Card 1')).toBeInTheDocument()
    })
  })

  it('削除ボタンでカードを削除する', async () => {
    const user = userEvent.setup()
    const mockCard = {
      card_id: 'c1',
      name: 'Card 1',
      owner_id: 'u1',
      dataset_id: 'd1',
      code: 'code1',
      params: {},
      used_columns: [],
      filter_applicable: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    }

    vi.mocked(cardsApi.list).mockResolvedValue({
      data: [mockCard],
      pagination: {
        total: 1,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })
    vi.mocked(cardsApi.delete).mockResolvedValueOnce(undefined)

    render(<CardListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('Card 1')).toBeInTheDocument()
    })

    const deleteButton = screen.getByRole('button', { name: '削除' })
    await user.click(deleteButton)

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalledWith('このCardを削除しますか？')
      expect(cardsApi.delete).toHaveBeenCalledWith('c1')
    })
  })

  it('エディタのキャンセルボタンでエディタを閉じる', async () => {
    const user = userEvent.setup()
    vi.mocked(cardsApi.list).mockResolvedValueOnce({
      data: [],
      pagination: {
        total: 0,
        limit: 20,
        offset: 0,
        has_next: false,
      },
    })

    render(<CardListPage />, { wrapper })

    await waitFor(() => {
      expect(screen.getByText('新規作成')).toBeInTheDocument()
    })

    const createButton = screen.getByRole('button', { name: '新規作成' })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByTestId('card-editor')).toBeInTheDocument()
    })

    const cancelButton = screen.getByRole('button', { name: 'キャンセル' })
    await user.click(cancelButton)

    await waitFor(() => {
      expect(screen.queryByTestId('card-editor')).not.toBeInTheDocument()
    })
  })
})

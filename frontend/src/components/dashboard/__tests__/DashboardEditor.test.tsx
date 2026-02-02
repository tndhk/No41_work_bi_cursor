import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardEditor from '../DashboardEditor'

// react-grid-layout をモック
vi.mock('react-grid-layout', () => ({
  default: ({ children, onDragStop, onResizeStop, onLayoutChange }: any) => (
    <div data-testid="grid-layout">
      <button onClick={() => onLayoutChange?.([])}>Layout Change</button>
      <button onClick={() => onDragStop?.([{ i: 'c1', x: 1, y: 1, w: 4, h: 4 }])}>Drag Stop</button>
      <button onClick={() => onResizeStop?.([{ i: 'c1', x: 0, y: 0, w: 6, h: 6 }])}>Resize Stop</button>
      {children}
    </div>
  ),
}))

// CardContainer をモック
vi.mock('../CardContainer', () => ({
  default: ({ cardId }: any) => <div data-testid={`card-${cardId}`}>Card: {cardId}</div>,
}))

describe('DashboardEditor', () => {
  let queryClient: QueryClient
  const mockOnLayoutCommit = vi.fn()

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

  const mockCards = [
    { cardId: 'c1', x: 0, y: 0, w: 4, h: 4 },
    { cardId: 'c2', x: 4, y: 0, w: 4, h: 4 },
  ]

  it('グリッドレイアウトを表示する', () => {
    render(<DashboardEditor cards={mockCards} onLayoutCommit={mockOnLayoutCommit} />, { wrapper })

    expect(screen.getByTestId('grid-layout')).toBeInTheDocument()
    expect(screen.getByTestId('card-c1')).toBeInTheDocument()
    expect(screen.getByTestId('card-c2')).toBeInTheDocument()
  })

  it('空のカードリストを表示する', () => {
    render(<DashboardEditor cards={[]} onLayoutCommit={mockOnLayoutCommit} />, { wrapper })

    expect(screen.getByTestId('grid-layout')).toBeInTheDocument()
    expect(screen.queryByTestId('card-c1')).not.toBeInTheDocument()
  })

  it('ドラッグ停止時にonLayoutCommitを呼び出す', async () => {
    const user = userEvent.setup()

    render(<DashboardEditor cards={mockCards} onLayoutCommit={mockOnLayoutCommit} />, { wrapper })

    const dragStopButton = screen.getByRole('button', { name: 'Drag Stop' })
    await user.click(dragStopButton)

    expect(mockOnLayoutCommit).toHaveBeenCalled()
  })

  it('リサイズ停止時にonLayoutCommitを呼び出す', async () => {
    const user = userEvent.setup()

    render(<DashboardEditor cards={mockCards} onLayoutCommit={mockOnLayoutCommit} />, { wrapper })

    const resizeStopButton = screen.getByRole('button', { name: 'Resize Stop' })
    await user.click(resizeStopButton)

    expect(mockOnLayoutCommit).toHaveBeenCalled()
  })

  it('レイアウト変更時にステートを更新する', async () => {
    const user = userEvent.setup()

    render(<DashboardEditor cards={mockCards} onLayoutCommit={mockOnLayoutCommit} />, { wrapper })

    const layoutChangeButton = screen.getByRole('button', { name: 'Layout Change' })
    await user.click(layoutChangeButton)

    // レイアウト変更だけではonLayoutCommitは呼ばれない（ドラッグ/リサイズ停止時のみ）
    expect(mockOnLayoutCommit).not.toHaveBeenCalled()
  })

  it('カードIDをドラッグハンドルに表示する', () => {
    render(<DashboardEditor cards={mockCards} onLayoutCommit={mockOnLayoutCommit} />, { wrapper })

    expect(screen.getByText('c1')).toBeInTheDocument()
    expect(screen.getByText('c2')).toBeInTheDocument()
  })
})

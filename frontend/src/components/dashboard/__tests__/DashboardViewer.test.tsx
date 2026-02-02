import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import DashboardViewer from '../DashboardViewer'

// FilterBar, CardContainer, ChatbotPanel をモック
vi.mock('../FilterBar', () => ({
  default: ({ filters, values, onChange }: any) => (
    <div data-testid="filter-bar">
      <span>Filters: {filters.length}</span>
      <button onClick={() => onChange({ category: 'test' })}>Change Filter</button>
    </div>
  ),
}))

vi.mock('../CardContainer', () => ({
  default: ({ cardId, filters }: any) => (
    <div data-testid={`card-container-${cardId}`}>
      <span>Card: {cardId}</span>
      <span>Filters: {JSON.stringify(filters)}</span>
    </div>
  ),
}))

vi.mock('../../chatbot/ChatbotPanel', () => ({
  default: ({ dashboardId, isOpen, onClose }: any) => (
    isOpen ? (
      <div data-testid="chatbot-panel">
        <span>Chatbot for {dashboardId}</span>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null
  ),
}))

describe('DashboardViewer', () => {
  const mockDashboard = {
    dashboard_id: 'd1',
    name: 'Test Dashboard',
    layout: {
      cards: [
        { cardId: 'c1', x: 0, y: 0, w: 4, h: 4 },
        { cardId: 'c2', x: 4, y: 0, w: 4, h: 4 },
      ],
    },
    filters: [
      { name: 'category', type: 'string', column: 'category' },
    ],
    permission: 'owner',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('ダッシュボード名を表示する', () => {
    render(
      <MemoryRouter>
        <DashboardViewer dashboard={mockDashboard} />
      </MemoryRouter>
    )

    expect(screen.getByText('Test Dashboard')).toBeInTheDocument()
  })

  it('FilterBarを表示する', () => {
    render(
      <MemoryRouter>
        <DashboardViewer dashboard={mockDashboard} />
      </MemoryRouter>
    )

    expect(screen.getByTestId('filter-bar')).toBeInTheDocument()
  })

  it('カードコンテナを表示する', () => {
    render(
      <MemoryRouter>
        <DashboardViewer dashboard={mockDashboard} />
      </MemoryRouter>
    )

    expect(screen.getByTestId('card-container-c1')).toBeInTheDocument()
    expect(screen.getByTestId('card-container-c2')).toBeInTheDocument()
  })

  it('カードが空の場合にメッセージを表示する', () => {
    const emptyDashboard = {
      ...mockDashboard,
      layout: { cards: [] },
    }

    render(
      <MemoryRouter>
        <DashboardViewer dashboard={emptyDashboard} />
      </MemoryRouter>
    )

    expect(screen.getByText('カードがありません')).toBeInTheDocument()
  })

  it('チャットボタンでチャットパネルを開閉する', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <DashboardViewer dashboard={mockDashboard} />
      </MemoryRouter>
    )

    const chatButton = screen.getByLabelText('チャットを開く')
    expect(chatButton).toBeInTheDocument()

    await user.click(chatButton)

    expect(screen.getByTestId('chatbot-panel')).toBeInTheDocument()
    expect(screen.getByText('Chatbot for d1')).toBeInTheDocument()

    const closeButton = screen.getByRole('button', { name: 'Close' })
    await user.click(closeButton)

    expect(screen.queryByTestId('chatbot-panel')).not.toBeInTheDocument()
  })

  it('showEditLinkがtrueで権限がある場合に編集リンクを表示する', () => {
    render(
      <MemoryRouter>
        <DashboardViewer dashboard={mockDashboard} showEditLink={true} />
      </MemoryRouter>
    )

    const editLink = screen.getByRole('link', { name: '編集' })
    expect(editLink).toBeInTheDocument()
    expect(editLink).toHaveAttribute('href', '/dashboards/d1/edit')
  })

  it('showEditLinkがtrueでも権限がない場合に編集リンクを表示しない', () => {
    const viewerDashboard = {
      ...mockDashboard,
      permission: 'viewer',
    }

    render(
      <MemoryRouter>
        <DashboardViewer dashboard={viewerDashboard} showEditLink={true} />
      </MemoryRouter>
    )

    expect(screen.queryByRole('link', { name: '編集' })).not.toBeInTheDocument()
  })

  it('フィルタ変更時にCardContainerにフィルタを渡す', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <DashboardViewer dashboard={mockDashboard} />
      </MemoryRouter>
    )

    const changeFilterButton = screen.getByRole('button', { name: 'Change Filter' })
    await user.click(changeFilterButton)

    const cardContainer = screen.getByTestId('card-container-c1')
    expect(cardContainer).toHaveTextContent('Filters: {"category":"test"}')
  })
})

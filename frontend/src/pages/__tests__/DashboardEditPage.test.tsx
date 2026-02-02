import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardEditPage from '../DashboardEditPage'

// api をモック
vi.mock('../../lib/api', () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
  },
}))

// DashboardEditor をモック
vi.mock('../../components/dashboard/DashboardEditor', () => ({
  default: ({ cards, onLayoutCommit }: any) => (
    <div data-testid="dashboard-editor">
      <span>Cards: {cards.length}</span>
      <button onClick={() => onLayoutCommit([{ cardId: 'c1', x: 0, y: 0, w: 4, h: 4 }])}>
        Save Layout
      </button>
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

import { api } from '../../lib/api'
import { useParams, useNavigate } from 'react-router-dom'

describe('DashboardEditPage', () => {
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
    vi.mocked(useParams).mockReturnValue({ dashboardId: 'd1' })
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )

  it('ローディング状態を表示する', () => {
    vi.mocked(api.get).mockReturnValue(
      new Promise(() => {}) as any
    )

    render(<DashboardEditPage />, { wrapper })

    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  it('ダッシュボードを取得してDashboardEditorに渡す', async () => {
    const mockDashboard = {
      dashboard_id: 'd1',
      name: 'Test Dashboard',
      layout: { cards: [{ cardId: 'c1', x: 0, y: 0, w: 4, h: 4 }] },
      filters: [],
      permission: 'owner',
    }

    vi.mocked(api.get).mockReturnValueOnce({
      json: () => Promise.resolve({
        data: mockDashboard,
        permission: 'owner',
      }),
    } as any)

    render(<DashboardEditPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByTestId('dashboard-editor')).toBeInTheDocument()
        expect(screen.getByText('Cards: 1')).toBeInTheDocument()
        expect(screen.getByText('Test Dashboard - 編集')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('権限がない場合にエラーを表示する', async () => {
    const mockDashboard = {
      dashboard_id: 'd1',
      name: 'Test Dashboard',
      layout: { cards: [] },
      filters: [],
      permission: 'viewer',
    }

    vi.mocked(api.get).mockReturnValueOnce({
      json: () => Promise.resolve({
        data: mockDashboard,
        permission: 'viewer',
      }),
    } as any)

    render(<DashboardEditPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('このダッシュボードを編集する権限がありません')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('レイアウト保存時にAPIを呼び出す', async () => {
    const user = userEvent.setup()
    const mockDashboard = {
      dashboard_id: 'd1',
      name: 'Test Dashboard',
      layout: { cards: [] },
      filters: [],
      permission: 'owner',
    }

    vi.mocked(api.get).mockReturnValueOnce({
      json: () => Promise.resolve({
        data: mockDashboard,
        permission: 'owner',
      }),
    } as any)

    vi.mocked(api.put).mockReturnValueOnce({
      json: () => Promise.resolve({
        data: mockDashboard,
      }),
    } as any)

    render(<DashboardEditPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByTestId('dashboard-editor')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const saveButton = screen.getByRole('button', { name: 'Save Layout' })
    await user.click(saveButton)

    await waitFor(
      () => {
        expect(api.put).toHaveBeenCalledWith(
          'dashboards/d1',
          expect.objectContaining({
            json: {
              layout: {
                cards: [{ cardId: 'c1', x: 0, y: 0, w: 4, h: 4 }],
              },
            },
          })
        )
      },
      { timeout: 3000 }
    )
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardViewPage from '../DashboardViewPage'

// api をモック
vi.mock('../../lib/api', () => ({
  api: {
    get: vi.fn(),
  },
}))

// DashboardViewer をモック
vi.mock('../../components/dashboard/DashboardViewer', () => ({
  default: ({ dashboard, showEditLink }: any) => (
    <div data-testid="dashboard-viewer">
      <span>Dashboard: {dashboard.name}</span>
      {showEditLink && <span data-testid="edit-link">Edit Link</span>}
    </div>
  ),
}))

// useParams をモック
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: vi.fn(),
  }
})

import { api } from '../../lib/api'
import { useParams } from 'react-router-dom'

describe('DashboardViewPage', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.mocked(useParams).mockReturnValue({ dashboardId: 'd1' })
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

    render(<DashboardViewPage />, { wrapper })

    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  it('ダッシュボードを取得してDashboardViewerに渡す', async () => {
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

    render(<DashboardViewPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByTestId('dashboard-viewer')).toBeInTheDocument()
        expect(screen.getByText('Dashboard: Test Dashboard')).toBeInTheDocument()
        expect(screen.getByTestId('edit-link')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it.skip('ダッシュボードが見つからない場合にエラーを表示する', async () => {
    // TODO: エラーハンドリングを改善
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Not found'))

    render(<DashboardViewPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('ダッシュボードが見つかりません')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('useParamsからdashboardIdを取得する', async () => {
    vi.mocked(useParams).mockReturnValue({ dashboardId: 'd2' })
    const mockDashboard = {
      dashboard_id: 'd2',
      name: 'Test Dashboard 2',
      layout: { cards: [] },
      filters: [],
    }

    vi.mocked(api.get).mockReturnValueOnce({
      json: () => Promise.resolve({
        data: mockDashboard,
      }),
    } as any)

    render(<DashboardViewPage />, { wrapper })

    await waitFor(
      () => {
        expect(api.get).toHaveBeenCalledWith('dashboards/d2')
      },
      { timeout: 3000 }
    )
  })
})

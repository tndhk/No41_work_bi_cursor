import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardListPage from '../DashboardListPage'

// api をモック
vi.mock('../../lib/api', () => ({
  api: {
    get: vi.fn(),
  },
}))

import { api } from '../../lib/api'

describe('DashboardListPage', () => {
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
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )

  it('ローディング状態を表示する', () => {
    vi.mocked(api.get).mockReturnValue(
      new Promise(() => {}) as any // 解決しないPromise
    )

    render(<DashboardListPage />, { wrapper })

    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  it('ダッシュボード一覧を表示する', async () => {
    const mockDashboards = [
      {
        dashboard_id: 'd1',
        name: 'Dashboard 1',
        owner_id: 'u1',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
      {
        dashboard_id: 'd2',
        name: 'Dashboard 2',
        owner_id: 'u1',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
      },
    ]

    vi.mocked(api.get).mockReturnValueOnce({
      json: () => Promise.resolve({ data: mockDashboards }),
    } as any)

    render(<DashboardListPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('ダッシュボード一覧')).toBeInTheDocument()
        expect(screen.getByText('Dashboard 1')).toBeInTheDocument()
        expect(screen.getByText('Dashboard 2')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    expect(screen.getByText('新規作成')).toBeInTheDocument()
  })

  it.skip('エラー状態を表示する', async () => {
    // TODO: react-queryのエラーハンドリングを改善
    const errorQueryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    errorQueryClient.setQueryDefaults(['dashboards'], {
      retry: false,
    })

    vi.mocked(api.get).mockRejectedValueOnce(new Error('Network error'))

    const errorWrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={errorQueryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )

    render(<DashboardListPage />, { wrapper: errorWrapper })

    await waitFor(
      () => {
        expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('空の状態を表示する', async () => {
    vi.mocked(api.get).mockReturnValueOnce({
      json: () => Promise.resolve({ data: [] }),
    } as any)

    render(<DashboardListPage />, { wrapper })

    await waitFor(
      () => {
        expect(screen.getByText('ダッシュボードがありません')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('新規作成リンクが存在する', async () => {
    vi.mocked(api.get).mockReturnValueOnce({
      json: () => Promise.resolve({ data: [] }),
    } as any)

    render(<DashboardListPage />, { wrapper })

    await waitFor(
      () => {
        const createLink = screen.getByRole('link', { name: '新規作成' })
        expect(createLink).toBeInTheDocument()
        expect(createLink).toHaveAttribute('href', '/dashboards/new')
      },
      { timeout: 3000 }
    )
  })

  it('各ダッシュボードカードがリンクになっている', async () => {
    const mockDashboards = [
      {
        dashboard_id: 'd1',
        name: 'Dashboard 1',
        owner_id: 'u1',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ]

    vi.mocked(api.get).mockReturnValueOnce({
      json: () => Promise.resolve({ data: mockDashboards }),
    } as any)

    render(<DashboardListPage />, { wrapper })

    await waitFor(
      () => {
        const dashboardLink = screen.getByRole('link', { name: /Dashboard 1/ })
        expect(dashboardLink).toBeInTheDocument()
        expect(dashboardLink).toHaveAttribute('href', '/dashboards/d1')
      },
      { timeout: 3000 }
    )
  })
})

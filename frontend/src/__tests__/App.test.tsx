import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

// BrowserRouterをMemoryRouterに置き換える
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    BrowserRouter: ({ children }: any) => {
      const { MemoryRouter } = actual as any
      return <MemoryRouter>{children}</MemoryRouter>
    },
  }
})

// useAuthStore をモック
vi.mock('../stores/auth', () => ({
  useAuthStore: vi.fn(),
}))

// authApi をモック
vi.mock('../lib/api', () => ({
  authApi: {
    getMe: vi.fn(),
  },
}))

import { useAuthStore } from '../stores/auth'
import { authApi } from '../lib/api'

describe('App', () => {
  it('認証済みの場合、ダッシュボードを表示する', () => {
    const mockSetUser = vi.fn()
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: () => true,
      setUser: mockSetUser,
      setAuthChecked: vi.fn(),
      authChecked: true,
    } as any)

    vi.mocked(authApi.getMe).mockResolvedValue({
      user_id: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
    })

    render(<App />)
    
    // ダッシュボードが表示されることを確認（Layoutコンポーネントがレンダリングされる）
    expect(screen.getByText('社内BI・Pythonカード')).toBeInTheDocument()
  })

  it('未認証の場合、ログインページにリダイレクトする', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: () => false,
      setUser: vi.fn(),
      setAuthChecked: vi.fn(),
      authChecked: true,
    } as any)

    render(<App />)
    
    // ログインページが表示されることを確認
    expect(screen.getByText('ログインしてください')).toBeInTheDocument()
  })
})

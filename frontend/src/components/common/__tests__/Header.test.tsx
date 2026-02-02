import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Header from '../Header'

// useAuthStore をモック
vi.mock('../../../stores/auth', () => ({
  useAuthStore: vi.fn(),
}))

// useNavigate をモック
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: vi.fn(),
  }
})

// authApi をモック
vi.mock('../../../lib/api', () => ({
  authApi: {
    logout: vi.fn(),
  },
}))

import { useAuthStore } from '../../../stores/auth'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../../lib/api'

describe('Header', () => {
  const mockNavigate = vi.fn()
  const mockClearAuth = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)
  })

  it('ヘッダーを表示する', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
      clearAuth: mockClearAuth,
    } as any)

    render(<Header />)
    
    expect(screen.getByText('社内BI・Pythonカード')).toBeInTheDocument()
  })

  it('ユーザー情報がある場合、ユーザー名とログアウトボタンを表示する', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: {
        user_id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      },
      clearAuth: mockClearAuth,
    } as any)

    render(<Header />)
    
    expect(screen.getByText('Test User')).toBeInTheDocument()
    expect(screen.getByText('ログアウト')).toBeInTheDocument()
  })

  it('ログアウトボタンをクリックするとログアウト処理が実行される', async () => {
    const user = userEvent.setup()
    
    vi.mocked(useAuthStore).mockReturnValue({
      user: {
        user_id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      },
      clearAuth: mockClearAuth,
    } as any)

    vi.mocked(authApi.logout).mockResolvedValue(undefined)

    render(<Header />)
    
    const logoutButton = screen.getByText('ログアウト')
    await user.click(logoutButton)
    
    expect(authApi.logout).toHaveBeenCalled()
    expect(mockClearAuth).toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  it('ログアウトAPIでエラーが発生してもログアウト処理が実行される', async () => {
    const user = userEvent.setup()
    
    vi.mocked(useAuthStore).mockReturnValue({
      user: {
        user_id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      },
      clearAuth: mockClearAuth,
    } as any)

    vi.mocked(authApi.logout).mockRejectedValue(new Error('Network error'))

    render(<Header />)
    
    const logoutButton = screen.getByText('ログアウト')
    await user.click(logoutButton)
    
    expect(authApi.logout).toHaveBeenCalled()
    expect(mockClearAuth).toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })
})

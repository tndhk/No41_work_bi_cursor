import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from '../LoginPage'

// useAuthStore をモック
vi.mock('../../stores/auth', () => ({
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
vi.mock('../../lib/api', () => ({
  authApi: {
    login: vi.fn(),
  },
}))

import { useAuthStore } from '../../stores/auth'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../lib/api'

describe('LoginPage', () => {
  const mockNavigate = vi.fn()
  const mockSetUser = vi.fn()
  const mockSetAuthChecked = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)
    vi.mocked(useAuthStore).mockReturnValue({
      setUser: mockSetUser,
      setAuthChecked: mockSetAuthChecked,
    } as any)
  })

  it('ログインフォームを表示する', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    
    expect(screen.getByPlaceholderText('メールアドレス')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('パスワード')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ログイン/i })).toBeInTheDocument()
  })

  it('ログインに成功するとトークンとユーザー情報を保存してリダイレクトする', async () => {
    const user = userEvent.setup()
    
    const mockLoginResponse = {
      access_token: 'token-123',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        user_id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      },
    }

    vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    
    const emailInput = screen.getByPlaceholderText('メールアドレス')
    const passwordInput = screen.getByPlaceholderText('パスワード')
    const loginButton = screen.getByRole('button', { name: /ログイン/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(loginButton)

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
      expect(mockSetUser).toHaveBeenCalledWith(mockLoginResponse.user)
      expect(mockSetAuthChecked).toHaveBeenCalledWith(true)
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('ログインに失敗するとエラーメッセージを表示する', async () => {
    const user = userEvent.setup()
    
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid credentials'))

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    
    const emailInput = screen.getByPlaceholderText('メールアドレス')
    const passwordInput = screen.getByPlaceholderText('パスワード')
    const loginButton = screen.getByRole('button', { name: /ログイン/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrong-password')
    await user.click(loginButton)

    await waitFor(() => {
      // エラーメッセージが表示されることを確認（err.messageが表示される）
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })
})

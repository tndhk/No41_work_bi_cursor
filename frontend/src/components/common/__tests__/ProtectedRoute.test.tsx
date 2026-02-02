import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ProtectedRoute from '../ProtectedRoute'

// useAuthStore をモック
vi.mock('../../../stores/auth', () => ({
  useAuthStore: vi.fn(),
}))

import { useAuthStore } from '../../../stores/auth'

describe('ProtectedRoute', () => {
  it('認証済みの場合、childrenをレンダリングする', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: () => true,
    } as any)

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    )
    
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('未認証の場合、ログインページにリダイレクトする', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: () => false,
    } as any)

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    )
    
    // リダイレクトが発生するため、Protected Contentは表示されない
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })
})

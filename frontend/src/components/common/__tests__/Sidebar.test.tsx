import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Sidebar from '../Sidebar'

// useLocation をモック
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useLocation: vi.fn(),
  }
})

import { useLocation } from 'react-router-dom'

describe('Sidebar', () => {
  it('ナビゲーションリンクを表示する', () => {
    vi.mocked(useLocation).mockReturnValue({
      pathname: '/',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    } as any)

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )
    
    expect(screen.getByText('ダッシュボード')).toBeInTheDocument()
    expect(screen.getByText('Dataset管理')).toBeInTheDocument()
    expect(screen.getByText('Card管理')).toBeInTheDocument()
    expect(screen.getByText('Transform管理')).toBeInTheDocument()
  })

  it('アクティブなリンクにスタイルが適用される', () => {
    vi.mocked(useLocation).mockReturnValue({
      pathname: '/datasets',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    } as any)

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )
    
    const datasetLink = screen.getByText('Dataset管理').closest('a')
    expect(datasetLink).toHaveClass('bg-indigo-50', 'text-indigo-700')
  })

  it('非アクティブなリンクにスタイルが適用される', () => {
    vi.mocked(useLocation).mockReturnValue({
      pathname: '/datasets',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    } as any)

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )
    
    const dashboardLink = screen.getByText('ダッシュボード').closest('a')
    expect(dashboardLink).toHaveClass('text-gray-700', 'hover:bg-gray-50')
    expect(dashboardLink).not.toHaveClass('bg-indigo-50', 'text-indigo-700')
  })
})

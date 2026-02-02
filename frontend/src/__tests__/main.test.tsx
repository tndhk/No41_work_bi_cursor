import { describe, it, expect, vi, beforeEach } from 'vitest'

// ReactDOM をモック
vi.mock('react-dom/client', () => ({
  default: {
    createRoot: vi.fn(() => ({
      render: vi.fn(),
    })),
  },
}))

// App をモック
vi.mock('../App', () => ({
  default: () => <div>App</div>,
}))

describe('main', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // document.getElementById をモック
    document.getElementById = vi.fn().mockReturnValue(document.createElement('div'))
  })

  it('エントリーポイントが存在する', async () => {
    // main.tsx をインポート
    await import('../main')
    
    expect(document.getElementById).toHaveBeenCalledWith('root')
  })
})

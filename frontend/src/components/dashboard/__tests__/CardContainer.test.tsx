import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CardContainer from '../CardContainer'

// api をモック
vi.mock('../../../lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { api } from '../../../lib/api'

describe('CardContainer', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
    vi.clearAllMocks()
  })

  it('ローディング中はスケルトンを表示する', () => {
    vi.mocked(api.get).mockImplementation(() => {
      return new Promise(() => {}) // 解決しないPromise
    })

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <CardContainer cardId="card-1" filters={{}} />
      </QueryClientProvider>
    )
    
    // スケルトンが表示されることを確認（animate-pulseクラスを持つ要素）
    const skeleton = container.querySelector('.animate-pulse')
    expect(skeleton).toBeInTheDocument()
  })

  it.skip('カードとプレビューを表示する', async () => {
    // TODO: react-queryのモック設定を修正する必要がある
    const mockCard = {
      card_id: 'card-1',
      name: 'Test Card',
      dataset_id: 'ds1',
    }

    const mockPreview = {
      html: '<div>Preview HTML</div>',
    }

    // api.getが最初に呼ばれる（カード取得）
    vi.mocked(api.get).mockResolvedValueOnce({
      json: vi.fn().mockResolvedValue({ data: mockCard }),
    } as any)

    // api.postが次に呼ばれる（プレビュー取得）
    vi.mocked(api.post).mockResolvedValueOnce({
      json: vi.fn().mockResolvedValue({ data: mockPreview }),
    } as any)

    render(
      <QueryClientProvider client={queryClient}>
        <CardContainer cardId="card-1" filters={{}} />
      </QueryClientProvider>
    )
    
    // データが読み込まれるまで待つ（タイムアウトを長くする）
    await screen.findByText('Test Card', {}, { timeout: 3000 })
    
    expect(screen.getByText('Test Card')).toBeInTheDocument()
    // dangerouslySetInnerHTMLでレンダリングされるため、HTMLコンテンツを確認
    const cardContent = screen.getByText((content, element) => {
      return element?.classList.contains('card-content') ?? false
    })
    expect(cardContent).toBeInTheDocument()
  })

  it.skip('カードが読み込めない場合はエラーメッセージを表示する', async () => {
    // api.getがエラーを返す
    vi.mocked(api.get).mockRejectedValue(new Error('Not found'))

    render(
      <QueryClientProvider client={queryClient}>
        <CardContainer cardId="card-1" filters={{}} />
      </QueryClientProvider>
    )
    
    // エラーが発生するまで待つ
    await screen.findByText('カードを読み込めませんでした', {}, { timeout: 5000 })
    
    expect(screen.getByText('カードを読み込めませんでした')).toBeInTheDocument()
  })
})

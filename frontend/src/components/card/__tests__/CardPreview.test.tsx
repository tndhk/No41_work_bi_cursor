import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CardPreview from '../CardPreview'
import { createTestQueryClient, createQueryWrapper } from '../../../test-utils/setup'

vi.mock('../../../lib/cards', () => ({
  cardsApi: {
    preview: vi.fn(),
  },
}))

vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string) => html,
  },
}))

import { cardsApi } from '../../../lib/cards'

describe('CardPreview', () => {
  let queryClient: ReturnType<typeof createTestQueryClient>
  let wrapper: ReturnType<typeof createQueryWrapper>

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = createTestQueryClient()
    wrapper = createQueryWrapper(queryClient)
  })

  it('プレビューUIを表示する', () => {
    render(<CardPreview card_id="c1" />, { wrapper })

    expect(screen.getByText('プレビュー')).toBeInTheDocument()
    expect(screen.getByLabelText(/フィルタ値/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'プレビュー実行' })).toBeInTheDocument()
  })

  it('有効なJSONフィルタでプレビューを実行する', async () => {
    const user = userEvent.setup()
    const mockPreview = {
      html: '<div>Preview HTML</div>',
      used_columns: ['col1'],
      filter_applicable: ['category'],
    }

    vi.mocked(cardsApi.preview).mockResolvedValueOnce(mockPreview)

    render(<CardPreview card_id="c1" />, { wrapper })

    const filterInput = screen.getByLabelText(/フィルタ値/) as HTMLInputElement
    await user.clear(filterInput)
    await user.paste('{"category": "A"}')

    const previewButton = screen.getByRole('button', { name: 'プレビュー実行' })
    await user.click(previewButton)

    await waitFor(
      () => {
        expect(cardsApi.preview).toHaveBeenCalledWith('c1', {
          filters: { category: 'A' },
        })
        expect(screen.getByText('Preview HTML')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('無効なJSONフィルタでエラーを表示する', async () => {
    render(<CardPreview card_id="c1" />, { wrapper })

    const filterInput = screen.getByLabelText(/フィルタ値/) as HTMLTextAreaElement
    fireEvent.change(filterInput, { target: { value: '{invalid json}' } })

    await waitFor(
      () => {
        expect(filterInput).toHaveAttribute('aria-invalid', 'true')
      },
      { timeout: 3000 }
    )
  })

  it('プレビュー実行中にローディング状態を表示する', async () => {
    const user = userEvent.setup()

    vi.mocked(cardsApi.preview).mockImplementation(() => new Promise(() => {}))

    render(<CardPreview card_id="c1" />, { wrapper })

    const previewButton = screen.getByRole('button', { name: 'プレビュー実行' })
    await user.click(previewButton)

    await waitFor(
      () => {
        expect(screen.getByText('実行中...')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: '実行中...' })).toBeDisabled()
      },
      { timeout: 3000 }
    )
  })

  it('プレビューエラー時にエラーメッセージを表示する', async () => {
    const user = userEvent.setup()

    vi.mocked(cardsApi.preview).mockRejectedValueOnce(new Error('Preview failed'))

    render(<CardPreview card_id="c1" />, { wrapper })

    const previewButton = screen.getByRole('button', { name: 'プレビュー実行' })
    await user.click(previewButton)

    await waitFor(
      () => {
        expect(screen.getByText('Preview failed')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })
})

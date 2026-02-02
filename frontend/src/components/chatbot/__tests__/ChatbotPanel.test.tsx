import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChatbotPanel from '../ChatbotPanel'

vi.mock('../../../stores/auth', () => ({
  useAuthStore: vi.fn(),
}))

import { useAuthStore } from '../../../stores/auth'

describe('ChatbotPanel', () => {
  const defaultProps = {
    dashboardId: 'd1',
    isOpen: true,
    onClose: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAuthStore).mockReturnValue('test-token' as any)
    global.fetch = vi.fn()
    Element.prototype.scrollIntoView = vi.fn()
  })

  it('閉じている時は何も表示しない', () => {
    const { container } = render(<ChatbotPanel {...defaultProps} isOpen={false} />)

    expect(container).toBeEmptyDOMElement()
  })

  it('開いている時はチャットUIを表示する', () => {
    render(<ChatbotPanel {...defaultProps} />)

    expect(screen.getByPlaceholderText(/データについて質問してください/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /送信/ })).toBeInTheDocument()
  })

  it('閉じるボタンでonCloseを呼び出す', async () => {
    const user = userEvent.setup()
    const mockOnClose = vi.fn()

    render(<ChatbotPanel {...defaultProps} onClose={mockOnClose} />)

    const closeButton = screen.getByLabelText(/閉じる/)
    await user.click(closeButton)

    expect(mockOnClose).toHaveBeenCalled()
  })

  it('メッセージを送信できる', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      answer: 'This is a response',
    }

    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    } as any)

    render(<ChatbotPanel {...defaultProps} />)

    const input = screen.getByPlaceholderText(/データについて質問してください/)
    await user.type(input, 'Test question')

    const sendButton = screen.getByRole('button', { name: /送信/ })
    await user.click(sendButton)

    await waitFor(
      () => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/dashboards/d1/chat'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              Authorization: 'Bearer test-token',
            }),
            body: expect.stringContaining('Test question'),
          })
        )
        expect(screen.getByText('Test question')).toBeInTheDocument()
        expect(screen.getByText('This is a response')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('エラー時にエラーメッセージを表示する', async () => {
    const user = userEvent.setup()

    vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Network error'))

    render(<ChatbotPanel {...defaultProps} />)

    const input = screen.getByPlaceholderText(/データについて質問してください/)
    await user.type(input, 'Test question')

    const sendButton = screen.getByRole('button', { name: /送信/ })
    await user.click(sendButton)

    await waitFor(
      () => {
        const errorMessages = screen.getAllByText(/Network error/)
        expect(errorMessages.length).toBeGreaterThan(0)
      },
      { timeout: 3000 }
    )
  })

  it('空のメッセージは送信できない', async () => {
    const user = userEvent.setup()

    render(<ChatbotPanel {...defaultProps} />)

    const sendButton = screen.getByRole('button', { name: /送信/ })
    await user.click(sendButton)

    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('ローディング中は送信できない', async () => {
    const user = userEvent.setup()

    vi.mocked(global.fetch).mockImplementation(() => new Promise(() => {}))

    render(<ChatbotPanel {...defaultProps} />)

    const input = screen.getByPlaceholderText(/データについて質問してください/)
    await user.type(input, 'First message')

    const sendButton = screen.getByRole('button', { name: /送信/ })
    await user.click(sendButton)

    // 2回目の送信は無視される
    await user.type(input, 'Second message')
    await user.click(sendButton)

    expect(global.fetch).toHaveBeenCalledTimes(1)
  })
})

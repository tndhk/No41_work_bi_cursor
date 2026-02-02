import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DatasetImport from '../DatasetImport'
import { createTestQueryClient, createQueryWrapper, mockDataset, getFileInput } from '../../../test-utils/setup'

vi.mock('../../../lib/datasets', () => ({
  datasetsApi: {
    create: vi.fn(),
    s3Import: vi.fn(),
  },
}))

import { datasetsApi } from '../../../lib/datasets'

describe('DatasetImport', () => {
  let queryClient: ReturnType<typeof createTestQueryClient>
  let wrapper: ReturnType<typeof createQueryWrapper>
  const mockOnSuccess = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = createTestQueryClient()
    wrapper = createQueryWrapper(queryClient)
  })

  it('ローカルファイルインポートUIを表示する', () => {
    render(<DatasetImport onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, { wrapper })

    expect(screen.getByText(/Dataset取り込み/)).toBeInTheDocument()
    expect(screen.getByText(/名前/)).toBeInTheDocument()
    expect(screen.getByText(/ファイルを選択/)).toBeInTheDocument()
  })

  it('ファイルを選択できる', async () => {
    const user = userEvent.setup()
    const file = new File(['col1,col2\nval1,val2'], 'test.csv', { type: 'text/csv' })

    render(<DatasetImport onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, { wrapper })

    const fileInput = getFileInput()
    await user.upload(fileInput, file)

    expect(fileInput.files?.[0]).toBe(file)
    expect(screen.getByText('test.csv')).toBeInTheDocument()
  })

  it('ローカルファイルアップロードを実行する', async () => {
    const user = userEvent.setup()
    const file = new File(['col1,col2\nval1,val2'], 'test.csv', { type: 'text/csv' })
    const testDataset = {
      ...mockDataset,
      dataset_id: 'd1',
      name: 'Test Dataset',
      row_count: 1,
      column_count: 2,
    }

    vi.mocked(datasetsApi.create).mockResolvedValueOnce(testDataset)

    render(<DatasetImport onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, { wrapper })

    const fileInput = getFileInput()
    await user.upload(fileInput, file)

    const inputs = screen.getAllByRole('textbox')
    const nameInput = inputs[0]
    await user.type(nameInput, 'Test Dataset')

    const submitButton = screen.getByRole('button', { name: /取り込み/ })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(datasetsApi.create).toHaveBeenCalledWith(
          file,
          expect.objectContaining({
            name: 'Test Dataset',
          })
        )
        expect(mockOnSuccess).toHaveBeenCalled()
      },
      { timeout: 3000 }
    )
  })

  it('S3インポートに切り替える', async () => {
    const user = userEvent.setup()

    render(<DatasetImport onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, { wrapper })

    const s3Tab = screen.getByRole('button', { name: /S3/ })
    await user.click(s3Tab)

    await waitFor(
      () => {
        expect(screen.getByText(/S3バケット/)).toBeInTheDocument()
        expect(screen.getByText(/S3キー/)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })

  it('S3インポートを実行する', async () => {
    const user = userEvent.setup()
    const testDataset = {
      ...mockDataset,
      dataset_id: 'd1',
      name: 'S3 Dataset',
      source_type: 's3',
      row_count: 0,
      column_count: 0,
    }

    vi.mocked(datasetsApi.s3Import).mockResolvedValueOnce(testDataset)

    render(<DatasetImport onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, { wrapper })

    const s3Tab = screen.getByRole('button', { name: /S3/ })
    await user.click(s3Tab)

    await waitFor(
      () => {
        expect(screen.getByText(/S3バケット/)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    const inputs = screen.getAllByRole('textbox')
    const nameInput = inputs[0]
    await user.type(nameInput, 'S3 Dataset')

    const bucketInput = inputs[1]
    await user.type(bucketInput, 'my-bucket')

    const keyInput = inputs[2]
    await user.type(keyInput, 'data/file.csv')

    const submitButton = screen.getByRole('button', { name: /取り込み/ })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(datasetsApi.s3Import).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'S3 Dataset',
            bucket: 'my-bucket',
            key: 'data/file.csv',
          })
        )
        expect(mockOnSuccess).toHaveBeenCalled()
      },
      { timeout: 3000 }
    )
  })

  it('キャンセルボタンでonCancelを呼び出す', async () => {
    const user = userEvent.setup()

    render(<DatasetImport onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, { wrapper })

    const cancelButton = screen.getByRole('button', { name: /キャンセル/ })
    await user.click(cancelButton)

    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('バリデーションエラーを表示する', async () => {
    const user = userEvent.setup()
    const file = new File(['col1,col2\nval1,val2'], 'test.csv', { type: 'text/csv' })

    render(<DatasetImport onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, { wrapper })

    const fileInput = getFileInput()
    await user.upload(fileInput, file)

    const submitButton = screen.getByRole('button', { name: /取り込み/ })
    await user.click(submitButton)

    await waitFor(
      () => {
        expect(screen.getByText(/名前は必須です/)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
  })
})

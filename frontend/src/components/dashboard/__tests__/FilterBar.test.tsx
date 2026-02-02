import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FilterBar from '../FilterBar'

describe('FilterBar', () => {
  it('フィルタがない場合は何も表示しない', () => {
    const { container } = render(
      <FilterBar filters={[]} values={{}} onChange={vi.fn()} />
    )
    
    expect(container.firstChild).toBeNull()
  })

  it('フィルタを表示する', () => {
    const filters = [
      { name: 'Category', type: 'category', column: 'category' },
      { name: 'Date', type: 'date', column: 'date' },
    ]
    
    render(
      <FilterBar filters={filters} values={{}} onChange={vi.fn()} />
    )
    
    expect(screen.getByText('フィルタ')).toBeInTheDocument()
    expect(screen.getByLabelText('Category')).toBeInTheDocument()
    expect(screen.getByLabelText('Date')).toBeInTheDocument()
  })

  it('categoryタイプのフィルタに値を入力できる', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const filters = [
      { name: 'Category', type: 'category', column: 'category' },
    ]
    
    render(
      <FilterBar filters={filters} values={{}} onChange={onChange} />
    )
    
    const input = screen.getByLabelText('Category')
    await user.type(input, 'Test')
    
    // userEvent.typeは1文字ずつ入力するため、onChangeが呼ばれることを確認
    expect(onChange).toHaveBeenCalled()
  })

  it('dateタイプのフィルタに値を入力できる', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const filters = [
      { name: 'Date', type: 'date', column: 'date' },
    ]
    
    render(
      <FilterBar filters={filters} values={{}} onChange={onChange} />
    )
    
    const input = screen.getByLabelText('Date') as HTMLInputElement
    await user.type(input, '2024-01-01')
    
    expect(onChange).toHaveBeenCalled()
  })

  it('既存の値を表示する', () => {
    const filters = [
      { name: 'Category', type: 'category', column: 'category' },
    ]
    
    render(
      <FilterBar filters={filters} values={{ Category: 'Existing Value' }} onChange={vi.fn()} />
    )
    
    const input = screen.getByLabelText('Category') as HTMLInputElement
    expect(input.value).toBe('Existing Value')
  })
})

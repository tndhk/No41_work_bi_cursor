import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import CardList from '../CardList'
import type { Card } from '../../../lib/cards'

const mockCards: Card[] = [
  {
    card_id: 'c1',
    name: 'Test Card',
    owner_id: 'user1',
    dataset_id: 'ds1',
    code: 'def render(...): pass',
    params: {},
    used_columns: ['col1', 'col2'],
    filter_applicable: ['category'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

describe('CardList', () => {
  it('renders empty state when no cards', () => {
    render(
      <CardList
        cards={[]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onPageChange={vi.fn()}
      />
    )
    expect(screen.getByText('Cardがありません')).toBeInTheDocument()
  })

  it('renders card list', () => {
    render(
      <CardList
        cards={mockCards}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onPageChange={vi.fn()}
      />
    )
    expect(screen.getByText('Test Card')).toBeInTheDocument()
    expect(screen.getByText('Dataset ID: ds1')).toBeInTheDocument()
  })
})

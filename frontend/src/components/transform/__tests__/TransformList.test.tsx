import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import TransformList from '../TransformList'
import type { Transform } from '../../../lib/transforms'

const mockTransforms: Transform[] = [
  {
    transform_id: 't1',
    name: 'Test Transform',
    owner_id: 'user1',
    code: 'def transform(...): pass',
    input_dataset_ids: ['ds1', 'ds2'],
    output_dataset_id: 'ds3',
    params: {},
    schedule: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    last_executed_at: null,
  },
]

describe('TransformList', () => {
  it('renders empty state when no transforms', () => {
    render(
      <TransformList
        transforms={[]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onPageChange={vi.fn()}
      />
    )
    expect(screen.getByText('Transformがありません')).toBeInTheDocument()
  })

  it('renders transform list', () => {
    render(
      <TransformList
        transforms={mockTransforms}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onPageChange={vi.fn()}
      />
    )
    expect(screen.getByText('Test Transform')).toBeInTheDocument()
    expect(screen.getByText('入力Dataset数: 2')).toBeInTheDocument()
  })
})

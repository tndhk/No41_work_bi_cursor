import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import DatasetList from '../DatasetList'
import type { Dataset } from '../../../lib/datasets'

const mockDatasets: Dataset[] = [
  {
    dataset_id: 'ds1',
    name: 'Test Dataset 1',
    owner_id: 'user1',
    source_type: 'local_csv',
    source_config: {},
    schema: [],
    row_count: 100,
    column_count: 5,
    s3_path: 's3://bucket/ds1',
    partition_column: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    last_import_at: null,
    last_import_by: null,
  },
]

describe('DatasetList', () => {
  it('renders empty state when no datasets', () => {
    render(
      <MemoryRouter>
        <DatasetList
          datasets={[]}
          onDelete={vi.fn()}
          onPageChange={vi.fn()}
        />
      </MemoryRouter>
    )
    expect(screen.getByText('Datasetがありません')).toBeInTheDocument()
  })

  it('renders dataset list', () => {
    render(
      <MemoryRouter>
        <DatasetList
          datasets={mockDatasets}
          onDelete={vi.fn()}
          onPageChange={vi.fn()}
        />
      </MemoryRouter>
    )
    expect(screen.getByText('Test Dataset 1')).toBeInTheDocument()
    expect(screen.getByText('行数: 100')).toBeInTheDocument()
    expect(screen.getByText('列数: 5')).toBeInTheDocument()
  })
})

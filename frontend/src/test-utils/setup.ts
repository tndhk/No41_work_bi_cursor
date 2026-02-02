import { QueryClient } from '@tanstack/react-query'
import { QueryClientProvider } from '@tanstack/react-query'
import React, { type ReactNode } from 'react'
import type { Card, CardListResponse } from '../lib/cards'
import type { Dataset, DatasetListResponse } from '../lib/datasets'
import type { Transform, TransformListResponse } from '../lib/transforms'

export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

export function createQueryWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children)
  }
}

export const mockCard: Card = {
  card_id: 'c1',
  name: 'Test Card',
  owner_id: 'u1',
  dataset_id: 'd1',
  code: 'print("test")',
  params: {},
  used_columns: [],
  filter_applicable: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

export const mockDataset: Dataset = {
  dataset_id: 'd1',
  name: 'Test Dataset',
  owner_id: 'u1',
  source_type: 'file',
  source_config: {},
  schema: [],
  row_count: 100,
  column_count: 5,
  s3_path: 's3://bucket/key',
  partition_column: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  last_import_at: null,
  last_import_by: null,
}

export const mockTransform: Transform = {
  transform_id: 't1',
  name: 'Test Transform',
  owner_id: 'u1',
  code: 'SELECT * FROM dataset',
  input_dataset_ids: ['d1'],
  output_dataset_id: null,
  params: {},
  schedule: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  last_executed_at: null,
}

export function createMockCardListResponse(data: Card[] = [mockCard]): CardListResponse {
  return {
    data,
    pagination: { total: data.length, limit: 10, offset: 0, has_next: false },
  }
}

export function createMockDatasetListResponse(data: Dataset[] = [mockDataset]): DatasetListResponse {
  return {
    data,
    pagination: { total: data.length, limit: 10, offset: 0, has_next: false },
  }
}

export function createMockTransformListResponse(data: Transform[] = [mockTransform]): TransformListResponse {
  return {
    data,
    pagination: { total: data.length, limit: 10, offset: 0, has_next: false },
  }
}

export function getFileInput(): HTMLInputElement {
  const input = document.querySelector('input[type="file"]')
  if (!input) {
    throw new Error('File input not found')
  }
  return input as HTMLInputElement
}

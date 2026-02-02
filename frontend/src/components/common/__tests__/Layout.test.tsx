import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Layout from '../Layout'

describe('Layout', () => {
  it('childrenをレンダリングする', () => {
    render(
      <MemoryRouter>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </MemoryRouter>
    )
    
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('複数のchildrenをレンダリングする', () => {
    render(
      <MemoryRouter>
        <Layout>
          <div>First Content</div>
          <div>Second Content</div>
        </Layout>
      </MemoryRouter>
    )
    
    expect(screen.getByText('First Content')).toBeInTheDocument()
    expect(screen.getByText('Second Content')).toBeInTheDocument()
  })
})

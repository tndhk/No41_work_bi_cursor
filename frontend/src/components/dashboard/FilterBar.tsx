import { useState } from 'react'

interface Filter {
  name: string
  type: string
  column: string
}

interface FilterBarProps {
  filters: Filter[]
  values: Record<string, any>
  onChange: (values: Record<string, any>) => void
}

export default function FilterBar({ filters, values, onChange }: FilterBarProps) {
  const handleFilterChange = (name: string, value: any) => {
    onChange({ ...values, [name]: value })
  }

  if (filters.length === 0) {
    return null
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">フィルタ</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filters.map((filter) => {
          const inputId = `filter-${filter.name}`
          return (
            <div key={filter.name}>
              <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
                {filter.name}
              </label>
              {filter.type === 'category' && (
                <input
                  id={inputId}
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  value={values[filter.name] || ''}
                  onChange={(e) => handleFilterChange(filter.name, e.target.value)}
                  placeholder="値を入力"
                />
              )}
              {filter.type === 'date' && (
                <input
                  id={inputId}
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  value={values[filter.name] || ''}
                  onChange={(e) => handleFilterChange(filter.name, e.target.value)}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

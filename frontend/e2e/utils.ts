import { APIRequestContext } from '@playwright/test'

const API_BASE_URL = process.env.API_URL || 'http://localhost:8000'

export interface TestSetupData {
  email: string
  password: string
  dashboard_id: string
  dashboard_name: string
  filter_name: string
}

export async function setupTestData(
  request: APIRequestContext
): Promise<TestSetupData> {
  const response = await request.post(`${API_BASE_URL}/api/test/setup`)
  
  if (!response.ok()) {
    const errorText = await response.text()
    throw new Error(
      `Failed to setup test data: ${response.status()} ${errorText}`
    )
  }
  
  const data = await response.json()
  
  return {
    email: data.email,
    password: data.password,
    dashboard_id: data.dashboard_id,
    dashboard_name: data.dashboard_name,
    filter_name: data.filter_name,
  }
}

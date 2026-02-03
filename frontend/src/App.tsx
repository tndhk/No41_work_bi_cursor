import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/common/Layout'
import ProtectedRoute from './components/common/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import DashboardListPage from './pages/DashboardListPage'
import DashboardViewPage from './pages/DashboardViewPage'
import DashboardEditPage from './pages/DashboardEditPage'
import DatasetListPage from './pages/DatasetListPage'
import DatasetDetailPage from './pages/DatasetDetailPage'
import TransformListPage from './pages/TransformListPage'
import CardListPage from './pages/CardListPage'
import { useAuthStore } from './stores/auth'
import { authApi } from './lib/api'

const queryClient = new QueryClient()

function AppContent(): JSX.Element {
  const { setUser, setAuthChecked } = useAuthStore()

  useEffect(() => {
    authApi.getMe()
      .then((user) => setUser(user))
      .catch(() => {
        // 認証エラー時はapi.tsで処理
      })
      .finally(() => {
        setAuthChecked(true)
      })
  }, [setAuthChecked, setUser])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboards" replace />} />
          <Route path="dashboards" element={<DashboardListPage />} />
          <Route path="dashboards/:dashboardId" element={<DashboardViewPage />} />
          <Route path="dashboards/:dashboardId/edit" element={<DashboardEditPage />} />
          <Route path="datasets" element={<DatasetListPage />} />
          <Route path="datasets/:datasetId" element={<DatasetDetailPage />} />
          <Route path="cards" element={<CardListPage />} />
          <Route path="transforms" element={<TransformListPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}

export default App

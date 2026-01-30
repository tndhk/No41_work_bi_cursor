import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect } from 'react'
import Layout from './components/common/Layout'
import ProtectedRoute from './components/common/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import DashboardListPage from './pages/DashboardListPage'
import DashboardViewPage from './pages/DashboardViewPage'
import { useAuthStore } from './stores/auth'
import { authApi } from './lib/api'

const queryClient = new QueryClient()

function AppContent() {
  const { token, setUser } = useAuthStore()

  useEffect(() => {
    // トークンがある場合、ユーザ情報を取得
    if (token) {
      authApi.getMe()
        .then((user) => setUser(user))
        .catch(() => {
          // エラー時は何もしない（認証エラーはapi.tsで処理）
        })
    }
  }, [token, setUser])

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
          <Route path="datasets" element={<div className="p-6"><h2 className="text-2xl font-bold">Dataset管理</h2><p className="mt-4 text-gray-600">実装予定...</p></div>} />
          <Route path="cards" element={<div className="p-6"><h2 className="text-2xl font-bold">Card管理</h2><p className="mt-4 text-gray-600">実装予定...</p></div>} />
          <Route path="transforms" element={<div className="p-6"><h2 className="text-2xl font-bold">Transform管理</h2><p className="mt-4 text-gray-600">実装予定...</p></div>} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}

export default App

import { useAuthStore } from '../../stores/auth'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../lib/api'

export default function Header() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch (err) {
      // エラーは無視
    }
    clearAuth()
    navigate('/login')
  }

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              社内BI・Pythonカード
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            {user && (
              <>
                <span className="text-sm text-gray-700">{user.name}</span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  ログアウト
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

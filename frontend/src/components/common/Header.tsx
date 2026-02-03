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
    <header className="sticky top-0 z-10 border-b border-border bg-panel/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-2xl bg-accent-soft text-accent flex items-center justify-center text-base font-semibold">
            BI
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-text sm:text-xl">
              社内BI・Pythonカード
            </h1>
            <p className="text-xs text-text-muted">Data workspace</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
            {user && (
              <>
                <span className="text-sm font-medium text-text">
                  {user.name}
                </span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-text-muted hover:text-text"
                >
                  ログアウト
                </button>
              </>
            )}
        </div>
      </div>
    </header>
  )
}

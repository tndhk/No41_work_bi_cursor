import { Link, useLocation } from 'react-router-dom'

const navigation = [
  { name: 'ダッシュボード', href: '/', icon: '📊' },
  { name: 'Dataset管理', href: '/datasets', icon: '📁' },
  { name: 'Card管理', href: '/cards', icon: '🎴' },
  { name: 'Transform管理', href: '/transforms', icon: '🔄' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-screen">
      <nav className="p-4">
        <ul className="space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className={`flex items-center px-4 py-2 text-sm font-medium rounded-md ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.name}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
    </aside>
  )
}

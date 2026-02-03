import { Link, useLocation } from 'react-router-dom'

const DashboardIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M3 3h8v8H3zM13 3h8v5h-8zM13 10h8v11h-8zM3 13h8v8H3z" />
  </svg>
)

const DatasetIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z" />
    <path d="M4 12c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z" />
    <path d="M4 18c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z" />
  </svg>
)

const CardIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="3" y="5" width="18" height="14" rx="3" />
    <path d="M7 9h10M7 13h6" />
  </svg>
)

const TransformIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M7 7h10l-2.5-2.5M17 17H7l2.5 2.5" />
    <path d="M7 7a7 7 0 0 0-2 5M17 17a7 7 0 0 0 2-5" />
  </svg>
)

const navigation = [
  { name: 'ダッシュボード', href: '/', icon: DashboardIcon },
  { name: 'Dataset管理', href: '/datasets', icon: DatasetIcon },
  { name: 'Card管理', href: '/cards', icon: CardIcon },
  { name: 'Transform管理', href: '/transforms', icon: TransformIcon },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-full border-b border-border bg-panel md:w-60 md:border-b-0 md:border-r md:min-h-[calc(100vh-4rem)]">
      <nav className="p-4">
        <ul className="space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            const Icon = item.icon
            return (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className={`group flex items-center gap-3 rounded-xl border border-transparent px-3 py-2 text-sm font-medium transition ${
                    isActive
                      ? 'bg-accent-soft text-accent shadow-card'
                      : 'text-text-muted hover:text-text hover:bg-muted'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
    </aside>
  )
}

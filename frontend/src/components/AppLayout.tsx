import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiFetch } from '../api/client'

interface AppLayoutProps {
  children: ReactNode
}

interface NavItem {
  to: string
  label: string
  end?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/network-types', label: 'Network Types' },
  { to: '/networks', label: 'Networks' },
]

function Sidebar() {
  return (
    <nav className="w-56 shrink-0 bg-gray-900 border-r border-gray-700 flex flex-col py-4">
      {NAV_ITEMS.map(({ to, label, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            [
              'px-4 py-2.5 text-sm font-medium transition-colors',
              isActive
                ? 'bg-indigo-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800',
            ].join(' ')
          }
        >
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

export function AppLayout({ children }: AppLayoutProps) {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    try {
      await apiFetch('/api/v1/auth/logout/', { method: 'POST' })
    } catch {
      // best-effort
    }
    setUser(null)
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-950 text-white">
      {/* Top header */}
      <header className="flex items-center justify-between px-6 py-3 bg-gray-900 border-b border-gray-700 shrink-0">
        <span className="text-base font-semibold tracking-tight">NITA Webapp</span>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">
            Signed in as{' '}
            <span className="text-white font-medium">{user?.username}</span>
            {user?.is_superuser && (
              <span className="ml-2 px-1.5 py-0.5 text-xs bg-indigo-600 rounded">
                admin
              </span>
            )}
          </span>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            Log out
          </button>
        </div>
      </header>

      {/* Body: sidebar + main */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}

import { useAuth } from '../context/AuthContext'
import { AppLayout } from '../components/AppLayout'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <AppLayout>
      <div className="max-w-lg">
        <h2 className="text-2xl font-semibold mb-2">
          Welcome{user?.username ? `, ${user.username}` : ''}
        </h2>
        <p className="text-gray-400 text-sm">
          Use the sidebar to navigate to Network Types or Networks.
        </p>
      </div>
    </AppLayout>
  )
}


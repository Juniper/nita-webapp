import { Link } from 'react-router-dom'
import { useAuth } from '../context/useAuth'
import { AppLayout } from '../components/AppLayout'
import { useApiResource } from '../hooks/useApiResource'
import { usePollWhile } from '../hooks/usePollWhile'
import {
  isInProgress,
  relativeTime,
  rowAccent,
  selectFeed,
  statusBadge,
  type ActionHistoryEntry,
} from './dashboardFeed'

const POLL_INTERVAL_MS = 15_000

interface Paginated<T> {
  count: number
  results: T[]
}

export function DashboardPage() {
  const { user } = useAuth()
  const { data, loading, error, reload } =
    useApiResource<Paginated<ActionHistoryEntry>>('/api/v1/action-history/')

  const feed = selectFeed(data?.results ?? [])
  usePollWhile(feed.some(h => isInProgress(h.status)), reload, POLL_INTERVAL_MS)

  return (
    <AppLayout>
      <div className="max-w-4xl">
        <h2 className="text-2xl font-semibold mb-1">
          Welcome back{user?.username ? `, ${user.username}` : ''}
        </h2>
        <p className="text-gray-400 text-sm mb-6">
          The most recent runs across the networks you can see.
        </p>

        <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-2">
          Recent activity
        </h3>

        {error ? (
          <p className="text-red-400 text-sm">Failed to load recent activity.</p>
        ) : loading && !data ? (
          <p className="text-gray-400 text-sm">Loading recent activity…</p>
        ) : feed.length === 0 ? (
          <p className="text-gray-400 text-sm">
            No recent activity yet. Runs you trigger will appear here.
          </p>
        ) : (
          <ul className="divide-y divide-gray-800 border-t border-gray-800">
            {feed.map(h => (
              <li key={h.id}>
                <Link
                  to={`/networks/${h.campus_network_id}?tab=history`}
                  className={`flex items-center gap-3 py-2.5 pl-3 pr-2 hover:bg-gray-900 transition-colors ${rowAccent(h.status)}`}
                >
                  <span className={statusBadge(h.status)}>{h.status}</span>
                  <span className="text-white font-medium truncate">{h.action_name}</span>
                  <span className="text-gray-400 truncate">{h.network_name}</span>
                  <span className="text-gray-500 text-sm truncate ml-auto">
                    {h.triggered_by_username || '—'}
                  </span>
                  <span
                    className="text-gray-500 text-sm shrink-0 w-20 text-right"
                    title={new Date(h.timestamp).toLocaleString()}
                  >
                    {relativeTime(h.timestamp)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </AppLayout>
  )
}

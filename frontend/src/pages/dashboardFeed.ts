/** Pure selection and presentation logic for the dashboard recent-activity feed.
 *
 * Kept free of React so it can be exercised directly.
 */

export const MAX_ROWS = 10

export interface ActionHistoryEntry {
  id: number
  status: string
  timestamp: string
  action_name: string
  network_name: string
  campus_network_id: number
  triggered_by_username: string
}

// Jenkins' vocabulary, title-cased by the status updater. `status` is free text,
// so an unrecognised value falls through to the neutral group rather than being
// hidden or mis-highlighted.
const ATTENTION_STATUSES = new Set(['FAILURE', 'FAILED', 'ABORTED', 'UNSTABLE'])

export const GROUP_IN_PROGRESS = 0
export const GROUP_ATTENTION = 1
export const GROUP_OTHER = 2

export function isInProgress(status: string): boolean {
  return (status || '').toUpperCase() === 'RUNNING'
}

export function statusGroup(status: string): number {
  const s = (status || '').toUpperCase()
  if (s === 'RUNNING') return GROUP_IN_PROGRESS
  if (ATTENTION_STATUSES.has(s)) return GROUP_ATTENTION
  return GROUP_OTHER
}

/** In-progress first, then runs needing attention, newest-first within each. */
export function sortForFeed(rows: ActionHistoryEntry[]): ActionHistoryEntry[] {
  return [...rows].sort((a, b) => {
    const byGroup = statusGroup(a.status) - statusGroup(b.status)
    if (byGroup !== 0) return byGroup
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  })
}

/** The rows the dashboard displays: sorted by attention, then capped. */
export function selectFeed(rows: ActionHistoryEntry[]): ActionHistoryEntry[] {
  return sortForFeed(rows).slice(0, MAX_ROWS)
}

export function relativeTime(iso: string, now: number = Date.now()): string {
  const seconds = Math.floor((now - new Date(iso).getTime()) / 1000)
  if (!Number.isFinite(seconds)) return ''
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export function statusBadge(status: string): string {
  const base = 'px-2 py-0.5 rounded text-xs font-semibold uppercase shrink-0'
  switch (statusGroup(status)) {
    case GROUP_IN_PROGRESS:
      return `${base} bg-yellow-800 text-yellow-200`
    case GROUP_ATTENTION:
      return `${base} bg-red-800 text-red-200`
    default:
      return `${base} bg-gray-700 text-gray-300`
  }
}

export function rowAccent(status: string): string {
  switch (statusGroup(status)) {
    case GROUP_IN_PROGRESS:
      return 'border-l-2 border-yellow-600'
    case GROUP_ATTENTION:
      return 'border-l-2 border-red-600'
    default:
      return 'border-l-2 border-transparent'
  }
}

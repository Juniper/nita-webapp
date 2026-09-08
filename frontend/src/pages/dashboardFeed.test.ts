import { describe, it, expect } from 'vitest'
import {
  GROUP_ATTENTION,
  GROUP_IN_PROGRESS,
  GROUP_OTHER,
  MAX_ROWS,
  relativeTime,
  selectFeed,
  statusGroup,
  type ActionHistoryEntry,
} from './dashboardFeed'

function row(
  id: number,
  status: string,
  minutesAgo: number,
): ActionHistoryEntry {
  return {
    id,
    status,
    timestamp: new Date(Date.now() - minutesAgo * 60_000).toISOString(),
    action_name: `action-${id}`,
    network_name: `net-${id}`,
    campus_network_id: id,
    triggered_by_username: '',
  }
}

describe('statusGroup', () => {
  it('puts Running in the in-progress group', () => {
    expect(statusGroup('Running')).toBe(GROUP_IN_PROGRESS)
  })

  it('treats Unstable as needing attention alongside failures', () => {
    for (const s of ['Failure', 'Failed', 'Aborted', 'Unstable']) {
      expect(statusGroup(s)).toBe(GROUP_ATTENTION)
    }
  })

  it('matches case-insensitively', () => {
    expect(statusGroup('running')).toBe(GROUP_IN_PROGRESS)
    expect(statusGroup('FAILURE')).toBe(GROUP_ATTENTION)
  })

  it('falls back to the neutral group for an unrecognised status', () => {
    expect(statusGroup('Some_New_Jenkins_Result')).toBe(GROUP_OTHER)
    expect(statusGroup('')).toBe(GROUP_OTHER)
  })
})

describe('selectFeed', () => {
  it('sorts in-progress above attention, and attention above the rest', () => {
    const feed = selectFeed([row(1, 'Success', 1), row(2, 'Failure', 2), row(3, 'Running', 3)])
    expect(feed.map(r => r.status)).toEqual(['Running', 'Failure', 'Success'])
  })

  it('orders newest-first within a group', () => {
    const feed = selectFeed([row(1, 'Success', 60), row(2, 'Success', 1), row(3, 'Success', 30)])
    expect(feed.map(r => r.id)).toEqual([2, 3, 1])
  })

  it(`renders at most ${MAX_ROWS} rows`, () => {
    const many = Array.from({ length: 25 }, (_, i) => row(i, 'Success', i))
    expect(selectFeed(many)).toHaveLength(MAX_ROWS)
  })

  it('never displaces an in-progress run with newer completed runs', () => {
    const rows = [
      row(99, 'Running', 500),
      ...Array.from({ length: 15 }, (_, i) => row(i, 'Success', i)),
    ]
    const feed = selectFeed(rows)
    expect(feed[0].id).toBe(99)
    expect(feed.some(r => r.id === 99)).toBe(true)
  })

  it('displays an unrecognised status rather than hiding it', () => {
    const feed = selectFeed([row(1, 'Some_New_Jenkins_Result', 1)])
    expect(feed).toHaveLength(1)
    expect(feed[0].status).toBe('Some_New_Jenkins_Result')
  })

  it('does not mutate the input array', () => {
    const rows = [row(1, 'Success', 1), row(2, 'Running', 2)]
    const before = rows.map(r => r.id)
    selectFeed(rows)
    expect(rows.map(r => r.id)).toEqual(before)
  })

  it('handles an empty list', () => {
    expect(selectFeed([])).toEqual([])
  })
})

describe('relativeTime', () => {
  const now = Date.parse('2026-09-03T12:00:00Z')

  it('formats sub-minute, minute, hour and day distances', () => {
    expect(relativeTime('2026-09-03T11:59:30Z', now)).toBe('just now')
    expect(relativeTime('2026-09-03T11:58:00Z', now)).toBe('2m ago')
    expect(relativeTime('2026-09-03T09:00:00Z', now)).toBe('3h ago')
    expect(relativeTime('2026-09-01T12:00:00Z', now)).toBe('2d ago')
  })

  it('returns an empty string for an unparseable timestamp', () => {
    expect(relativeTime('not-a-date', now)).toBe('')
  })
})

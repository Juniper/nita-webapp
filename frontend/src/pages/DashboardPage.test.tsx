import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { act, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DashboardPage } from './DashboardPage'

const { mockApiFetch } = vi.hoisted(() => ({ mockApiFetch: vi.fn() }))

vi.mock('../api/client', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  clearCsrfCache: () => {},
}))

const HISTORY_URL = '/api/v1/action-history/'

function entry(id: number, status: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    status,
    timestamp: new Date(Date.now() - id * 60_000).toISOString(),
    action_name: `action-${id}`,
    network_name: `net-${id}`,
    campus_network_id: id,
    triggered_by_username: 'alice',
    ...overrides,
  }
}

let payload: ReturnType<typeof entry>[] = []
let failRequest = false

function historyCallCount() {
  return mockApiFetch.mock.calls.filter(c => c[0] === HISTORY_URL).length
}

/** Feed rows only — AppLayout's sidebar also renders nav links. */
function feedLinks() {
  return screen
    .queryAllByRole('link')
    .filter(a => a.getAttribute('href')?.includes('?tab=history'))
}

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

async function flush() {
  await act(async () => {
    await Promise.resolve()
  })
}

async function advance(ms: number) {
  await act(async () => {
    vi.advanceTimersByTime(ms)
  })
  await flush()
}

beforeEach(() => {
  vi.useFakeTimers()
  payload = []
  failRequest = false
  mockApiFetch.mockReset()
  mockApiFetch.mockImplementation((url: string) => {
    if (url === HISTORY_URL) {
      if (failRequest) return Promise.resolve({ ok: false, status: 500 } as Response)
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ count: payload.length, results: payload }),
      } as unknown as Response)
    }
    return Promise.resolve({ ok: false, status: 404 } as Response)
  })
})

afterEach(() => {
  vi.useRealTimers()
})

describe('DashboardPage recent activity', () => {
  it('deep-links each row to its own network history tab', async () => {
    payload = [entry(7, 'Success'), entry(9, 'Failure')]
    renderDashboard()
    await flush()

    const hrefs = feedLinks().map(a => a.getAttribute('href'))
    expect(hrefs).toContain('/networks/7?tab=history')
    expect(hrefs).toContain('/networks/9?tab=history')
  })

  it('renders the triggering user, and an em dash when unknown', async () => {
    payload = [entry(1, 'Success'), entry(2, 'Success', { triggered_by_username: '' })]
    renderDashboard()
    await flush()

    expect(screen.getByText('alice')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('renders an empty state when there is no activity', async () => {
    payload = []
    renderDashboard()
    await flush()

    expect(screen.getByText(/No recent activity yet/)).toBeInTheDocument()
    expect(feedLinks()).toHaveLength(0)
  })

  it('renders an error state when the request fails', async () => {
    failRequest = true
    renderDashboard()
    await flush()

    expect(screen.getByText(/Failed to load recent activity/)).toBeInTheDocument()
  })

  it('shows at most ten rows', async () => {
    payload = Array.from({ length: 25 }, (_, i) => entry(i + 1, 'Success'))
    renderDashboard()
    await flush()

    expect(feedLinks()).toHaveLength(10)
  })

  it('polls while a Running row is displayed', async () => {
    payload = [entry(1, 'Running')]
    renderDashboard()
    await flush()
    expect(historyCallCount()).toBe(1)

    await advance(15_000)
    expect(historyCallCount()).toBe(2)
  })

  it('does not poll when nothing is Running', async () => {
    payload = [entry(1, 'Success')]
    renderDashboard()
    await flush()
    expect(historyCallCount()).toBe(1)

    await advance(60_000)
    expect(historyCallCount()).toBe(1)
  })

  it('stops polling once the running row reaches a terminal status', async () => {
    payload = [entry(1, 'Running')]
    renderDashboard()
    await flush()

    payload = [entry(1, 'Success')]
    await advance(15_000)
    expect(historyCallCount()).toBe(2)

    await advance(60_000)
    expect(historyCallCount()).toBe(2)
  })

  it('stops polling when the page unmounts', async () => {
    payload = [entry(1, 'Running')]
    const { unmount } = renderDashboard()
    await flush()

    unmount()
    const afterUnmount = historyCallCount()

    await advance(60_000)
    expect(historyCallCount()).toBe(afterUnmount)
  })

  it('keeps rows visible across a polled refresh', async () => {
    payload = [entry(1, 'Running')]
    renderDashboard()
    await flush()
    expect(screen.getByText('action-1')).toBeInTheDocument()

    await advance(15_000)
    expect(screen.getByText('action-1')).toBeInTheDocument()
    expect(screen.queryByText(/Loading recent activity/)).not.toBeInTheDocument()
  })
})

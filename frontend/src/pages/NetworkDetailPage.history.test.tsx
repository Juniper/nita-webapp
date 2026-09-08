import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { act, render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { NetworkDetailPage } from './NetworkDetailPage'

const { mockApiFetch } = vi.hoisted(() => ({ mockApiFetch: vi.fn() }))

vi.mock('../api/client', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  clearCsrfCache: () => {},
}))

const HISTORY_URL = '/api/v1/action-history/?campus_network_id=1'

function jsonResponse(data: unknown, ok = true) {
  return Promise.resolve({
    ok,
    status: ok ? 200 : 403,
    json: () => Promise.resolve(data),
  } as unknown as Response)
}

function historyRow(id: number, status: string) {
  return {
    id,
    action_name: `action-${id}`,
    category_name: 'BUILD',
    network_name: 'net-1',
    timestamp: '2026-09-03T10:00:00Z',
    status,
    triggered_by_username: 'alice',
    action_id: id,
    category_id: 1,
    campus_network_id: 1,
    jenkins_job_build_no: id,
    jenkins_job_name: `job-${id}`,
  }
}

/** Queue of history payloads; the last one is reused once exhausted. */
let historyPayloads: ReturnType<typeof historyRow>[][] = []

function historyCallCount() {
  return mockApiFetch.mock.calls.filter(c => c[0] === HISTORY_URL).length
}

function renderHistoryTab() {
  return render(
    <MemoryRouter initialEntries={['/networks/1?tab=history']}>
      <Routes>
        <Route path="/networks/:id" element={<NetworkDetailPage />} />
      </Routes>
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
  historyPayloads = [[historyRow(1, 'Success')]]
  mockApiFetch.mockReset()
  mockApiFetch.mockImplementation((url: string) => {
    if (url === '/api/v1/networks/1/') {
      return jsonResponse({
        id: 1,
        name: 'net-1',
        description: '',
        status: 'ok',
        campus_type: 1,
        campus_type_name: 'type-1',
        host_file: '',
        owner_username: 'alice',
        team: null,
        team_name: null,
      })
    }
    if (url === HISTORY_URL) {
      const next = historyPayloads.length > 1 ? historyPayloads.shift()! : historyPayloads[0]
      return jsonResponse({ results: next })
    }
    if (url.includes('robot-summary')) return jsonResponse({ available: false })
    return jsonResponse(null, false)
  })
})

afterEach(() => {
  vi.useRealTimers()
})

describe('History tab in-flight refresh', () => {
  it('refetches after the interval while a run is Running', async () => {
    historyPayloads = [[historyRow(1, 'Running')]]
    renderHistoryTab()
    await flush()
    expect(historyCallCount()).toBe(1)

    await advance(15_000)
    expect(historyCallCount()).toBe(2)

    await advance(15_000)
    expect(historyCallCount()).toBe(3)
  })

  it('issues no interval refetch when nothing is Running', async () => {
    historyPayloads = [[historyRow(1, 'Success'), historyRow(2, 'Failure')]]
    renderHistoryTab()
    await flush()
    expect(historyCallCount()).toBe(1)

    await advance(60_000)
    expect(historyCallCount()).toBe(1)
  })

  it('stops polling once the last Running entry reaches a terminal status', async () => {
    historyPayloads = [[historyRow(1, 'Running')], [historyRow(1, 'Success')]]
    renderHistoryTab()
    await flush()
    expect(historyCallCount()).toBe(1)

    // First interval fires and returns the terminal status.
    await advance(15_000)
    expect(historyCallCount()).toBe(2)

    // Nothing is Running any more, so the interval must not fire again.
    await advance(60_000)
    expect(historyCallCount()).toBe(2)
  })

  it('stops polling when the History tab is left', async () => {
    historyPayloads = [[historyRow(1, 'Running')]]
    renderHistoryTab()
    await flush()

    fireEvent.click(screen.getByRole('button', { name: 'hosts' }))
    await flush()
    const afterLeaving = historyCallCount()

    await advance(60_000)
    expect(historyCallCount()).toBe(afterLeaving)
  })

  it('stops polling when the page unmounts', async () => {
    historyPayloads = [[historyRow(1, 'Running')]]
    const { unmount } = renderHistoryTab()
    await flush()

    unmount()
    const afterUnmount = historyCallCount()

    await advance(60_000)
    expect(historyCallCount()).toBe(afterUnmount)
  })

  it('keeps rows rendered across a polled refresh, with no loading indicator', async () => {
    historyPayloads = [[historyRow(1, 'Running')]]
    renderHistoryTab()
    await flush()
    expect(screen.getByText('action-1')).toBeInTheDocument()

    await advance(15_000)

    expect(screen.getByText('action-1')).toBeInTheDocument()
    expect(screen.queryByText(/Loading history/)).not.toBeInTheDocument()
  })

  it('shows the triggering user, and an em dash when unknown', async () => {
    const known = historyRow(1, 'Success')
    const unknown = { ...historyRow(2, 'Success'), triggered_by_username: '' }
    historyPayloads = [[known, unknown]]
    renderHistoryTab()
    await flush()

    expect(screen.getByText('alice')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()
  })
})

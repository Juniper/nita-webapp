import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext, type User } from '../context/auth-context'
import { NetworksPage } from './NetworksPage'

const { mockApiFetch } = vi.hoisted(() => ({ mockApiFetch: vi.fn() }))

vi.mock('../api/client', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  clearCsrfCache: () => {},
}))

const rows = [
  { id: 1, name: 'mine', description: '', status: 'ok', campus_type: 1, campus_type_name: 't', host_file: '', owner_username: 'alice', team_name: null },
  { id: 2, name: 'shared', description: '', status: 'ok', campus_type: 1, campus_type_name: 't', host_file: '', owner_username: 'bob', team_name: 'netops' },
]

function renderAs(user: User) {
  return render(
    <AuthContext.Provider value={{ user, loading: false, setUser: () => {}, logout: async () => {} }}>
      <MemoryRouter>
        <NetworksPage />
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

function deleteButtonsIn(name: string) {
  const row = screen.getByText(name).closest('tr')!
  return Array.from(row.querySelectorAll('button')).filter(b => b.textContent === 'Delete')
}

beforeEach(() => {
  mockApiFetch.mockReset()
  mockApiFetch.mockImplementation((url: string) => {
    if (url === '/api/v1/networks/') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ count: rows.length, results: rows }),
      } as unknown as Response)
    }
    return Promise.resolve({ ok: false, status: 404 } as Response)
  })
})

describe('NetworksPage delete control', () => {
  it('is shown to the owner and hidden on a team-shared network they do not own', async () => {
    renderAs({ id: 3, username: 'alice', is_superuser: false, role: 'user' })
    await waitFor(() => expect(screen.getByText('shared')).toBeInTheDocument())
    expect(deleteButtonsIn('mine')).toHaveLength(1)
    expect(deleteButtonsIn('shared')).toHaveLength(0)
  })

  it('is shown on every row to a power user', async () => {
    renderAs({ id: 4, username: 'pat', is_superuser: false, role: 'power_user' })
    await waitFor(() => expect(screen.getByText('shared')).toBeInTheDocument())
    expect(deleteButtonsIn('mine')).toHaveLength(1)
    expect(deleteButtonsIn('shared')).toHaveLength(1)
  })
})

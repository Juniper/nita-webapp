import { beforeEach, describe, it, expect, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { apiFetch } from '../api/client'
import { LoginPage } from './LoginPage'

vi.mock('../api/client', () => ({
  apiFetch: vi.fn(),
  clearCsrfCache: () => {},
}))

const mockedApiFetch = vi.mocked(apiFetch)

function renderLogin(initialEntry = '/login') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/jenkins/*" element={<p>Jenkins page</p>} />
        <Route path="/" element={<p>Home page</p>} />
        <Route path="*" element={<p>Unknown page</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function mockSuccessfulLogin() {
  mockedApiFetch
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 1, username: 'tester', is_superuser: false }),
    } as Response)
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 1,
        username: 'tester',
        is_superuser: false,
        role: 'admin',
        teams: [],
      }),
    } as Response)
}

async function submitLogin() {
  fireEvent.change(screen.getByLabelText('Username'), {
    target: { value: 'tester' },
  })
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'secret' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
}

beforeEach(() => mockedApiFetch.mockReset())

describe('LoginPage brand mark', () => {
  it('renders the brand mark', () => {
    const { container } = renderLogin()
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('places the mark above the heading', () => {
    const { container } = renderLogin()
    const mark = container.querySelector('svg')!
    const heading = screen.getByRole('heading', { name: 'NITA Webapp' })
    // DOCUMENT_POSITION_FOLLOWING === the heading comes after the mark.
    expect(mark.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_FOLLOWING)
      .toBeTruthy()
  })

  it('hides the mark from assistive technology', () => {
    const { container } = renderLogin()
    const mark = container.querySelector('svg')!
    expect(mark).toHaveAttribute('aria-hidden', 'true')
    expect(mark).toHaveAttribute('focusable', 'false')
  })

  it('announces the brand name exactly once', () => {
    renderLogin()
    expect(screen.getAllByText('NITA Webapp')).toHaveLength(1)
  })

  it('does not make the mark interactive', () => {
    const { container } = renderLogin()
    const mark = container.querySelector('svg')!
    expect(mark.closest('a')).toBeNull()
    expect(mark.closest('button')).toBeNull()
  })
})

describe('LoginPage next destination', () => {
  it('returns to a safe relative path after login', async () => {
    mockSuccessfulLogin()
    renderLogin('/login?next=%2Fjenkins%2Fjob%2Ftest-robot-net1%2F')

    await submitLogin()

    expect(await screen.findByText('Jenkins page')).toBeInTheDocument()
  })

  it.each([
    ['/login?next=//evil.example/', 'protocol-relative path'],
    ['/login?next=https%3A%2F%2Fevil.example%2F', 'absolute URL'],
    ['/login?next=%5C%5Cevil.example', 'backslash path'],
    ['/login', 'missing next'],
  ])('falls back to home for %s (%s)', async (entry) => {
    mockSuccessfulLogin()
    renderLogin(entry)

    await submitLogin()

    expect(await screen.findByText('Home page')).toBeInTheDocument()
  })
})

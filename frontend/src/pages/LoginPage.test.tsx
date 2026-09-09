import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { LoginPage } from './LoginPage'

vi.mock('../api/client', () => ({
  apiFetch: vi.fn(() => Promise.resolve({ ok: false, status: 403 } as Response)),
  clearCsrfCache: () => {},
}))

function renderLogin() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  )
}

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

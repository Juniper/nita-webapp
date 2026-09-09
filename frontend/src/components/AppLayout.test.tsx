import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AppLayout } from './AppLayout'

vi.mock('../api/client', () => ({
  apiFetch: vi.fn(() => Promise.resolve({ ok: true, status: 200 } as Response)),
  clearCsrfCache: () => {},
}))

function renderLayout() {
  return render(
    <MemoryRouter>
      <AppLayout>
        <p>page content</p>
      </AppLayout>
    </MemoryRouter>,
  )
}

function brandMark(container: HTMLElement) {
  return container.querySelector('header svg')!
}

describe('AppLayout brand mark', () => {
  it('renders the mark in the header', () => {
    const { container } = renderLayout()
    expect(brandMark(container)).toBeInTheDocument()
  })

  it('places the mark before the brand name', () => {
    const { container } = renderLayout()
    const name = screen.getByText('NITA Webapp')
    expect(
      brandMark(container).compareDocumentPosition(name) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
  })

  it('hides the mark from assistive technology', () => {
    const { container } = renderLayout()
    const mark = brandMark(container)
    expect(mark).toHaveAttribute('aria-hidden', 'true')
    expect(mark).toHaveAttribute('focusable', 'false')
  })

  it('announces the brand name exactly once', () => {
    renderLayout()
    expect(screen.getAllByText('NITA Webapp')).toHaveLength(1)
  })

  it('does not make the mark a link', () => {
    const { container } = renderLayout()
    const mark = brandMark(container)
    expect(mark.closest('a')).toBeNull()
    expect(mark.closest('button')).toBeNull()
  })

  it('still renders its children', () => {
    renderLayout()
    expect(screen.getByText('page content')).toBeInTheDocument()
  })
})

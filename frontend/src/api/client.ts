/**
 * CSRF-aware fetch wrapper for the NITA Webapp API.
 *
 * - GET requests are sent as-is with session credentials.
 * - Mutating requests (POST, PUT, PATCH, DELETE) first obtain the CSRF token
 *   from GET /api/v1/auth/csrf/ (cached after first call) and attach it as
 *   the X-CSRFToken header.
 */

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

function readCsrfCookie(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

async function getCsrfToken(): Promise<string> {
  // Always read from the cookie — never cache.  Django rotates the CSRF secret
  // on login(), so a cached value from before login will mismatch the cookie.
  const token = readCsrfCookie()
  if (token) return token
  // Cookie not set yet: call the CSRF endpoint so Django sets it, then re-read.
  const res = await fetch('/api/v1/auth/csrf/', { credentials: 'include' })
  if (!res.ok) throw new Error(`Failed to fetch CSRF token: ${res.status}`)
  return readCsrfCookie()
}

export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const method = (options.method ?? 'GET').toUpperCase()
  const headers = new Headers(options.headers)

  headers.set('Content-Type', headers.get('Content-Type') ?? 'application/json')

  if (MUTATING_METHODS.has(method)) {
    const token = await getCsrfToken()
    headers.set('X-CSRFToken', token)
  }

  return fetch(path, {
    ...options,
    headers,
    credentials: 'include',
  })
}

/** No-op — kept for API compatibility. Cache was removed in favour of always
 *  reading from document.cookie so stale tokens after login are not possible. */
export function clearCsrfCache(): void {}

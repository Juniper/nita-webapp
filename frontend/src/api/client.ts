/**
 * CSRF-aware fetch wrapper for the NITA Webapp API.
 *
 * - GET requests are sent as-is with session credentials.
 * - Mutating requests (POST, PUT, PATCH, DELETE) first obtain the CSRF token
 *   from GET /api/v1/auth/csrf/ (cached after first call) and attach it as
 *   the X-CSRFToken header.
 */

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

let csrfTokenCache: string | null = null

async function getCsrfToken(): Promise<string> {
  if (csrfTokenCache) return csrfTokenCache
  const res = await fetch('/api/v1/auth/csrf/', { credentials: 'include' })
  if (!res.ok) throw new Error(`Failed to fetch CSRF token: ${res.status}`)
  const data = await res.json()
  csrfTokenCache = data.csrfToken as string
  return csrfTokenCache
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

/** Call after logout to force a fresh CSRF token next time. */
export function clearCsrfCache(): void {
  csrfTokenCache = null
}

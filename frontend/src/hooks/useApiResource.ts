import { useCallback, useEffect, useState } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import { apiFetch } from '../api/client'

export interface UseApiResourceResult<T> {
  data: T | null
  loading: boolean
  error: string | null
  reload: () => void
  setData: Dispatch<SetStateAction<T | null>>
  setError: Dispatch<SetStateAction<string | null>>
}

/**
 * Shared data-fetching hook: reads `path` via the CSRF-aware `apiFetch` and
 * returns `{ data, loading, error, reload, setData }`.
 *
 * State is only updated after the request resolves, so no component sets state
 * synchronously inside an effect body (satisfies react-hooks/set-state-in-effect).
 * `reload()` re-runs the request (and is safe to call from event handlers);
 * `setData` supports optimistic updates. Pass `{ enabled: false }` to skip the
 * fetch until a guard becomes true.
 */
export function useApiResource<T>(
  path: string,
  options?: { enabled?: boolean },
): UseApiResourceResult<T> {
  const enabled = options?.enabled ?? true
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(enabled)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  const reload = useCallback(() => {
    setLoading(true)
    setTick((t) => t + 1)
  }, [])

  useEffect(() => {
    if (!enabled) return
    const controller = new AbortController()
    void (async () => {
      try {
        const res = await apiFetch(path, { signal: controller.signal })
        if (!res.ok) throw new Error(`Failed to load: ${res.status}`)
        const json = (await res.json()) as T
        if (controller.signal.aborted) return
        setData(json)
        setError(null)
      } catch (e) {
        if (controller.signal.aborted) return
        if (e instanceof DOMException && e.name === 'AbortError') return
        setError(e instanceof Error ? e.message : 'Unknown error')
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    })()
    return () => controller.abort()
  }, [path, enabled, tick])

  return { data, loading, error, reload, setData, setError }
}

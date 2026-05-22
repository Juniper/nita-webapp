## Context

The `handleTrigger` function in `NetworkDetailPage.tsx` calls
`apiFetch(…, { method: 'POST' })`, chains `.then(r => r.json())` on the
result, and immediately enters the EventSource setup block. `apiFetch` is a thin
CSRF-aware wrapper around `fetch`; like `fetch`, it resolves with the Response
object regardless of HTTP status — it does **not** reject on 4xx or 5xx.

### Observed failure sequence (from k8s logs)

```
WARNING  "POST /api/v1/networks/2/trigger/1/ HTTP/1.0" 403 115
WARNING  "GET  /api/v1/action-history/undefined/stream/ HTTP/1.0" 404 6
```

1. Trigger POST → Django returns 403 (CSRF token stale or session expired).
2. `r.json()` parses the 403 body (`{"detail": "…"}`) — no
   `action_history_id` key.
3. `histId = d.action_history_id` → `undefined`.
4. `new EventSource('/api/v1/action-history/undefined/stream/')` opens.
5. Server returns 404. EventSource dispatches an `'error'` DOM event with
   `readyState === CLOSED`.
6. `es.addEventListener('error', handler)` fires. `(e as MessageEvent).data`
   is `undefined` (no SSE payload in a 404). The template
   `` `[error] ${undefined ?? 'stream error'}` `` produces the observed
   `[error] stream error` console line.
7. `es.onerror` fires on the same event (duplicate), but its guard
   `readyState === EventSource.CLOSED` is now true — so it also tries to
   update `streamState` to `'error'` redundantly.

### Root cause of the 403

Django's `SessionAuthentication` enforces CSRF for all non-safe methods.
`apiFetch` fetches the CSRF token once and caches it in the module-level
`csrfTokenCache` variable. If:

- the page was loaded before the user had an active session (CSRF token from
  an unauthenticated request), or
- the session was rotated (login in a second tab), or
- the user's Django session cookie expired while the SPA remained open,

the cached CSRF token no longer matches the `csrftoken` cookie, and Django
returns 403. The `clearCsrfCache()` utility is already exported by `client.ts`
but is never called on a 403 response.

---

## Goals / Non-Goals

**Goals:**
- Trigger failures show a clear human-readable error in the console panel.
- No EventSource is opened when the trigger POST does not return 202.
- A stale CSRF cache is automatically cleared on 403 so the next attempt
  succeeds without a page reload.
- Server-sent SSE `event: error` messages and network-level EventSource
  failures are handled by distinct code paths.

**Non-Goals:**
- Auto-retry the trigger request (two clicks is acceptable after CSRF refresh).
- Investigate or fix session expiry / authentication timeout behaviour.
- Change backend trigger logic.

---

## Decisions

### D1 — Guard `handleTrigger` against non-2xx trigger responses

**Decision**: After `apiFetch(…, { method: 'POST' })` resolves, check
`r.ok` before parsing the body.  If `!r.ok`:

1. If `r.status === 403`, call `clearCsrfCache()` so the next attempt fetches
   a fresh token.
2. Append `[error] Trigger failed (HTTP <status>)` to `consoleLines`.
3. Set `streamState` to `'error'`.
4. Return without opening an EventSource.

If `r.ok` but `d.action_history_id` is falsy (defensive guard), treat it the
same way with message `[error] Trigger returned no job ID`.

**Rationale**: `fetch` and `apiFetch` resolve on network success regardless of
HTTP status; callers must check `r.ok` explicitly. The `.catch(() => {})`
currently swallows all rejection-path errors silently; it should also show an
error in the console panel.

**Alternative considered**: Throw in `apiFetch` on non-2xx. Rejected because it
would require updating every callsite; the localised guard in `handleTrigger` is
sufficient and keeps the change minimal.

---

### D2 — Separate server-sent error events from network-level EventSource errors

**Decision**: In the `es.addEventListener('error', handler)` block, add an
early-return guard:

```typescript
es.addEventListener('error', (e) => {
  const data = (e as MessageEvent).data
  if (!data) return   // network-level error — handled by es.onerror
  setStreamState('error')
  setConsoleLines(prev => [...prev, `[error] ${data}`])
  es.close()
  setLoaded(l => ({ ...l, history: false }))
})
```

The `es.onerror` handler already exists and handles the network-level case
(sets `streamState` to `'error'` when `readyState === CLOSED`).  Having both
paths fire on the same event is harmless today (both set the same state) but is
confusing and leads to the spurious `[error] stream error` message.

**Rationale**: The EventSource specification dispatches a single `Event` (not a
`MessageEvent`) for network-level failures; it carries no `data` property.
Server-sent events typed `event: error` are dispatched as `MessageEvent` and
DO carry `data`.  Checking `data` truthy/falsy reliably separates the two cases
without inspecting `e.type` or `e.constructor`.

**Alternative considered**: Rename `es.onerror` to cover both paths and remove
`addEventListener('error')` entirely for network errors.  Rejected because
`addEventListener('error')` is the correct way to receive server-sent named
events and removing it would break the SSE contract.

---

## Implementation

### `frontend/src/pages/NetworkDetailPage.tsx`

Replace the current `handleTrigger` body:

```typescript
const handleTrigger = (action: Action) => {
  setTriggerLoading(action.id)
  apiFetch(`/api/v1/networks/${id}/trigger/${action.id}/`, { method: 'POST' })
    .then(r => {
      if (!r.ok) {
        if (r.status === 403) clearCsrfCache()
        setConsoleLines([`[error] Trigger failed (HTTP ${r.status})`])
        setStreamState('error')
        return
      }
      return r.json().then((d: { action_history_id: number; status: string }) => {
        const histId = d.action_history_id
        if (!histId) {
          setConsoleLines(['[error] Trigger returned no job ID'])
          setStreamState('error')
          return
        }
        setConsoleHistoryId(histId)
        setConsoleLines([])
        setStreamState('streaming')
        const es = new EventSource(`/api/v1/action-history/${histId}/stream/`)
        es.onmessage = (e) => {
          setConsoleLines(prev => [...prev, e.data])
        }
        es.addEventListener('done', () => {
          setStreamState('done')
          es.close()
          setLoaded(l => ({ ...l, history: false }))
        })
        es.addEventListener('error', (e) => {
          const data = (e as MessageEvent).data
          if (!data) return  // network-level — handled by es.onerror below
          setStreamState('error')
          setConsoleLines(prev => [...prev, `[error] ${data}`])
          es.close()
          setLoaded(l => ({ ...l, history: false }))
        })
        es.addEventListener('timeout', () => {
          setStreamState('timeout')
          setConsoleLines(prev => [...prev, '[timeout] Build stream timed out after 30 minutes.'])
          es.close()
          setLoaded(l => ({ ...l, history: false }))
        })
        es.onerror = () => {
          if (es.readyState === EventSource.CLOSED) {
            setStreamState(s => s === 'streaming' ? 'error' : s)
            es.close()
            setLoaded(l => ({ ...l, history: false }))
          }
        }
      })
    })
    .catch(() => {
      setConsoleLines(['[error] Trigger request failed'])
      setStreamState('error')
    })
    .finally(() => setTriggerLoading(null))
}
```

Import `clearCsrfCache` from `'../api/client'` (already exported).

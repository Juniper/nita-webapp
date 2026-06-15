## Why

Triggering a Jenkins job via the webapp UI shows `[error] stream error` in the
console panel immediately after clicking Run, even when the Jenkins service is
running. Two bugs combine to produce this symptom:

1. **`handleTrigger` does not check the trigger response status before opening
   the EventSource.** `apiFetch` does not throw on non-2xx responses; the code
   calls `.then(r => r.json())` unconditionally. When the trigger POST returns
   403 the parsed JSON body has no `action_history_id`, so `histId` is
   `undefined`. The EventSource opens at
   `/api/v1/action-history/undefined/stream/`, the server returns 404, and the
   EventSource dispatches an error event.

2. **The EventSource `'error'` named-event listener conflates server-sent error
   events with network-level EventSource errors.** `es.addEventListener('error',
   handler)` fires for *both* `event: error\n` lines emitted by the SSE server
   *and* network-level errors (connection refused, 404, etc.). Because the
   message template falls back to the string `'stream error'` when `e.data` is
   absent, every network-level EventSource failure produces the misleading
   `[error] stream error` entry in the console panel. The `es.onerror` handler,
   which was intended to cover network-level failures, is therefore also
   redundantly triggered on the same event.

The 403 from Django itself is a separate upstream condition (CSRF token stale in
the module-level cache, or a session that expired after the SPA loaded) that
exposes the frontend bugs; both frontend bugs need to be fixed regardless of why
the 403 occurred.

## What Changes

- **Frontend `handleTrigger`**: check `r.ok` after the trigger POST; if the
  response is not 2xx, append a human-readable error line to the console panel,
  set `streamState` to `'error'`, and return without opening an EventSource.
  Also guard against a missing `action_history_id` in a 2xx body.
- **Frontend EventSource error listener**: the named `'error'` listener SHALL
  only process server-sent error events (those that carry a `data` field); it
  SHALL return early for network-level events (where `data` is absent) and let
  `es.onerror` handle them — removing the duplicate-handling.
- **Frontend CSRF cache**: on a 403 response from the trigger endpoint, clear
  `csrfTokenCache` so that the next trigger attempt fetches a fresh CSRF token
  rather than re-using a stale one.

## Capabilities

### Modified Capabilities

- `jenkins-trigger-security`: Add a frontend requirement that the SPA checks the
  trigger response status before opening an EventSource; specifies the error
  display contract for non-202 trigger responses.
- `console-streaming`: Clarify that the `'error'` named event listener on
  EventSource SHALL only process server-sent SSE error events (those with a
  `data` payload) and shall not attempt to parse network-level EventSource
  errors, which are handled solely by `es.onerror`.

## Impact

- **Frontend** (`NetworkDetailPage.tsx`): guard `handleTrigger` response;
  differentiate server-sent error events from network-level EventSource errors;
  clear CSRF cache on 403.
- **Frontend** (`api/client.ts`): `clearCsrfCache()` is already exported; no
  change to the module API required.
- No backend changes; no nginx changes; no database changes.
- No external API contract changes.

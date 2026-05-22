## 1. Guard `handleTrigger` Against Non-2xx Trigger Responses

- [x] 1.1 In `frontend/src/pages/NetworkDetailPage.tsx`, add `import {
  clearCsrfCache } from '../api/client'` (the function is already exported)
- [x] 1.2 Rewrite `handleTrigger` so that after `apiFetch(…)` resolves, `r.ok`
  is checked before calling `r.json()`: if `!r.ok`, call `clearCsrfCache()` when
  `r.status === 403`, append `[error] Trigger failed (HTTP <status>)` to
  `consoleLines`, set `streamState` to `'error'`, and return without opening an
  EventSource
- [x] 1.3 Add a guard after parsing the 2xx body: if `d.action_history_id` is
  falsy, append `[error] Trigger returned no job ID`, set `streamState` to
  `'error'`, and return without opening an EventSource
- [x] 1.4 Replace the current `.catch(() => {})` silent swallow with a handler
  that appends `[error] Trigger request failed` to `consoleLines` and sets
  `streamState` to `'error'`

## 2. Fix EventSource Named Error Listener

- [x] 2.1 In `frontend/src/pages/NetworkDetailPage.tsx`, inside the
  `es.addEventListener('error', …)` handler body, add an early-return guard:
  `const data = (e as MessageEvent).data; if (!data) return` — this prevents
  the handler from logging `[error] stream error` when a network-level
  EventSource error (no `data` property) fires, leaving `es.onerror` as the
  sole handler for network-level failures
- [x] 2.2 Update the `setConsoleLines` call in the same handler to use `data`
  directly (the variable already holds the server-sent message) instead of
  re-casting `e`

## 3. Verification

- [ ] 3.1 Trigger a job while unauthenticated (or with a stale session) and
  confirm the console panel shows `[error] Trigger failed (HTTP 403)` and no
  EventSource is opened (check browser network tab for absence of a request to
  `/api/v1/action-history/undefined/stream/`)
- [ ] 3.2 Trigger a job normally and confirm the console panel streams live
  output and shows the `done` state when the build finishes — confirming the
  fix has not broken the happy path
- [x] 3.3 Run `npm run build` inside `frontend/` and confirm no TypeScript
  errors

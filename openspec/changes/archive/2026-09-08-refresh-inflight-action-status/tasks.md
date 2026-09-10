## 1. Frontend — polling hook

- [x] 1.1 Add a `usePollWhile(active, callback, intervalMs)` hook under
  `frontend/src/hooks/` that runs `callback` every `intervalMs` while `active`
  is true and does nothing while it is false
- [x] 1.2 Clear the interval on unmount and whenever `active` becomes false
- [x] 1.3 Keep the hook free of any action-history knowledge (boolean + callback
  only) so the dashboard change can reuse it

## 2. Frontend — History tab

- [x] 2.1 Derive an in-flight predicate from the loaded history rows:
  at least one entry with `status === 'Running'`
- [x] 2.2 Drive `usePollWhile` from that predicate at a 15 s interval, calling
  the existing `fetchHistory`, and only while `activeTab === 'history'`
- [x] 2.3 Confirm polled refreshes keep existing rows visible and do not show the
  loading indicator (existing `fetchHistory` behaviour — verify, do not change)
- [x] 2.4 Abort any in-flight request on tab change and unmount
- [x] 2.5 `npm run lint` and `npm run build` green

## 3. Frontend — tests

- [x] 3.1 A list containing a `Running` entry issues a refetch after the interval
- [x] 3.2 A list with no `Running` entry issues no refetch
- [x] 3.3 Polling stops once the last `Running` entry reaches a terminal status
- [x] 3.4 Polling stops when the History tab is left and when the page unmounts
- [x] 3.5 Rows remain rendered across a polled refresh (no loading flash)

## 4. Verify

- [ ] 4.1 Manual check: trigger an action, stay on the History tab without
  interacting, and confirm the row moves from `Running` to its terminal status
  on its own within ~45 s
- [ ] 4.2 Manual check: on a network whose runs are all finished, confirm no
  action-history requests are issued while the tab sits open

## Blockers

Only the manual checks in section 4 remain. They require a running deployment
with Jenkins and have not been performed.

**Resolved — Node toolchain.** The build requires Node 22 (per `Dockerfile`,
`node:22-slim`); Node 22.23.2 is installed at
`~/.local/opt/node-v22.23.2-linux-x64`. `npm ci`, `npm run lint` and
`npm run build` all pass.

**Resolved — frontend test infrastructure.** Added by the `frontend-test-harness`
change. Section 3 is covered by `src/pages/NetworkDetailPage.history.test.tsx`,
which renders the History tab with `apiFetch` mocked and fake timers, asserting
that polling starts only when a `Running` row is present and stops on terminal
status, tab change and unmount. The two polling tests were confirmed to fail when
the `usePollWhile` predicate is replaced with `false`.

## Why

Runs appear to get stuck in `Running` on the History tab, then "fix themselves"
when the page is refreshed. The data was never wrong — the screen simply stops
asking.

`NetworkDetailPage` fetches the action-history list **only when the History tab
is opened**:

```tsx
// NetworkDetailPage.tsx:229
useEffect(() => {
  if (activeTab === 'history') fetchHistory()
}, [activeTab, fetchHistory])
```

Meanwhile `StatusUpdater` polls Jenkins every 30 seconds and writes the terminal
status to the database. So:

```
t=0     open History tab      → fetch → row shows "Running"      correct
t=30s   StatusUpdater runs    → DB row becomes "Success"
t=60s   still on the tab      → no refetch → still "Running"     stale
t=90s   refresh / switch tabs → fetch → "Success"                "it fixed itself"
```

The user watching the tab is the one person who cannot see the update. The
longer a build runs, the more likely they are sitting on exactly that screen.

The backend contract is already correct — the `actions` capability requires that
action-history status reaches a terminal value after the build completes, and it
does. This is purely a client-side refresh gap.

## What Changes

- **The History tab polls while work is in flight.** When the displayed list
  contains at least one entry with `status = "Running"`, the tab SHALL re-fetch
  the action-history list every **15 seconds**.
- **Polling stops when nothing is running.** When no displayed entry is
  `Running`, no polling requests are issued at all. A tab showing only completed
  runs generates zero background traffic.
- **Polling stops when the tab is left or the page unmounts.** Leaving the
  History tab or navigating away cancels the timer and any in-flight request.
- **Refreshes are silent.** Already-displayed rows stay visible and the loading
  indicator does not appear — extending the behaviour the existing requirement
  already specifies for tab re-entry, so a poll never causes a flash or a scroll
  jump.
- **The polling behaviour is extracted as a reusable hook** so the planned
  dashboard recent-activity feed inherits it rather than reimplementing it.

## Capabilities

### Modified Capabilities

- `spa-networks`: the History tab refreshes on an interval while any displayed
  run is in progress, in addition to refreshing when the tab is opened.

## Impact

- **Frontend only.** A small hook that owns an interval and calls the existing
  `fetchHistory` callback in `NetworkDetailPage`, plus the in-flight predicate.
  No change to `fetchHistory` itself, which already refreshes rows in place and
  only shows the loading indicator on first load.
- **Backend**: none. No new endpoints, no change to `StatusUpdater`.
- **Load**: at most one extra `GET /api/v1/action-history/?campus_network_id={id}`
  per 15 s, per user sitting on a History tab that has a running build, and only
  for as long as it is running.
- **Tests**: polling starts when a `Running` row is present; stops on transition
  to terminal; stops on tab change and unmount; no request is issued when nothing
  is running; rows remain visible across a refresh.

### Out of Scope

- **Server-sent events per row.** The SSE console stream already exists for
  watching a single run in detail; opening one connection per row to keep a list
  fresh is disproportionate.
- **Changing `StatusUpdater`** — its 30 s cadence and its terminal-state contract
  are unchanged.
- **The dashboard feed itself**, which is a separate change that consumes the
  hook introduced here.
- **Other tabs.** Hosts, Workbook and Actions have no time-varying server state
  and are left alone.
- **Refreshing the `CampusNetwork.status` field** shown elsewhere on the page.

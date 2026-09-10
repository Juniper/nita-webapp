## Why

The landing page is dead weight. `DashboardPage` is nineteen lines that greet the
user and point at a sidebar which is already on screen:

```tsx
<h2>Welcome{user?.username ? `, ${user.username}` : ''}</h2>
<p>Use the sidebar to navigate to Network Types or Networks.</p>
```

It is the first screen after login and the destination of the first nav entry,
and it tells the user nothing they did not already know.

Meanwhile the application has **no cross-network view at all**. Action history is
only reachable one network at a time, through the History tab of a network detail
page. Answering "did anything fail overnight?" means opening every network in
turn. There is nowhere in the product that answers it.

The data to answer it already exists: `GET /api/v1/action-history/` returns runs
newest-first with `network_name`, `action_name`, `category_name` and
`jenkins_job_name` denormalised onto each entry specifically so that "consumers
can display context without extra look-ups" — a consumer that has never existed.

## What Changes

- **`DashboardPage` becomes a recent-activity feed**, replacing the welcome text.
- **Ten rows, one request.** The page issues a single unfiltered
  `GET /api/v1/action-history/` and displays at most ten entries. There are no
  counters, no totals and no aggregates — the dashboard is a **tripwire**, not a
  report. Complete history stays where it already lives, per network.
- **Sorted by what needs attention, not purely by time.** Entries are grouped —
  in-progress first, then runs needing attention (`Failure` / `Failed` /
  `Aborted` / `Unstable`), then everything else — and ordered newest-first within
  each group. Because in-progress runs sort first, active work can never be
  pushed off the list by newer completed runs.
- **Each row deep-links to its network's History tab** at
  `/networks/{campus_network_id}?tab=history`, an already-supported route.
- **Each row names who triggered it**, using the `triggered_by_username` field
  added by the `record-action-triggered-by` change, rendering `—` when unknown.
- **The feed refreshes itself while work is in flight**, reusing the 15-second
  polling hook introduced by the `refresh-inflight-action-status` change. A quiet
  dashboard makes no background requests.
- **Scope follows network visibility.** The feed shows exactly what the caller
  may see, per the `scope-action-history-visibility` change: a `role=user` sees
  their own and their teams' networks; `power_user` and `admin` see everything,
  consistent with how they already see all networks.
- **An empty state** replaces the feed when there is no activity, so a new
  account still lands somewhere coherent.

## Capabilities

### Added Capabilities

- `spa-dashboard`: the dashboard landing page presents a scoped, self-refreshing
  recent-activity feed with deep links into each run's network history.

### Modified Capabilities

- `frontend-skeleton`: the Dashboard Shell Placeholder requirement is superseded
  by the real dashboard.

## Impact

- **Frontend only.** `DashboardPage.tsx` is rewritten; it consumes the polling
  hook from `refresh-inflight-action-status` and the `triggered_by_username`
  field from `record-action-triggered-by`.
- **Backend**: none. No new endpoints, no new query parameters, no serializer
  changes. Every field the page renders is already returned.
- **Routing**: none. The SPA allowlist in `ngcn_workbench/urls.py` already routes
  `/` to `spa_index`, and `/networks/{id}?tab=history` is already a supported
  deep link.
- **Load**: one `GET /api/v1/action-history/` per dashboard visit, plus one per
  15 s only while a displayed run is in progress.
- **Tests**: ordering across the three groups; the ten-row cap; deep-link targets;
  `—` for unknown actor; empty state; polling starts and stops with in-flight
  work.

### Depends On

- `scope-action-history-visibility` — without it, an unfiltered feed would
  disclose every network's activity to every user. This is a hard prerequisite.
- `record-action-triggered-by` — supplies the actor column.
- `refresh-inflight-action-status` — supplies the polling hook.

### Out of Scope

- **Counters and aggregates** ("3 running / 12 succeeded"). They cannot be
  computed correctly from a paginated endpoint without a new summary endpoint,
  and with ten visible rows they would restate what is already on screen.
- **Network status.** `CampusNetwork.status` (for example a network stuck in
  `Initializing`) does not appear in an action-history feed. A real blind spot,
  deliberately deferred.
- **Lifecycle runs** (network create/delete, network-type upload). They live in a
  separate model with a separate endpoint.
- **Filtering, searching or paging the feed.** It is ten rows; history is
  elsewhere.
- **Role-specific dashboard layouts.** Power users and admins get the same
  component with a wider scope; tuning their noisier feed is a later question.
- **Live console streaming from the dashboard.** Rows link through to the History
  tab, which already has the console viewer.

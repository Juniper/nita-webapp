## Context

Everything this page renders already exists on the wire. `ActionHistorySerializer`
uses `fields = "__all__"` plus explicit denormalised fields, so a single
`GET /api/v1/action-history/` entry carries:

```
id, timestamp, status, jenkins_job_build_no,
campus_network_id, action_id, category_id,
action_name, category_name, network_name, jenkins_job_name
                                    + triggered_by_username  (added by change 2)
```

`campus_network_id` is the network's primary key, which is what the deep link
needs. `NetworkDetailPage` reads its active tab from the query string
(`parseTabParam(searchParams.get('tab'))`) and its refresh effect is already
annotated as handling deep links, so `/networks/{id}?tab=history` is a supported
entry point requiring no routing work.

Status is an unconstrained `CharField`. Values in practice come from two writers:
the trigger endpoint writes `"Running"`, and `StatusUpdater` writes
`result.title()` from Jenkins — `Success`, `Failure`, `Aborted`, `Unstable`.
There is no enumeration and no guarantee the set is closed.

DRF paginates at `PAGE_SIZE: 50`, newest-first.

## Goals / Non-Goals

**Goals:**
- Replace the placeholder landing page with something that answers "is anything
  wrong?" at a glance.
- One request, ten rows, no new backend surface.
- Every row is a route to the place where the question can be answered fully.

**Non-Goals:**
- Counters, aggregates, filtering, paging, network status, lifecycle runs,
  per-role layouts, or console streaming on the dashboard.

## Decisions

### Decision 1: A tripwire, not a report

**Choice**: Ten rows, no counters, no totals.

**Rationale**: Complete history is already available per network, so the
dashboard does not need to be exhaustive — it needs to be *noticed*. Ten rows is
enough to reveal that something failed and not enough to invite reading it as an
authoritative record.

This also removes the entire class of problems that counters would introduce:
computing "12 succeeded" correctly requires either a new aggregate endpoint or
walking every page, and computing it from one page would produce a number that
looks authoritative and is wrong. With ten visible rows, a counter would restate
what the user can already see.

### Decision 2: Sort by attention, then recency

**Choice**: Three groups, each newest-first:

```
  1  in progress   status == "Running"
  2  attention     status in {Failure, Failed, Aborted, Unstable}
  3  everything else
```

Comparison is case-insensitive to absorb the free-text column.

**Rationale**: A purely chronological feed buries the thing you opened the page
to find. A busy network's successful runs would push another network's failure
off a ten-row list within minutes — the tripwire would develop exactly the blind
spot that makes a monitoring surface worse than none, because people start
trusting it.

Grouping also gives the "in-progress work is never lost" property for free: since
`Running` sorts first, active runs cannot be displaced by newer completed ones.
No special-case merge logic is required.

**`Unstable` is grouped with failures.** In Jenkins it means the build ran but
tests failed — for a NITA test action that is precisely the signal this page
exists to surface. The asymmetry of errors decides it: mis-grouping a successful
run as needing attention costs a glance, mis-grouping a failed one costs a missed
failure.

### Decision 3: Match the known in-flight value, not the terminal set

**Choice**: Detect in-progress work by `status === "Running"` (case-insensitive);
treat the attention set as a known-value list; everything else falls through to
group 3.

**Rationale**: `status` is unconstrained, so no client can enumerate all terminal
values safely — but the in-flight value *is* known, because the trigger endpoint
writes exactly `"Running"` and `StatusUpdater` selects on exactly `"Running"`.
Testing for the one reliable value and letting unknown strings fall into the
neutral group means a new status string degrades to "shown, not highlighted"
rather than to "silently miscounted".

### Decision 4: One request, client-side selection

**Choice**: Fetch page 1 of `GET /api/v1/action-history/` (50 newest, scoped by
change 1), sort per Decision 2, display the first ten.

**Rationale**: No new endpoint, no new query parameters, and the page-1 window is
five times the display size, so the selection has ample material. Adding a
`?limit=` parameter or a summary endpoint would be backend work in service of a
ten-row list.

**Consequence (accepted)**: a run still `Running` but older than the fifty most
recent entries would not be fetched, and so would not appear. This requires fifty
newer runs to complete during one build's lifetime within the user's scope —
implausible at current volumes, and the failure mode is a missing row rather than
a wrong one. Recorded in Open Questions.

### Decision 5: Deep-link every row to the network's History tab

**Choice**: Each row links to `/networks/{campus_network_id}?tab=history`.

**Rationale**: A status board that shows a problem and then hands the user back
to navigation is an anxiety generator. The History tab is where the console
viewer, the Jenkins link and the Robot summary already live, so the dashboard's
job ends at getting the user there. It costs nothing: the route, the query
parameter and the network id are all already available.

### Decision 6: Reuse the polling hook rather than re-implementing

**Choice**: Drive `usePollWhile` from "at least one displayed row is `Running`",
at the same 15-second interval as the History tab.

**Rationale**: The staleness bug this hook fixes applies identically here — more
so, since the dashboard is a page people leave open. Sharing one mechanism keeps
the two surfaces from drifting, and keeps the interval decision in one place. A
dashboard with nothing running issues no background requests.

### Decision 7: Same feed for every role, wider scope for some

**Choice**: One component. `power_user` and `admin` see all activity because
change 1 scopes the endpoint that way, mirroring how they already see all
networks.

**Rationale**: Consistency with networks, and no role-branching logic to
maintain. The accepted downside is that the busiest users get the least useful
feed — an admin's ten rows may all belong to other people. Tuning that (scoping
admins to their own networks by default, or adding a toggle) is a later change
that this one does not foreclose.

## Risks / Trade-offs

- **The admin feed may be noise.** See Decision 7 — accepted, adjustable later.
- **Blind spot: network status.** A network stuck in `Initializing` performs no
  action, so it never appears here. The dashboard says "nothing is wrong" when
  something might be. Explicitly out of scope, and worth stating plainly rather
  than letting the page imply completeness.
- **Blind spot: lifecycle runs.** Network create/delete and type uploads live in
  `LifecycleRun` and are likewise invisible here.
- **Free-text status.** Mitigated by Decision 3 (unknown values degrade to
  neutral) rather than eliminated.
- **Hard dependency on the scoping fix.** Shipping this page before
  `scope-action-history-visibility` would turn a latent data leak into the
  application's landing page. Sequencing is a correctness requirement, not a
  preference.
- **Relative timestamps.** "2m ago" rendered from a mount-time snapshot goes
  stale if the page sits open with nothing running (no polling, so no re-render).
  Minor; an absolute timestamp on hover is the cheap mitigation.

## Migration Plan

No schema, data or API change. `DashboardPage` is replaced in place; the route,
the nav entry and the SPA allowlist are unchanged. Must ship after its three
dependencies, of which `scope-action-history-visibility` is a correctness gate
rather than merely an ordering preference.

## Open Questions

- **Is a fifty-row fetch window always sufficient?** See Decision 4. If networks
  become busy enough for this to bite, the answer is a `?status=` filter or a
  small dedicated endpoint — both backend work deliberately avoided for now.
- **Should the empty state differ for a brand-new account** (no networks at all)
  versus an established one with no recent runs? The first is an onboarding
  moment and could point at "create a network"; the second is simply quiet.
- **Should the page acknowledge its blind spots** — for example a line linking to
  Networks for current network status — so users do not read "no failures" as
  "everything is healthy"?
- **A "last updated" indicator?** Shared with the polling change; answering it
  once for both surfaces would be better than twice.

## Context

Three pieces already exist and are not changing:

- **`StatusUpdater`** (`ngcn/statusupdater.py`) runs a daemon thread on a 30 s
  interval, selecting `ActionHistory.objects.filter(status="Running")`, asking
  Jenkins for each build's result, and writing back `result.title()` — `Success`,
  `Failure`, `Aborted`, `Unstable`. `"Running"` is the exact string it keys on.
- **`fetchHistory`** in `NetworkDetailPage` fetches the list and then the Robot
  Framework summaries for TEST-category rows. It already updates rows in place
  and only sets the loading indicator when there is no data yet.
- **`useApiResource`** exposes a `reload()` explicitly documented as "safe to
  call from event handlers", i.e. designed to be driven from outside its own
  effect. The History tab does not use it (it has the extra robot-summary fetch),
  but the same pattern applies.

The `actions` capability already requires that action-history status reaches a
terminal value after the build completes, and `StatusUpdater` satisfies it. The
defect is entirely in when the client asks.

## Goals / Non-Goals

**Goals:**
- A user watching the History tab sees a run reach its terminal state without
  interacting with the page.
- Screens with nothing in flight issue no background requests.
- The mechanism is reusable by the dashboard feed.

**Non-Goals:**
- Per-row SSE, changes to `StatusUpdater`, other tabs, or `CampusNetwork.status`.

## Decisions

### Decision 1: Poll at 15 seconds

**Choice**: A fixed 15 s interval.

**Rationale**: `StatusUpdater` runs on 30 s, so the database cannot change more
often than that. Polling at 15 s guarantees observing a transition within one
updater cycle — worst case one full 30 s cycle plus one 15 s poll — while
staying an order of magnitude cheaper than a per-second refresh. Polling faster
than 15 s buys nothing, because the data it is reading is itself only 30 s
fresh.

Rejected: matching the updater's 30 s exactly, which risks phase alignment
making an update appear a full cycle late; and exponential backoff, which adds
state for a loop that is short-lived by construction.

### Decision 2: Poll only while something is `Running`

**Choice**: Start the interval when the displayed list contains at least one
entry with `status === "Running"`; stop as soon as none do.

**Rationale**: This is what makes the feature nearly free. The overwhelmingly
common state is a History tab full of finished runs, which under this rule costs
exactly zero requests. It also self-terminates: the condition that starts
polling is the same condition the polling is trying to clear, so the loop ends
on its own.

Keying on the literal string `"Running"` is deliberate. `status` is an
unconstrained `CharField` holding Jenkins vocabulary, so there is no reliable
enumeration of terminal values — but there *is* a reliable in-flight value,
because `"Running"` is exactly what the trigger endpoint writes and exactly what
`StatusUpdater` selects on. Testing for the one known non-terminal value is
sound where testing for the set of terminal values would not be.

**Consequence (accepted)**: if a row is somehow left in `Running` permanently —
for example a build Jenkins lost track of — the tab polls every 15 s for as long
as it stays open. Bounded by the user's attention rather than by the code, and a
symptom worth seeing rather than hiding.

### Decision 3: Silent refresh, no loading state

**Choice**: A poll reuses the existing `fetchHistory`, which keeps rows rendered
and suppresses the loading indicator when data is already present.

**Rationale**: The existing spec already requires this for tab re-entry
("already-displayed rows SHALL remain visible while refreshing"). A poll is the
same operation on a timer, so it inherits the same rule. Anything else would
flash the table every 15 s.

**Amendment made during implementation**: `fetchHistory` also called
`setRobotSummaries({})` before re-fetching the Robot Framework summaries. On a
tab re-entry that reset is invisible, because the table is being re-rendered
anyway. On a 15-second poll it is not: every displayed test result would blank
out and then reappear as each summary request resolved — a flash on a cadence,
which is exactly what this decision forbids. The reset was therefore removed and
summaries are now **merged** into the existing map. Stale entries for rows that
disappear are harmless, since summaries are only read for rows currently
rendered. This was the one change to `fetchHistory` beyond adding cancellation;
task 2.3's "verify, do not change" refers to the loading indicator, which was
verified unchanged.

### Decision 3a: Cancellation is per-fetch, latest-wins

**Choice**: `fetchHistory` owns an `AbortController` in a ref. Each call aborts
the previous request before starting its own, and the tab effect's cleanup
aborts on tab change and unmount. Error and loading state are only written when
the signal was not aborted.

**Rationale**: Polling makes overlapping requests possible for the first time —
a slow response can still be in flight when the next interval fires, and without
latest-wins ordering a stale response could overwrite fresher rows. Guarding the
`catch` on `signal.aborted` also prevents a cancelled request from rendering
"Failed to load history", which is what a naive abort would produce on every tab
change. The Robot summary sub-requests share the same signal, so leaving the tab
cancels the whole fan-out rather than letting it resolve into an unmounted page.

### Decision 4: Extract a reusable hook

**Choice**: A small hook — something like
`usePollWhile(active: boolean, callback: () => void, intervalMs: number)` — that
owns the interval, and is given the in-flight predicate by its caller.

**Rationale**: The dashboard change needs the identical behaviour over a
different list and a different fetch function. Extracting it here, where it has
one real consumer and a concrete test, avoids the dashboard either duplicating
the logic or triggering a refactor of this page. The hook deliberately knows
nothing about action history — it takes a boolean and a callback — so it does
not become a dumping ground.

### Decision 5: Cleanup on tab change and unmount

**Choice**: The interval is cleared when the History tab is left, when the
component unmounts, and whenever the in-flight condition goes false. In-flight
requests are aborted rather than left to resolve into unmounted state.

**Rationale**: `fetchHistory` also issues N robot-summary requests per refresh;
leaking a timer across navigation would multiply that. `useApiResource` already
establishes the `AbortController` pattern in this codebase.

## Risks / Trade-offs

- **Request amplification via robot summaries.** Each refresh fetches the list
  *plus* one robot-summary request per TEST-category row. On a network with many
  test runs, a 15 s poll multiplies that. Mitigated by polling only while
  something is running; if it proves heavy, the follow-up is to re-fetch
  summaries only for rows whose status changed. Noted rather than pre-optimised.
- **A permanently-`Running` row polls forever** while the tab is open — see
  Decision 2.
- **Background tabs keep polling.** The interval does not currently pause when
  the document is hidden; see Open Questions.
- **Wall-clock drift.** `setInterval` in a throttled background tab fires
  irregularly. Harmless here: every poll is an idempotent GET and the UI reflects
  whatever the latest response says.

## Migration Plan

No schema, data or API change. Frontend-only, additive, and independently
shippable — it depends on nothing and fixes an existing user-visible defect on
its own.

## Open Questions

- **Pause polling when the document is hidden?** Using
  `document.visibilityState` would stop background tabs polling and refresh once
  on re-focus. Cheap and clearly correct, but it adds a second trigger path and
  its own tests; left out to keep the first version to one mechanism. Worth
  adding if background traffic proves noticeable.
- **Should the tab show a "last updated" hint?** A silent refresh gives the user
  no signal that the list is live rather than frozen — the same ambiguity that
  produced the original "stuck in Running" report, in milder form. Deferred, but
  the dashboard change may want to answer it for both surfaces.
- **Re-fetch robot summaries selectively?** See the amplification risk above.

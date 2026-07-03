## Context

Two "View" affordances in the SPA show a Jenkins build's console:

1. **Action-history** rows on the network detail page (`NetworkDetailPage.tsx`)
   — one per triggered action run for a network.
2. **Lifecycle-runs** rows in `LifecycleHistoryModal.tsx` — network
   create/delete runs (opened from the Networks page) and network-type load runs
   (opened from the Network Types page).

Both currently do a one-shot `fetch` of a static console endpoint. The trigger,
create, delete, and load flows already use live SSE consoles via the
`useJenkinsStream` hook (generic job stream) or a manual `EventSource`
(`handleTrigger`).

## Goals

- Every history "View" opens a **live** console (SSE) that keeps updating.
- Reuse the existing streaming infrastructure rather than adding new endpoints.
- Keep the same UX affordances: streaming/finished state, error handling, empty
  placeholder, and dismissable viewer.

## Decisions

### Reuse existing SSE endpoints (no backend change)

- Action-history View → `GET /api/v1/action-history/{id}/stream/`
  (`ActionHistoryViewSet.stream`, already implemented).
- Lifecycle-runs View → `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`
  (`JenkinsJobStreamView`, already implemented).

Both call the shared `jenkins_jobs.stream_response(...)` generator, which polls
Jenkins progressive text, strips ANSI codes, replays the full log for a finished
build, and terminates with `done`/`error`/`timeout`. Because completed builds
replay fully and then emit `done`, a single streaming path serves both running
and finished builds — no separate "historical" fetch is needed.

### Generalize `useJenkinsStream`

The hook currently only exposes `start(jobName, buildNo)`, which builds the
generic job stream URL. Add a `startUrl(url)` that streams from an arbitrary SSE
URL, and implement `start` in terms of it. This lets the action-history
`.../stream/` route (a different URL shape) reuse the same battle-tested
`done`/`error`/`timeout` handling.

### Viewer state mapping

The modal/console body renders from the hook's `lines` + `state`:

- `streaming` → show lines with a "(streaming…)" indicator.
- `done` with no lines → show the "No console output available." placeholder.
- `error` / `timeout` → show an error/timeout message.

`reset()` is called when the viewer is dismissed (Close/Back/backdrop) so the
`EventSource` is closed and no orphaned connection remains.

## Alternatives Considered

- **Keep static fetch, add polling**: rejected — reinvents what the SSE stream
  already does and doubles the console code paths.
- **New "historical stream" endpoint**: rejected — the existing streams already
  replay completed builds, so no new endpoint is warranted.

## Risks

- A long-finished build whose Jenkins records were rotated will stream nothing
  and emit `done`; the placeholder covers this (same as the old empty case).
- Each open viewer holds one `EventSource`; `reset()` on dismiss prevents leaks.

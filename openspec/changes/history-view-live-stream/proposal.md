## Why

The history "View" actions in the SPA currently fetch a **static snapshot** of a
Jenkins build's console output:

- The network detail page's action-history rows call
  `GET /api/v1/action-history/{id}/console/`.
- The Networks and Network Types lifecycle history modal
  (`LifecycleHistoryModal`) calls
  `GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>`.

Both endpoints return a one-shot text blob. If the user opens View while a job is
still running they see a partial, frozen log ("Build is queued or console output
is not yet available.") and must close and reopen to get more. This is
inconsistent with the trigger / create / delete / load flows, which already open
a **live SSE console** that streams output until the build finishes.

The backend already exposes live SSE stream endpoints for both cases
(`GET /api/v1/action-history/{id}/stream/` and the generic
`GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`). These streams also
replay the full console for a completed build and then emit `done`, so a single
streaming code path serves both in-progress and finished builds. This change
switches every history "View" instance to that live stream so the console keeps
updating in real time and matches the rest of the app.

## What Changes

- The action-history **View** on the network detail page SHALL open a live
  console that streams `GET /api/v1/action-history/{id}/stream/` instead of
  fetching the static `.../console/` snapshot.
- The lifecycle-runs **View** in `LifecycleHistoryModal` (used by both the
  Networks and Network Types history buttons) SHALL open a live console that
  streams `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/` instead of
  fetching the static `/api/v1/lifecycle-runs/console/` snapshot.
- The shared `useJenkinsStream` hook SHALL gain the ability to stream from an
  arbitrary SSE URL (so the action-history `.../stream/` route can reuse it
  alongside the generic job stream URL).
- The console viewers SHALL show a streaming state indicator, render an error
  message on stream failure/timeout, and show a placeholder when a finished
  build produced no output — preserving the existing loading/error/empty and
  dismissable behavior, now with live semantics.

No backend, database, or API-contract changes are required: both SSE endpoints
already exist and already replay completed builds.

## Capabilities

### Modified Capabilities
- `spa-networks`: The action-history console viewer and the Networks lifecycle
  history viewer change from a static console fetch to a live SSE stream.
- `spa-network-types`: The Network Types lifecycle history viewer changes from a
  static console fetch to a live SSE stream.

## Impact

- **Frontend only**:
  - `frontend/src/components/LifecycleConsole.tsx` (`useJenkinsStream` gains a
    URL-based start).
  - `frontend/src/pages/NetworkDetailPage.tsx` (action-history View streams).
  - `frontend/src/components/LifecycleHistoryModal.tsx` (lifecycle View streams).
- **No backend / API / DB changes**: the `.../stream/` endpoints already exist
  and already handle completed builds (replay + `done`).
- **Behavior change**: opening View now keeps updating while a job runs; the
  static `.../console/` and `/lifecycle-runs/console/` endpoints are no longer
  called by the SPA (they remain available on the backend).

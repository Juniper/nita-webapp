## 1. Generalize the shared stream hook

- [x] 1.1 In `frontend/src/components/LifecycleConsole.tsx`, add `startUrl(url:
  string)` to `useJenkinsStream` that opens an `EventSource` on the given URL
  with the existing `message`/`done`/`error`/`timeout` handling.
- [x] 1.2 Reimplement `start(jobName, buildNo)` in terms of `startUrl` using
  `lifecycleStreamUrl(...)`, and export `startUrl` from the hook.

## 2. Stream the action-history View (network detail page)

- [x] 2.1 In `frontend/src/pages/NetworkDetailPage.tsx`, replace the static
  `handleViewConsole` fetch of `/api/v1/action-history/{id}/console/` with a live
  stream of `/api/v1/action-history/{id}/stream/` using a `useJenkinsStream`
  instance and `startUrl`.
- [x] 2.2 Render the console viewer modal from the hook's `lines`/`state`:
  streaming indicator, error/timeout message, and the "No console output
  available." placeholder when a finished stream produced no lines.
- [x] 2.3 Call `reset()` when the modal is dismissed (Close button and backdrop)
  so the `EventSource` is closed.

## 3. Stream the lifecycle-runs View (Networks + Network Types history)

- [x] 3.1 In `frontend/src/components/LifecycleHistoryModal.tsx`, replace the
  static `viewConsole` fetch of `/api/v1/lifecycle-runs/console/` with
  `useJenkinsStream().start(run.job_name, run.build_no)`
  (`/api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`).
- [x] 3.2 Render the console body from the hook's `lines`/`state` with the same
  streaming/error/empty semantics, and `reset()` on Back, Close, and backdrop
  dismiss.

## 4. Verify

- [ ] 4.1 `npm run build` (via the container build) type-checks and bundles.
- [ ] 4.2 Deploy and confirm the action-history View streams live output and a
  finished build replays its full log then stops at a "done" state.
- [ ] 4.3 Confirm the Networks and Network Types history View stream live output.

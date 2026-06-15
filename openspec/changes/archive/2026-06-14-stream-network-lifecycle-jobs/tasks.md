## 1. Shared Jenkins job library

- [x] 1.1 Create `build-and-test-webapp/nita-webapp/ngcn_workbench/ngcn/jenkins_jobs.py`.
- [x] 1.2 Move `_jenkins_progressive_text_generator` from `ngcn/api/views.py`
  into the library as `progressive_text_events(job_name, build_no)` (unchanged
  behavior: queued-404 tolerance, ANSI stripping, `done`/`error`/`timeout`).
- [x] 1.3 Add `stream_response(job_name, build_no)` that wraps the generator in a
  `StreamingHttpResponse` and sets `Content-Type: text/event-stream`,
  `Cache-Control: no-cache`, and `X-Accel-Buffering: no`.
- [x] 1.4 Add `invoke_job(job_name, build_params=None, files=None) -> int` that
  reserves `nextBuildNumber`, performs the authenticated `CrumbRequester`
  invoke, retries once on a `Forbidden` crumb error, and raises on unreachable
  Jenkins.

## 2. Refactor existing trigger/stream onto the library

- [x] 2.1 Refactor `CampusNetworkViewSet.trigger` to call `invoke_job` instead
  of its inline crumb/invoke block, preserving the existing 202 +
  `action_history_id` contract.
- [x] 2.2 Refactor `ActionHistoryViewSet.stream` to call
  `jenkins_jobs.stream_response(job_url, build_no)`.
- [x] 2.3 Refactor `ngcn/views.deleteCampusTypeView` to call `invoke_job`.

## 3. Generic authenticated stream endpoint

- [x] 3.1 Add an `IsAuthenticated` view for
  `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/` that returns
  `jenkins_jobs.stream_response(job_name, build_no)`.
- [x] 3.2 Register the route with `job_name` constrained to `[A-Za-z0-9_.\-]+`
  and `build_no` to `[0-9]+` in the API URLconf.
- [x] 3.3 Ensure the SSE renderer / `text/event-stream` content negotiation is
  applied to this endpoint (as done for the action-history stream).

## 4. Lifecycle run persistence and history API

- [x] 4.1 Add a `LifecycleRun` model (`kind`, `subject`, `job_name`, `build_no`,
  `timestamp`, `status`) and generate its Django migration.
- [x] 4.2 Add a serializer and a read-only `LifecycleRunViewSet` at
  `/api/v1/lifecycle-runs/`, ordered newest-first and filterable by `?kind=`,
  `IsAuthenticated`.
- [x] 4.3 Add a `console` detail action
  `GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>` that resolves
  the supplied `job_name`/`build_no` via `get_build_console_output`, strips ANSI
  codes, and returns a placeholder when output is not yet available.
- [x] 4.4 Register the viewset route in the API URLconf.

## 5. Non-blocking lifecycle endpoints

- [x] 5.1 Rewrite `CampusNetworkViewSet.create` to persist the row immediately
  with status `Initializing`, call `invoke_job("network_template_mgr", {...,
  operation: "create"})`, and return `201` with the network data plus `job_name`
  and `build_no`; return `503` (no row persisted) if Jenkins is unreachable.
  Remove the blocking wait and the failure-path cleanup delete.
- [x] 5.2 Rewrite `CampusNetworkViewSet.destroy` to reserve the build number,
  remove the row immediately, call `invoke_job("network_template_mgr", {...,
  operation: "delete"})`, and return `202` with `job_name` and `build_no`;
  return `503` (row not removed) if Jenkins is unreachable. Remove the blocking
  wait.
- [x] 5.3 Make `CampusTypeViewSet.upload` (network-type load) non-blocking:
  invoke `network_type_validator` via `invoke_job`, return `202` with `result`,
  `name`, `job_name`, and `build_no`, without waiting for the build; keep the
  missing-file `400` and unreachable-Jenkins `503` paths.

## 6. Infra and API docs

- [x] 6.1 Add an nginx location for `/api/v1/jenkins/jobs/` with
  `proxy_buffering off`, `proxy_cache off`, and `proxy_read_timeout 1850s`.
- [x] 6.2 Update `openapi.yaml`: add the generic stream endpoint, the
  `/api/v1/lifecycle-runs/` list and `console` endpoints, and update the
  create/delete/network-type-upload response schemas to include `job_name` and
  `build_no` and the new status codes.

## 7. Frontend

- [x] 7.1 Add an API client helper that builds the lifecycle stream URL
  `/api/v1/jenkins/jobs/{job_name}/{build_no}/stream/` and reuse the existing
  console panel / EventSource handling (named `done`/`error`/`timeout`
  listeners).
- [x] 7.2 On successful network create, open the console panel using the
  returned `job_name`/`build_no`.
- [x] 7.3 On successful network delete, open the console panel using the
  returned handle.
- [x] 7.4 On successful network-type upload, open the console panel using the
  returned handle.
- [x] 7.5 Add a History button to the top-level Networks table that opens a
  lifecycle history view listing `network_create`/`network_delete` runs from
  `GET /api/v1/lifecycle-runs/`, with a per-run console viewer fetching
  `GET /api/v1/lifecycle-runs/{id}/console/`.
- [x] 7.6 Add a History button to the top-level Network Types table that opens a
  lifecycle history view listing `network_type_load` runs, with the same per-run
  console viewer.

## 8. Verification

- [x] 8.1 Backend: exercise create/delete/upload return the handle without
  blocking, and the generic stream endpoint streams console output and rejects
  unauthenticated requests with `403`.
- [x] 8.2 Backend: `GET /api/v1/lifecycle-runs/` lists runs (filterable by
  `kind`) and `/console/` returns historical output; both reject unauthenticated
  requests with `403`.
- [x] 8.3 Confirm the existing `trigger` + `action-history` stream still work
  after the refactor.
- [x] 8.4 Build the frontend (`npm run build` in `frontend/`) and confirm no
  TypeScript errors.
- [x] 8.5 Manually verify in the SPA: creating a network, deleting a network,
  and loading a network type each open the live console panel and stream to a
  `done` terminator; and the Networks and Network Types History buttons list
  past runs and show their historical console output.

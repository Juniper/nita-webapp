## Context

Today three lifecycle operations trigger a Jenkins job and **block the HTTP
request** until the build finishes:

- `CampusNetworkViewSet.create` → `network_template_mgr` (`operation=create`),
  via `wait_and_get_build_status`. Persists the row only on success; on failure
  it runs a cleanup delete and returns `502`/`503`.
- `CampusNetworkViewSet.destroy` → `network_template_mgr` (`operation=delete`),
  also blocking; removes the row only on success.
- `CampusTypeViewSet.upload` → `NetworkTypeParser.parseProjectFile`, which
  invokes `network_type_validator` and blocks.

Meanwhile `CampusNetworkViewSet.trigger` already does the right thing: it makes
an **authenticated crumbed** Jenkins invocation, records a build number, returns
`202` immediately, and the SPA opens
`GET /api/v1/action-history/{id}/stream/`. That stream is produced by
`_jenkins_progressive_text_generator(job_url, build_no)` — which is **already
generic** (it takes a raw job name and build number) — wrapped in a
`StreamingHttpResponse` with `X-Accel-Buffering: no`.

The crumb-invoke logic is duplicated across `trigger`,
`ngcn/views.deleteCampusTypeView`, and the blocking create/delete paths.

Constraints:
- `ActionHistory` requires non-null `action_id`, `category_id`, and
  `campus_network_id`. It cannot represent a network that does not exist yet
  (create) or a network-type job (no `CampusNetwork`). So lifecycle streaming
  cannot reuse the action-history stream URL.
- `network_template_mgr` is a **single shared Jenkins job** (not per-network);
  concurrent creates/deletes are distinguished only by their reserved build
  numbers.
- nginx already disables buffering for `/api/v1/action-history/` streams; a new
  path needs the same treatment.

## Goals / Non-Goals

**Goals:**
- Make network create, network delete, and network-type load **non-blocking**,
  returning a streaming handle so the SPA shows a live console (the console is
  the user's incentive to wait).
- Share one backend library for Jenkins **invoke** and **console stream** across
  trigger, create, delete, and network-type load.
- Provide a **generic, authenticated** SSE endpoint keyed by `job_name` +
  `build_no`, independent of `ActionHistory`.
- Reuse the existing SPA console panel for all four flows.
- **Persist each lifecycle run** so the top-level Networks and Network Types
  tables can offer a History view (like the per-network triggered-actions
  history) with access to each run's historical Jenkins console output.

**Non-Goals:**
- Changing the per-network `trigger` API contract or its `action-history`
  history list (it keeps using `ActionHistory`; only its internals are
  refactored onto the shared library).
- Reusing `ActionHistory` for lifecycle runs (it requires a non-null network and
  action, which create/network-type runs do not have — a dedicated model is used
  instead).
- Changing the Jenkins jobs themselves or their build parameters.
- Server-side interpretation of build success/failure for create/delete; the
  client reads the streamed `done`/`error` terminators.

## Decisions

### Decision: Extract a shared `ngcn/jenkins_jobs.py` library
Move the crumb-authenticated invoke and the console generator into one module:
- `invoke_job(job_name, build_params=None, files=None) -> int` — captures
  `nextBuildNumber`, performs the authenticated `CrumbRequester` invoke, retries
  once on `Forbidden`, raises on unreachable. This is the logic currently inline
  in `trigger`/`deleteCampusTypeView`.
- `progressive_text_events(job_name, build_no)` — the existing
  `_jenkins_progressive_text_generator` moved verbatim (it is already generic).
- `stream_response(job_name, build_no) -> StreamingHttpResponse` — wraps the
  generator and sets `Content-Type`, `Cache-Control: no-cache`, and
  `X-Accel-Buffering: no`.

`trigger` and `ActionHistoryViewSet.stream` are refactored to call these,
resolving `job_name = action.jenkins_url + "-" + network.name` themselves.

*Alternative considered:* leave duplication in place and only add the generic
endpoint. Rejected — the user explicitly asked for shared libraries and
consistency; duplication is the current source of drift.

### Decision: Generic stream endpoint keyed by job name + build number
Add `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/` (function-based
DRF view or a small APIView), `IsAuthenticated`, using `stream_response`. The
`{job_name}` segment is constrained to the safe charset Jenkins job names use
(`[A-Za-z0-9_.\-]+`) to avoid path/SSRF abuse, and `{build_no}` to `[0-9]+`.

*Alternative considered:* make `ActionHistory.campus_network_id` nullable and
create history rows for lifecycle jobs. Rejected — larger blast radius (schema
migration, history-list semantics) for jobs that are not per-network actions.

### Decision: Streaming handle shape
Lifecycle endpoints return `{ "job_name": "...", "build_no": <int>, ... }`. The
SPA builds the stream URL as
`/api/v1/jenkins/jobs/${job_name}/${build_no}/stream/`. Keeping the handle as
`job_name`+`build_no` (rather than a server-built URL) mirrors how
`action-history` exposes an `id` the client turns into a stream URL.

### Decision: Optimistic persistence
- **Create**: persist the row immediately with status `Initializing`, then
  invoke. A failed build leaves an error-state row the user can delete (the
  spec documents this trade-off). Removes the need for the server-side cleanup
  delete on failure.
- **Delete**: reserve the build number, remove the row immediately, then invoke.
  The stream handle is `(network_template_mgr, build_no)`, independent of the
  removed row, so the console still works.
- **Network-type load**: register the type per existing parser behavior and
  return the validator job handle.

### Decision: `LifecycleRun` model for history
Add a dedicated model `LifecycleRun` (new table + migration) written at invoke
time, with fields: `kind` (`network_create` | `network_delete` |
`network_type_load`), `subject` (network or network-type name, stored as a
string so it survives row deletion), `job_name`, `build_no`, `timestamp`, and
`status`. It is exposed read-only via a DRF `ReadOnlyModelViewSet` at
`/api/v1/lifecycle-runs/` (filterable by `kind`) plus a `console` detail action
at `/api/v1/lifecycle-runs/{id}/console/` that resolves stored
`job_name`/`build_no` through `server.get_build_console_output` and strips ANSI
codes — mirroring `ActionHistoryViewSet.console`. Live streaming still uses the
generic `jenkins/jobs/.../stream/` endpoint; the per-run `console` endpoint
serves the *historical* (completed) output for the table's History view.

*Alternative considered:* make `ActionHistory` fields nullable and reuse it.
Rejected — it conflates per-network actions with lifecycle runs and complicates
the existing action-history list semantics. A small dedicated model is cleaner
and keeps `subject` as a plain string that survives network/type deletion.

### Decision: nginx and OpenAPI
Add an nginx location for `/api/v1/jenkins/jobs/` with `proxy_buffering off`,
`proxy_cache off`, `proxy_read_timeout 1850s` (mirroring the action-history
block). Document the new endpoint and the changed lifecycle response bodies in
`openapi.yaml`.

## Risks / Trade-offs

- **Orphaned error-state networks after a failed create** → The row remains;
  the SPA surfaces status and the user deletes it. Documented in the spec; this
  replaces the old auto-cleanup, which itself could fail silently.
- **Delete row removed before the Jenkins job succeeds** → If the delete build
  fails, the DB no longer reflects the (still partially present) deployment.
  Mitigation: the streamed console shows failure so the user can re-run delete;
  acceptable given the explicit "don't block" direction.
- **`job_name` path segment is attacker-influenced** → Mitigation: strict regex
  charset on the route plus `IsAuthenticated`; the value only ever reaches
  Jenkins' progressive-text URL for an existing job.
- **Shared `network_template_mgr` concurrency** → Distinct reserved build
  numbers keep concurrent streams separate; no shared state beyond Jenkins'
  own queue.
- **Refactor regression risk in `trigger`** → Mitigation: keep `trigger`'s
  external contract identical; only swap its internals to the shared helpers and
  cover with the existing trigger/stream scenarios.

## Migration Plan

1. Add `ngcn/jenkins_jobs.py`; move the generator and invoke logic in.
2. Refactor `trigger` and `ActionHistoryViewSet.stream` onto the library
   (no API change).
3. Add the generic stream view + URL route.
4. Add the `LifecycleRun` model + migration and the `/api/v1/lifecycle-runs/`
   list + `console` endpoints.
5. Switch `create`/`destroy`/`upload` to non-blocking, record a `LifecycleRun`
   at invoke time, and return handles.
6. Update nginx config and `openapi.yaml`.
7. Update the SPA: open the console panel on create/delete/load, and add the
   History button + history view to the Networks and Network Types tables.

**Rollback:** revert the commit; the Jenkins jobs and the `action-history`
stream are unchanged, so reverting restores the prior blocking behavior. The
only schema addition is the additive `LifecycleRun` table; rolling back can
leave the unused table in place (no destructive migration) or drop it via the
reverse migration.

## Open Questions

- Should a failed create auto-set the network `status` to a distinct
  `Failed`/`Error` value (vs leaving `Initializing`)? Leaning yes via the client
  on the `error` stream event, but the server has no post-completion hook.
- Should network-type load also persist a visible status the way networks do?
  Current parser registers on validation; left as-is unless product wants a
  pending state.

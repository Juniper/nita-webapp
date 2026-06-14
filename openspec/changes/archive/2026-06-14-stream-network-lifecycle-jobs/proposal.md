## Why

Creating and deleting a network, and loading a network type, each trigger a
Jenkins job that can take minutes to run. Today the create/delete REST calls
**block** until the Jenkins build finishes (and network-type load blocks the
same way), so the browser shows a frozen spinner with no feedback, and a slow
build can exceed proxy timeouts. The `trigger` action already solved this for
per-network actions: it returns immediately and the SPA watches a live console
stream. We should give the lifecycle jobs (network create, network delete, and
network-type load) the same live-console experience and stop blocking — the
streamed console is itself the incentive for the user to wait for completion.

## What Changes

- **BREAKING**: `POST /api/v1/networks/` no longer blocks on the Jenkins
  `network_template_mgr` create build. It persists the network row immediately
  (status `Initializing`), invokes the job, and returns a streaming handle so
  the SPA can watch the console.
- **BREAKING**: `DELETE /api/v1/networks/{id}/` no longer blocks on the Jenkins
  delete build. It captures the build number, removes the row optimistically,
  invokes the job, and returns a streaming handle.
- **BREAKING**: `POST /api/v1/network-types/upload/` (network-type load) no
  longer blocks on the `network_type_validator` build; it returns a streaming
  handle for the validation/load console.
- Add a **generic, authenticated SSE endpoint** that streams any Jenkins job's
  console keyed by job name + build number, decoupled from `ActionHistory`
  (which cannot represent a not-yet-created network or a network-type job).
- Extract the Jenkins **invoke** (authenticated crumb call) and **console
  stream** logic into a shared backend library reused by `trigger`, create,
  delete, and network-type load — so all four paths behave consistently.
- The SPA shows the same console panel (used today after `trigger`) when a
  network is created, deleted, or a network type is loaded.
- **Persist each lifecycle job run** (network create, network delete,
  network-type load) so its console output can be reviewed later, and expose a
  read-only history endpoint listing those runs.
- Add a **History** button to the top-level Networks table and the top-level
  Network Types table that opens a history view — like the per-network triggered
  actions history — listing the lifecycle job runs with the ability to view the
  historical Jenkins console output for each run.

## Capabilities

### New Capabilities
- `network-lifecycle-streaming`: A shared backend library for invoking Jenkins
  jobs with an authenticated crumb and streaming their console as SSE, plus a
  generic authenticated stream endpoint keyed by job name + build number, used
  by the non-blocking network create, network delete, and network-type load
  flows.
- `network-lifecycle-history`: Persistence of lifecycle job runs (network
  create, network delete, network-type load) and a read-only history API that
  lists those runs and serves each run's historical Jenkins console output.

### Modified Capabilities
- `networks`: Create and delete change from synchronous, block-until-complete
  behavior to non-blocking — persisting/removing the row immediately and
  returning a Jenkins streaming handle instead of waiting for the build result.
- `network-types`: Network-type load (zip upload) changes from
  block-until-complete to non-blocking, returning a Jenkins streaming handle.
- `spa-networks`: The Network create and delete flows open the live console
  panel (as the trigger flow already does) instead of waiting on a spinner. The
  top-level Networks table gains a History button that opens a lifecycle history
  view with per-run console output.
- `spa-network-types`: The network-type load flow opens the live console panel.
  The top-level Network Types table gains a History button that opens a
  lifecycle history view with per-run console output.
## Impact

- **Backend**: `ngcn/api/views.py` (`CampusNetworkViewSet.create`/`destroy`,
  `CampusTypeViewSet.upload`, `ActionHistoryViewSet.stream`, the
  `_jenkins_progressive_text_generator` helper), a new shared module
  (e.g. `ngcn/jenkins_jobs.py`), URL routing for the generic stream endpoint,
  and `openapi.yaml`.
- **Data model**: a new model/table persisting lifecycle job runs (job name,
  build number, kind, subject name, timestamp, status) plus a Django migration.
- **New API**: a read-only lifecycle history list endpoint and a per-run
  historical console endpoint.
- **Frontend**: the networks and network-types pages (new History button +
  history view), and the shared console panel component.
- **Infra**: nginx must also disable buffering / extend read timeout for the
  new generic stream path (same rules already applied to the action-history
  stream).
- **Behavior change**: a failed create now leaves a network row in an error
  state for the user to clean up, rather than the call returning an error with
  no row; clients that relied on the blocking 201/204/502 contract must adapt.

## Why

Several behavioural changes have landed on this fork's `main` since the last
spec-sync (`close-webapp-gaps` and the two trigger fixes) without corresponding
OpenSpec updates. The live specs in `openspec/specs/` now disagree with the
running code in a few important places — most notably, the
`jenkins-trigger-security` spec still asserts that all internal Jenkins
communication is **unauthenticated**, while the code now authenticates every
Jenkins call with a username/password and a CSRF crumb.

Leaving this drift unreconciled is dangerous: future contributors (human or AI)
who treat the specs as the source of truth will make decisions based on
behaviour that no longer exists. This change reconciles the specs with the
fork's current implementation in one pass.

The drifting commits (all already merged) are:

- `ba88500` — `CampusNetworkViewSet.create`/`.destroy` now run the
  `network_template_mgr` Jenkins job synchronously and only persist/remove the
  DB row on job success (502 on failure, 503 when Jenkins is unreachable).
- `fde58cb` — the trigger action now authenticates to Jenkins with
  `jenkinsapi` + `CrumbRequester` instead of posting anonymously.
- `c17a933` — removed `dynamic_ansible_workspace`; added an action-history
  console viewer to the network detail page; renamed the networks-list "View"
  button to "Modify". (Only the `dynamic_ansible_workspace` removal reached the
  specs; the UI additions did not.)
- `7ffd4f2` — the Add Network form's Host File is now a required file upload.
- `7561cc9` — the Add Network form sends an initial `status: 'Initialized'`.
- `5e40c0d` — the network-type upload uses the multipart field name
  `app_zip_file`.
- `664cbee` — `apiFetch` no longer forces `Content-Type: application/json` on
  `FormData` bodies (multipart uploads were rejected with 415).

## What Changes

- **Networks (backend)**: Document that creating and deleting a network now
  synchronously runs the `network_template_mgr` Jenkins job and reflects job
  outcome in the HTTP status (201/204 on success, 502 on job failure, 503 when
  Jenkins is unreachable; a failed create triggers a cleanup delete job).
- **Jenkins trigger security**: Reverse the "internal Jenkins communication is
  unauthenticated" requirement — all Jenkins communication from Django is now
  authenticated (username/password) with a CSRF crumb, including the trigger,
  create, and delete paths. Drop the now-false "no credentials/CSRF crumb"
  claim from the deployment-topology requirement. The 503-when-unreachable and
  SPA error-handling requirements are unchanged.
- **SPA — Networks page**: The list "Actions" column link is labelled "Modify"
  (was "View"); the Add Network form requires a Host File **upload** (file
  contents are read and sent as `host_file`) and sends `status: 'Initialized'`.
- **SPA — Network detail page**: A new action-history console viewer lets the
  user open a modal showing the Jenkins console output for any history entry via
  `GET /api/v1/action-history/{id}/console/`.
- **SPA — Network Types page**: The zip upload uses the multipart field name
  `app_zip_file`.
- **Frontend API client**: `apiFetch` must not set `Content-Type` on `FormData`
  request bodies so the browser can supply the multipart boundary.

No new product behaviour is introduced by this change — it only brings the
specs into agreement with code that already shipped.

## Capabilities

### Modified Capabilities

- `networks`: Create/Delete now run a synchronous Jenkins job and surface its
  outcome via HTTP status.
- `jenkins-trigger-security`: Internal Jenkins communication is authenticated
  (username/password + CSRF crumb), not anonymous.
- `spa-networks`: "Modify" list link; required Host File upload; initial
  `status` sent on create; new action-history console viewer.
- `spa-network-types`: Upload uses the `app_zip_file` multipart field.
- `frontend-skeleton`: The CSRF-aware API client preserves `FormData` content
  types for multipart uploads.

## Impact

- **Specs only** for the most part — the goal is reconciliation, not new code.
- Affected specs: `networks`, `jenkins-trigger-security`, `spa-networks`,
  `spa-network-types`, `frontend-skeleton`.
- Code already implements every requirement asserted here; the implementation
  tasks are limited to verifying parity, not changing behaviour.
- No database, nginx, or external API contract changes beyond what already
  shipped on `main`.

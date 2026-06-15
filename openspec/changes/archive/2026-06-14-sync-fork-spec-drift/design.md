## Context

This change is a **spec reconciliation**, not a feature. The implementation
already exists on `main`; the OpenSpec specs simply fell behind across a handful
of commits. The job here is to make the specs in `openspec/specs/` describe the
code as it actually runs today, so the spec set remains a trustworthy source of
truth.

The verified current behaviour (read from
`build-and-test-webapp/nita-webapp/ngcn_workbench/ngcn/api/views.py`,
`.../ngcn/views.py`, and the `frontend/src` tree):

- `CampusNetworkViewSet.create` and `.destroy` build the `network_template_mgr`
  Jenkins job (`operation=create` / `operation=delete`) via
  `_make_jenkins_server()` and block on `wait_and_get_build_status(...)`. The DB
  row is only persisted/removed when the job succeeds. Jenkins unreachable →
  `503`; job ran but failed → `502`; a failed create additionally runs a
  cleanup `delete` job.
- `_make_jenkins_server()` returns
  `jenkins.Jenkins(URL, username=JENKINS_SERVER_USER, password=JENKINS_SERVER_PASS)`
  — i.e. **authenticated**. The `trigger` action additionally wraps the
  `jenkinsapi` client with a `CrumbRequester` (username/password) and calls
  `.invoke(files={'data.json': ...}, build_params={'build_dir': ...})`.
- The networks-list row link reads "Modify" and points at the detail route.
- The Add Network form has a required file input whose contents are read into
  `host_file`, and the create POST body includes `status: 'Initialized'`.
- The network detail page renders a "View" button per action-history row that
  opens a modal fetching `GET /api/v1/action-history/{id}/console/`.
- The Network Types upload posts a `FormData` with the field `app_zip_file`.
- `apiFetch` skips the `application/json` default when the body is a `FormData`
  instance.

## Goals / Non-Goals

**Goals:**
- Make `networks`, `jenkins-trigger-security`, `spa-networks`,
  `spa-network-types`, and `frontend-skeleton` specs match shipped behaviour.
- Explicitly reverse the obsolete "unauthenticated internal Jenkins" assertion,
  since it actively misleads.

**Non-Goals:**
- Changing any runtime behaviour. If a spec and the code disagree, the spec is
  updated to match the code (the code is the shipped contract), not vice versa.
- Re-litigating the authentication design decision. Whether anonymous or
  authenticated Jenkins access is preferable is out of scope; the spec records
  what the code does.
- Reconciling unrelated pre-existing drift (e.g. legacy `roles`/`resources`
  references) beyond what these commits touched.

## Decisions

### Spec follows code for the Jenkins auth reversal
The `close-webapp-gaps` change asserted an unauthenticated internal path.
Commit `fde58cb` replaced that with authenticated `jenkinsapi` calls (Jenkins
returned 403 to anonymous build requests). Rather than restate history, this
change **removes** the "Internal Jenkins Communication Is Unauthenticated"
requirement and **adds** "Internal Jenkins Communication Is Authenticated",
and trims the false "no credentials/CSRF crumb required" sentence from the
deployment-topology requirement.

### Create/Delete documented as synchronous, outcome-reflecting
The synchronous create/delete behaviour is materially different from a plain
REST create (it can return 502/503 and can roll back via a cleanup job), so it
is captured as scenarios on the existing `networks` Create/Delete requirements
rather than as silent prose.

### Console viewer is a new SPA requirement, not a console-streaming change
The detail-page console viewer consumes the existing
`GET /api/v1/action-history/{id}/console/` proxy endpoint (already specced under
`actions`). It is purely a frontend addition, so it is added to `spa-networks`
(which owns the network detail page) rather than to `console-streaming`.

## Risks / Trade-offs

- **Risk**: Reversing the auth requirement could be read as endorsing one
  design over another. *Mitigation*: the spec records current behaviour; the
  proposal notes the design choice is out of scope.
- **Trade-off**: Documenting HTTP 502/503 outcomes on create/delete couples the
  `networks` spec to Jenkins availability. This is accurate to the code and is
  the behaviour the GUI depends on, so it is worth recording.

## Migration Plan

None. No data, schema, or API-contract migration — the specs are being aligned
to already-deployed behaviour.

## Open Questions

- Should the authenticated-Jenkins decision be revisited in a future change
  (e.g. to scope credentials per environment)? Out of scope here; flagged for
  follow-up.

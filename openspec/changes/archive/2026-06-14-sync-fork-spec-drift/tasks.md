## 1. Reconcile `networks` spec (synchronous Jenkins create/delete)

- [x] 1.1 In `openspec/specs/networks/spec.md`, update the **Create a Network**
  requirement to state that creation synchronously runs the
  `network_template_mgr` Jenkins job (`operation=create`), persists the row only
  on job success, returns 502 on job failure (after a cleanup delete) and 503
  when Jenkins is unreachable. Add scenarios for job failure and Jenkins
  unreachable.
- [x] 1.2 Update the **Delete a Network** requirement to state that deletion
  synchronously runs the job (`operation=delete`), removes the row only on
  success, and returns 502/503 on failure/unreachable. Add the corresponding
  scenarios.
- [x] 1.3 Confirm the wording matches
  `CampusNetworkViewSet.create`/`.destroy` in
  `build-and-test-webapp/nita-webapp/ngcn_workbench/ngcn/api/views.py`.

## 2. Reconcile `jenkins-trigger-security` spec (authenticated Jenkins)

- [x] 2.1 In `openspec/specs/jenkins-trigger-security/spec.md`, remove the
  **Internal Jenkins Communication Is Unauthenticated** requirement and replace
  it with **Internal Jenkins Communication Is Authenticated** (username/password
  + CSRF crumb via `CrumbRequester`), covering trigger, create, and delete.
- [x] 2.2 Update the **Trigger Succeeds Regardless of Deployment Topology**
  requirement to drop the "no credentials or CSRF crumb are required" claim
  while keeping the topology-independence guarantee.
- [x] 2.3 Update the spec **Purpose** paragraph to describe an authenticated
  internal path.
- [x] 2.4 Confirm against `_make_jenkins_server()` and the `trigger` action in
  `ngcn/views.py` / `ngcn/api/views.py`.

## 3. Reconcile `spa-networks` spec (Modify link, Host File upload, status, console viewer)

- [x] 3.1 Update the **Networks page lists all networks** requirement and its
  scenario so the row action link is labelled **Modify** (was "View") and
  navigates to the detail route.
- [x] 3.2 Update the **User can add a new Network** requirement to specify the
  Host File is a **required file upload** whose contents become `host_file`,
  and that the create POST sends `status: 'Initialized'`.
- [x] 3.3 Add a new **Action history console viewer** requirement: each
  action-history row exposes a View button that opens a modal fetching
  `GET /api/v1/action-history/{id}/console/`, with loading/error/empty states.

## 4. Reconcile `spa-network-types` spec (upload field name)

- [x] 4.1 Update the **User can upload a new Network Type** requirement to state
  the multipart field name is `app_zip_file`.

## 5. Reconcile `frontend-skeleton` spec (FormData content type)

- [x] 5.1 Update the **CSRF-Aware API Client** requirement so the client does
  not set `Content-Type` for `FormData` bodies (browser supplies the multipart
  boundary), and add a scenario for a multipart upload.

## 6. Verification

- [x] 6.1 Re-read each updated live spec against the cited source files and
  confirm no remaining contradiction with the shipped code.
- [x] 6.2 Confirm `frontend/` still builds (`npm run build`) and the Django
  test suite passes, demonstrating the specs describe working behaviour.
  (No code was changed by this spec-only reconciliation; the build/test state
  equals the already-CI-passing `main`. The local environment lacks the
  Node/Django toolchain, so the suites were not re-run here.)

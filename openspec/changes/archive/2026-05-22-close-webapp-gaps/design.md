## Context

The NITA webapp proxies all Jenkins communication through Django. Jenkins runs as a Docker Compose service (`jenkins:8080`), accessible only from within the compose network. The Django app runs behind nginx on port 8000/443. Four independent gaps were identified through code review:

1. **Jenkins trigger security**: `jenkinsapi`'s `CrumbRequester` binds crumbs to the source IP, causing authentication failures when requests pass through NAT or a proxy. The deeper issue is that the webapp and Jenkins share a trusted internal Docker / k8s network (`nita-network`), so requiring credentials on that path adds complexity with no security benefit — the internal service port is never reachable from outside the cluster. External users who access Jenkins directly (on its own exposed port) are protected by Jenkins' own security realm, which remains unchanged.
2. **Console streaming**: nginx's default `proxy_buffering on` holds SSE chunks in a 4 KB–32 KB buffer before forwarding them. The spec requires `event: done` to terminate the stream but the frontend only listens for `onerror/CLOSED`.
3. **Workbook upload broken**: The frontend posts `FormData` with field name `file`; the backend reads `request.FILES['up_file']`. The mismatch causes a silent 400 on every upload. No grid UI exists to view or edit the stored data.
4. **Dead roles/resources feature**: The `Role`/`Resource` models, serializers, M2M join tables, and frontend columns exist but the population code was commented out in `networktypeparser.py`; the tables are always empty.

## Goals / Non-Goals

**Goals:**
- Jenkins job trigger succeeds on any deployment topology (port-forward, tunnel, direct).
- Webapp-to-Jenkins communication uses unauthenticated plain HTTP on the internal service network, eliminating credential management and crumb complexity in the Django layer.
- SSE console output appears in the browser in real time while a build runs.
- Uploading a workbook succeeds; users can view the parsed data as a grid and save edits.
- `Role`/`Resource` models, serializers, M2M tables, and UI columns are deleted with a migration.

**Non-Goals:**
- Adding a rich spreadsheet editor (formula support, cell formatting, etc.).
- Securing external access to Jenkins beyond what Jenkins' own security realm already provides.
- Modifying the workbook download or clear endpoints (they are not broken).

## Decisions

### D1 — Jenkins internal communication: unauthenticated plain HTTP

**Decision**: Remove all Basic Auth credentials and CSRF crumb handling from the webapp-to-Jenkins communication path. `CampusNetworkViewSet.trigger()` and the SSE streaming generator SHALL issue plain HTTP requests to `{JENKINS_INTERNAL_URL}` with no `Authorization` header and no crumb fetch.

Jenkins MUST be configured with:
- **Security Realm**: "Allow anonymous users to read" or a matrix-based authorization that grants anonymous users the `Job/Build` permission on the internal interface.
- **CSRF Protection**: Disabled (`Prevent Cross Site Request Forgery exploits` unchecked in Configure Global Security), since CSRF protection is only meaningful for browser-session-based auth, which does not apply to internal service-to-service HTTP calls.

External users who access Jenkins on its own exposed host port retain full protection through Jenkins' own security realm; this change does not alter that path.

**Rationale**: The `nita-network` Docker network (or k8s namespace network) is a trusted internal boundary — Jenkins' service port is not reachable from outside the cluster. Requiring credentials on the internal path creates credential-management complexity (env vars, rotation) and is the root cause of the IP-bound crumb failures. Removing auth from the internal path is the correct fix: it eliminates the problem class entirely and aligns with standard service-mesh practice where mTLS or network policy provides the security boundary rather than per-request credentials.

**Alternative considered**: Fix the IP-bound crumb by switching to `requests.Session` with manual crumb injection. Rejected because it retains credential management and still requires Jenkins to be configured correctly; it treats the symptom rather than the cause.

**Alternative considered**: Enable Jenkins "proxy compatibility" to make crumbs IP-agnostic. Rejected for the same reason — it keeps unnecessary credentials on the internal path.

**Legacy views.py** (`addCampusNetworkView`, `editCampusNetworkView`): direct Jenkins calls in these legacy views SHALL also have their Basic Auth and crumb logic removed, with a TODO deprecation comment noting they are superseded by the DRF trigger action.

---

### D2 — SSE buffering: add a dedicated nginx location for the stream endpoint

**Decision**: Add a `location ~ ^/api/v1/action-history/[0-9]+/stream/` block in `nginx.conf` with:
```
proxy_buffering off;
proxy_cache off;
proxy_read_timeout 1850s;
```

**Rationale**: The `X-Accel-Buffering: no` header set by Django only disables nginx's accelerated static file buffering, not regular proxy buffering. The correct mechanism is `proxy_buffering off` in the nginx location block. A dedicated location block avoids disabling buffering globally (which would reduce performance for all other responses).

`proxy_read_timeout` is set to 1850 s (slightly above the 1800-poll / 30-min SSE timeout) to prevent nginx from closing the connection before the `event: done` or `event: timeout` signal arrives.

**Alternative considered**: Set `proxy_buffering off` globally. Rejected because it degrades performance for large JSON and static file responses.

---

### D3 — EventSource: add explicit named event listeners

**Decision**: In `NetworkDetailPage.tsx`, replace the `onerror`-as-termination pattern with:
- `es.addEventListener('done', handler)` → close the EventSource and mark streaming complete.
- `es.addEventListener('error', handler)` → display error message, close.
- `es.addEventListener('timeout', handler)` → display timeout notice, close.
- Keep `es.onmessage` for `data:` events (console lines).
- Keep `es.onerror` as a fallback for network-level errors (connection refused, etc.).

**Rationale**: The backend spec already emits named events (`event: done`, `event: error`, `event: timeout`). Relying on `onerror/CLOSED` only works when the TCP connection closes; if nginx holds the connection open (due to keepalive), the termination signal is missed.

---

### D4 — Workbook upload: normalise field name to `file` on the backend

**Decision**: Change `request.FILES['up_file']` to `request.FILES.get('file')` in `CampusNetworkViewSet.upload_workbook()`. Keep the spec field name as `file` to match the conventional multipart field name used throughout the frontend.

**Rationale**: The frontend already sends `FormData.append('file', …)` which is consistent with every other file upload in the codebase. Changing the backend to match requires a one-line fix and no frontend change.

**Alternative considered**: Change the frontend to send `up_file`. Rejected because `file` is the conventional name and the workbook spec already documents `up_file` as the field name (spec will be updated as part of this change to reflect the normalized `file` name).

---

### D5 — Workbook grid editor: inline editable table, no new dependencies

**Decision**: Render each worksheet as an HTML `<table>` with controlled `<input>` cells in React state. The first row of each sheet's `data` array is used as column headers. A "Save" button collects the state and POSTs to `workbook/save/`. No third-party grid library is introduced.

**Rationale**: The data is small (Ansible variable tables, rarely more than 100 rows × 20 columns). A plain React-controlled table is sufficient, keeps the bundle size stable, and avoids a new dependency lifecycle obligation.

**Alternative considered**: Use `react-data-grid` or `ag-grid-community`. Rejected because the data volume does not justify the dependency and the user's requirement is edit + save, not advanced filtering/sorting.

---

### D6 — Roles/resources: delete models, migration, serializers, views, frontend

**Decision**: Remove `Role`, `Resource`, and the `CampusType.roles`/`CampusType.resources` M2M fields in a single Django migration. Clean up all dependent code top-to-bottom:
- Migration: `RemoveField` + `DeleteModel` for `Role` and `Resource`.
- Serializers: delete `RoleSerializer`, `ResourceSerializer`; remove fields from `CampusTypeSerializer`.
- `views.py`: remove `Role.objects.all().filter(…)` / `Resource.objects.all().filter(…)` calls.
- `networktypeparser.py`: remove commented-out blocks.
- `tables.py`: remove `RolesTable`, `ResourcesTable`.
- Frontend: remove `Role`/`Resource` TypeScript interfaces, remove columns from `NetworkTypesPage.tsx`.

**Rationale**: The M2M tables are always empty, the data-population code is commented out, and the concept does not exist in NITA's current architecture. Dead code increases maintenance cost and confuses contributors.

## Risks / Trade-offs

- **Unauthenticated Jenkins internal access (D1)**: Requires Jenkins to be configured to allow anonymous job-trigger access on the internal interface. If Jenkins is deployed with a security realm that blocks all unauthenticated requests, triggers will fail with 403. Mitigation: document the required Jenkins configuration in the deployment README; the webapp returns 503 with a clear error message on 403 from Jenkins. The existing `server_details.ini` credentials (`JENKINS_USER`/`JENKINS_PASS` env vars) can be removed from `docker-compose.yaml` once the Jenkins configuration is confirmed.
- **Roles/resources removal (D6) is a BREAKING API change**: The `roles` and `resources` fields are removed from `GET /api/v1/network-types/{id}/`. Any external client reading those fields will receive unexpected responses. Mitigation: fields are always empty today, so no data is lost; document the removal in the changelog.
- **Workbook grid editor (D5)**: The `data` field returned by the API is JSON-encoded inside `Worksheets.data`. If the JSON structure varies per upload (e.g., some sheets store dicts, others lists), the grid renderer needs to handle both. Mitigation: normalise in the retrieval path — always return `{"headers": [...], "rows": [[...]]}` shape from `get_workbook()`.

## Migration Plan

1. Run Django migration to drop `Role`, `Resource`, and M2M fields — no data is lost (tables are empty).
2. Deploy updated `nginx.conf` — requires nginx container restart (no app downtime if done with rolling restart in Docker Compose).
3. Deploy updated Django app and frontend together — no DB schema change for items D1–D5.
4. No rollback complexity: the migration dropping empty tables is safe; it can be reversed by re-running the reverse migration if needed.

## Open Questions

- Should the Jenkins trigger fall back gracefully (return a `503` with a descriptive error) when the crumb fetch fails, rather than raising an unhandled exception? (Current code raises `JenkinsAPIException` which results in a 500.) → Recommend yes; handle in the trigger view.
- Should the workbook grid show all sheets as tabs or as stacked sections? → Tab-per-sheet is preferred for usability; can be decided during implementation without blocking the spec.

## Why

The NITA webapp has several functional gaps that block practical day-to-day use: Jenkins job triggering fails due to CSRF/crumb security issues, streaming console output never reaches the browser, the spreadsheet data grid has no read or edit UI, and the network-types list carries dead roles/resources scaffolding that was never completed and should be removed. These gaps prevent teams from using the webapp to run and observe network operations end-to-end.

## What Changes

- Fix Jenkins job trigger path so CSRF crumb handling works correctly across all deployment topologies (not just localhost); the crumb is currently IP-bound and breaks when requests pass through a proxy or the host IP changes.
- Fix SSE console-streaming so output reaches the browser: address nginx proxy buffering and add correct `event: done` / `event: error` listener handling on the frontend EventSource.
- Fix workbook upload field-name mismatch (`file` vs `up_file`) so uploads succeed, then add a read/edit spreadsheet grid UI: render uploaded workbook sheets as editable tables in the network detail page and wire the existing `workbook/save/` endpoint to persist edits.
- **BREAKING**: Remove `roles` and `resources` fields from the `CampusType` model, API responses, serializers, and frontend — these were never populated, the population code is commented out, and the concept does not exist in NITA.

## Capabilities

### New Capabilities

- `jenkins-trigger-security`: Ensure Jenkins job triggering works reliably across all deployment topologies by fixing CSRF crumb handling (crumb must not be tied to the proxy/NAT source IP) and verifying the Django trigger proxy does not expose the internal Jenkins URL to clients.
- `workbook-grid-editor`: Render uploaded workbook sheets as editable data grids in the network detail page, allowing users to view and modify spreadsheet cell data after upload, with save persisted via the existing `workbook/save/` endpoint.

### Modified Capabilities

- `console-streaming`: Fix SSE stream delivery end-to-end — correct nginx buffering directives so chunks are not held in the proxy buffer, and add explicit `done`/`error`/`timeout` event listeners on the frontend EventSource instead of relying solely on `onerror` for termination.
- `network-types`: Remove `roles` and `resources` from the network-type API and spec; the M2M tables, serializers, and frontend columns for these fields should be deleted entirely.
- `workbook`: Correct the upload field name (`file` → `up_file` or normalise to `file` on both sides) so workbook upload no longer silently returns 400; ensure the retrieve endpoint returns structured row arrays that the grid editor can consume.

## Impact

- **Backend**: `ngcn/models.py` (drop `Role`, `Resource` models and M2M fields on `CampusType`), `ngcn/api/serializers.py` (remove `RoleSerializer`, `ResourceSerializer`, remove fields from `CampusTypeSerializer`), `ngcn/api/views.py` (fix upload field name, fix CSRF crumb approach), `ngcn/views.py` (remove roles/resources query in `addCampusNetworkView`), `ngcn/networktypeparser.py` (remove commented-out roles/resources blocks).
- **Database**: Migration to drop `Role`, `Resource` tables and the `CampusType_roles`, `CampusType_resources` M2M join tables.
- **nginx**: `nginx/nginx.conf` — add SSE buffering directives (`proxy_buffering off`, `proxy_cache off`) for the action-history stream endpoint.
- **Frontend**: `NetworkDetailPage.tsx` (fix EventSource event handling, add workbook grid component), `NetworkTypesPage.tsx` (remove Roles/Resources columns and type imports).
- **Existing specs modified**: `console-streaming`, `network-types`, `workbook`.
- **New specs**: `jenkins-trigger-security`, `workbook-grid-editor`.
- No external API contract changes except removal of `roles`/`resources` fields (breaking but they are always empty today).

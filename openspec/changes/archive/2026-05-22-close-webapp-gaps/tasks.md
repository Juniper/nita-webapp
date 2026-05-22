## 1. Remove Roles and Resources (Backend)

- [x] 1.1 Create a Django migration in `ngcn` that removes `roles` and `resources` ManyToManyFields from `CampusType`, then deletes the `Role` and `Resource` models (use `RemoveField` + `DeleteModel` operations)
- [x] 1.2 Delete `RoleSerializer` and `ResourceSerializer` from `ngcn/api/serializers.py`
- [x] 1.3 Remove `roles` and `resources` fields from `CampusTypeSerializer` (both field declarations and any `SerializerMethodField` or nested serializer references)
- [x] 1.4 Remove `Role.objects.all().filter(campustype=…)` and `Resource.objects.all().filter(campustype=…)` queries from `addCampusNetworkView` and any other legacy views in `ngcn/views.py`; remove the `roles_and_resources` key from the `project_yaml` dict passed to Jenkins
- [x] 1.5 Remove all commented-out roles/resources blocks from `ngcn/networktypeparser.py` (the `validateProjectYaml` and `updateNetworkTypeDetailsOnDB` sections)
- [x] 1.6 Delete `RolesTable` and `ResourcesTable` from `ngcn/tables.py`

## 2. Remove Roles and Resources (Frontend)

- [x] 2.1 Remove the `Role` and `Resource` TypeScript interfaces from the types/interfaces file(s) in `frontend/src/`
- [x] 2.2 Remove the "Roles" and "Resources" columns from the `NetworkTypesPage.tsx` table and remove the corresponding import/usage of those types
- [x] 2.3 Remove `roles` and `resources` from the `CampusType` / `NetworkType` TypeScript type used in `NetworkTypesPage.tsx`

## 3. Fix Jenkins Job Trigger Security

- [x] 3.1 In `ngcn/api/views.py`, replace the `jenkinsapi.jenkins.Jenkins` + `CrumbRequester` usage inside `CampusNetworkViewSet.trigger()` with a `requests.Session` that: (a) fetches the crumb from `{JENKINS_URL}/crumbIssuer/api/json` using Basic Auth, (b) triggers the Jenkins job POST with the crumb header injected
- [x] 3.2 Wrap the crumb fetch and job trigger in a try/except block; return `HTTP 503` with `{"error": "Jenkins service unavailable"}` on connection error, timeout, or non-200 crumb response — do not expose internal URLs, hostnames, or stack traces in the response
- [x] 3.3 Return `HTTP 404` when the specified `action_id` does not exist or does not belong to the network's type (verify existing behaviour and add if missing)
- [x] 3.4 Add a deprecation comment to the direct Jenkins calls in `addCampusNetworkView` and `editCampusNetworkView` in `ngcn/views.py` noting they are superseded by the DRF trigger action

## 4. Fix SSE Console Streaming

- [x] 4.1 Add a dedicated nginx location block in `nginx/nginx.conf` for `/api/v1/action-history/` stream paths with `proxy_buffering off;`, `proxy_cache off;`, and `proxy_read_timeout 1850s;`
- [x] 4.2 In `NetworkDetailPage.tsx`, replace the sole reliance on `es.onerror` for stream termination with explicit named event listeners: `es.addEventListener('done', …)` closes the EventSource and marks the console panel complete; `es.addEventListener('error', …)` displays an error message and closes; `es.addEventListener('timeout', …)` displays a timeout notice and closes
- [x] 4.3 Keep `es.onerror` as a fallback for network-level failures (e.g. connection refused before stream starts)

## 5. Fix Workbook Upload Field Name

- [x] 5.1 In `ngcn/api/views.py`, change `request.FILES['up_file']` to `request.FILES.get('file')` in `CampusNetworkViewSet.upload_workbook()`; add a 400 response when the field is absent
- [x] 5.2 Update the workbook upload spec and any backend docstring to reflect the canonical field name `file`

## 6. Normalise Workbook Retrieve Response Shape

- [x] 6.1 In `ngcn/api/views.py`, update `CampusNetworkViewSet.get_workbook()` (or `GridDataManager.get_sheets_by_campus_network`) to return each sheet as `{"name": "...", "headers": [...], "rows": [[...]]}` — extract the first row of each sheet's `data` array as `headers` and the remaining rows as `rows`
- [x] 6.2 Update the `Workbook` / `WorksheetData` TypeScript types in the frontend to reflect the new `headers`/`rows` shape

## 7. Add Workbook Grid Editor (Frontend)

- [x] 7.1 Create a `WorkbookGrid` React component in `frontend/src/components/` that accepts `sheets` (array of `{name, headers, rows}`) as a prop; renders each sheet as a tab; renders the active sheet as an HTML table with column headers and one `<input>` per data cell
- [x] 7.2 Manage edited cell values in component state; visually distinguish edited cells (e.g. with a border or background colour change)
- [x] 7.3 Add a Save button that collects the current state and POSTs to `POST /api/v1/networks/{id}/workbook/save/`; on success, clear the edited-cell visual distinction; on failure, display an error message and preserve edits
- [x] 7.4 Add a Discard button that resets the component state to the last saved data, discarding all unsaved edits
- [x] 7.5 Replace the current "data present" / row-count display in `NetworkDetailPage.tsx` with the new `WorkbookGrid` component, passing the workbook data from the existing `GET /api/v1/networks/{id}/workbook/` fetch
- [x] 7.6 Handle the empty-workbook case: show the existing upload UI when `workbook` is an empty array; show the grid when data is present

## 8. Verification

- [ ] 8.1 Verify the Django migration applies cleanly on a fresh database (`python manage.py migrate`) and that `GET /api/v1/network-types/{id}/` no longer returns `roles` or `resources` fields
- [ ] 8.2 Verify that uploading a workbook with field name `file` returns 200 and that the network detail page renders the grid with tabs and editable cells
- [ ] 8.3 Verify that saving edits via the grid calls `workbook/save/` and that a subsequent page reload shows the saved values
- [ ] 8.4 Trigger a Jenkins job and verify the console panel shows live output and displays a completion state when the build finishes (SSE `event: done` received and handled)
- [ ] 8.5 Verify that triggering a job while Jenkins is stopped returns a 503 with `{"error": "Jenkins service unavailable"}` and no stack trace
- [ ] 8.6 Run the existing test suite (`pytest`) and confirm no regressions

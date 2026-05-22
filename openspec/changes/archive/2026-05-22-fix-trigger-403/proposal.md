## Why

`POST /api/v1/networks/{id}/trigger/{action_id}/` returned 403 for authenticated users because DRF's built-in `SessionAuthentication` runs CSRF validation through Django's raw `CsrfViewMiddleware`, which rejects requests not made via `https://` when a `Referer` header is present — breaking in-cluster HTTP proxying. A second 403 was also possible when Django rotated the CSRF token on login but the frontend held a cached (pre-login) copy.

## What Changes

- Replace DRF's `SessionAuthentication` with a project-local `LabSessionAuthentication` that delegates CSRF enforcement to `LabCsrfMiddleware` (which already strips the origin/referer host check)
- Update `DEFAULT_AUTHENTICATION_CLASSES` in `settings.py` to use the new class
- Remove the CSRF token in-memory cache from `frontend/src/api/client.ts`; read `csrftoken` directly from `document.cookie` on every mutating request
- Add a 60-poll retry window in `_jenkins_progressive_text_generator` (views.py) for HTTP 404 responses — these occur when an SSE stream is opened before Jenkins has registered the build URL (build still in queue)

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `jenkins-trigger-security`: CSRF enforcement updated to use `LabCsrfMiddleware` via `LabSessionAuthentication`; frontend CSRF token stale-cache bug fixed
- `console-streaming`: SSE generator now tolerates a transient 404 from Jenkins (build queued, URL not yet available) by retrying for up to 60 seconds before failing

## Impact

- `build-and-test-webapp/nita-webapp/ngcn_workbench/ngcn/api/authentication.py` — new file
- `build-and-test-webapp/nita-webapp/ngcn_workbench/ngcn_workbench/settings.py` — `DEFAULT_AUTHENTICATION_CLASSES`
- `build-and-test-webapp/nita-webapp/ngcn_workbench/ngcn/api/views.py` — `_jenkins_progressive_text_generator`
- `frontend/src/api/client.ts` — `getCsrfToken` / `clearCsrfCache`

## MODIFIED Requirements

### Requirement: Django serves SPA index.html for root routes
Django SHALL serve `frontend/dist/index.html` for `GET /` and for `GET /<subpath>` that belongs to the SPA's own client-side routes (the configured top-level SPA route segments and their sub-paths). Requests that match neither a backend route (`api/`, `admin/`, `api/schema`, `api/docs`) nor a SPA route SHALL return Django's default HTTP 404 — they MUST NOT be served the SPA shell. This makes the React SPA the default application, served at the site root.

#### Scenario: Root URL returns index.html
- **WHEN** a GET request is made to `/`
- **THEN** the response is `frontend/dist/index.html` with status 200 and `Content-Type: text/html`

#### Scenario: Deep SPA route returns index.html
- **WHEN** a GET request is made to `/login`
- **THEN** the response is `frontend/dist/index.html` with status 200 (React Router handles the route client-side)

#### Scenario: SPA deep link survives a browser refresh
- **WHEN** a GET request is made to `/networks/5`
- **THEN** the response is `frontend/dist/index.html` with status 200 so React Router can render the detail route

#### Scenario: Unknown non-SPA path returns 404
- **WHEN** a GET request is made to a path that is neither a backend route nor a SPA route (e.g. a removed legacy path `/campustype/`)
- **THEN** the response is HTTP 404 (the SPA shell is not served)

#### Scenario: Reserved API prefix is not swallowed by the SPA
- **WHEN** a GET request is made to `/api/v1/network-types/`
- **THEN** the response is the API JSON, not `index.html`

#### Scenario: Reserved admin prefix is not swallowed by the SPA
- **WHEN** a GET request is made to `/admin/`
- **THEN** the response is the Django admin, not `index.html`

#### Scenario: SPA not built returns graceful error
- **WHEN** a GET request is made to `/` and `frontend/dist/index.html` does not exist
- **THEN** the response is status 503

### Requirement: React Router uses root basename
The React SPA SHALL configure `<BrowserRouter basename="/">` so all client-side routes are served from the site root.

#### Scenario: Login route resolves correctly
- **WHEN** the SPA navigates to the login page
- **THEN** the browser URL is `/login`

#### Scenario: Dashboard route resolves correctly
- **WHEN** the SPA navigates to the dashboard
- **THEN** the browser URL is `/`

### Requirement: Existing backend routes are unaffected
All existing Django API and admin endpoints SHALL continue to respond as before after this change. The SPA occupying the root SHALL NOT change any `/api/**`, `/admin/**`, `/api/schema`, or `/api/docs` behaviour.

#### Scenario: API endpoint unchanged
- **WHEN** a GET request is made to `/api/v1/network-types/`
- **THEN** the response is the same JSON as before this change

#### Scenario: API docs endpoint unchanged
- **WHEN** a GET request is made to `/api/docs/`
- **THEN** the Swagger UI is served as before

## ADDED Requirements

### Requirement: Legacy server-rendered UI is removed
The legacy server-rendered Django template UI that previously occupied the site root SHALL be removed. Its URL routes, templates, `django_tables2` tables, and forms SHALL no longer exist, and no non-legacy module SHALL import from the legacy `ngcn.views` module.

#### Scenario: Legacy root no longer serves the template UI
- **WHEN** a GET request is made to `/`
- **THEN** the response is the React SPA `index.html`, not the legacy Django template index page

#### Scenario: Legacy management path no longer serves a legacy page
- **WHEN** a GET request is made to a former legacy path such as `/campustype/`
- **THEN** the response is HTTP 404 (the route no longer exists and the SPA shell is not served)

## REMOVED Requirements

### Requirement: Django serves SPA index.html for /app/ routes
**Reason**: The SPA is re-rooted from `/app/` to `/`; superseded by "Django serves SPA index.html for root routes".
**Migration**: Requests to `/app/` and `/app/<subpath>` are replaced by `/` and `/<subpath>`. Update any bookmarks or links that referenced `/app/...`.

### Requirement: React Router uses /app basename
**Reason**: The SPA is re-rooted to `/`; superseded by "React Router uses root basename".
**Migration**: `basename="/app"` becomes `basename="/"`; client-side routes drop the `/app` prefix.

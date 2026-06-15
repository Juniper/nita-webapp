## ADDED Requirements

### Requirement: Django serves SPA static assets via WhiteNoise
Django SHALL use `whitenoise.middleware.WhiteNoiseMiddleware` to serve files from the `WHITENOISE_ROOT` directory (pointing to `frontend/dist/`). Asset requests matching files on disk SHALL be served with appropriate caching headers without reaching URL routing.

#### Scenario: Vite-built JS asset is served
- **WHEN** a GET request is made to `/assets/index-<hash>.js`
- **THEN** the response is the compiled JavaScript file with a 200 status

#### Scenario: Vite-built CSS asset is served
- **WHEN** a GET request is made to `/assets/index-<hash>.css`
- **THEN** the response is the compiled CSS file with a 200 status

### Requirement: Django serves SPA index.html for /app/ routes
Django SHALL serve `frontend/dist/index.html` for `GET /app/` and any `GET /app/<subpath>`. This enables React Router (with `basename="/app"`) to handle all client-side navigation.

#### Scenario: Root SPA URL returns index.html
- **WHEN** a GET request is made to `/app/`
- **THEN** the response is `frontend/dist/index.html` with status 200 and `Content-Type: text/html`

#### Scenario: Deep SPA route returns index.html
- **WHEN** a GET request is made to `/app/login`
- **THEN** the response is `frontend/dist/index.html` with status 200 (React Router handles the route client-side)

#### Scenario: SPA not built returns graceful error
- **WHEN** a GET request is made to `/app/` and `frontend/dist/index.html` does not exist
- **THEN** the response is status 503

### Requirement: Existing Django routes are unaffected
All existing Django template URLs and API endpoints SHALL continue to respond as before after this change.

#### Scenario: API endpoint unchanged
- **WHEN** a GET request is made to `/api/v1/network-types/`
- **THEN** the response is the same JSON as before this change

#### Scenario: Django template root unchanged
- **WHEN** a GET request is made to `/`
- **THEN** the response is the existing Django template index view (not the SPA)

### Requirement: React Router uses /app basename
The React SPA SHALL configure `<BrowserRouter basename="/app">` so all client-side routes are prefixed with `/app`.

#### Scenario: Login route resolves correctly
- **WHEN** the SPA navigates to the login page
- **THEN** the browser URL is `/app/login`

#### Scenario: Dashboard route resolves correctly
- **WHEN** the SPA navigates to the dashboard
- **THEN** the browser URL is `/app/`

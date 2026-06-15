## MODIFIED Requirements

### Requirement: Session Authentication
The system SHALL accept Django session cookies for browser-based access to the API, including the DRF browsable interface and the React SPA frontend.

Session credentials are established via `POST /api/v1/auth/login/` (see `spa-session-auth` capability). The SPA SHALL obtain a CSRF token via `GET /api/v1/auth/csrf/` before any state-mutating request and include it as the `X-CSRFToken` request header. Sessions are terminated via `POST /api/v1/auth/logout/`.

#### Scenario: Session cookie accepted
- GIVEN a user is logged in via the Django session mechanism
- WHEN an API endpoint is accessed from the same browser session
- THEN the request is authenticated and returns data

#### Scenario: SPA login establishes a usable session
- GIVEN a valid Django user exists
- WHEN `POST /api/v1/auth/login/` is called with valid credentials and a valid `X-CSRFToken` header
- THEN a `sessionid` cookie is set
- AND subsequent `GET /api/v1/` requests authenticated only via that cookie return 200

# Authentication Specification

## Purpose
Token-based authentication for the NITA Webapp REST API. All API endpoints
require a valid token obtained from the token endpoint.

## Requirements

### Requirement: Token Issuance
The system SHALL issue an authentication token when valid credentials are
submitted to POST /api/v1/auth/token/.

#### Scenario: Valid credentials
- GIVEN a Django superuser with username and password
- WHEN POST /api/v1/auth/token/ is called with those credentials as JSON
- THEN a 200 response is returned containing a `token` string

#### Scenario: Invalid credentials
- GIVEN an incorrect username or password
- WHEN POST /api/v1/auth/token/ is called
- THEN a 400 response is returned and no token is issued

### Requirement: Token Authentication on All Endpoints
The system SHALL reject requests to any /api/v1/ endpoint that do not include a
valid Authorization header.

#### Scenario: Missing token
- GIVEN no Authorization header is present
- WHEN any GET /api/v1/ endpoint is called
- THEN a 401 or 403 response is returned

#### Scenario: Valid token accepted
- GIVEN a valid token is included as `Authorization: Token <token>`
- WHEN any /api/v1/ endpoint is called
- THEN the request is processed normally

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

### Requirement: Default Credentials
The system SHALL ship with a bootstrap admin mechanism. The default
`vagrant/vagrant123` credential is superseded by the `create_admin` management
command and the `NITA_BOOTSTRAP_ADMIN_*` environment variable path (see
`user-registration` capability). Development and CI environments SHALL use the
bootstrap mechanism to create the initial admin user.

#### Scenario: Bootstrap admin can log in after fresh install
- GIVEN NITA has just been installed with bootstrap env vars or `create_admin`
- WHEN `POST /api/v1/auth/login/` is called with the configured credentials
- THEN a session is established and `GET /api/v1/auth/me/` returns `"role": "admin"`

### Requirement: Me Endpoint Returns Role and Teams
The system SHALL extend the `GET /api/v1/auth/me/` response to include the
authenticated user's `role` and a list of team IDs they belong to.

#### Scenario: Me response includes role
- GIVEN a logged-in user with `role=power_user`
- WHEN `GET /api/v1/auth/me/` is called
- THEN the response includes `"role": "power_user"`

#### Scenario: Me response includes team memberships
- GIVEN a logged-in user who is a member of teams with ids 1 and 3
- WHEN `GET /api/v1/auth/me/` is called
- THEN the response includes `"teams": [1, 3]`

### Requirement: Forward-Auth Endpoint for Reverse Proxies
The system SHALL expose `GET /api/v1/auth/forward/` for reverse-proxy
forward-auth checks, using `LabSessionAuthentication` only. For an
authenticated caller it SHALL answer `200` with `X-Forwarded-User` and
`X-Forwarded-Groups` (role plus one `team-<id>` per team, `|`-delimited).
Otherwise it SHALL answer `302` to `/login?next=<path>` with neither header.
It SHALL NOT write to the database.

#### Scenario: Valid session is approved with identity headers
- GIVEN a browser holding a valid `sessionid` cookie for user `alice` with role `power_user` who belongs to team 7
- WHEN `GET /api/v1/auth/forward/` is called with that cookie
- THEN the response status is 200
- AND the response includes `X-Forwarded-User: alice` and `X-Forwarded-Groups: power_user|team-7`

#### Scenario: Missing or invalid session is denied
- GIVEN no session cookie, or an expired one
- WHEN `GET /api/v1/auth/forward/` is called
- THEN the response status is 302 to the login page
- AND the response includes neither `X-Forwarded-User` nor `X-Forwarded-Groups`

#### Scenario: API tokens are not accepted
- GIVEN a valid `Authorization: Token <token>` header and no session cookie
- WHEN `GET /api/v1/auth/forward/` is called
- THEN the response status is 302 to the login page

### Requirement: Forward-auth login redirect uses a safe return path
When denying a request, the endpoint SHALL use the proxy-supplied
`X-Forwarded-Uri` as the `next` value only if it is a same-origin path equal to
`/jenkins` or under `/jenkins/` with no backslash, control character or
fragment; otherwise it SHALL use `/jenkins/`.

#### Scenario: Jenkins deep link is preserved
- GIVEN no session and `X-Forwarded-Uri: /jenkins/job/test-robot-net1/`
- WHEN `GET /api/v1/auth/forward/` is called
- THEN it redirects to `/login?next=%2Fjenkins%2Fjob%2Ftest-robot-net1%2F`

#### Scenario: Unsafe return path is replaced
- GIVEN no session and `X-Forwarded-Uri: //evil.example/jenkins/`
- WHEN `GET /api/v1/auth/forward/` is called
- THEN it redirects to `/login?next=%2Fjenkins%2F`

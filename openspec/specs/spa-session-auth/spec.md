### Requirement: Session Login
The system SHALL accept username and password credentials at `POST /api/v1/auth/login/` and, on success, create a Django session, set a `sessionid` cookie, and return the authenticated user's `id`, `username`, and `is_superuser` in a JSON response with status 200.

The SPA SHALL call `GET /api/v1/auth/csrf/` before this request and include the returned token as the `X-CSRFToken` request header.

#### Scenario: Valid credentials create a session
- GIVEN a valid Django user exists with known username and password
- WHEN `POST /api/v1/auth/login/` is called with `{"username": "...", "password": "..."}` and a valid `X-CSRFToken` header
- THEN the response status is 200
- AND the response body contains `{"id": <int>, "username": "<str>", "is_superuser": <bool>}`
- AND the response sets a `sessionid` cookie

#### Scenario: Invalid credentials are rejected
- GIVEN an incorrect password is submitted
- WHEN `POST /api/v1/auth/login/` is called
- THEN a 400 response is returned with a non-empty `detail` field
- AND no `sessionid` cookie is set

#### Scenario: Missing CSRF token is rejected
- GIVEN no `X-CSRFToken` header is present
- WHEN `POST /api/v1/auth/login/` is called
- THEN a 403 response is returned (CSRF verification failure)

### Requirement: Session Logout
The system SHALL destroy the current Django session at `POST /api/v1/auth/logout/`. Authentication is required; unauthenticated requests receive a 403 response. On success a 204 No Content response is returned.

#### Scenario: Authenticated logout destroys session
- GIVEN a user is authenticated via a valid session cookie
- WHEN `POST /api/v1/auth/logout/` is called with the `X-CSRFToken` header
- THEN the response status is 204
- AND the session is invalidated (subsequent authenticated requests with the old cookie fail)

#### Scenario: Unauthenticated logout is rejected
- GIVEN no valid session cookie or token is present
- WHEN `POST /api/v1/auth/logout/` is called
- THEN a 403 response is returned

### Requirement: Current User Info
The system SHALL return the authenticated user's `id`, `username`, and `is_superuser` at `GET /api/v1/auth/me/`. Authentication is required; unauthenticated requests receive a 403 response.

#### Scenario: Authenticated user retrieves their info
- GIVEN a user is authenticated via session cookie or token
- WHEN `GET /api/v1/auth/me/` is called
- THEN the response status is 200
- AND the response body contains `{"id": <int>, "username": "<str>", "is_superuser": <bool>}`

#### Scenario: Unauthenticated request is rejected
- GIVEN no valid authentication credential is present
- WHEN `GET /api/v1/auth/me/` is called
- THEN a 403 response is returned

### Requirement: CSRF Token Vending
The system SHALL return the current CSRF token string at `GET /api/v1/auth/csrf/` as `{"csrfToken": "<value>"}` with status 200. No authentication is required. Calling this endpoint also ensures the `csrftoken` cookie is set on the response.

#### Scenario: CSRF token returned for unauthenticated request
- GIVEN no session or token credential is present
- WHEN `GET /api/v1/auth/csrf/` is called
- THEN the response status is 200
- AND the response body contains `{"csrfToken": "<non-empty string>"}`

#### Scenario: CSRF token returned for authenticated request
- GIVEN a user is authenticated
- WHEN `GET /api/v1/auth/csrf/` is called
- THEN the response status is 200
- AND the response body contains `{"csrfToken": "<non-empty string>"}`

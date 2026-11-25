## ADDED Requirements

### Requirement: Traefik forward-auth response contract
The existing session-only `GET /api/v1/auth/forward/` endpoint SHALL return
`X-Forwarded-User` and `X-Forwarded-Groups` for authenticated sessions. An
unauthenticated request SHALL receive a login redirect with a validated,
same-origin Jenkins return path. API tokens SHALL NOT authenticate this
endpoint. No Nginx compatibility mode SHALL be provided.

#### Scenario: Valid session returns Jenkins identity
- **GIVEN** a valid session for a user with team memberships
- **WHEN** Traefik calls the endpoint
- **THEN** it receives the user's identity and groups in the Jenkins header names

#### Scenario: Unauthenticated Jenkins request
- **WHEN** Traefik calls the endpoint without a valid session
- **THEN** the response redirects to login without returning identity headers

#### Scenario: Unsafe return path
- **WHEN** the forwarded original URI is not a safe same-origin Jenkins path
- **THEN** the login redirect does not use it as the return destination

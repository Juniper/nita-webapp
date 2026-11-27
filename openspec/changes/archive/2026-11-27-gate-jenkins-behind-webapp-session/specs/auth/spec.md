## ADDED Requirements

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

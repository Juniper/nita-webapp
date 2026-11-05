## ADDED Requirements

### Requirement: Forward-Auth Endpoint for Reverse Proxies
The system SHALL expose `GET /api/v1/auth/forward/` for reverse-proxy
authentication sub-requests, using `LabSessionAuthentication` only. For an
authenticated caller it SHALL answer `200` with an empty body and the
`X-Auth-User`, `X-Auth-Role` and `X-Auth-Groups` headers (role plus one
`team-<id>` per team, `|`-delimited); otherwise `401`/`403` with none of them.
It SHALL NOT write to the database.

#### Scenario: Valid session is approved with identity headers
- GIVEN a browser holding a valid `sessionid` cookie for user `alice` with role `power_user` who belongs to team 7
- WHEN `GET /api/v1/auth/forward/` is called with that cookie
- THEN the response status is 200 with an empty body
- AND the response includes `X-Auth-User: alice`, `X-Auth-Role: power_user` and `X-Auth-Groups: power_user|team-7`

#### Scenario: Missing or invalid session is denied
- GIVEN no session cookie, or an expired one
- WHEN `GET /api/v1/auth/forward/` is called
- THEN the response status is 401 or 403
- AND the response includes neither `X-Auth-User` nor `X-Auth-Role`

#### Scenario: API tokens are not accepted
- GIVEN a valid `Authorization: Token <token>` header and no session cookie
- WHEN `GET /api/v1/auth/forward/` is called
- THEN the response status is 401 or 403

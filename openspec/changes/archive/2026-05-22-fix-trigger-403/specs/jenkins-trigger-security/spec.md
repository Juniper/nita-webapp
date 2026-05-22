## ADDED Requirements

### Requirement: Backend CSRF Enforcement Uses LabCsrfMiddleware
The Django REST Framework authentication layer SHALL enforce CSRF using
`LabCsrfMiddleware` (project-local subclass of Django's `CsrfViewMiddleware`)
rather than the raw `CsrfViewMiddleware`. This ensures that CSRF token
validation succeeds regardless of the `Referer` or `Origin` header value —
which can differ from `Host` when the API is accessed through a reverse proxy,
port-forward, or NAT layer.

`DEFAULT_AUTHENTICATION_CLASSES` in `settings.py` SHALL reference
`ngcn.api.authentication.LabSessionAuthentication` instead of
`rest_framework.authentication.SessionAuthentication`.

`LabSessionAuthentication` SHALL override `enforce_csrf` to instantiate
`LabCsrfMiddleware`, call `process_request` and `process_view` on the incoming
request, and raise `PermissionDenied` if either returns a rejection reason.

#### Scenario: Trigger succeeds from browser behind reverse proxy
- **WHEN** `POST /api/v1/networks/{id}/trigger/{action_id}/` is called from a
  browser whose `Referer` header contains an external host that differs from
  Django's `Host` (e.g. proxy rewrites)
- **THEN** a 202 Accepted response is returned (CSRF token value is valid)
- **AND** no 403 Forbidden is raised due to a host mismatch in `Referer`

#### Scenario: Trigger is still rejected when CSRF token is absent or wrong
- **WHEN** `POST /api/v1/networks/{id}/trigger/{action_id}/` is called without
  a valid `X-CSRFToken` header
- **THEN** a 403 Forbidden response is returned

### Requirement: Frontend CSRF Token Is Always Read From Cookie
The SPA SHALL read the `csrftoken` cookie value directly on every mutating
request rather than storing the token in an in-memory variable. An in-memory
cache becomes stale after Django rotates the CSRF token on `login()`.

If the cookie is absent (e.g. first load before any authenticated request),
the SPA SHALL fetch `GET /api/v1/auth/csrf/` once to seed the cookie, then
read it.

`clearCsrfCache()` MAY remain as an exported no-op for backward compatibility
with existing call sites.

#### Scenario: Trigger succeeds after fresh login without page reload
- **WHEN** the user logs in and immediately triggers a job (without reloading)
- **THEN** the trigger POST includes the current `csrftoken` cookie value
- **AND** a 202 Accepted response is returned (no 403 from stale token)

#### Scenario: clearCsrfCache has no observable side effect
- **WHEN** `clearCsrfCache()` is called (e.g. on a 403 trigger response)
- **THEN** the next trigger attempt reads the current cookie value correctly
- **AND** no error is thrown

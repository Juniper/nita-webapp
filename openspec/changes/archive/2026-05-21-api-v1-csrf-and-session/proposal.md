## Why

The planned React SPA frontend authenticates via session cookies (not token headers) and must perform state-mutating requests that require CSRF protection. The current API has only `POST /api/v1/auth/token/` (DRF token auth), with no session login/logout or CSRF machinery, making it impossible for the SPA to authenticate or issue safe mutations without bypassing Django's CSRF middleware.

## What Changes

- Add `POST /api/v1/auth/login/` — authenticates with username/password, opens a Django session, sets `sessionid` cookie, returns logged-in user info.
- Add `POST /api/v1/auth/logout/` — destroys the current Django session. Requires authentication.
- Add `GET /api/v1/auth/me/` — returns the authenticated user's `id`, `username`, `is_superuser`. Requires authentication. Used by the SPA on startup to determine login state.
- Add `GET /api/v1/auth/csrf/` — returns the CSRF token string in JSON. No authentication required. SPA calls this before first mutation.
- Existing `POST /api/v1/auth/token/` and token-based auth remain unchanged (backward-compatible).

## Capabilities

### New Capabilities
- `spa-session-auth`: Session-based login, logout, and current-user endpoints for the SPA, plus a CSRF token vending endpoint.

### Modified Capabilities
- `auth`: Existing auth spec gains requirements for the new session login/logout/me/csrf endpoints alongside the existing token requirement.

## Impact

- `ngcn_workbench/urls.py` — new URL entries for login, logout, me, csrf.
- `ngcn/api/views.py` or a new `ngcn/api/auth_views.py` — four new view functions/classes.
- `ngcn/api/urls.py` — route the four new views under `auth/`.
- `openapi.yaml` — regenerated to include the new endpoints.
- Django settings: `CSRF_COOKIE_HTTPONLY = False` may need to be confirmed so the SPA's JS can read the cookie (or the `/csrf/` JSON endpoint is used instead).
- No new pip dependencies. Uses Django's built-in `login()`, `logout()`, and `get_token()` from `django.middleware.csrf`.

## Context

The NITA webapp currently has one auth mechanism on the API: `POST /api/v1/auth/token/` issues a DRF `Token` object, which callers attach as `Authorization: Token <token>`. This works well for CLI tools and scripts, but an SPA (React) that uses session cookies faces two problems:

1. **No session login endpoint** — the SPA cannot authenticate via the API (only via the Django admin login form).
2. **CSRF protection** — Django's `SessionAuthentication` already enforces CSRF checks on state-mutating requests. The SPA needs to obtain the CSRF token before its first POST/PUT/DELETE.

Both issues are solvable with small additions on top of the existing Django session/auth infrastructure — no new dependencies.

## Goals / Non-Goals

**Goals:**
- `POST /api/v1/auth/login/` — creates a session from username/password, returns user info.
- `POST /api/v1/auth/logout/` — destroys the current session.
- `GET /api/v1/auth/me/` — returns `{id, username, is_superuser}` for the session holder. Used on SPA startup to determine if already logged in.
- `GET /api/v1/auth/csrf/` — returns `{csrfToken: "<value>"}`. No auth required. Called by SPA on first load before any mutation.
- Existing `POST /api/v1/auth/token/` and token-based auth remain **fully unchanged**.
- Tests for all four endpoints.
- Regenerated `openapi.yaml`.

**Non-Goals:**
- OAuth2, social auth, JWT — out of scope.
- Password change or reset — out of scope.
- Rate-limiting the login endpoint — out of scope for this change.
- Changing how CLI tools authenticate — they continue to use token auth.

## Decisions

### D1: Session cookies, not tokens, for the SPA
**Choice:** Session cookie authentication.
**Rationale:** Cookies are set HttpOnly (by Django), follow same-origin policy, and are automatically attached to every fetch. Token storage in `localStorage` is vulnerable to XSS. Django's `SessionAuthentication` is already enabled on all DRF views (it is already in `DEFAULT_AUTHENTICATION_CLASSES`). This requires CSRF handling but that is solved by D3.

**Alternatives considered:**
- *DRF token in localStorage* — simpler, but XSS-unsafe.
- *HTTP-only cookie carrying DRF token* — non-standard and requires custom middleware.

### D2: Plain Django views, not DRF ViewSets
**Choice:** Use `django.contrib.auth.authenticate`, `django.contrib.auth.login`, `django.contrib.auth.logout` wrapped in `@api_view` functions.
**Rationale:** These are simple, stateless operations that don't fit the resource/collection model of DRF ViewSets. DRF `@api_view` gives us schema generation, renderer negotiation, and authentication without unnecessary boilerplate.

### D3: JSON CSRF endpoint instead of relying on cookie
**Choice:** `GET /api/v1/auth/csrf/` returns `{"csrfToken": "..."}` JSON.
**Rationale:** Django sets `csrftoken` as a non-HttpOnly cookie by default, so JS can read it with `document.cookie`. However, the CORS and SPA-in-subdirectory setup may make cookie access unreliable. A JSON endpoint is unambiguous and testable. Uses `django.middleware.csrf.get_token(request)` (the canonical function that both returns the value and ensures the cookie is set).

### D4: `me` endpoint returns minimal user info
**Choice:** Return only `{id, username, is_superuser}`.
**Rationale:** The SPA only needs to show the logged-in username and gate admin-only UI. Full `User` serializer fields (email, groups, permissions) are unnecessary and expose information the SPA doesn't need.

### D5: Place new views in `ngcn/api/views.py`, routed via `ngcn/api/urls.py`
**Choice:** Add auth views to the existing `ngcn/api/views.py` module.
**Rationale:** Keeps all API logic co-located. If the file grows too large this can be split in a future refactor — a separate `auth_views.py` is unnecessary overhead now.

## Risks / Trade-offs

- **CSRF enforcement on login** — Django's CSRF middleware is active. `POST /api/v1/auth/login/` is a mutation from an unauthenticated context so the SPA must call `GET /api/v1/auth/csrf/` first and send the token in the `X-CSRFToken` header. Design handles this by documenting the call sequence.
  - *Mitigation*: Mark `login` and `csrf` in `@extend_schema` so the OpenAPI spec documents the `X-CSRFToken` header expectation.
  - *Alternative*: Exempt `login` from CSRF using `@csrf_exempt` — **deliberately not chosen** because it would weaken security.
- **Session fixation** — Django's `login()` calls `cycle_key()` internally since Django 1.7, rotating the session ID on login. No additional protection needed.
- **Concurrent token + session** — A client could hold both a token and a session simultaneously. This is harmless because DRF evaluates authenticators in order and stops at the first success.

## Open Questions

- None. All decisions are resolved.

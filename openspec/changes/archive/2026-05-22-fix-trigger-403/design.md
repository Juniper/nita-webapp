## Context

Django REST Framework's `SessionAuthentication` enforces CSRF by instantiating the raw `CsrfViewMiddleware`. That middleware validates the `Referer` header against the current `Host` and rejects any HTTPS-origin request whose referer host doesn't match — making every browser `POST` fail with 403 when the request travels through the nginx reverse proxy over HTTP inside the cluster, because Django sees an HTTP `Host` but the browser may send an HTTPS-origin `Referer`.

The project already has `LabCsrfMiddleware` (in `csrf.py`) that overrides `_origin_verified` to return `True` and `_check_referer` to return `None`, effectively skipping the host-comparison while still validating the CSRF token value. The middleware is wired into Django's `MIDDLEWARE` list, so it works for regular Django views. DRF bypasses `MIDDLEWARE` for CSRF and calls `CsrfViewMiddleware` directly, so `LabCsrfMiddleware` was never reached for API views.

A secondary bug: `client.ts` cached the CSRF token in an in-memory variable. Django rotates the token on `login()`. After a fresh login the cached value was stale and every mutating request returned 403 until a page reload.

A third bug: the SSE generator in `views.py` opened the Jenkins progressive-text URL immediately after triggering a build. Jenkins queues the build first; the build URL (and therefore the progressive-text endpoint) does not exist until the executor picks it up, causing an immediate HTTP 404 that the generator surfaced as a stream error.

## Goals / Non-Goals

**Goals:**
- Fix 403 on `POST /api/v1/networks/{id}/trigger/{action_id}/` for authenticated users
- Ensure CSRF token is always fresh on the frontend — no stale-cache 403
- Prevent the console panel from showing `[error] HTTP Error 404: Not Found` when a build is queued

**Non-Goals:**
- Changing the CSRF model or authentication scheme
- Making CSRF optional or disabling it
- Fixing any Jenkins credential or authorization issues (handled separately in the nita-jenkins repo)

## Decisions

### 1. Subclass `SessionAuthentication` rather than patching DRF

`LabSessionAuthentication` extends `rest_framework.authentication.SessionAuthentication` and overrides only `enforce_csrf`. It instantiates `LabCsrfMiddleware` (using the same inner-`_reject`-override pattern DRF itself uses) and runs `process_request` + `process_view` on the Django request.

**Why not monkey-patch DRF?** A subclass is explicit, testable, and survives DRF upgrades without re-patching.

**Why not remove CSRF entirely for API views?** The session cookie is the only credential; CSRF protection is necessary.

### 2. Read CSRF cookie directly instead of caching

`getCsrfToken()` now calls a local `readCsrfCookie()` helper on every request. If the cookie is absent it falls back to a single `GET /api/v1/auth/csrf/` fetch. `clearCsrfCache()` becomes a no-op (kept for backward compatibility with call sites).

**Why not invalidate on 403?** A 403 could have other causes. Reading the cookie directly is simpler and always correct: Django sets `csrftoken` as a readable cookie on every response after login, so the value is always fresh.

### 3. Retry on Jenkins 404 with a bounded window

`_jenkins_progressive_text_generator` tracks a `queued_polls` counter (max 60). On each HTTP 404 it increments the counter, sleeps 1 second, and retries. After 60 retries it yields an `event: error` and stops.

**Why 60 polls?** Jenkins typically starts a build within seconds; 60 seconds is enough to cover heavy-load queueing. This matches the `DEFAULT_TRIGGER_TIMEOUT` value already used elsewhere in `views.py`.

**Why not poll the Jenkins queue API instead?** The queue API would be cleaner but requires an extra endpoint and complicates the generator. A simple retry is sufficient for the observed failure mode.

## Risks / Trade-offs

- **`LabSessionAuthentication` is project-specific** → Must be kept in sync if DRF changes `enforce_csrf` internals. The override is small enough that future breakage would be obvious.
- **60-second retry adds latency on genuine 404s** → Only triggered when Jenkins returns 404; a real missing job would always 404, so the generator would wait 60 s before surfacing the error. Acceptable: users would see the console spinner rather than an immediate error, then get the error after timeout.
- **No-op `clearCsrfCache()`** → Call sites in `NetworkDetailPage.tsx` still call `clearCsrfCache()` on 403. This is harmless but does nothing. Left as-is to avoid churn; can be removed in a future cleanup.

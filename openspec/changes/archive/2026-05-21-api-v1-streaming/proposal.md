## Why

The current `GET /api/v1/action-history/{id}/console/` endpoint fetches the complete Jenkins build log in one blocking call and returns it as a single JSON response. Jenkins builds routinely run for several minutes; users must wait for the entire build to finish before seeing any output. The SPA frontend (the primary consumer of the API going forward) has no way to stream incremental log output, making the action-history console the most obviously "broken" experience in the modernised UI. Adding a Server-Sent Events (SSE) endpoint gives the SPA a standard browser API (`EventSource`) to stream live console output with zero polling overhead and no WebSocket complexity.

## What Changes

- Add `GET /api/v1/action-history/{id}/stream/` — an SSE endpoint that opens a persistent HTTP response and emits console output lines as `data:` events, flushing incrementally as the build progresses. Emits a final `event: done` when the build ends and closes the connection.
- Authentication: session cookie (same as the rest of the API). GET requests are exempt from CSRF token requirements by Django's middleware, so no special handling is needed for `EventSource`.
- The existing `GET /api/v1/action-history/{id}/console/` endpoint is **unchanged** — it remains available as a bulk-fetch fallback.

### Out of scope

- Removing or deprecating the existing `/console/` endpoint.
- WebSocket support.
- Any frontend code.
- Re-authenticating a dropped SSE connection (client responsibility — `EventSource` auto-reconnects).

## Capabilities

### New Capabilities
- `console-streaming`: SSE endpoint that streams Jenkins build console output incrementally for a given action history entry.

### Modified Capabilities
_None._

## Impact

- **Code**: new `stream` `@action` on `ActionHistoryViewSet` in `ngcn/api/views.py`; uses Django's `StreamingHttpResponse` with `text/event-stream` content type; polls Jenkins progressive text API (`/logText/progressiveText`) in a generator loop.
- **Schema**: `openapi.yaml` regenerated; the SSE endpoint documented with `text/event-stream` response type. Note: OpenAPI 3.0 has limited native SSE support — endpoint is documented as a streaming text response.
- **Dependencies**: no new pip packages. Uses `urllib.request` (stdlib) to call Jenkins progressive text endpoint directly, since `jenkinsapi` does not expose a streaming interface.
- **Tests**: new pytest tests mock the Jenkins progressive text HTTP call and assert the yielded SSE lines; includes auth-failure scenario.
- **Drift test**: the existing `test_openapi_drift.py` will enforce that `openapi.yaml` is regenerated after this change.

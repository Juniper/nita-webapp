## Context

The NITA Webapp already exposes `GET /api/v1/action-history/{id}/console/` which returns the full Jenkins build log in one blocking JSON call. Jenkins builds can run for several minutes. The SPA frontend needs a way to show live log output without waiting for the build to complete.

Jenkins natively supports progressive (chunked) log retrieval via:
```
GET <jenkins>/job/<name>/<build>/logText/progressiveText?start=<byte-offset>
```
Response headers:
- `X-Text-Size`: new byte offset to use on the next request
- `X-More-Data: true` if the build is still running

This is the same mechanism the Jenkins web UI uses internally. It is a stable, documented Jenkins API.

Django supports streaming HTTP responses via `StreamingHttpResponse` with a Python generator. The SSE wire format is simple plain text:
```
data: <line>\n\n
event: done\ndata: \n\n    (on completion)
```

`EventSource` in all modern browsers handles reconnection automatically on dropped connections.

## Goals / Non-Goals

**Goals:**
- `GET /api/v1/action-history/{id}/stream/` emits SSE events containing Jenkins console output lines as the build runs.
- Authenticated via session cookie (standard Django login); unauthenticated requests get 403.
- Emits `event: done` when the build log is complete, then closes.
- ANSI escape codes stripped (same as the existing `/console/` endpoint).
- Documented in `openapi.yaml`; drift test enforces regeneration.

**Non-Goals:**
- Removing or changing the existing `/console/` endpoint.
- Token authentication for SSE (browser `EventSource` cannot set `Authorization` headers; session cookie is the right mechanism).
- Persistent connection multiplexing / backpressure.
- Replaying past log from a specific offset on reconnect (EventSource reconnects from 0; Jenkins progressive text handles this).

## Decisions

### Decision: stdlib `urllib.request` for Jenkins progressive text, not `jenkinsapi`

**Options considered:**
- A) `jenkinsapi` library — already a dependency; but inspection shows it fetches the full log at once via `get_build_console_output`. No streaming interface exposed.
- B) `requests` library with `stream=True` — would work, but `requests` is not in the existing requirements.
- C) stdlib `urllib.request` — zero new dependencies, straightforward for a GET with Basic Auth and response header reading.

**Choice: C**

Rationale: No new pip dependency. The progressive text call is a simple GET with Basic Auth and two response headers to read. The generator pattern (`yield`) hides the polling loop from the Django response layer completely.

### Decision: Poll interval of 1 second while `X-More-Data: true`

Jenkins progressive text is a pull API — the caller decides when to poll again. 1-second sleep between polls is the same interval the Jenkins web UI uses and is a good balance between latency and server load.

Maximum poll attempts: 1800 (30 minutes). Beyond that the generator closes with `event: timeout`, preventing zombie server-side generators from hanging forever.

### Decision: `StreamingHttpResponse` not `django-channels` / ASGI

**Options considered:**
- A) `StreamingHttpResponse` with a sync generator — works today with the existing WSGI/Gunicorn setup. No infra change.
- B) Django Channels (ASGI, WebSocket) — much heavier; requires replacing Gunicorn with Daphne or Uvicorn; separate channels layer.

**Choice: A**

Rationale: WSGI streaming (`StreamingHttpResponse`) ties up a worker thread per active stream, but NITA is a low-concurrency internal tool. The existing Gunicorn config is retained. Channels can be adopted later if needed.

### Decision: `@login_required` enforced via `request.user.is_authenticated` check inside the action, not a DRF permission class

The DRF `action` decorator on a `ReadOnlyModelViewSet` already inherits `IsAuthenticated` by default, so no extra code is needed. An unauthenticated request will receive a 403 before the generator is even created.

### Decision: ANSI stripping applied per-chunk, not per-line

The `re.sub` for ANSI escapes is applied to each chunk returned by the Jenkins progressive text API before splitting into lines. This avoids partial ANSI sequences at chunk boundaries being emitted raw.

## Risks / Trade-offs

- **Worker thread held open** — each active SSE connection holds a Gunicorn worker for the build duration. For an internal tool with few concurrent users this is acceptable. Mitigation: 30-minute generator timeout closes abandoned streams.
- **Jenkins unreachable mid-stream** — if Jenkins goes away while a build is running, the generator catches the exception, emits `event: error\ndata: Jenkins unreachable\n\n`, and closes. The client sees a clean terminal event rather than a hanging connection.
- **OpenAPI SSE representation** — OpenAPI 3.0 has no first-class SSE type. The endpoint is documented as `text/event-stream` with a string response schema and a note in the description. This is standard practice and understood by `openapi-typescript`.

## Decisions — DO NOT REVISIT

(For AI implementers: these decisions are final for this change.)
- Do not add `requests`, `django-channels`, `channels`, or any new pip dependency.
- Use `urllib.request` with `base64`-encoded Basic Auth for the Jenkins progressive text call.
- Poll interval is exactly 1 second (`time.sleep(1)`). Do not vary it.
- Maximum 1800 poll attempts (30 min).
- Strip ANSI codes per-chunk using the same regex already used in the `/console/` endpoint.
- Do not modify the existing `/console/` endpoint.
- Regenerate `openapi.yaml` after adding the endpoint; drift test will fail otherwise.
- The generator must catch all exceptions and emit a terminal SSE event before closing — never let an uncaught exception escape into the streaming response.

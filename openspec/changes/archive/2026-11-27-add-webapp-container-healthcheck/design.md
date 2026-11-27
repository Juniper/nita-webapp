## Context

The Compose stack needs a reliable process health signal without adding curl or
wget to the webapp image. Django exposes an unauthenticated CSRF endpoint that
can establish whether the HTTP server is responding.

## Decisions

- Use Python's standard-library `urllib` from the existing Python runtime.
- Give the request a five-second timeout. Any HTTP response below 500 means the
  server is alive; an HTTP 5xx, connection failure or timeout means unhealthy.
- Report connection failures on stderr so Docker health logs explain failures.

## Risks / Trade-offs

- A 4xx response can indicate host validation configuration rather than a dead
  process. It is considered healthy because the probe measures server
  availability, not application configuration correctness.

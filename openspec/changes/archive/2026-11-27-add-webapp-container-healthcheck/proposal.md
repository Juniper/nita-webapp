## Why

The webapp image has no endpoint-based Docker health status, so Compose can
report a running but unresponsive Django process as healthy.

## What Changes

- Add a Docker `HEALTHCHECK` using a Python standard-library probe against the
  unauthenticated CSRF endpoint.
- Treat HTTP responses below 500 as healthy, but timeouts, connection errors,
  and server errors as unhealthy.
- Cover the probe's status handling with focused tests.

## Capabilities

### New Capabilities

- `container-health`: Define the webapp container's HTTP health probe.

## Impact

The webapp `Dockerfile`, healthcheck script and backend test suite change. The
image gains no runtime dependency.

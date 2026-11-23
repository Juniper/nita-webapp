## Why

The webapp's Docker Compose deployment and proxy specifications depend on
Nginx. The companion NITA change replaces the main Kubernetes proxy and the
optional MCP sidecar with Traefik. Compose and the webapp's proxy contracts
need a coordinated migration so deployment methods continue to behave alike.

## What Changes

- Replace the Compose Nginx proxy with pinned Traefik configuration, retaining
  HTTPS, certificates, webapp and Jenkins routing, session authentication,
  trusted identity propagation, request limits, and streams.
- Update Nginx-specific proxy requirements to describe Traefik behavior for
  both Compose and Kubernetes.
- Add proxy-level Compose verification and document certificate migration and
  rollback.

## Capabilities

### New Capabilities

- `compose-proxy`: Traefik proxy configuration and migration for Compose.

### Modified Capabilities

- `api`: HTTPS termination by the Traefik proxy.
- `jenkins-reverse-proxy`: Traefik routing and forwarded headers for Jenkins.
- `console-streaming`: Unbuffered action-history streams through Traefik.
- `network-lifecycle-streaming`: Unbuffered lifecycle streams through Traefik.

## Impact

Changes affect `docker-compose.yaml`, proxy configuration, tests,
documentation and OpenSpec. Coordinate with NITA's
`migrate-main-proxy-to-traefik` change and the existing
`gate-jenkins-behind-webapp-session` and Jenkins security changes. No change to
the webapp API, Jenkins authentication model or database is intended.

Before applying this change, create and archive a separate console-streaming
specification cleanup that preserves existing behavior and scenarios while
resolving both long-requirement warnings under strict validation. Reconcile
this change's console-streaming delta with the cleaned-up requirement names.

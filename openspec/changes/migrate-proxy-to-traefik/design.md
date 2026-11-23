## Context

Compose currently mounts `nginx/nginx.conf` and its certificate directory,
exposes host port 443, and joins the external `nita-network`. The shared proxy
configuration routes webapp and Jenkins traffic, applies a 20 MiB request
limit, and enables long-lived SSE. The Jenkins session-gate change requires
forward authentication and trusted identity propagation. Jenkins is not a
service in this Compose file; its name must resolve on the external network or
through the operator's existing setup.

## Decisions

- Replace the Compose proxy with the same reviewed Traefik release family as
  the NITA controller. Use explicit static and dynamic file configuration,
  not Docker socket access. Retain the `proxy` service name, network, host
  port 443, internal HTTP listener on 8000, existing certificate and key, and
  webapp and Jenkins backend addresses. Preserve the existing certificate path
  as an upgrade input and document any new configuration paths.
- Preserve host/IP/no-SNI certificate presentation, `/jenkins` normalization,
  pass-through of Jenkins' prefix, redirects through forwarded ports, 20 MiB
  request limit, and unbuffered SSE with at least 1850 seconds idle time. Verify
  the chosen Traefik release rather than assuming equivalent timeout behavior.
- Transform `/api/v1/auth/forward/` into a single Traefik contract: valid
  sessions return the `X-Forwarded-User` and `X-Forwarded-Groups` headers;
  unauthenticated requests return a login redirect with a validated, safely
  encoded original Jenkins path. Traefik's forward-auth middleware relays the
  redirect and replaces client-supplied identity headers with those from the
  authenticated response. Remove client-supplied Authorization before
  forwarding to Jenkins, and fail closed when authentication fails. Do not
  retain an Nginx-specific response mode.
- Coordinate OpenSpec deltas and release sequencing with the in-progress
  `gate-jenkins-behind-webapp-session` change, which defines the authentication
  contract, and with NITA's Kubernetes change. Retain the old Compose proxy
  configuration, prior webapp image and certificate inputs until successful
  verification and document an explicit rollback. Because the auth contract
  changes, restoring Nginx also requires restoring the prior webapp image.
  Do not remove Nginx assets while an existing deployment or rollback needs them.

## Risks / Trade-offs

- Compose has no Ingress API; its file-provider config is independent of
  Kubernetes manifests and must be tested separately for behavioral parity.
- The Compose file does not create Jenkins. Tests need a controlled Jenkins
  backend or an existing reachable service, and must not silently skip
  authentication and identity checks.
- The new forward-auth contract is incompatible with the old Nginx proxy. Both
  deployments must be upgraded as a coordinated pair; the NITA Kubernetes
  migration must be ready before publishing the webapp image as `latest`.

## Migration Plan

Check and reuse the operator's existing certificate and key, then start the
replacement proxy with the existing service and port. Verify certificate
identity, webapp and Jenkins access, session/identity behavior, and streaming.
If verification fails, restore both the previous Compose proxy configuration
and its compatible webapp image, then verify HTTPS again. Coordinate version
compatibility and rollback with NITA's Kubernetes migration.

## Open Questions

- Confirm middleware ordering and the endpoint's redirect validation through
  end-to-end testing before deployment.

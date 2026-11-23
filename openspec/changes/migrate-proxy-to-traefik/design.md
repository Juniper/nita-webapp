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
- Preserve the webapp session gate: consult `/api/v1/auth/forward/`, fail closed
  on errors, redirect denied browser requests to login with a safe return path,
  and pass only authenticated user and group headers to Jenkins while removing
  client-supplied Authorization. Verify the actual middleware combination
  supports denial redirects and spoof resistance before replacing Nginx.
- Coordinate OpenSpec deltas and release sequencing with the in-progress
  `gate-jenkins-behind-webapp-session` change, which defines the authentication
  contract, and with NITA's Kubernetes change. Retain the old Compose proxy
  configuration and certificate inputs until successful verification and
  document an explicit rollback. Do not remove Nginx assets while an existing
  supported deployment or upgrade still needs them.

## Risks / Trade-offs

- Compose has no Ingress API; its file-provider config is independent of
  Kubernetes manifests and must be tested separately for behavioral parity.
- The Compose file does not create Jenkins. Tests need a controlled Jenkins
  backend or an existing reachable service, and must not silently skip
  authentication and identity checks.
- Authentication denial redirects are not necessarily provided by Traefik's
  forward-auth middleware alone. A tested solution is required before cutover.

## Migration Plan

Check and reuse the operator's existing certificate and key, then start the
replacement proxy with the existing service and port. Verify certificate
identity, webapp and Jenkins access, session/identity behavior, and streaming.
If verification fails, restore the previous Compose proxy configuration and
verify HTTPS again. Coordinate version compatibility and rollback with NITA's
Kubernetes migration; either deployment can be rolled back independently.

## Open Questions

- Which supported middleware combination reproduces session denial redirects
  without weakening identity checks? Resolve and verify before deployment.

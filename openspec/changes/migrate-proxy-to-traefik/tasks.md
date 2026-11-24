## 1. Compose proxy

- [x] 1.0 Create and archive a separate console-streaming spec cleanup; preserve behavior and scenarios, resolve both strict-validation length warnings, and reconcile this change's delta with the resulting requirement names.
- [x] 1.1 Pin Traefik and replace the Compose proxy with file-provider routing, retaining the existing network, port, certificates and backend resolution.
- [x] 1.2 Transform the existing forward-auth endpoint for Traefik, including safe login redirects and Jenkins identity headers; verify spoof protection and coordinate with the existing session-gate change.
- [x] 1.3 Configure TLS fallback, nonstandard-port redirects, 20 MiB request limit and stream-safe timeouts without a Docker socket.

## 2. Documentation and specifications

- [ ] 2.1 Update Nginx-specific proxy requirements and documentation for both Compose and Kubernetes; coordinate release ordering with NITA and Jenkins.
- [x] 2.2 Document reuse of existing certificate files, coordinated proxy/webapp migration, validation and rollback to the compatible Nginx proxy and webapp image together.
- [ ] 2.3 After the session-gate change is archived, replace its original forward-auth requirement with the Traefik contract in this change's auth delta before archiving this change.

## 3. Verification

- [x] 3.1 Test actual HTTPS routes, certificate identity for hostname/IP/no-SNI, Jenkins assets, forwarded headers, redirects and request-size limits.
- [x] 3.2 Test anonymous and authenticated Jenkins requests, login return, auth-service failure and spoofed identity/Authorization headers against controlled backends.
- [x] 3.3 Test incremental output for both SSE routes and the 1850-second idle threshold; run the latter separately if needed.
- [x] 3.4 Exercise existing-certificate upgrade and rollback; validate Compose configuration and strict OpenSpec deltas.

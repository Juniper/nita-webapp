## MODIFIED Requirements

### Requirement: HTTPS Enforcement
The Traefik proxy SHALL terminate TLS and route webapp HTTP traffic to the
webapp on port 8000. It SHALL listen on port 443 for HTTPS and port 8000 for
internal HTTP without exposing port 8000 on the host.

#### Scenario: HTTPS access
- **GIVEN** the proxy is running with a valid certificate
- **WHEN** a client connects to the host on port 443
- **THEN** the connection is served over TLS

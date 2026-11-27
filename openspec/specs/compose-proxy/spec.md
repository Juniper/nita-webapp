# compose-proxy Specification

## Purpose

Specify the Compose deployment's Traefik proxy, including safe migration,
request limits, TLS identity, and rollback behavior.

## Requirements

### Requirement: Traefik Compose proxy
The webapp Compose deployment SHALL use a pinned Traefik proxy configured via
files without Docker socket access. It SHALL retain host HTTPS port 443, the
external NITA network, the webapp and Jenkins backend routes, and an in-container
HTTP listener on port 8000 without exposing that port on the host. It SHALL
reject request bodies larger than 20 MiB and preserve externally visible ports
in redirects.

#### Scenario: HTTPS webapp access
- **GIVEN** the Compose services and existing certificate are available
- **WHEN** a client connects to the host on port 443
- **THEN** Traefik serves the webapp over HTTPS

#### Scenario: Oversized request
- **WHEN** a client sends a request body larger than 20 MiB through the proxy
- **THEN** the proxy rejects it instead of forwarding it as an accepted request

### Requirement: Compose proxy migration and recovery
An upgrade SHALL reuse the existing certificate and key and preserve the
previous proxy configuration until the replacement is verified. Documentation
SHALL describe how to restore the previous proxy if verification fails.

#### Scenario: Upgrade preserves certificate
- **GIVEN** a Compose installation with a usable certificate and key
- **WHEN** its proxy is upgraded
- **THEN** hostname, IP-address and no-SNI clients receive the existing certificate

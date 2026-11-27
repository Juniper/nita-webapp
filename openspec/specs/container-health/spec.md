# container-health Specification

## Purpose

Define how the webapp container reports HTTP server availability to its
container runtime.

## Requirements

### Requirement: Webapp image reports HTTP health
The webapp image SHALL probe `/api/v1/auth/csrf/` with a five-second timeout,
using no added runtime dependency. HTTP responses below 500 SHALL be healthy;
HTTP 5xx responses and connection failures SHALL be unhealthy.

#### Scenario: Webapp responds
- **WHEN** the health probe receives any HTTP response below 500
- **THEN** it exits successfully

#### Scenario: Webapp is unavailable
- **WHEN** the health probe receives an HTTP 5xx, times out, or cannot connect
- **THEN** it exits unsuccessfully and reports connection failures to stderr

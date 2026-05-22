# Jenkins Trigger Security Specification

## Purpose
The webapp SHALL trigger Jenkins jobs via an internal unauthenticated HTTP path
(Django → Jenkins service), so that job triggering works reliably regardless of
how the user accesses NITA externally (proxy, port-forward, NAT, etc.).

## Requirements

### Requirement: Trigger Succeeds Regardless of Deployment Topology
The system SHALL successfully trigger a Jenkins job via
`POST /api/v1/networks/{id}/trigger/{action_id}/` when NITA is accessed through
any proxy, port-forward, or NAT layer, without requiring the caller to know the
internal Jenkins hostname or port.

All Jenkins communication SHALL originate from the Django application container
to the internal Jenkins service (`jenkins:8080`), never from the client browser
directly. No credentials or CSRF crumb are required for this internal path.

#### Scenario: Trigger via port-forwarded host
- GIVEN NITA is accessed at an externally assigned IP and port (e.g. `https://10.x.x.x:8443/`)
- WHEN the user triggers a job via the UI
- THEN a 202 Accepted response is returned
- AND the Jenkins job is queued successfully

#### Scenario: Trigger via localhost tunnel
- GIVEN NITA is accessed via an SSH tunnel or localhost port-forward
- WHEN POST /api/v1/networks/{id}/trigger/{action_id}/ is called
- THEN a 202 Accepted response is returned
- AND the Jenkins job is queued successfully

### Requirement: Internal Jenkins Communication Is Unauthenticated
The Django application SHALL communicate with the Jenkins internal service using
plain unauthenticated HTTP — no `Authorization` header and no CSRF crumb.

Jenkins SHALL be configured to allow anonymous access with `Job/Build` permission
and CSRF protection disabled on its internal service port. External access to
Jenkins on its own exposed port retains Jenkins' full security realm; this
requirement applies only to the internal service-to-service path.

#### Scenario: Trigger request contains no Authorization header
- GIVEN a valid NITA session and a Jenkins service configured for anonymous internal access
- WHEN POST /api/v1/networks/{id}/trigger/{action_id}/ is called
- THEN the Django backend sends the job trigger POST to Jenkins with no Authorization header
- AND no crumb fetch is made before the trigger request

### Requirement: Trigger Returns Descriptive Error When Jenkins Unreachable
The system SHALL return a `503 Service Unavailable` response with a
human-readable JSON error message when the Jenkins service cannot be reached
during a trigger request (connection refused, timeout, or crumb fetch failure).

The error SHALL NOT expose internal hostnames or stack traces to the client.

#### Scenario: Jenkins unreachable returns 503
- GIVEN the Jenkins service is not running or unreachable from the Django container
- WHEN POST /api/v1/networks/{id}/trigger/{action_id}/ is called
- THEN a 503 response is returned with `{"error": "Jenkins service unavailable"}`

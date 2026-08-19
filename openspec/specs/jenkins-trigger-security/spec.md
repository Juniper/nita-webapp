# Jenkins Trigger Security Specification

## Purpose
The webapp SHALL trigger Jenkins jobs via an internal authenticated HTTP path
(Django → Jenkins service), so that job triggering works reliably regardless of
how the user accesses NITA externally (proxy, port-forward, NAT, etc.). The
Django container authenticates to Jenkins on the caller's behalf, so the caller
never needs Jenkins credentials.
## Requirements
### Requirement: Trigger Succeeds Regardless of Deployment Topology
The system SHALL successfully trigger a Jenkins job via
`POST /api/v1/networks/{id}/trigger/{action_id}/` when NITA is accessed through
any proxy, port-forward, or NAT layer, without requiring the caller to know the
internal Jenkins hostname or port.

All Jenkins communication SHALL originate from the Django application container
to the internal Jenkins service (`jenkins:8080`), never from the client browser
directly. The Django container authenticates to Jenkins on the caller's behalf,
so the caller never needs Jenkins credentials or a crumb.

#### Scenario: Trigger via port-forwarded host
- GIVEN NITA is accessed at an externally assigned IP and port (e.g. `https://10
.x.x.x:8443/`)
- WHEN the user triggers a job via the UI
- THEN a 202 Accepted response is returned
- AND the Jenkins job is queued successfully

#### Scenario: Trigger via localhost tunnel
- GIVEN NITA is accessed via an SSH tunnel or localhost port-forward
- WHEN POST /api/v1/networks/{id}/trigger/{action_id}/ is called
- THEN a 202 Accepted response is returned
- AND the Jenkins job is queued successfully

### Requirement: Internal Jenkins Communication Is Authenticated
The Django application SHALL communicate with the internal Jenkins service using
authenticated requests — a username and password (`JENKINS_SERVER_USER` /
`JENKINS_SERVER_PASS`) — and SHALL supply a CSRF crumb for build requests via a
`CrumbRequester`. This applies to all Django→Jenkins paths: triggering an action, and the
synchronous create/delete network jobs. The internal base URL SHALL target the Jenkins
service under its `/jenkins` context path (e.g. `http://jenkins:8080/jenkins`).

All Jenkins communication SHALL still originate from the Django application container to the
internal Jenkins service, never from the client browser directly.

#### Scenario: Trigger uses authenticated Jenkins client with a crumb
- GIVEN a valid NITA session and configured Jenkins credentials
- WHEN POST /api/v1/networks/{id}/trigger/{action_id}/ is called
- THEN the Django backend authenticates to Jenkins with username/password
- AND a CSRF crumb is obtained before the build is invoked
- AND the Jenkins job is invoked successfully

#### Scenario: Create/delete jobs use the authenticated Jenkins server
- GIVEN configured Jenkins credentials
- WHEN a network create or delete runs the `network_template_mgr` job
- THEN the job is submitted through the authenticated Jenkins server
- AND anonymous (credential-less) submission is not used

#### Scenario: Internal base URL includes the /jenkins prefix
- GIVEN Jenkins serves under the `/jenkins` context path
- WHEN the Django Jenkins client constructs `JENKINS_SERVER_URL`
- THEN the base URL includes the `/jenkins` path prefix (e.g. `http://jenkins:8080/jenkins`)

#### Scenario: Container startup scripts use the prefixed base URL
- GIVEN Jenkins serves under the `/jenkins` context path
- WHEN the webapp entrypoint runs its Jenkins readiness gate and job bootstrap (`ping_jenkins.py`, `configure_jenkins.py`, `add_jenkins_job.py`)
- THEN each script targets `http://jenkins:8080/jenkins` and the startup gate succeeds so Django boots

### Requirement: Trigger Returns Descriptive Error When Jenkins Unreachable
The system SHALL return a `503 Service Unavailable` response with a
human-readable JSON error message when the Jenkins service cannot be reached
during a trigger request (connection refused, timeout, or crumb fetch failure).

The error SHALL NOT expose internal hostnames or stack traces to the client.

#### Scenario: Jenkins unreachable returns 503
- GIVEN the Jenkins service is not running or unreachable from the Django
  container
- WHEN POST /api/v1/networks/{id}/trigger/{action_id}/ is called
- THEN a 503 response is returned with `{"error": "Jenkins service unavailable"}`

### Requirement: SPA Checks Trigger Response Before Opening EventSource
The SPA SHALL inspect the HTTP status of the trigger response before opening a
Server-Sent Events stream. A non-202 response means no `action_history_id` is
available; opening `EventSource('/api/v1/action-history/undefined/stream/')` is
incorrect and SHALL be prevented.

When the trigger POST returns a non-2xx status the SPA SHALL:
- Display a human-readable error line in the console panel
  (e.g. `[error] Trigger failed (HTTP 403)`).
- Set the console panel state to `error`.
- NOT open an EventSource connection.

When the trigger POST returns 403 specifically, the SPA SHALL clear its cached
CSRF token so that the next trigger attempt fetches a fresh token rather than
re-using a stale one.

When the trigger POST returns 2xx but the response body does not contain an
`action_history_id`, the SPA SHALL treat this as a trigger failure and display
an error (`[error] Trigger returned no job ID`) without opening an EventSource.

#### Scenario: Trigger returns 403 — console shows error, no stream opened
- GIVEN the CSRF token in the SPA is stale or the user session has expired
- WHEN the user clicks Run for a Jenkins action
- THEN the trigger POST returns 403
- AND the console panel shows `[error] Trigger failed (HTTP 403)`
- AND no EventSource connection is opened
- AND the CSRF token cache is cleared so the next attempt re-fetches the token

#### Scenario: Trigger returns 503 — console shows error, no stream opened
- GIVEN the Jenkins service is unreachable
- WHEN the user clicks Run for a Jenkins action
- THEN the trigger POST returns 503 with `{"error": "Jenkins service unavailable"}`
- AND the console panel shows `[error] Trigger failed (HTTP 503)`
- AND no EventSource connection is opened

#### Scenario: Network failure on trigger — console shows error
- GIVEN the Django backend is unreachable (network error)
- WHEN the user clicks Run for a Jenkins action
- THEN the SPA catches the fetch rejection
- AND the console panel shows `[error] Trigger request failed`
- AND no EventSource connection is opened


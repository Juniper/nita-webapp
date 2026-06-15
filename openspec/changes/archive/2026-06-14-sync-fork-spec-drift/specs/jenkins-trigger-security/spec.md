## REMOVED Requirements

### Requirement: Internal Jenkins Communication Is Unauthenticated
**Reason**: Jenkins rejects anonymous build requests with `403 Forbidden` (no
CSRF crumb), which surfaced to users as `HTTP 503` in the GUI. Commit `fde58cb`
switched all Jenkins communication to authenticated `jenkinsapi`/python-jenkins
calls with a username/password and a CSRF crumb. The "unauthenticated internal
path" assertion no longer describes the system.
**Migration**: No client-facing migration. The Django container must have valid
`JENKINS_USER` / `JENKINS_PASS` credentials available; these are already
configured at startup. External clients are unaffected.

## ADDED Requirements

### Requirement: Internal Jenkins Communication Is Authenticated
The Django application SHALL communicate with the internal Jenkins service using
authenticated requests — a username and password (`JENKINS_SERVER_USER` /
`JENKINS_SERVER_PASS`) — and SHALL supply a CSRF crumb for build requests via a
`CrumbRequester`. This applies to all Django→Jenkins paths: triggering an
action, and the synchronous create/delete network jobs.

All Jenkins communication SHALL still originate from the Django application
container to the internal Jenkins service, never from the client browser
directly.

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

## MODIFIED Requirements

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
- GIVEN NITA is accessed at an externally assigned IP and port (e.g. `https://10.x.x.x:8443/`)
- WHEN the user triggers a job via the UI
- THEN a 202 Accepted response is returned
- AND the Jenkins job is queued successfully

#### Scenario: Trigger via localhost tunnel
- GIVEN NITA is accessed via an SSH tunnel or localhost port-forward
- WHEN POST /api/v1/networks/{id}/trigger/{action_id}/ is called
- THEN a 202 Accepted response is returned
- AND the Jenkins job is queued successfully

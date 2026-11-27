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
directly.

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

#### Scenario: Caller needs no Jenkins credentials or crumb
- GIVEN a caller with a valid NITA session but no Jenkins credentials
- WHEN the caller triggers an action
- THEN the Django container authenticates to Jenkins on the caller's behalf
- AND the caller never supplies Jenkins credentials or a crumb

### Requirement: Internal Jenkins Communication Is Authenticated
The Django application SHALL assert the appropriate user or service identity
on every internal Jenkins request without sending a password or relying on
anonymous permissions. Build requests SHALL include a CSRF crumb. The internal
service URL SHALL include `/jenkins`. Browser access to Jenkins SHALL use the
session-gated proxy, not the internal service or Jenkins credentials.

#### Scenario: Trigger uses authenticated Jenkins client with a crumb
- GIVEN a valid NITA session
- WHEN POST /api/v1/networks/{id}/trigger/{action_id}/ is called
- THEN the Django backend asserts the acting user's Jenkins identity
- AND a CSRF crumb is obtained before the build is invoked
- AND the Jenkins job is invoked successfully

#### Scenario: Create/delete jobs use the authenticated Jenkins server
- GIVEN a configured Jenkins service identity
- WHEN a network create or delete runs the `network_template_mgr` job
- THEN the job is submitted through the authenticated Jenkins server
- AND anonymous (credential-less) submission is not used

#### Scenario: Console stream requests carry the service identity
- GIVEN a configured Jenkins service identity
- WHEN the SSE console generator requests `/job/{job}/{build}/logText/progressiveText`
- THEN each request asserts the service identity using `X-Forwarded-User`
- AND does not send an `Authorization` header

#### Scenario: All internal Jenkins paths assert identity
- GIVEN Django communicates with Jenkins
- WHEN it triggers actions or network management jobs, validates network types, polls build status, reads lifecycle history, relays Robot summaries or streams console text
- THEN every request originates from the Django container and asserts the appropriate user or service identity

#### Scenario: Console stream works without anonymous Job/Read
- GIVEN Jenkins grants no permissions to the `anonymous` user
- WHEN an authenticated NITA user opens the console stream for a running build
- THEN log lines are streamed and the stream ends with `event: done`

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
Server-Sent Events stream, and opening
`EventSource('/api/v1/action-history/undefined/stream/')` SHALL be prevented.

When the trigger POST returns a non-2xx status the SPA SHALL:
- Display a human-readable error line in the console panel
  (e.g. `[error] Trigger failed (HTTP 403)`).
- Set the console panel state to `error`.
- NOT open an EventSource connection.

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

#### Scenario: Non-202 response carries no job ID to stream
- GIVEN the trigger POST returns a non-202 status
- WHEN the SPA handles the response
- THEN it treats `action_history_id` as unavailable
- AND it never requests `/api/v1/action-history/undefined/stream/`

### Requirement: SPA Clears Cached CSRF Token After Trigger 403
When the trigger POST returns 403 specifically, the SPA SHALL clear its cached
CSRF token so that the next trigger attempt fetches a fresh token rather than
re-using a stale one.

#### Scenario: Next trigger after a 403 fetches a fresh CSRF token
- GIVEN the SPA holds a cached CSRF token
- AND a trigger POST returned 403
- WHEN the user triggers an action again
- THEN the SPA fetches a fresh token from `GET /api/v1/auth/csrf/` before
  sending the trigger POST

### Requirement: SPA Treats a Trigger Response Without a Job ID as a Failure
When the trigger POST returns 2xx but the response body does not contain an
`action_history_id`, the SPA SHALL treat this as a trigger failure and display
an error (`[error] Trigger returned no job ID`) without opening an EventSource.

#### Scenario: 2xx response missing action_history_id
- GIVEN the trigger POST returns a 2xx status
- AND the response body has no `action_history_id`
- WHEN the SPA processes the response
- THEN the console panel shows `[error] Trigger returned no job ID`
- AND no EventSource connection is opened

### Requirement: Builds Are Attributed to the Triggering Webapp User
Per-network action builds SHALL assert the acting user's identity and groups to
Jenkins (`X-Forwarded-User` / `X-Forwarded-Groups`), so Jenkins records a
`UserIdCause` and applies that user's job permissions. Management jobs and all
other webapp→Jenkins calls SHALL assert the `JENKINS_USER` service identity.
The webapp SHALL NOT send a password to Jenkins.

#### Scenario: Action trigger is attributed to the user
- GIVEN user `alice` (role `user`, member of team 7) triggers an action on a network
- WHEN the Jenkins build is invoked
- THEN the build request carries `X-Forwarded-User: alice` and `X-Forwarded-Groups: user|team-7`
- AND `GET /job/{job}/{build}/api/json` lists a `hudson.model.Cause$UserIdCause` with `userId` `alice`

#### Scenario: Network create runs as the service identity
- GIVEN user `bob` creates a network
- WHEN the `network_template_mgr` build is invoked
- THEN the build request carries `X-Forwarded-User: <JENKINS_USER>`
- AND the webapp records `bob` as the network owner

#### Scenario: Network-type validation runs as the service identity
- GIVEN user `carol` uploads a network type for validation
- WHEN the `network_type_validator` build is invoked
- THEN the build request carries `X-Forwarded-User: <JENKINS_USER>`
- AND the webapp records `carol` as the type's creator

#### Scenario: Service calls use the service identity without a password
- GIVEN the webapp relays a console stream or Robot summary, or polls build status
- WHEN it calls Jenkins
- THEN the request carries `X-Forwarded-User: <JENKINS_USER>` and no `Authorization` header

#### Scenario: Webapp startup does not define a Jenkins password
- GIVEN the webapp image, Compose configuration, and startup scripts are inspected
- WHEN Jenkins connection settings are configured
- THEN they do not define or synthesize `JENKINS_PASS`

### Requirement: Network job management runs without Jenkins passwords
The `network_template_mgr` job definition shipped by the webapp SHALL create
and delete per-network Jenkins jobs through the Jenkins REST API
(`POST /createItem`, `POST /job/<name>/doDelete`) with a crumb and the
`X-Forwarded-User` service identity, not through `jenkins-cli.jar` with a
password. A failure to create or delete a job SHALL fail the build.

#### Scenario: Creating a network creates its jobs
- GIVEN a network type with actions `build_x`, `dump_x`, `test_x`
- WHEN a user creates network `n1` from the webapp
- THEN the `network_template_mgr` build creates jobs `build_x-n1`, `dump_x-n1`, `test_x-n1`
- AND they can be triggered from the network page by users the webapp allows

#### Scenario: Job creation failure is not silent
- GIVEN Jenkins rejects the job creation request (e.g. HTTP 401/403/500)
- WHEN the `network_template_mgr` build runs
- THEN the build finishes `FAILURE` with the HTTP status in its log

#### Scenario: Deleting a network deletes its jobs
- GIVEN network `n1` exists with its three jobs
- WHEN the user deletes the network
- THEN the `network_template_mgr` build deletes the three jobs (a missing job is tolerated) and removes the project folder

### Requirement: Per-network Jenkins jobs mirror the webapp access model
Each per-network job SHALL carry an `AuthorizationMatrixProperty` (inheriting
the global matrix) granting the network owner and the network's team group
`team-<id>` `Job/Read`, `Job/Build` and `Job/Cancel`. The webapp SHALL pass
`owner` and `team_group` to `network_template_mgr` on create, and SHALL
re-apply the matrix (`operation=acl`) when a network's team changes or its
networks are transferred to another owner.

#### Scenario: Owner, team member, stranger
- GIVEN `alice` owns network `n1` shared with team 7, `bob` is in team 7, and `carl` (role `user`) is in neither
- WHEN each opens `/jenkins/job/build_x-n1/` and POSTs a build with a valid crumb
- THEN `alice` and `bob` get 200 and their builds are queued (201), attributed to each of them
- AND `carl` gets 404 for both

#### Scenario: Power users and admins are unrestricted
- GIVEN `pat` has role `power_user`
- WHEN she opens any per-network job or triggers it
- THEN the request is permitted, with no per-job grant for her

#### Scenario: Sharing a network updates its jobs
- GIVEN `alice` sets `team` on `n1` to team 9 via `PATCH /api/v1/networks/{id}/`
- WHEN the request succeeds
- THEN a `network_template_mgr` `operation=acl` build runs with `team_group=team-9`
- AND members of team 9 can read `n1`'s jobs afterwards

#### Scenario: Ownership transfer updates the jobs
- GIVEN an admin transfers `alice`'s networks to `dave` via `POST /api/v1/users/{id}/transfer/`
- WHEN the transfer succeeds
- THEN an `operation=acl` build runs per transferred network with `owner=dave`

#### Scenario: Management jobs are not exposed to regular users
- GIVEN a user with role `user`
- WHEN they open `/jenkins/job/network_template_mgr/` or POST a build to it
- THEN both are HTTP 404

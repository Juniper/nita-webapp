## MODIFIED Requirements

### Requirement: Internal Jenkins Communication Is Authenticated
The Django application SHALL communicate with the internal Jenkins service using
authenticated requests — a username and password (`JENKINS_SERVER_USER` /
`JENKINS_SERVER_PASS`) — and SHALL supply a CSRF crumb for build requests via a
`CrumbRequester`. This applies to **every** Django→Jenkins HTTP path without
exception: action triggers, network create/delete jobs, network-type
validation, build-status polling, lifecycle history, the Robot Framework
summary relay, and the progressive console text used by the SSE stream. The
Django application SHALL NOT depend on Jenkins granting any permission to the
`anonymous` user. The
internal base URL SHALL target the Jenkins service under its `/jenkins` context
path (e.g. `http://jenkins:8080/jenkins`).

All Django-initiated Jenkins API and job-operation requests SHALL originate
from the Django application container to the internal Jenkins service. Browser
access to the Jenkins UI SHALL use only the session-gated reverse proxy; the
browser SHALL NOT connect to the internal Jenkins service directly or receive
Jenkins credentials.

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

#### Scenario: Console stream requests carry credentials
- GIVEN configured Jenkins credentials
- WHEN the SSE console generator requests `/job/{job}/{build}/logText/progressiveText`
- THEN each request includes an `Authorization: Basic` header built from `JENKINS_SERVER_USER` / `JENKINS_SERVER_PASS`

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

## ADDED Requirements

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

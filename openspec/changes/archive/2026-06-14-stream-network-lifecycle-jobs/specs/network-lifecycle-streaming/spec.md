## ADDED Requirements

### Requirement: Shared Jenkins Job Invocation Library
The system SHALL provide a single shared backend helper for invoking a Jenkins
job that performs the authenticated build request used by every job-triggering
endpoint. The helper SHALL authenticate using the configured Jenkins username
and password with a CSRF crumb (Jenkins rejects anonymous build requests with
`403`), reserve and return the job's build number (`nextBuildNumber`) for the
invocation, and accept optional build parameters and file attachments. On a
crumb/`Forbidden` failure it SHALL rebuild the server connection and retry once.
If Jenkins is unreachable it SHALL raise an error that callers translate into a
`503 Service Unavailable` response.

The network create, network delete, network-type load, and per-network action
trigger flows SHALL all invoke Jenkins through this shared helper rather than
duplicating crumb/authentication logic.

#### Scenario: Helper reserves and returns the build number
- **WHEN** a caller invokes a Jenkins job through the shared helper
- **THEN** the job is started with an authenticated crumbed request
- **AND** the build number reserved for that invocation is returned to the caller

#### Scenario: Crumb rejection is retried once
- **WHEN** the first invocation fails with a `Forbidden` crumb error
- **THEN** the helper rebuilds the Jenkins connection and retries the invocation once

#### Scenario: Unreachable Jenkins raises for a 503
- **WHEN** the Jenkins service is not reachable from the Django container
- **THEN** the helper raises an error
- **AND** the calling endpoint returns `503 Service Unavailable` with a failure reason

### Requirement: Shared Jenkins Console Stream Library
The system SHALL provide a single shared backend generator that streams a
Jenkins build's console output as Server-Sent Events for a given job name and
build number. The generator SHALL poll the Jenkins progressive-text API, emit
`data: <line>` events for new output, strip ANSI escape codes, tolerate the
initial queued window where the build returns `404`, and terminate with
`event: done`, `event: error`, or `event: timeout` exactly as the existing
action-history stream does. The action-history stream and the generic
lifecycle stream SHALL both use this shared generator.

#### Scenario: Action-history and lifecycle streams share one generator
- **WHEN** either the action-history stream or the generic lifecycle stream runs
- **THEN** both produce SSE output from the same shared generator
- **AND** both strip ANSI escape codes and emit `done`/`error`/`timeout` terminators

### Requirement: Generic Authenticated Jenkins Console Stream Endpoint
The system SHALL expose an authenticated SSE endpoint
`GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/` that streams the
console output of the named Jenkins job build using the shared console stream
library. The endpoint SHALL respond with `Content-Type: text/event-stream`,
set the `X-Accel-Buffering: no` and `Cache-Control: no-cache` response headers,
and require an authenticated session — unauthenticated requests SHALL receive a
`403` before any streaming begins. The endpoint SHALL NOT require an
`ActionHistory` row, so it can stream lifecycle jobs (network create, network
delete, network-type load) that are not associated with a persisted network or
action.

#### Scenario: Stream a lifecycle job by name and build number
- **WHEN** an authenticated client opens
  `GET /api/v1/jenkins/jobs/network_template_mgr/{build_no}/stream/`
- **THEN** the response has `Content-Type: text/event-stream`
- **AND** console output for that build is emitted as `data:` events
- **AND** an `event: done` event is emitted when the build finishes

#### Scenario: Unauthenticated request rejected
- **WHEN** the endpoint is called without a valid session
- **THEN** a `403` response is returned before any streaming begins

#### Scenario: Header set to defeat proxy buffering
- **WHEN** the endpoint responds
- **THEN** the `X-Accel-Buffering: no` response header is present

### Requirement: Lifecycle Endpoints Return a Jenkins Streaming Handle
Lifecycle endpoints SHALL return a streaming handle in their response body that
identifies the Jenkins job that was started, so the SPA can open the generic
stream endpoint. This applies to the non-blocking network create, network
delete, and network-type load endpoints. The handle SHALL include the Jenkins `job_name` and the `build_no`
reserved for the invocation. Endpoints SHALL return without waiting for the
Jenkins build to complete.

#### Scenario: Create returns a streaming handle
- **WHEN** `POST /api/v1/networks/` starts the create job
- **THEN** the response body includes `job_name` and `build_no`
- **AND** the response is returned without waiting for the build to finish

#### Scenario: Delete returns a streaming handle
- **WHEN** `DELETE /api/v1/networks/{id}/` starts the delete job
- **THEN** the response body includes `job_name` and `build_no`
- **AND** the response is returned without waiting for the build to finish

#### Scenario: Network-type load returns a streaming handle
- **WHEN** `POST /api/v1/network-types/upload/` starts the validation/load job
- **THEN** the response body includes `job_name` and `build_no`
- **AND** the response is returned without waiting for the build to finish

### Requirement: Nginx Must Not Buffer the Generic Lifecycle Stream
The nginx reverse proxy SHALL disable response buffering and caching for the
generic Jenkins stream path so SSE events reach the browser in real time, and
SHALL set `proxy_read_timeout` to at least 1850 seconds to accommodate the
30-minute maximum stream duration. The location matching
`/api/v1/jenkins/jobs/` stream paths SHALL set `proxy_buffering off` and
`proxy_cache off`.

#### Scenario: Lifecycle SSE events reach the browser in real time
- **WHEN** a browser opens the generic lifecycle stream for a running build
- **THEN** console lines appear within about 2 seconds of Jenkins producing them
- **AND** the proxy does not close the connection before the build completes

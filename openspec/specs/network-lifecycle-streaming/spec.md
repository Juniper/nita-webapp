# network-lifecycle-streaming Specification

## Purpose
A shared backend library for invoking Jenkins jobs and streaming their console
output as Server-Sent Events, plus the generic authenticated stream endpoint and
non-blocking lifecycle handles that let the SPA watch network create, delete,
and network-type load jobs run in real time.

## Requirements

### Requirement: Shared Jenkins Job Invocation Library
The system SHALL provide a single shared backend helper for invoking a Jenkins
job that performs the authenticated build request used by every job-triggering
endpoint. The helper SHALL authenticate using the configured Jenkins username
and password with a CSRF crumb (Jenkins rejects anonymous build requests with
`403`), reserve and return the job's build number (`nextBuildNumber`) for the
invocation, and accept optional build parameters and file attachments.

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

### Requirement: Jenkins Invocation Retry and Unavailability Handling
On a crumb/`Forbidden` failure the shared Jenkins job invocation helper SHALL
rebuild the server connection and retry once. If Jenkins is unreachable it SHALL
raise an error that callers translate into a `503 Service Unavailable` response.

#### Scenario: Crumb failure is retried once
- **WHEN** a build request through the shared helper fails with a crumb/`Forbidden` error
- **THEN** the helper rebuilds the server connection and retries the request once

#### Scenario: Unreachable Jenkins becomes a 503
- **WHEN** a job-triggering endpoint invokes the shared helper and Jenkins is unreachable
- **THEN** the helper raises an error
- **AND** the endpoint responds `503 Service Unavailable`

### Requirement: All Job-Triggering Flows Use the Shared Invocation Helper
The network create, network delete, network-type load, and per-network action
trigger flows SHALL all invoke Jenkins through the shared job invocation helper
rather than duplicating crumb/authentication logic.

#### Scenario: Lifecycle and action flows share one invocation path
- **WHEN** a network is created or deleted, a network type is loaded, or a
  per-network action is triggered
- **THEN** the Jenkins build is started through the shared invocation helper

### Requirement: Shared Jenkins Console Stream Library
The system SHALL provide a single shared backend generator that streams a
Jenkins build's console output as Server-Sent Events for a job name and build
number. It SHALL poll the Jenkins progressive-text API, emit
`data: <line>` events for new output, strip ANSI escape codes, tolerate the
initial queued window where the build returns `404`, and terminate with
`event: done`, `event: error`, or `event: timeout`. The action-history and
generic lifecycle streams SHALL both use it.

#### Scenario: Action-history and lifecycle streams share one generator
- **WHEN** either the action-history stream or the generic lifecycle stream runs
- **THEN** both produce SSE output from the same shared generator
- **AND** both strip ANSI escape codes and emit `done`/`error`/`timeout` terminators

### Requirement: Generic Authenticated Jenkins Console Stream Endpoint
The system SHALL expose an authenticated SSE endpoint
`GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/` streaming the named
build's console output via the shared console stream library. The endpoint SHALL respond with `Content-Type: text/event-stream` and
set the `X-Accel-Buffering: no` and `Cache-Control: no-cache` headers.
Unauthenticated requests SHALL receive a `403` before any streaming begins. The
endpoint SHALL NOT require an `ActionHistory` row.

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

#### Scenario: Lifecycle jobs without a persisted network can be streamed
- **WHEN** a network create, network delete, or network-type load job is running
  that is not associated with a persisted network or action
- **THEN** its console can be streamed from the generic endpoint, because no
  `ActionHistory` row is required

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

### Requirement: Proxy Must Not Buffer the Generic Lifecycle Stream
The Traefik proxy SHALL deliver the generic Jenkins lifecycle SSE stream without
response buffering or caching and SHALL allow at least 1850 seconds of idle
stream time.

#### Scenario: Lifecycle SSE events reach the browser in real time
- **WHEN** a browser opens the generic lifecycle stream for a running build
- **THEN** console lines appear within 2 seconds under normal test conditions
  without waiting for the stream to finish

#### Scenario: Proxy does not close an idle lifecycle stream prematurely
- **WHEN** a healthy lifecycle stream is idle for 1850 seconds and then emits an event
- **THEN** the connection remains open and the browser receives the event

## ADDED Requirements

### Requirement: Persist Lifecycle Job Runs
The system SHALL persist a record for each lifecycle Jenkins job run it starts —
network create, network delete, and network-type load. Each record SHALL store
the Jenkins `job_name`, the reserved `build_no`, the run `kind` (one of
`network_create`, `network_delete`, `network_type_load`), a human-readable
`subject` (the network or network-type name the run concerns), a `timestamp`,
and a `status`. The record SHALL be written at the moment the job is invoked so
the run is recoverable even after the associated network or network-type row is
created or deleted.

#### Scenario: Create run is recorded
- **WHEN** `POST /api/v1/networks/` invokes the create job
- **THEN** a lifecycle run is persisted with kind `network_create`, the network
  name as `subject`, and the invoked `job_name` and `build_no`

#### Scenario: Delete run is recorded
- **WHEN** `DELETE /api/v1/networks/{id}/` invokes the delete job
- **THEN** a lifecycle run is persisted with kind `network_delete`, the network
  name as `subject`, and the invoked `job_name` and `build_no`
- **AND** the run remains after the network row is removed

#### Scenario: Network-type load run is recorded
- **WHEN** `POST /api/v1/network-types/upload/` invokes the load job
- **THEN** a lifecycle run is persisted with kind `network_type_load`, the
  network-type name as `subject`, and the invoked `job_name` and `build_no`

### Requirement: List Lifecycle Job Runs
The system SHALL expose a read-only, authenticated endpoint
`GET /api/v1/lifecycle-runs/` that lists persisted lifecycle job runs ordered
newest-first. The endpoint SHALL support filtering by `kind` so the Networks
table can show network create/delete runs and the Network Types table can show
network-type load runs. Each item SHALL include the run `id`, `kind`,
`subject`, `job_name`, `build_no`, `timestamp`, and `status`. Unauthenticated
requests SHALL receive a `403`.

#### Scenario: List returns runs newest-first
- **WHEN** an authenticated client calls `GET /api/v1/lifecycle-runs/`
- **THEN** a 200 response lists persisted lifecycle runs ordered newest-first
- **AND** each item includes `id`, `kind`, `subject`, `job_name`, `build_no`,
  `timestamp`, and `status`

#### Scenario: Filter by kind
- **WHEN** `GET /api/v1/lifecycle-runs/?kind=network_type_load` is called
- **THEN** only network-type load runs are returned

#### Scenario: Unauthenticated request rejected
- **WHEN** `GET /api/v1/lifecycle-runs/` is called without a valid session
- **THEN** a 403 response is returned

### Requirement: View Historical Lifecycle Console Output
The system SHALL expose an authenticated endpoint
`GET /api/v1/lifecycle-runs/{id}/console/` that returns the historical Jenkins
console output for a persisted lifecycle run, resolved from the run's stored
`job_name` and `build_no`. ANSI escape codes SHALL be stripped. When the build
output is not yet available the endpoint SHALL return a placeholder message
rather than an error. Unauthenticated requests SHALL receive a `403`.

#### Scenario: Console output returned for a past run
- **WHEN** an authenticated client calls
  `GET /api/v1/lifecycle-runs/{id}/console/` for a completed run
- **THEN** a 200 response returns the run's console text with ANSI codes stripped

#### Scenario: Console not yet available
- **WHEN** the run's build output is not yet available
- **THEN** a 200 response returns a placeholder message rather than an error

#### Scenario: Unauthenticated request rejected
- **WHEN** `GET /api/v1/lifecycle-runs/{id}/console/` is called without a valid
  session
- **THEN** a 403 response is returned

## ADDED Requirements

### Requirement: Derive Lifecycle Job Runs from Jenkins
The system SHALL derive the history of lifecycle Jenkins job runs — network
create, network delete, and network-type load — directly from Jenkins build
records rather than from a local table. For each run it SHALL report the Jenkins
`job_name`, the `build_no`, the run `kind` (one of `network_create`,
`network_delete`, `network_type_load`), a human-readable `subject` (the network
or network-type name the run concerns, derived from the build parameters), a
`timestamp`, and a `status` derived from the Jenkins build result. Deriving from
Jenkins ensures every run is visible — including runs triggered outside the
React UI — and that history survives a database reset.

The run `kind` SHALL be resolved from the Jenkins job and the build's
`operation` parameter: `network_template_mgr` with `operation=create` is a
`network_create` run, `operation=delete` is a `network_delete` run, and
`network_type_validator` with `operation=add` is a `network_type_load` run.

#### Scenario: Create runs are derived from Jenkins
- **WHEN** the `network_template_mgr` job has builds with `operation=create`
- **THEN** those builds appear as `network_create` runs with the build's
  `network_name` parameter as `subject` and the Jenkins `job_name`/`build_no`

#### Scenario: Delete runs are derived from Jenkins
- **WHEN** the `network_template_mgr` job has builds with `operation=delete`
- **THEN** those builds appear as `network_delete` runs with the build's
  `network_name` parameter as `subject`
- **AND** the runs remain visible after the network row is removed

#### Scenario: Network-type load runs are derived from Jenkins
- **WHEN** the `network_type_validator` job has builds with `operation=add`
- **THEN** those builds appear as `network_type_load` runs with the
  network-type name (from the build's `file_name` parameter, without the `.zip`
  suffix) as `subject`

### Requirement: List Lifecycle Job Runs
The system SHALL expose a read-only, authenticated endpoint
`GET /api/v1/lifecycle-runs/` that lists lifecycle job runs derived from Jenkins
ordered newest-first. The endpoint SHALL support filtering by `kind` so the
Networks table can show network create/delete runs and the Network Types table
can show network-type load runs. Each item SHALL include the run `id` (the
composite `"<job_name>#<build_no>"`), `kind`, `subject`, `job_name`, `build_no`,
`timestamp`, and `status`. When Jenkins is unreachable the endpoint SHALL return
an empty list rather than an error. Unauthenticated requests SHALL receive a
`403`.

#### Scenario: List returns runs newest-first
- **WHEN** an authenticated client calls `GET /api/v1/lifecycle-runs/`
- **THEN** a 200 response lists lifecycle runs ordered newest-first
- **AND** each item includes `id`, `kind`, `subject`, `job_name`, `build_no`,
  `timestamp`, and `status`

#### Scenario: Filter by kind
- **WHEN** `GET /api/v1/lifecycle-runs/?kind=network_type_load` is called
- **THEN** only network-type load runs are returned

#### Scenario: Jenkins unreachable returns empty list
- **WHEN** Jenkins is not reachable from the Django container
- **THEN** a 200 response with an empty list is returned

#### Scenario: Unauthenticated request rejected
- **WHEN** `GET /api/v1/lifecycle-runs/` is called without a valid session
- **THEN** a 403 response is returned

### Requirement: View Historical Lifecycle Console Output
The system SHALL expose an authenticated endpoint
`GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>` that returns
the historical Jenkins console output for a single build, resolved from the
supplied `job_name` and `build_no`. ANSI escape codes SHALL be stripped. The
`job_name` SHALL be constrained to `[A-Za-z0-9_.\-]+` and `build_no` to digits;
an invalid value SHALL return `400`. When the build output is not yet available
the endpoint SHALL return a placeholder message rather than an error.
Unauthenticated requests SHALL receive a `403`.

#### Scenario: Console output returned for a past run
- **WHEN** an authenticated client calls
  `GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>` for a
  completed build
- **THEN** a 200 response returns the build's console text with ANSI codes stripped

#### Scenario: Invalid job name or build number
- **WHEN** `job_name` does not match `[A-Za-z0-9_.\-]+` or `build_no` is not a number
- **THEN** a 400 response is returned

#### Scenario: Console not yet available
- **WHEN** the build output is not yet available
- **THEN** a 200 response returns a placeholder message rather than an error

#### Scenario: Unauthenticated request rejected
- **WHEN** `GET /api/v1/lifecycle-runs/console/` is called without a valid
  session
- **THEN** a 403 response is returned

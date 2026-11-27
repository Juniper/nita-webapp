# network-lifecycle-history Specification

## Purpose
Network lifecycle history exposes the record of network create, network delete,
and network-type load Jenkins job runs, derived live from Jenkins build records,
so operators can list past runs and review their historical console output.
## Requirements
### Requirement: Derive Lifecycle Job Runs from Jenkins
The system SHALL derive the history of lifecycle Jenkins job runs — network
create, network delete, and network-type load — directly from Jenkins build
records rather than from a local table. For each run it SHALL report `job_name`,
`build_no`, `kind` (`network_create`, `network_delete`, or `network_type_load`),
a human-readable `subject` (the network or network-type name, from the build
parameters), a `timestamp`, and a `status` derived from the build result.

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

#### Scenario: Runs triggered outside the React UI are visible
- **WHEN** a lifecycle job is run directly in Jenkins rather than from the React UI
- **THEN** that run still appears in the derived lifecycle history

#### Scenario: History survives a database reset
- **WHEN** the application database is reset
- **THEN** previously executed lifecycle runs are still reported, because they are
  derived from Jenkins build records

### Requirement: Resolve Lifecycle Run Kind from Job and Operation
The run `kind` SHALL be resolved from the Jenkins job and the build's
`operation` parameter: `network_template_mgr` with `operation=create` is a
`network_create` run, `network_template_mgr` with `operation=delete` is a
`network_delete` run, and `network_type_validator` with `operation=add` is a
`network_type_load` run.

#### Scenario: Delete builds resolve to network_delete
- **WHEN** the `network_template_mgr` job has a build with `operation=delete`
- **THEN** that build is reported with `kind` `network_delete`

#### Scenario: Validator add builds resolve to network_type_load
- **WHEN** the `network_type_validator` job has a build with `operation=add`
- **THEN** that build is reported with `kind` `network_type_load`

### Requirement: List Lifecycle Job Runs
The system SHALL expose a read-only, authenticated endpoint
`GET /api/v1/lifecycle-runs/` listing lifecycle job runs derived from Jenkins,
newest-first. It SHALL support filtering by `kind`. Each item SHALL include the
run `id` (composite `"<job_name>#<build_no>"`), `kind`, `subject`, `job_name`,
`build_no`, `timestamp`, and `status`. When Jenkins is unreachable it SHALL
return an empty list rather than an error. Unauthenticated requests SHALL
receive a `403`.

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

#### Scenario: Kind filter serves the Networks and Network Types tables
- **WHEN** the Networks table requests runs filtered to `network_create` and
  `network_delete`, and the Network Types table requests runs filtered to
  `network_type_load`
- **THEN** each table receives only the runs of the requested kinds

### Requirement: View Historical Lifecycle Console Output
The system SHALL expose an authenticated endpoint
`GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>` returning
that build's historical Jenkins console output with ANSI escape codes stripped.
`job_name` SHALL be constrained to `[A-Za-z0-9_.\-]+` and `build_no` to
digits; an invalid value SHALL return `400`. When the output is not yet
available it SHALL return a placeholder message rather than an error.
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

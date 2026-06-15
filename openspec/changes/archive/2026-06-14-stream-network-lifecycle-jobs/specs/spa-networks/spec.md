## MODIFIED Requirements

### Requirement: User can add a new Network
The page SHALL provide an inline form (toggled by "Add Network" button) with fields for name, description, network type (dropdown), and a required Host File upload. The Host File field SHALL be a file input; on submit the file contents SHALL be read and sent as the `host_file` value. The submit SHALL POST to `POST /api/v1/networks/` with an initial `status` of `Initialized`, and refresh the list on success.

On a successful create, the page SHALL open the live console panel (the same panel used by the action trigger flow) using the streaming handle (`job_name`, `build_no`) returned by the create response, connecting to `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`, so the user can watch the create job run instead of waiting on a spinner.

#### Scenario: Successful network creation opens the console
- **WHEN** the user fills in the required fields, selects a host file, and submits the Add form
- **THEN** a POST is made to `/api/v1/networks/` with `host_file` set to the uploaded file's contents and `status` set to `Initialized`, the form closes, the new network appears in the list, and the live console panel opens streaming the create job

#### Scenario: Host File is required
- **WHEN** the user attempts to submit the Add form without selecting a host file
- **THEN** the form is not submitted (the file input is required)

#### Scenario: Network type dropdown populated
- **WHEN** the user opens the Add form
- **THEN** the Network Type dropdown is populated with types from `GET /api/v1/network-types/`

#### Scenario: Form submission error
- **WHEN** the POST request fails
- **THEN** an error message is displayed inside the form

### Requirement: User can delete a Network
The page SHALL allow deleting a network via `DELETE /api/v1/networks/{id}/` with inline confirmation. On a successful delete, the page SHALL open the live console panel using the streaming handle (`job_name`, `build_no`) returned by the delete response, connecting to `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`, so the user can watch the delete job run.

#### Scenario: Delete with confirmation opens the console
- **WHEN** the user clicks Delete on a row then confirms
- **THEN** `DELETE /api/v1/networks/{id}/` is called, the row is removed, and the live console panel opens streaming the delete job

## ADDED Requirements

### Requirement: Networks table lifecycle history view
The Networks page SHALL provide a History button on the top-level Networks table that opens a history view, similar to the per-network triggered actions history, listing the network create and delete lifecycle runs derived from Jenkins build history. The view SHALL fetch `GET /api/v1/lifecycle-runs/?kind=network_create` and `?kind=network_delete` (or the equivalent combined query) and display each run's subject (network name), kind, timestamp, and status. Each row SHALL provide a View action that opens a console viewer fetching `GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>` and displaying the returned historical console text. The console viewer SHALL show a loading indicator while fetching, an error message on failure, and a placeholder when output is empty, and SHALL be dismissable.

#### Scenario: Open the Networks lifecycle history
- **WHEN** the user clicks the History button on the Networks table
- **THEN** a history view opens listing network create and delete runs from `GET /api/v1/lifecycle-runs/`
- **AND** each run shows its subject network name, kind, timestamp, and status

#### Scenario: View historical console for a run
- **WHEN** the user clicks View on a lifecycle run row
- **THEN** `GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>` is requested
- **AND** the returned historical console text is displayed in the viewer

#### Scenario: Console fetch error
- **WHEN** the console fetch returns a non-2xx response
- **THEN** an error message is displayed in the viewer

## MODIFIED Requirements

### Requirement: User can upload a new Network Type
The page SHALL allow the user to select a zip file and upload it via `POST /api/v1/network-types/upload/`. The file SHALL be sent as multipart form data using the field name `app_zip_file` (the field name the backend expects). On success the list SHALL refresh.

On a successful upload, the page SHALL open the live console panel (the same panel used by the action trigger flow) using the streaming handle (`job_name`, `build_no`) returned by the upload response, connecting to `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`, so the user can watch the network-type load job run.

#### Scenario: Successful upload opens the console
- **WHEN** the user selects a zip file and confirms upload
- **THEN** the file is POSTed to the API as multipart form data with the field name `app_zip_file`, the network types list refreshes, and the live console panel opens streaming the load job

#### Scenario: Upload in progress
- **WHEN** a zip file upload is in progress
- **THEN** the upload button SHALL be disabled

#### Scenario: Upload error
- **WHEN** the upload request returns a non-2xx response
- **THEN** an error message SHALL be displayed

## ADDED Requirements

### Requirement: Network Types table lifecycle history view
The Network Types page SHALL provide a History button on the top-level Network Types table that opens a history view, similar to the per-network triggered actions history, listing the network-type load lifecycle runs derived from Jenkins build history. The view SHALL fetch `GET /api/v1/lifecycle-runs/?kind=network_type_load` and display each run's subject (network-type name), timestamp, and status. Each row SHALL provide a View action that opens a console viewer fetching `GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>` and displaying the returned historical console text. The console viewer SHALL show a loading indicator while fetching, an error message on failure, and a placeholder when output is empty, and SHALL be dismissable.

#### Scenario: Open the Network Types lifecycle history
- **WHEN** the user clicks the History button on the Network Types table
- **THEN** a history view opens listing network-type load runs from `GET /api/v1/lifecycle-runs/?kind=network_type_load`
- **AND** each run shows its subject network-type name, timestamp, and status

#### Scenario: View historical console for a load run
- **WHEN** the user clicks View on a lifecycle run row
- **THEN** `GET /api/v1/lifecycle-runs/console/?job_name=<job>&build_no=<n>` is requested
- **AND** the returned historical console text is displayed in the viewer

#### Scenario: Console fetch error
- **WHEN** the console fetch returns a non-2xx response
- **THEN** an error message is displayed in the viewer

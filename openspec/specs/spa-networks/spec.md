# SPA Networks Page Specification

## Purpose
The React SPA `/networks` page lists networks and lets the user add, modify,
delete, and review the lifecycle history of networks.
## Requirements
### Requirement: Networks page lists all networks
The `/networks` page SHALL fetch and display all networks from `GET /api/v1/networks/` in a table with columns: Name, Network Type, Description, Status, and Actions (Modify + Delete).

#### Scenario: Page loads with data
- **WHEN** the user navigates to `/networks`
- **THEN** a table is displayed with one row per network showing name, network type name, description, and status

#### Scenario: Modify link navigates to detail
- **WHEN** the user clicks "Modify" on a network row
- **THEN** the browser navigates to `/app/networks/:id`

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

### Requirement: Network detail stub route exists
A stub `NetworkDetailPage` SHALL exist at `/networks/:id` showing the network name and a back link, as a placeholder for the next change.

#### Scenario: Detail page renders without error
- **WHEN** the user navigates to `/app/networks/1`
- **THEN** the page renders inside `AppLayout` without a 404 or blank screen

### Requirement: Action history console viewer
The network detail page SHALL allow the user to view the Jenkins console output for any action-history entry. Each action-history row SHALL provide a View button that opens a modal streaming the Jenkins console output live via Server-Sent Events from `GET /api/v1/action-history/{id}/stream/`. Because the stream replays the full console of a finished build and then terminates, the same live console serves both in-progress and completed runs.

The History tab SHALL re-fetch the action-history list (via `GET /api/v1/action-history/?campus_network_id={id}`) each time the tab is opened, so the displayed runs and statuses are current. Already-displayed rows SHALL remain visible while refreshing; the loading indicator SHALL appear only on the first load when no data is present yet.

The modal SHALL indicate the streaming state while output is arriving, display an error message if the stream fails or times out, and show a placeholder when a finished stream produced no output. The modal SHALL be dismissable (close button or backdrop click), and dismissing it SHALL close the underlying stream.

#### Scenario: Re-opening the History tab refreshes the list
- **WHEN** the user switches away from the History tab and back to it
- **THEN** a fresh `GET /api/v1/action-history/?campus_network_id={id}` is issued and the rows are updated

#### Scenario: Open the live console viewer for a history entry
- **WHEN** the user clicks the View button on an action-history row
- **THEN** a modal opens and an SSE connection to `GET /api/v1/action-history/{id}/stream/` is established
- **AND** console output is rendered as it streams, with a streaming indicator while output is arriving

#### Scenario: Console stream error
- **WHEN** the stream emits an error or the connection fails before completion
- **THEN** the modal displays an error message

#### Scenario: Empty console output
- **WHEN** the stream finishes without emitting any console lines
- **THEN** the modal displays a "No console output available." placeholder

#### Scenario: Dismiss the modal closes the stream
- **WHEN** the user clicks Close or the modal backdrop
- **THEN** the modal closes and the underlying SSE connection is closed

### Requirement: Networks table lifecycle history view
The Networks page SHALL provide a History button on the top-level Networks table that opens a history view, similar to the per-network triggered actions history, listing the network create and delete lifecycle runs derived from Jenkins build history. The view SHALL fetch `GET /api/v1/lifecycle-runs/?kind=network_create` and `?kind=network_delete` (or the equivalent combined query) and display each run's subject (network name), kind, timestamp, and status. Each row SHALL provide a View action that opens a console viewer streaming the Jenkins console output live via Server-Sent Events from `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`. The console viewer SHALL indicate the streaming state while output is arriving, display an error message on stream failure or timeout, show a placeholder when a finished stream produced no output, and be dismissable; dismissing it SHALL close the underlying stream.

#### Scenario: Open the Networks lifecycle history
- **WHEN** the user clicks the History button on the Networks table
- **THEN** a history view opens listing network create and delete runs from `GET /api/v1/lifecycle-runs/`
- **AND** each run shows its subject network name, kind, timestamp, and status

#### Scenario: View live console for a run
- **WHEN** the user clicks View on a lifecycle run row
- **THEN** an SSE connection to `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/` is established
- **AND** console output is rendered as it streams, replaying a finished build's full log and then reaching a finished state

#### Scenario: Console stream error
- **WHEN** the stream emits an error or the connection fails before completion
- **THEN** an error message is displayed in the viewer

### Requirement: Action Jenkins job link
The network detail Actions tab SHALL display, for each action, a link that opens the action's Jenkins job page in a new browser tab. The link target SHALL be the reverse-proxied Jenkins job path `/jenkins/job/{jenkins_url}-{network_name}/`, where `jenkins_url` is the action's job-name prefix and `network_name` is the current network's name. The link SHALL open in a new tab with `rel="noopener"` and SHALL not interfere with the existing Run action.

#### Scenario: Action row shows a Jenkins link
- **WHEN** the user opens the Actions tab for a network
- **THEN** each action row shows a Jenkins link alongside its Run button
- **AND** the link points to `/jenkins/job/{jenkins_url}-{network_name}/` and opens in a new tab

#### Scenario: Jenkins link is routed by the proxy
- **WHEN** the user activates an action's Jenkins link
- **THEN** the request to `/jenkins/` is routed by the reverse proxy to the Jenkins service (not the SPA)

### Requirement: Action-history exposes the Jenkins job name
The action-history API (`GET /api/v1/action-history/`) SHALL include a read-only `jenkins_job_name` field for each entry equal to `{action.jenkins_url}-{network_name}`, so consumers can construct the Jenkins job/build URL without additional lookups.

#### Scenario: History entry includes the Jenkins job name
- **WHEN** a client fetches `GET /api/v1/action-history/`
- **THEN** each entry includes `jenkins_job_name` equal to the action's `jenkins_url` joined to the network name with a hyphen

### Requirement: Action-history Jenkins build link
Each row of the network detail History tab SHALL show a link that opens the run's Jenkins build result in a new browser tab, targeting `/jenkins/job/{jenkins_job_name}/{jenkins_job_build_no}/`. When a row has no build number, the link SHALL target the job page `/jenkins/job/{jenkins_job_name}/`. The link SHALL open with `rel="noopener"` and SHALL not interfere with the existing View (console) action.

#### Scenario: History row shows a Jenkins build link
- **WHEN** the user opens the History tab for a network with at least one run
- **THEN** each run row shows a Jenkins link alongside its View button
- **AND** the link points to `/jenkins/job/{jenkins_job_name}/{jenkins_job_build_no}/` and opens in a new tab

#### Scenario: Link is routed by the proxy to Jenkins
- **WHEN** the user activates a history row's Jenkins link
- **THEN** the request to `/jenkins/` is routed by the reverse proxy to the Jenkins service (not the SPA)

### Requirement: Action-history Robot Framework summary endpoint
The system SHALL expose `GET /api/v1/action-history/{id}/robot-summary/`, an authenticated endpoint that returns the Robot Framework result totals for the run's Jenkins build. The response SHALL include `available` (boolean) and, when available, `total`, `passed`, `failed`, `skipped`, and `pass_percentage`. The totals SHALL be sourced from the Jenkins Robot Framework plugin's per-build summary (`overallTotal`/`overallPassed`/`overallFailed`/`overallSkipped`/`passPercentage`). When the build has no Robot results or Jenkins is unreachable, the endpoint SHALL return `{ "available": false }`.

#### Scenario: Summary available for a TEST build
- **WHEN** an authenticated client requests `GET /api/v1/action-history/{id}/robot-summary/` for a run whose Jenkins build has Robot results
- **THEN** the response is `{ available: true, total, passed, failed, skipped, pass_percentage }` reflecting the build's Robot totals

#### Scenario: Summary unavailable
- **WHEN** the run's build has no Robot results or Jenkins is unreachable
- **THEN** the response is `{ available: false }`

### Requirement: History tab shows inline TEST result summary
For each History tab row in the **TEST** category, the network detail page SHALL fetch the run's Robot summary and, when available, display it inline as `Total N · Passed P · Failed F · Skipped S · Pass X%`. Rows in other categories SHALL NOT show a Robot summary.

#### Scenario: TEST row shows the inline summary
- **WHEN** the user opens the History tab and a TEST-category run has Robot results
- **THEN** that row shows an inline `Total / Passed / Failed / Skipped / Pass %` summary

#### Scenario: Non-TEST rows have no summary
- **WHEN** a history row is not in the TEST category
- **THEN** no Robot summary is shown for that row

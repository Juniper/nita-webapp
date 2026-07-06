## MODIFIED Requirements

### Requirement: Action history console viewer
The network detail page SHALL allow the user to view the Jenkins console output for any action-history entry. Each action-history row SHALL provide a View button that opens a modal streaming the Jenkins console output live via Server-Sent Events from `GET /api/v1/action-history/{id}/stream/`. Because the stream replays the full console of a finished build and then terminates, the same live console serves both in-progress and completed runs.

The modal SHALL indicate the streaming state while output is arriving, display an error message if the stream fails or times out, and show a placeholder when a finished stream produced no output. The modal SHALL be dismissable (close button or backdrop click), and dismissing it SHALL close the underlying stream.

#### Scenario: Open the live console viewer for a history entry
- **WHEN** the user clicks the View button on an action-history row
- **THEN** a modal opens and an SSE connection to `GET /api/v1/action-history/{id}/stream/` is established
- **AND** console output is rendered as it streams, with a streaming indicator while output is arriving

#### Scenario: Finished build replays then stops
- **WHEN** the viewed run has already completed
- **THEN** the stream replays the full console output and then reaches a finished (non-streaming) state

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

## MODIFIED Requirements

### Requirement: Network Types table lifecycle history view
The Network Types page SHALL provide a History button on the top-level Network Types table that opens a history view, similar to the per-network triggered actions history, listing the network-type load lifecycle runs derived from Jenkins build history. The view SHALL fetch `GET /api/v1/lifecycle-runs/?kind=network_type_load` and display each run's subject (network-type name), timestamp, and status. Each row SHALL provide a View action that opens a console viewer streaming the Jenkins console output live via Server-Sent Events from `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`. The console viewer SHALL indicate the streaming state while output is arriving, display an error message on stream failure or timeout, show a placeholder when a finished stream produced no output, and be dismissable; dismissing it SHALL close the underlying stream.

#### Scenario: Open the Network Types lifecycle history
- **WHEN** the user clicks the History button on the Network Types table
- **THEN** a history view opens listing network-type load runs from `GET /api/v1/lifecycle-runs/?kind=network_type_load`
- **AND** each run shows its subject network-type name, timestamp, and status

#### Scenario: View live console for a load run
- **WHEN** the user clicks View on a lifecycle run row
- **THEN** an SSE connection to `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/` is established
- **AND** console output is rendered as it streams, replaying a finished build's full log and then reaching a finished state

#### Scenario: Console stream error
- **WHEN** the stream emits an error or the connection fails before completion
- **THEN** an error message is displayed in the viewer

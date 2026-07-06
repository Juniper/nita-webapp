## MODIFIED Requirements

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

#### Scenario: Dismiss the modal closes the stream
- **WHEN** the user clicks Close or the modal backdrop
- **THEN** the modal closes and the underlying SSE connection is closed

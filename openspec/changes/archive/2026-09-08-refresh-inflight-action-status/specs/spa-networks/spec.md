## MODIFIED Requirements

### Requirement: Action history console viewer
The network detail page SHALL allow the user to view the Jenkins console output for any action-history entry. Each action-history row SHALL provide a View button that opens a modal streaming the Jenkins console output live via Server-Sent Events from `GET /api/v1/action-history/{id}/stream/`. Because the stream replays the full console of a finished build and then terminates, the same live console serves both in-progress and completed runs.

The History tab SHALL re-fetch the action-history list (via `GET /api/v1/action-history/?campus_network_id={id}`) each time the tab is opened, so the displayed runs and statuses are current. Already-displayed rows SHALL remain visible while refreshing; the loading indicator SHALL appear only on the first load when no data is present yet.

While the History tab is open and at least one displayed entry has
`status = "Running"`, the tab SHALL additionally re-fetch the action-history list
every 15 seconds, so that a run reaching its terminal state becomes visible
without user interaction. These refreshes SHALL follow the same rules as a tab
re-entry refresh: rows stay visible and no loading indicator is shown. When no
displayed entry is `Running`, no interval refresh SHALL be issued. The interval
SHALL stop when the last in-progress entry reaches a terminal status, when the
user leaves the History tab, and when the page unmounts.

The modal SHALL indicate the streaming state while output is arriving, display an error message if the stream fails or times out, and show a placeholder when a finished stream produced no output. The modal SHALL be dismissable (close button or backdrop click), and dismissing it SHALL close the underlying stream.

#### Scenario: Re-opening the History tab refreshes the list
- **WHEN** the user switches away from the History tab and back to it
- **THEN** a fresh `GET /api/v1/action-history/?campus_network_id={id}` is issued and the rows are updated

#### Scenario: In-progress run is refreshed automatically
- **GIVEN** the History tab is open and shows an entry with `status = "Running"`
- **WHEN** 15 seconds elapse without user interaction
- **THEN** a fresh `GET /api/v1/action-history/?campus_network_id={id}` is issued
- **AND** the displayed status reflects the latest server value

#### Scenario: Completed run reaches its terminal status without interaction
- **GIVEN** the History tab is open and shows an entry with `status = "Running"`
- **WHEN** the backend records a terminal status for that run
- **THEN** the row displays the terminal status without the user refreshing the
  page or switching tabs

#### Scenario: No polling when nothing is in progress
- **GIVEN** the History tab is open and no displayed entry has `status = "Running"`
- **WHEN** time elapses without user interaction
- **THEN** no further action-history requests are issued

#### Scenario: Polling stops when the last run finishes
- **GIVEN** the History tab is polling because one entry is `Running`
- **WHEN** that entry reaches a terminal status
- **THEN** no further interval refreshes are issued

#### Scenario: Polling stops when the tab is left
- **GIVEN** the History tab is polling because one entry is `Running`
- **WHEN** the user switches to another tab or navigates away from the page
- **THEN** the interval is cleared and no further requests are issued

#### Scenario: Interval refresh does not flash the table
- **GIVEN** the History tab is displaying rows and an interval refresh occurs
- **WHEN** the refresh is in flight
- **THEN** the existing rows remain visible and no loading indicator is shown

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

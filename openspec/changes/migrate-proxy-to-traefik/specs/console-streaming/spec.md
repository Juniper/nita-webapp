## RENAMED Requirements

- FROM: ### Requirement: Nginx Proxy Must Not Buffer SSE Stream
- TO: ### Requirement: Proxy Must Not Buffer SSE Stream

## MODIFIED Requirements

### Requirement: Proxy Must Not Buffer SSE Stream
The Traefik proxy SHALL deliver action-history SSE events without response
buffering or caching and SHALL allow at least 1850 seconds of idle stream time.

#### Scenario: SSE events reach browser in real time
- **GIVEN** a running Jenkins build producing console output
- **WHEN** the browser opens the SSE stream endpoint
- **THEN** console lines appear within 2 seconds under normal test conditions
  without waiting for the stream to finish

#### Scenario: Proxy does not close long-running stream prematurely
- **GIVEN** a Jenkins build that runs for more than 5 minutes
- **WHEN** the browser is connected to the SSE stream
- **THEN** the proxy does not close the connection before the build completes
- **AND** the browser receives the `event: done` signal

#### Scenario: Proxy does not close an idle stream prematurely
- **WHEN** a healthy stream is idle for 1850 seconds and then emits an event
- **THEN** the connection remains open and the browser receives the event

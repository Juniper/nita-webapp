## RENAMED Requirements

- FROM: ### Requirement: Nginx Must Not Buffer the Generic Lifecycle Stream
- TO: ### Requirement: Proxy Must Not Buffer the Generic Lifecycle Stream

## MODIFIED Requirements

### Requirement: Proxy Must Not Buffer the Generic Lifecycle Stream
The Traefik proxy SHALL deliver the generic Jenkins lifecycle SSE stream without
response buffering or caching and SHALL allow at least 1850 seconds of idle
stream time.

#### Scenario: Lifecycle SSE events reach the browser in real time
- **WHEN** a browser opens the generic lifecycle stream for a running build
- **THEN** console lines appear within 2 seconds under normal test conditions
  without waiting for the stream to finish

#### Scenario: Proxy does not close an idle lifecycle stream prematurely
- **WHEN** a healthy lifecycle stream is idle for 1850 seconds and then emits an event
- **THEN** the connection remains open and the browser receives the event

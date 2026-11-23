## Purpose

Define console streaming behavior for action-history entries and their proxy.

## Requirements

### Requirement: Nginx Proxy Must Not Buffer SSE Stream
The nginx location matching `/api/v1/action-history/` stream paths SHALL set
`proxy_buffering off`, `proxy_cache off`, and `proxy_read_timeout` to at least
1850 seconds so SSE events are delivered immediately and 30-minute streams
are not closed prematurely.

#### Scenario: SSE events reach browser in real time
- GIVEN a running Jenkins build producing console output
- WHEN the browser opens the SSE stream endpoint
- THEN console lines appear in the browser within 2 seconds of Jenkins producing
  them
- AND no buffering delay causes the console panel to remain blank while the
  build runs

#### Scenario: Proxy does not close long-running stream prematurely
- GIVEN a Jenkins build that runs for more than 5 minutes
- WHEN the browser is connected to the SSE stream
- THEN the nginx proxy does not close the connection before the build completes
- AND the `event: done` signal is received by the browser when the build
  finishes

### Requirement: Stream console output via SSE
The system SHALL expose `GET /api/v1/action-history/{id}/stream/` as a
`text/event-stream` endpoint that incrementally emits console output as
`data: <text>` events. Once the build log is complete, it SHALL emit
`event: done\ndata: \n\n` and close.

#### Scenario: Live output streams while build runs
- GIVEN a running Jenkins build for the given action history entry
- WHEN GET /api/v1/action-history/{id}/stream/ is called with a valid session
- THEN the response has Content-Type text/event-stream
- AND `data:` events are emitted containing console output lines as they are
  produced
- AND an `event: done` event is emitted when the build finishes

#### Scenario: Completed build streams full log then closes
- GIVEN a Jenkins build that has already completed
- WHEN GET /api/v1/action-history/{id}/stream/ is called
- THEN the full console log is emitted as `data:` events
- AND an `event: done` event is emitted and the connection closes

### Requirement: Stream errors and timeout
The endpoint SHALL emit `event: error\ndata: <message>\n\n` and close when
Jenkins is unreachable or an internal error occurs. After 30 minutes of
continuous streaming (1800 one-second poll attempts), it SHALL emit
`event: timeout\ndata: \n\n` and close.

#### Scenario: Jenkins unreachable emits error event
- GIVEN the Jenkins server is unreachable during streaming
- WHEN GET /api/v1/action-history/{id}/stream/ is called
- THEN an `event: error` SSE event is emitted with an explanatory message
- AND the connection closes cleanly

#### Scenario: Long-running stream times out
- GIVEN a build that has been streaming for 30 minutes without completing
- WHEN the 1800th poll attempt is reached
- THEN an `event: timeout` SSE event is emitted and the connection closes

### Requirement: Stream access and output handling
The endpoint SHALL require a session cookie and reject unauthenticated requests
with 403 before streaming. It SHALL strip ANSI escape codes from emitted output
and set `X-Accel-Buffering: no` on every streaming response.

#### Scenario: ANSI escape codes are stripped
- GIVEN a Jenkins build whose console output contains ANSI colour escape codes
- WHEN the stream endpoint is called
- THEN the emitted `data:` events contain no ANSI escape sequences

#### Scenario: Unauthenticated request rejected
- GIVEN no valid session cookie is present
- WHEN GET /api/v1/action-history/{id}/stream/ is called
- THEN a 403 response is returned before any streaming begins

### Requirement: Console stream client event handling
The SPA SHALL use named listeners for `done`, `error` and `timeout` events.
Its named `error` listener SHALL process only server-sent events with a `data`
payload; network-level EventSource errors without `data` SHALL be handled by
`es.onerror` instead.

#### Scenario: Browser receives done event before closing EventSource
- GIVEN a Jenkins build that completes normally
- WHEN the SPA receives the `event: done` SSE event
- THEN the SPA closes the EventSource connection
- AND the console panel is marked as complete (no longer showing a spinner)
- AND no further polling or reconnection is attempted

#### Scenario: Network-level EventSource error does not log spurious message
- GIVEN the SPA opens an EventSource connection
- AND the server returns a non-2xx response (e.g. 404)
- WHEN EventSource dispatches a network-level error event (no `data` property)
- THEN the named `'error'` event listener returns early without appending a
  console line
- AND `es.onerror` sets the console panel state to `error`

#### Scenario: Server-sent error event logs the server message
- GIVEN the Django stream endpoint emits `event: error\ndata: Build failed\n\n`
- WHEN the SPA receives this SSE named event
- THEN the named `'error'` listener appends `[error] Build failed` to the
  console panel
- AND the EventSource is closed

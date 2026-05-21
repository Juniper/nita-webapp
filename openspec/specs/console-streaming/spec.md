### Requirement: Stream Console Log via SSE
The system SHALL expose a Server-Sent Events endpoint at
`GET /api/v1/action-history/{id}/stream/` that streams the Jenkins build console
output incrementally for the given action history entry.

The endpoint SHALL:
- Respond with `Content-Type: text/event-stream`.
- Emit one or more `data: <text>` SSE events containing console output as the build runs.
- Emit `event: done\ndata: \n\n` when the build log is complete, then close the connection.
- Emit `event: error\ndata: <message>\n\n` and close if Jenkins is unreachable or an internal error occurs.
- Emit `event: timeout\ndata: \n\n` and close after 30 minutes of continuous streaming (1800 poll attempts at 1-second intervals) to prevent zombie connections.
- Strip ANSI escape codes from all emitted output.
- Require the request to be authenticated (session cookie). Unauthenticated requests SHALL receive a 403 response before any streaming begins.

#### Scenario: Live output streams while build runs
- GIVEN a running Jenkins build for the given action history entry
- WHEN GET /api/v1/action-history/{id}/stream/ is called with a valid session
- THEN the response has Content-Type text/event-stream
- AND `data:` events are emitted containing console output lines as they are produced
- AND an `event: done` event is emitted when the build finishes

#### Scenario: Completed build streams full log then closes
- GIVEN a Jenkins build that has already completed
- WHEN GET /api/v1/action-history/{id}/stream/ is called
- THEN the full console log is emitted as `data:` events
- AND an `event: done` event is emitted and the connection closes

#### Scenario: ANSI escape codes are stripped
- GIVEN a Jenkins build whose console output contains ANSI colour escape codes
- WHEN the stream endpoint is called
- THEN the emitted `data:` events contain no ANSI escape sequences

#### Scenario: Unauthenticated request rejected
- GIVEN no valid session cookie is present
- WHEN GET /api/v1/action-history/{id}/stream/ is called
- THEN a 403 response is returned before any streaming begins

#### Scenario: Jenkins unreachable emits error event
- GIVEN the Jenkins server is unreachable during streaming
- WHEN GET /api/v1/action-history/{id}/stream/ is called
- THEN an `event: error` SSE event is emitted with an explanatory message
- AND the connection closes cleanly

#### Scenario: Long-running stream times out
- GIVEN a build that has been streaming for 30 minutes without completing
- WHEN the 1800th poll attempt is reached
- THEN an `event: timeout` SSE event is emitted and the connection closes

## MODIFIED Requirements

### Requirement: Stream access and output handling
The endpoint SHALL require a session cookie and reject unauthenticated requests
with 403 before streaming. It SHALL strip ANSI escape codes and serialized
Jenkins ConsoleNote markers from emitted output and set
`X-Accel-Buffering: no` on every streaming response.

#### Scenario: ANSI escape codes are stripped
- GIVEN a Jenkins build whose console output contains ANSI colour escape codes
- WHEN the stream endpoint is called
- THEN the emitted `data:` events contain no ANSI escape sequences

#### Scenario: Serialized Jenkins ConsoleNotes are stripped
- GIVEN a Jenkins build whose progressive text contains `ESC[8mha:…ESC[0m`
  ConsoleNote markers
- WHEN the stream endpoint is called
- THEN the emitted `data:` events contain no ConsoleNote markers and preserve
  the surrounding console text

#### Scenario: Unauthenticated request rejected
- GIVEN no valid session cookie is present
- WHEN GET /api/v1/action-history/{id}/stream/ is called
- THEN a 403 response is returned before any streaming begins

## ADDED Requirements

### Requirement: SSE Generator Tolerates Transient 404 From Jenkins
The SSE generator for `GET /api/v1/action-history/{id}/stream/` SHALL retry
when Jenkins returns HTTP 404, for up to 60 seconds (one retry per second),
before treating the 404 as a permanent failure.

A 404 is expected when a build has just been triggered but Jenkins has not yet
moved it from the queue to an executor — the build URL and its progressive-text
endpoint do not exist until the executor picks up the job.

After 60 consecutive 404 responses the generator SHALL emit
`event: error\ndata: <message>\n\n` and close the stream.

Any non-404 HTTP error SHALL still cause an immediate `event: error` and stream
closure (no retry).

#### Scenario: Build queued — stream waits then starts
- **WHEN** `GET /api/v1/action-history/{id}/stream/` is called immediately
  after a trigger and Jenkins returns 404 for the progressive-text URL
- **THEN** the generator retries once per second for up to 60 seconds
- **AND** when Jenkins starts the build and the URL becomes available, the
  stream begins emitting console output normally
- **AND** no `event: error` is emitted during the retry window

#### Scenario: Build never starts — stream times out and errors
- **WHEN** Jenkins returns 404 for 60 consecutive polls
- **THEN** an `event: error` SSE event is emitted with a descriptive message
- **AND** the stream connection closes

#### Scenario: Non-404 Jenkins error is not retried
- **WHEN** Jenkins returns any HTTP error other than 404 (e.g. 500)
- **THEN** an `event: error` SSE event is emitted immediately
- **AND** the stream connection closes without waiting

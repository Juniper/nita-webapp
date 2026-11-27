## Why

Jenkins progressive console output can contain serialized `ConsoleNote` control
sequences. They are not human-readable log text and can obscure build
attribution and console output in the webapp.

## What Changes

- Strip serialized Jenkins `ConsoleNote` markers from streamed console chunks,
  alongside the existing ANSI escape filtering.
- Add a regression test that verifies readable text is preserved.

## Capabilities

### Modified Capabilities

- `console-streaming`: define sanitized output for the authenticated Jenkins
  console relay.

## Impact

The webapp's Jenkins console-stream parser and its streaming tests change. No
API response shape or dependency changes.

## Why

The console-streaming spec combines several behaviors in long requirement
descriptions, causing strict validation warnings.

## What Changes

- Split the streaming endpoint and client behavior into focused requirements.
- Shorten the existing Nginx requirement without changing its behavior.
- Preserve all existing scenarios.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `console-streaming`: Clarify existing requirements without changing behavior.

## Impact

Only the existing console-streaming specification changes. This cleanup
precedes the Traefik migration and does not change application behavior.

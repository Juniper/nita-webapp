## Why

Action history entries are persisted as `Running` when an action is triggered, but they are not reliably updated to terminal states (`Success`/`Failed`) after Jenkins finishes. In production, the UI and API both continue to show stale `Running` values even when Jenkins reports completed builds.

Investigation confirmed the primary cause is inconsistent internal Jenkins base URL construction: the status updater polls `http://jenkins:8080` while the deployed Jenkins instance is served under `http://jenkins:8080/jenkins`.

## What Changes

### Immediate Fix Scope

- Align the ActionHistory status updater Jenkins base URL with the canonical prefixed internal URL (`.../jenkins`).
- Keep existing polling behavior, threading model, and status mapping intact.
- Verify that existing stale `Running` rows transition on the next updater cycle once lookups succeed.

### Consistency Cleanup Scope

- Remove duplicate ad-hoc Jenkins URL construction in legacy helper modules and reuse a single canonical source.
- Ensure all backend Jenkins callers use the same base URL convention to prevent future drift.
- Add focused regression tests for prefixed Jenkins URL behavior in ActionHistory synchronization paths.

## Capabilities

### Modified Capabilities

- `actions`: Action history status synchronization SHALL resolve completed Jenkins builds and persist terminal status values.
- `jenkins-trigger-security`: Internal Jenkins callers SHALL use one canonical prefixed base URL.

## Impact

- Backend changes in status synchronization paths (`statusupdater` and shared Jenkins URL configuration usage).
- No API contract change for `/api/v1/action-history/`.
- No frontend contract change; UI correctness improves automatically once backend status data is updated.

## Why

The network detail History tab loads its data once and caches it (guarded by a
`loaded.history` flag). After running an action or navigating away and back, the
user re-opens the History tab but sees the **stale** list — new runs and updated
statuses do not appear until a full page reload. The tab should reflect the
latest run history each time it is opened.

## What Changes

- Switching to the History tab SHALL re-fetch the action-history list (and the
  TEST-category Robot summaries) so the contents are up to date on every visit.
- The refresh SHALL keep the currently displayed rows visible while reloading
  (the loading indicator is shown only on the first load when there is no data
  yet), avoiding a flicker on subsequent visits.

## Capabilities

### Modified Capabilities
- `spa-networks`: The action-history viewer refreshes its contents each time the
  History tab is opened instead of loading once and caching.

## Impact

- **Frontend only**: `frontend/src/pages/NetworkDetailPage.tsx` (history fetch is
  re-run on each switch to the History tab).
- **No backend / API / DB changes.**

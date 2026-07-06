## 1. Refresh history on tab switch

- [x] 1.1 Extract the history fetch (list + TEST Robot summaries) into a stable
  `fetchHistory` callback in `frontend/src/pages/NetworkDetailPage.tsx`.
- [x] 1.2 Run `fetchHistory` whenever the active tab becomes `history` (drop the
  one-shot `loaded.history` gate for history).
- [x] 1.3 Show the "Loading history…" indicator only when there is no data yet,
  so re-opening the tab refreshes in place without flicker.

## 2. Verify

- [x] 2.1 Build and deploy.
- [x] 2.2 Confirm switching away from and back to the History tab issues a fresh
  `GET /api/v1/action-history/?campus_network_id=<id>` and updates the rows.

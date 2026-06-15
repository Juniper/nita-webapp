## Why

The SPA has a layout shell and routing, but no feature pages yet. Network Types is the first domain concept in NITA — every Network depends on a Network Type. Replacing the Django `campustype/` views with a React page is the natural first feature page: the API is complete (`GET /api/v1/network-types/`, `POST /upload/`, `DELETE /{id}/`), the data shape is simple, and it unblocks the Networks page which comes next.

## What Changes

- New page `NetworkTypesPage` at route `/network-types` inside `AppLayout`
- Table listing all network types: name, description, zip filename, role count, resource count
- Upload button: opens a file picker → POSTs the selected zip to `POST /api/v1/network-types/upload/` → refreshes the list on success
- Delete button per row: inline confirmation → `DELETE /api/v1/network-types/{id}/` → removes the row on success
- Loading and error states for both list fetch and mutations
- Route `/network-types` added to `App.tsx`

## Capabilities

### New Capabilities
- `spa-network-types`: React page for listing, uploading, and deleting Network Types, backed by the existing REST API

### Modified Capabilities

## Impact

- New file: `frontend/src/pages/NetworkTypesPage.tsx`
- Modified: `frontend/src/App.tsx` — adds `/network-types` route
- No backend changes

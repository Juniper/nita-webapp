## Why

Network Types are now manageable via the SPA. Networks (campus networks) are the central working object in NITA — every workbook upload, configuration view, and action trigger is scoped to a Network. Before those deep-dive pages can be built, users need a way to list, create, and delete Networks in the SPA. This change builds the Networks list page at `/networks`, including an inline "Add Network" form.

## What Changes

- New page `NetworksPage` at route `/networks` inside `AppLayout`
- Table listing all networks: name, network type, description, status, with a "View" link to `/networks/:id` (placeholder for the future detail page)
- Inline "Add Network" form (toggled by a button): fields for name, description, network type (dropdown populated from API), host_file, dynamic_ansible_workspace checkbox — POSTs to `POST /api/v1/networks/`
- Per-row delete with inline confirmation → `DELETE /api/v1/networks/{id}/`
- Route `/networks` and `/networks/:id` (stub page) added to `App.tsx`

## Capabilities

### New Capabilities
- `spa-networks`: React page for listing, creating, and deleting Networks, with a stub detail route, backed by the existing REST API

### Modified Capabilities

## Impact

- New files: `frontend/src/pages/NetworksPage.tsx`, `frontend/src/pages/NetworkDetailPage.tsx` (stub)
- Modified: `frontend/src/App.tsx` — adds `/networks` and `/networks/:id` routes
- No backend changes

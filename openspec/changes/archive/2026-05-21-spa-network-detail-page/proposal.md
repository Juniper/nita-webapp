## Why

The Networks page links to `/networks/:id` which currently shows a stub. The Network Detail page is the core working surface of NITA: it's where operators upload workbooks, trigger network actions (build/test/deploy), and review execution history. The API for all of this is already complete (workbook CRUD, trigger, SSE stream, action history). This change replaces the stub with a functional three-tab detail page.

## What Changes

- Replace `NetworkDetailPage.tsx` stub with a full three-tab page: **Workbook** | **Actions** | **History**
- **Workbook tab**: upload Excel file → show sheet names from workbook data → download as xlsx → clear with confirmation
- **Actions tab**: list actions grouped by category (fetched by `campus_type_id`) → trigger → live SSE console panel showing streaming output
- **History tab**: table of past action history runs for this network (action name, category, timestamp, status)
- Network name/type/status shown in a header above the tabs

## Capabilities

### New Capabilities
- `spa-network-detail`: Full network detail page with workbook management, action triggering with live console streaming, and action history

### Modified Capabilities

## Impact

- Modified: `frontend/src/pages/NetworkDetailPage.tsx` (rewritten from stub)
- No new files, no backend changes
- No routing changes (`/networks/:id` already registered in `App.tsx`)

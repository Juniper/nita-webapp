## Why

The SPA currently has a `DashboardPage` with an inline header and placeholder content. Every future feature page (Network Types, Networks, Workbook, Action History) will need the same chrome: a persistent top header showing the current user, and a left sidebar with navigation links to each section. Without a shared layout shell, each page would duplicate this structure.

## What Changes

- New `AppLayout` component: top header (brand, user display, logout) + collapsible left sidebar navigation (Dashboard, Network Types, Networks)
- New sidebar link components that highlight the active route
- `DashboardPage` refactored to use `AppLayout` with a summary/welcome panel instead of inline header
- `LoginPage` is unaffected — it uses a standalone full-screen layout
- `ProtectedRoute` remains unchanged

## Capabilities

### New Capabilities
- `spa-layout`: Shared `AppLayout` component providing the application chrome (header + sidebar) used by all authenticated pages

### Modified Capabilities

## Impact

- New files: `frontend/src/components/AppLayout.tsx`, `frontend/src/components/Sidebar.tsx`
- Modified: `frontend/src/pages/DashboardPage.tsx` (uses `AppLayout`)
- No changes to routing, auth, API client, or backend

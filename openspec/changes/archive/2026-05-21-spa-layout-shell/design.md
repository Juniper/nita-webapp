## Context

The SPA is served at `/app/` with React Router `basename="/app"`. The existing `DashboardPage` has an inline header with logout. Future pages (Network Types, Networks, etc.) all need identical chrome. Tailwind v4 with dark mode (`@custom-variant dark`) is already configured; the app renders in dark mode by default (`document.documentElement.classList.add('dark')`).

## Goals / Non-Goals

**Goals:**
- `AppLayout` wraps all authenticated pages — renders header + sidebar + `{children}` main content
- Header: brand name left, user info + logout button right
- Sidebar: nav links for Dashboard, Network Types, Networks — active link highlighted
- `DashboardPage` uses `AppLayout`, shows a welcome panel
- No layout chrome on `LoginPage`

**Non-Goals:**
- Collapsible/mobile-responsive sidebar (can be added later)
- Breadcrumbs or sub-navigation
- Any data fetching in layout components

## Decisions

### `AppLayout` as a wrapper component
**Decision**: `AppLayout` accepts `children: ReactNode` and renders the full-page shell.  
**Rationale**: Simple composition pattern — each page just wraps its content in `<AppLayout>`. No React context or portal needed.

### `NavLink` from react-router-dom for sidebar items
**Decision**: Use `react-router-dom`'s `NavLink` with its `isActive` callback.  
**Rationale**: `NavLink` automatically provides `isActive` state for styling the active link without manual route comparison. Already a dependency.

### Sidebar + header in one `AppLayout` file
**Decision**: Co-locate `Sidebar` as a non-exported inner component inside `AppLayout.tsx`.  
**Rationale**: The sidebar has no standalone use; keeping it co-located reduces file count. Only `AppLayout` is exported.

## Risks / Trade-offs

- [Risk] `DashboardPage` currently owns logout logic — this moves to the header in `AppLayout`. `DashboardPage` becomes a pure content component → Mitigation: pass `useNavigate` + `useAuth` hooks into `AppLayout` directly; `DashboardPage` calls `AppLayout` with no special props.

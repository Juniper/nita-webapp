## Why

The `user-management` change deliberately kept all user/team administration out of
the React SPA, deferring day-one management to the Django Admin (`/admin/`). In
practice, dropping an admin from the dark-themed NITA SPA into the light,
visually-unrelated Django Admin is jarring and hard to discover. A first-cut
in-SPA `Users` page was since added, but it is intentionally minimal (a list with
inline role/active/delete controls) and does not cover team management or the
ownership-transfer flow that protected deletion requires.

This change formalises and completes a native, SPA-integrated user & team
management experience so administrators (and power users, for teams) can do their
day-to-day work without leaving the app, matching the look and feel of the rest
of the UI.

## What Changes

- Promote the existing ad-hoc `Users` page into a first-class, spec-backed
  **User Management** capability in the SPA
- Admin-only **Users** view: list (with search/pagination), inline role change,
  activate/deactivate, and delete — styled to match the existing SPA tables
- **Ownership-transfer dialog**: when deleting a user is blocked (409 — the user
  still owns networks or network types), present an in-app transfer flow
  (`POST /api/v1/users/{id}/transfer/`) instead of surfacing a raw error string
- Power-user/admin **Teams** view: create/delete teams, add/remove members
  (`/api/v1/teams/` + member sub-actions)
- Role-aware navigation: the sidebar exposes **User Management** to admins and
  **Teams** to power users/admins; routes are guarded client-side and added to
  the server SPA route allowlist
- Extend the SPA auth model to carry `role` and `teams` (already returned by
  `GET /api/v1/auth/me/`) so the UI can gate features by role

## Capabilities

### New Capabilities

- `spa-user-management`: Admin-only SPA screens for listing users, changing
  roles, activating/deactivating, deleting (with a guided ownership-transfer
  flow), plus power-user/admin team management — all served by the existing
  `user-management` REST API and matching the SPA design system

### Modified Capabilities

- `spa-layout`: Sidebar gains role-gated navigation entries (User Management /
  Teams); the SPA route allowlist in `ngcn_workbench/urls.py` is extended so the
  new client routes are served on direct load/refresh
- `auth`: The SPA-side user model is extended with `role` and `teams` (values the
  `me` endpoint already provides) to drive role-based UI gating

## Impact

- **Frontend**: new pages under `frontend/src/pages/` (Users, Teams) and a
  transfer dialog component; `AppLayout` navigation; `AuthContext` user type;
  new client-side admin/power-user route guards; `App.tsx` routes
- **Backend**: `ngcn_workbench/urls.py` SPA allowlist regex gains `users` and
  `teams`; no new API endpoints (reuses `user-management` REST surface)
- **Tests**: `test_spa_routing.py` allowlist parity for the new routes; frontend
  behaviour is validated via the build/typecheck and manual smoke tests
- **Docs/UX**: Django Admin remains available but is no longer the primary path
  for user/team management
- **Out of scope**: self-service profile editing, password reset, and any change
  to the underlying `user-management` REST API or permission model

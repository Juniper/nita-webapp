## Context

The `user-management` change delivered the full REST surface for users and teams:

- `GET/PATCH /api/v1/users/`, `POST /api/v1/users/{id}/transfer/`,
  `DELETE /api/v1/users/{id}/` (admin-only, protected deletion returning 409 with
  the blocking resources)
- `GET/POST/DELETE /api/v1/teams/` plus `POST /api/v1/teams/{id}/members/` and
  `DELETE /api/v1/teams/{id}/members/{user_id}/` (power-user/admin)
- `GET /api/v1/auth/me/` returns `role` and `teams`

The React SPA (Vite + React Router + Tailwind, dark theme) already has list pages
for Networks and Network Types that establish the visual and interaction
conventions (table layout, inline row actions, confirm-to-delete, error banners).
The SPA is served by Django/WhiteNoise; `ngcn_workbench/urls.py` holds an explicit
allowlist regex of client routes so direct loads/refreshes return `index.html`.

A minimal `Users` page and an admin-only sidebar link already exist. This design
covers turning that into a complete, spec-backed capability.

## Goals / Non-Goals

**Goals:**
- Native SPA screens for user administration matching the existing design system
- A guided ownership-transfer flow for protected user deletion (no raw 409 text)
- Team management for power users and admins in the SPA
- Role-gated navigation and client-side route guards
- Keep the server SPA route allowlist in sync (direct-load safe)

**Non-Goals:**
- New or changed REST endpoints, serializers, or permission classes
- Self-service profile/password management, email verification, SSO
- Removing Django Admin (it remains as a fallback)
- Bulk operations beyond the single-user transfer already provided

## Decisions

### Decision 1: Reuse the existing REST API unchanged

**Choice**: The SPA consumes the `user-management` endpoints exactly as-is via the
existing `apiFetch` CSRF-aware client; no backend API changes.

**Rationale**: The API already models every operation (list, role, active,
transfer, delete, teams, members). Keeping the change frontend-only minimises
risk and blast radius.

### Decision 2: Role gating on the client mirrors server enforcement

**Choice**: Navigation entries and routes are shown/guarded using
`user.role` / `user.is_superuser` from `me`. Admin-only: Users. Power-user or
admin: Teams. Non-permitted users are redirected to `/`.

**Rationale**: The server is the source of truth (endpoints already return
403/404); client gating is purely for UX. `me` already exposes `role` and
`teams`, so no extra calls are needed.

### Decision 3: Ownership-transfer dialog for protected deletion

**Choice**: On `DELETE` returning `409`, open a modal listing the blocking
networks/types and let the admin pick a recipient user, then call
`POST /api/v1/users/{id}/transfer/` and retry the delete.

**Rationale**: Protected deletion is intentional; the SPA should turn the 409 into
an actionable workflow rather than a dead-end error. Self-deletion (400) stays a
simple inline message.

### Decision 4: Keep the server SPA allowlist authoritative and tested

**Choice**: Add `users` (and `teams`) to the regex in `ngcn_workbench/urls.py`
and to `SPA_ROUTES` in `test_spa_routing.py`.

**Rationale**: The allowlist is the existing mechanism that makes direct loads
work; the routing test already guards drift between it and `App.tsx`.

## Risks / Trade-offs

**Client/server gating drift** → The server enforces access; client gating is
cosmetic. Mitigation: rely on API 403/404s as the real boundary and keep gating
logic tied to `me`.

**Allowlist drift** → A new SPA route not added to the regex 404s on refresh.
Mitigation: `test_spa_routing.py` parametrised over `SPA_ROUTES` fails on drift.

**Team-management surface creep** → Teams add several interactions. Mitigation:
scope to create/delete + member add/remove; defer richer team features.

## Migration Plan

1. Extend the SPA `User` type with `role`/`teams`
2. Ship the Users view (list + inline role/active/delete) — already present; fold
   into the spec and polish (always-visible actions, search/pagination)
3. Add the ownership-transfer dialog wired to the transfer endpoint
4. Add the Teams view (create/delete, member add/remove)
5. Add role-gated nav + client route guards; extend the server allowlist + tests
6. Rebuild the frontend bundle; deploy

## Open Questions

- Should Teams be a separate top-level nav item or a tab within User Management?
  Proposed: separate nav item, power-user/admin gated.
- Do we need server-side search/pagination params for users, or is client-side
  filtering of the existing paginated list sufficient for expected scale?
  Proposed: start client-side; add query params only if needed.

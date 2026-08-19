## Context

`UserViewSet` was `[IsAuthenticated, IsAdminRole]` for every action except
`directory`. `TeamViewSet` scoped a `power_user`'s list/management to teams they
created (`Team.created_by`). Net effect: a `power_user` had no user-management
surface and could only see teams they personally made — so in practice they could
not "see and manage teams and users" from the UI, which was the reported gap.

This change promotes `power_user` to a **junior administrator**, superseding the
earlier narrowly-scoped "reset a member of my own team" design.

## Goals / Non-Goals

**Goals:**
- A `power_user` sees and manages **all teams** (like an admin).
- A `power_user` has a **full Users screen** over **non-admin** accounts:
  list/view/reset-password/activate-deactivate/role changes capped at `power_user`.
- The admin tier stays protected: power users can never touch `admin` accounts or
  grant the `admin` role.

**Non-Goals:**
- Account **create/delete** by power users (admin-only).
- Any power-user action on `admin` accounts.

## Decisions

### Decision 1: A single role-ceiling predicate for user actions

**Choice**: `IsAdminOrManagesNonAdminUser` — admin manages any user; a
`power_user` manages any target whose `role != admin`. Applied (object-level) to
`retrieve`, `set_password`, `update`/`partial_update`. `list`/`directory` are
`IsPowerUserOrAdmin`; `create`/`destroy`/`transfer` stay `IsAdminRole`.

**Rationale**: One ceiling ("not admin") is simpler and more honest than the prior
team-membership predicate, which was porous (a power user can add anyone to a team
they created, so "member of my team" constrained nothing). The ceiling directly
encodes the real guarantee: the admin tier is untouchable.

### Decision 2: Admins are excluded from a power user's user list

**Choice**: `UserViewSet.get_queryset` excludes `role=admin` from the **list** for
a `power_user` (admins remain visible to admins). Detail/actions use the full
queryset so acting on an admin yields a clean `403` (via the object permission),
not a `404`.

**Rationale**: "Manage all non-admin users" — power users should not even see the
admin roster in their list, but a deterministic `403` on any admin-targeted detail
action is clearer than hiding existence inconsistently.

### Decision 3: Role changes are capped below admin

**Choice**: In `update`, a `power_user` setting `role=admin` is rejected with
`403` (the object permission already blocks admin targets). Power users may set
`role` to `user` or `power_user` and toggle `is_active` on any non-admin.

**Rationale**: Prevents self-escalation and minting new admins while still letting
junior admins run the non-admin tier. `create`/`delete` stay admin-only, and the
last-active-admin guard is retained (moot for power users since they can't touch
admins).

### Decision 4: Power users manage all teams

**Choice**: `TeamViewSet.get_queryset` returns all teams; `get_permissions` is
`IsPowerUserOrAdmin` for every action (the creator restriction is dropped). Any
power user can list/create/delete any team and manage any team's membership.

**Rationale**: Matches "see and manage all teams like an admin"; the creator-only
scoping was the other half of the reported gap.

### Decision 5: SPA gating — power_user access, admin-only create/delete

**Choice**: The nav **User Management** link and the `/users` and `/teams` screens
are gated by `useIsPowerUser`. On the Users screen the **New user** and **Delete**
controls are `useIsAdmin`-only, and the role picker omits `admin` for power users.
Server authorization is the real boundary; the UI gating just avoids predictable
`403`s.

**Rationale**: Give power users the operational surface they need without exposing
account creation/deletion or the admin role in the UI.

## Risks / Trade-offs

- **Power-user reach over the non-admin tier is broad** (any regular user, and
  peers) → accepted per the junior-admin decision; hard-capped below admin and
  audited for password resets. Create/delete stay admin-only.
- **Acting on an admin** → blocked by the object permission (`403`) and excluded
  from the power-user list.
- **Granting admin** → explicitly rejected in `update` (`403`).
- **`user-roles` invariant** ("Role Assignment Restricted to Admin") → this change
  intentionally relaxes it: power users may assign roles **up to** `power_user`,
  never `admin`; the admin role remains admin-only to grant.

## Migration Plan

No schema or model changes. Permission/queryset widening on `UserViewSet` and
`TeamViewSet`, plus SPA gating. Regenerate `openapi.yaml`; keep the drift test
green. No data migration.

## Open Questions

_Resolved during exploration:_
- **Teams visibility** → all teams for power users.
- **Users scope** → full Users screen over non-admin accounts (junior admin).

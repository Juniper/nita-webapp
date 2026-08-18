## Why

Password reset is **admin-only**, which makes admins a bottleneck for routine
team-lead help: a member forgets their password, or a newly-added member needs
initial credentials, and every such request escalates to an admin. Power users
already **own their teams** and manage membership, yet cannot help their own
members with credentials or even view a member's profile.

This delegates a **tightly-scoped** slice of user management to power users —
their own team's `role=user` members, **password reset and profile view only** —
removing the bottleneck without breaching the role ladder. Account creation, role
changes, and deactivation/deletion remain **admin-only**.

The whole design reduces to one authority predicate:

> A power user MAY act on user `U` ⇔ `U.role == "user"` **AND** `U` is a member of
> a team the power user **created**.

That predicate encodes all three escalation guards for free: `role=user` targets
mean power users can never touch admins or other power users; no role field is
ever changed; and authority is scoped to the requester's own teams.

## What Changes

- Extend `POST /api/v1/users/{id}/set_password/` so a **power user** may reset the
  password of a target that satisfies the predicate above. Admins keep full
  ability. Any other target → `403`.
- Add a **scoped profile read**: a power user may `GET /api/v1/users/{id}/` for a
  member they manage (so the UI can show who is being reset). Admins keep full
  list/retrieve.
- **SPA**: add a per-member **Reset password** action on the **Teams** screen
  (`/teams`), reusing the existing set-password dialog. The admin **Users** screen
  stays admin-only.
- Account lifecycle (create, role change, deactivate, delete) and the full
  `GET /api/v1/users/` list remain **admin-only** — unchanged.
- **Audit** every power-user password reset (actor, target, timestamp). The
  team-membership scope is intentionally **soft** — a power user can already add
  any `role=user` to a team they created — so the reset is bounded (never reaches
  power users or admins) but must be observable.

## Capabilities

### Modified Capabilities

- `user-management`: `set_password` extended to team-scoped power users; a new
  scoped member-profile read for power users.
- `spa-user-management`: the Teams screen gains a per-member reset-password
  affordance for power users.

## Impact

- **Backend**: an object-level authority helper
  `_manages_member(requester, target)`; `set_password` and `retrieve` allow a
  power user when the predicate holds (admins still allowed by role). All other
  actions keep blanket `IsAdminRole`; last-admin and self-action guards unchanged.
- **OpenAPI**: updated permission descriptions on `set_password` + the retrieve
  op; regenerate `openapi.yaml`.
- **Frontend**: per-member "Reset password" button + dialog on `TeamsPage`; a
  scoped member fetch as needed.
- **Tests**: power user resets own-team `role=user` member (200); non-member
  (403); `power_user`/`admin` member (403); another power user's team member
  (403); power-user create/role-change/deactivate/delete/list (403); admin paths
  unchanged.

### Out of Scope

- Account creation, role changes, deactivate/delete by power users (admin-only).
- Widening team visibility (teams stay creator-scoped).
- Hard membership isolation — constraining who a power user can add to a team
  (`add_member`) — the future fix if true isolation is ever required.
- A global `/users/` list for power users (the `directory` roster already exists).

## Why

Admins were the only role able to manage teams and users, making them a
bottleneck and leaving `power_user` — a nominally elevated role — unable to do
day-to-day operational work in the UI: a power user could only see teams they
personally created and had no user-management surface at all.

This promotes `power_user` to a **junior administrator**: they see and manage
**all teams** (like an admin), and get a **full Users screen** over **non-admin**
accounts — list, view, reset password, activate/deactivate, and change roles
capped **below** admin. The administrator tier stays protected: a power user can
never view, modify, deactivate, delete, or impersonate an `admin`, and can never
grant the `admin` role. Account **creation** and **deletion** remain admin-only.

This supersedes the earlier narrowly-scoped "reset a member of my own team"
design, which proved too restrictive in practice.

## What Changes

- **Teams**: a `power_user` sees and manages **every** team (list all, create,
  delete any, add/remove members on any) — not only teams they created.
- **Users (non-admin only)**: a `power_user` may
  - **list** users (admins excluded from their list) and **view** any non-admin,
  - **reset password** of any non-admin (audited),
  - **activate/deactivate** any non-admin,
  - **change role** of any non-admin, capped at `power_user` (never `admin`).
- **Guardrails**: a power user can never act on an `admin` account (403) and
  never set a role to `admin` (403). **Create** and **delete** of accounts, and
  the last-admin protection, remain **admin-only**.
- **SPA**: the **User Management** screen and nav link are available to
  `power_user`; the **New user** and **Delete** controls stay admin-only, and the
  role picker hides `admin` for power users. The Teams screen exposes per-member
  **Reset password**.

## Capabilities

### Modified Capabilities

- `user-management`: power users manage non-admin accounts (list/view/reset/
  activate-deactivate/role≤power_user); create/delete stay admin-only; admins are
  untouchable by power users.
- `teams`: power users see and manage all teams (not only ones they created).
- `spa-user-management`: the Users screen is available to power users with
  admin-only create/delete and an admin-capped role picker.

## Impact

- **Backend**: `IsAdminOrManagesNonAdminUser` permission; `UserViewSet`
  `get_permissions`/`get_queryset` open list/retrieve/update/set_password to power
  users over non-admins; `update` blocks a power user granting `admin`;
  `TeamViewSet` returns all teams and drops the creator restriction. Audit log on
  power-user password resets retained.
- **OpenAPI**: updated permission summaries; regenerate `openapi.yaml`.
- **Frontend**: nav + `UsersPage` gated by `useIsPowerUser`; create/delete
  admin-only; role picker capped; Teams reset affordance (already present).
- **Tests**: power-user user/team management (allowed vs 403 on admins and on
  granting admin), role/active changes, list excludes admins, audit.

### Out of Scope

- Account **create/delete** by power users (admin-only).
- Power users acting on `admin` accounts in any way.
- Deeper team features and an audit UI. (Team-membership isolation is moot now
  that the model is role-ceiling based rather than team-scoped.)

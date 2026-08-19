## Why

Onboarding is currently one-directional: the only way to create an account is
public self-registration (`POST /api/v1/auth/register/`), which always forces
`role=user`. An admin cannot create an account at all — there is no `create` on
the users API — so provisioning a `power_user` or `admin` means "register, then
promote," and even that first step has no UI. There is also no way for an admin
to reset a forgotten password without dropping into Django Admin or a shell.

At the same time, two safety gaps exist in the current admin API: nothing stops
an admin from demoting/deactivating/deleting the **last** administrator (the SPA
hides self-actions, but the REST API does not enforce it), which can lock an
organisation out.

This change gives admins a first-class onboarding path (create users with a
chosen role and an initial password), an admin-driven password reset, keeps
self-registration available behind a documented feature flag (default **on**),
and protects the last administrator at the API level.

## What Changes

- Add **admin user creation**: `POST /api/v1/users/` (admin-only) accepting
  `username`, `email`, `role`, and `password`; the password is validated with
  Django's validators and stored write-only (never echoed, never logged)
- Add **admin password reset**: `POST /api/v1/users/{id}/set_password/`
  (admin-only) that sets a validated password on any user (including the caller)
- Centralise password handling so create and reset share one validated,
  write-only path
- Make **self-registration configurable** via `NITA_SELF_REGISTRATION_ENABLED`
  (default **enabled** — both onboarding paths active); when disabled,
  `POST /api/v1/auth/register/` returns `403`. Documented extensively (settings,
  docker-compose, README/BUILD)
- Add **last-administrator protection**: the API SHALL reject any operation
  (role change, deactivation, deletion) that would leave zero active admins,
  with a clear `400`
- Add SPA affordances: a **New user** dialog (username, email, role, password
  with generate/copy) and a per-row **Reset password** action

## Capabilities

### Modified Capabilities

- `user-management`: gains admin **create** and **set-password** endpoints and
  **last-administrator protection** on update/deactivate/delete
- `user-registration`: self-registration becomes **feature-flagged**
  (`NITA_SELF_REGISTRATION_ENABLED`, default enabled); behaviour otherwise
  unchanged
- `spa-user-management`: the Users screen gains **create-user** and
  **reset-password** interactions

## Impact

- **Backend**: `UserViewSet` gains `CreateModelMixin` + a create serializer and a
  `set_password` action; a `set_password`-style write-only serializer; last-admin
  guard helper applied to `update`/`partial_update`/`destroy`; `register_view`
  reads the new setting
- **Settings / config**: new `SELF_REGISTRATION_ENABLED` setting sourced from
  `NITA_SELF_REGISTRATION_ENABLED` (default `True`); docker-compose env stub;
  README/BUILD documentation
- **Frontend**: create-user dialog and reset-password dialog on `UsersPage`; a
  small reusable password field (generate + copy)
- **OpenAPI**: new create/set-password operations; regenerate `openapi.yaml`
- **Tests**: create (roles, validation, duplicate), set-password (admin/self,
  validation), registration toggle (on/off), last-admin guard (demote,
  deactivate, delete)

### Out of Scope

- Self-service password change (users changing their own password) — remains an
  accepted gap; admin-reset only for now
- Email delivery / invite links / password-reset emails
- A self-registration **UI** (the endpoint stays API-only; only admin-create
  gets a screen)
- Team depth (team↔network views); the regular-user network→team assignment seam
  is noted as a known gap, not addressed here

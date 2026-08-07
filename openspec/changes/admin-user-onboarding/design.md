## Context

`UserViewSet` today exposes list / retrieve / update / destroy (+ `transfer`,
`directory`) but intentionally omits `create`. Onboarding is only
`POST /api/v1/auth/register/` (public, `role=user`). Passwords are set with
Django's `set_password()` in registration and the `create_admin` command; there
is no admin reset path. Password validation uses Django's configured
`AUTH_PASSWORD_VALIDATORS`. The SPA `UsersPage` (admin-only) lists users with
inline role/active/delete and a transfer dialog, but cannot create users or reset
passwords.

## Goals / Non-Goals

**Goals:**
- Admins can create users with a chosen role and an initial password
- Admins can reset any user's password
- Self-registration stays available but becomes a documented on/off flag
  (default on)
- The last active administrator cannot be demoted, deactivated, or deleted
- Password handling is one validated, write-only path shared by create + reset

**Non-Goals:**
- Self-service password change, email flows, self-registration UI, team depth

## Decisions

### Decision 1: Admin create via `POST /api/v1/users/` with a dedicated serializer

**Choice**: Re-enable `create` on `UserViewSet` (add `CreateModelMixin`) gated by
`IsAdminRole`, using a `UserCreateSerializer` with writable `username`, `email`,
`role`, and a **write-only** `password` validated by `validate_password`.

**Rationale**: This is the natural REST create for the resource and keeps the
admin surface in one viewset. A separate serializer keeps the read serializer
(no password) intact and lets create accept fields the read/update path does not.

**Alternative considered**: Reuse the registration serializer — rejected because
it forces `role=user` and is public.

### Decision 2: Password set/reset is one shared, write-only mechanism

**Choice**: A single validated path — Django validators → `set_password()` →
save — used by both create and a new `POST /api/v1/users/{id}/set_password/`
action (admin-only). Passwords are **write-only**: never returned in any
response and never included in log output. The action MAY target the caller's own
row (an admin resetting their own password).

**Rationale**: Create and reset are the same operation ("an admin sets a
password"). Centralising avoids two divergent validators and one place to audit
for leakage.

**Consequence (accepted)**: With admin-reset-only and no self-service change, an
admin-issued password is permanent until an admin resets it — the user cannot
rotate it. Acceptable for an internal tool; a future self-service "change my
password" (with current-password check) is a clean additive upgrade.

### Decision 3: Self-registration behind `NITA_SELF_REGISTRATION_ENABLED` (default on)

**Choice**: Add a boolean setting `SELF_REGISTRATION_ENABLED`, sourced from the
environment variable `NITA_SELF_REGISTRATION_ENABLED`, **defaulting to `True`**
so both onboarding paths are active out of the box (backwards compatible). When
`False`, `POST /api/v1/auth/register/` returns `403` with a clear message
("Self-registration is disabled; contact an administrator.").

**Rationale**: Keep the open door by default, but give operators a single switch
to move to admin-only onboarding for stricter deployments. A flag (not removal)
preserves the existing behaviour and the `user-registration` capability.

**Documentation (must be extensive — explicit ask):**
- `settings.py`: define the setting with a comment explaining default-on and the
  env var; e.g.
  `SELF_REGISTRATION_ENABLED = os.getenv("NITA_SELF_REGISTRATION_ENABLED", "True") == "True"`
- `docker-compose.yaml`: add a commented env stub
  `# - NITA_SELF_REGISTRATION_ENABLED=True   # set False to allow admin-created accounts only`
- `README.md` / `BUILD.md`: a short "Onboarding" note describing the two paths
  (public self-registration vs. admin-created) and how the flag switches between
  "both active" (default) and "admin-only"
- The `user-registration` spec captures the flag and its default

**Truthiness note**: parse the env var consistently with the existing
`DJANGO_DEBUG` pattern (`== "True"`), so `"False"`/`"0"`/empty disable it — document
the accepted values.

**SPA discovery (noted, out of scope)**: the SPA has no signup page today, so the
flag only gates the API. If a signup UI is added later it will need to learn the
flag (e.g. via a public config field); not addressed here.

### Decision 4: Protect the last administrator at the API

**Choice**: Add a guard used by `partial_update`/`update` (role or `is_active`
change) and `destroy`: an operation is rejected with `400` if it would leave
**zero active admins** (`role=admin AND is_active=True`). Covers demotion,
deactivation, and deletion of the final admin — regardless of whether the target
is the caller or another admin.

**Rationale**: The SPA already hides self-actions, but the REST API is the real
boundary; a direct call (or two admins in sequence) could otherwise remove the
last admin and lock everyone out. Enforcing the invariant server-side is the
correct place.

**Definition**: "last admin" = the target is currently an active admin and the
count of active admins is 1. Blocked messages name the reason
("Cannot remove the last administrator.").

## Risks / Trade-offs

- **Password in transit/logs** → write-only serializer field, no echo; verify no
  view logs the request body. TLS terminates at the proxy.
- **Flag truthiness confusion** → follow the existing `== "True"` convention and
  document accepted values.
- **Last-admin guard false blocks** → only fires when active-admin count is
  exactly 1 and the target is that admin; creating another admin first is always
  possible.
- **No self-service password rotation** → accepted; documented upgrade path.

## Migration Plan

No schema changes. Additive endpoints + one new setting (default preserves
current behaviour). Regenerate `openapi.yaml`. No data migration.

## Open Questions

- Should `set_password` live at `/users/{id}/set_password/` (chosen) or as a
  write-only `password` field on the update serializer? Proposed: dedicated
  action, so ordinary role/active PATCHes never carry a password.
- Should the create response include a one-time "copy this password" affordance
  only client-side (never server-persisted beyond the hash)? Proposed: yes,
  purely in the SPA dialog.

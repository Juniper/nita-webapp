## 1. Admin User Creation (Backend)

- [x] 1.1 Add `UserCreateSerializer` (writable `username`, `email`, `role`; write-only `password` validated via `validate_password`; `create()` uses `set_password`)
- [x] 1.2 Add `CreateModelMixin` to `UserViewSet`; use `UserCreateSerializer` for `create`, `UserSerializer` otherwise; keep `IsAdminRole`
- [x] 1.3 Ensure `create` returns the read representation (id, username, email, role, is_active) — never the password
- [x] 1.4 Tests: admin creates user/power_user/admin; duplicate username → 400; weak password → 400; non-admin → 403; password absent from response

## 2. Admin Password Reset (Backend)

- [x] 2.1 Add `SetPasswordSerializer` (write-only `password`, `validate_password`)
- [x] 2.2 Add `POST /api/v1/users/{id}/set_password/` action on `UserViewSet` (`IsAdminRole`); validate + `set_password` + save; return 200 with no password echoed
- [x] 2.3 Allow the action on the caller's own row (admin resetting own password)
- [x] 2.4 Tests: admin resets another user; admin resets self; weak password → 400; non-admin → 403; response contains no password

## 3. Self-Registration Flag

- [x] 3.1 Add `SELF_REGISTRATION_ENABLED = os.getenv("NITA_SELF_REGISTRATION_ENABLED", "True") == "True"` to `settings.py` with an explanatory comment
- [x] 3.2 `register_view` returns `403` (clear message) when the flag is disabled; unchanged when enabled
- [x] 3.3 Add commented `NITA_SELF_REGISTRATION_ENABLED=True` env stub to `docker-compose.yaml`
- [x] 3.4 Document onboarding (both paths + the flag, default on, accepted values) in `README.md` (and/or `BUILD.md`)
- [x] 3.5 Tests: registration succeeds when enabled (default); returns 403 when disabled

## 4. Protect the Last Administrator

- [x] 4.1 Add a helper `would_remove_last_active_admin(target, *, new_role=None, new_is_active=None, deleting=False)` (active admin = `role=admin AND is_active=True`)
- [x] 4.2 Enforce in `update`/`partial_update`: block role change away from admin, or `is_active=false`, on the last active admin → `400` with a clear message
- [x] 4.3 Enforce in `destroy`: block deleting the last active admin → `400` (before/alongside the existing self-delete and PROTECT checks)
- [x] 4.4 Tests: demote last admin → 400; deactivate last admin → 400; delete last admin → 400; the same operations succeed when another active admin exists

## 5. SPA — Create User & Reset Password

- [x] 5.1 Add a small reusable password field component (text input + "generate" + "copy")
- [x] 5.2 Add a **New user** button + dialog on `UsersPage` (username, email, role select, password) → `POST /api/v1/users/`; on success add to the list and surface the created password to copy
- [x] 5.3 Add a per-row **Reset password** action + dialog → `POST /api/v1/users/{id}/set_password/`; success confirmation
- [x] 5.4 Surface validation errors (400) inline in both dialogs

## 6. OpenAPI, Tests & Build

- [x] 6.1 Add `@extend_schema` for the create body and `set_password` action; ensure the password field is write-only in the schema
- [x] 6.2 Regenerate `openapi.yaml`; keep the drift test green
- [x] 6.3 Run the full backend suite; `tsc -b && vite build` clean

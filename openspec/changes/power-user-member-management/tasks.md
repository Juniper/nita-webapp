## 1. Backend — scoped authority

- [ ] 1.1 Add helper `_manages_member(requester, target)`: `requester.role ==
  power_user` AND `target.role == user` AND target is a member of a team
  `created_by=requester`
- [ ] 1.2 `set_password`: allow when the requester is `admin` OR
  `_manages_member(...)`; otherwise `403` (currently blanket `IsAdminRole`)
- [ ] 1.3 `retrieve`: allow when the requester is `admin` OR `_manages_member(...)`;
  otherwise `403`
- [ ] 1.4 Keep `list`/`create`/`update`/`destroy`/`transfer` admin-only; keep the
  last-active-admin and self-action guards intact
- [ ] 1.5 Emit an audit-log entry on every **power-user** password reset (actor id,
  target id, timestamp) via the standard logger; admin resets need not be audited
  here
- [ ] 1.6 Tests: power user resets own-team `role=user` member (200); non-member
  (403); `role=power_user`/`admin` member (403); another power user's team member
  (403); power-user `create`/role-change/`deactivate`/`delete`/`list` (403);
  admin paths unchanged; scoped `retrieve` mirrors these (200 for managed member,
  403 otherwise); an audit entry is emitted on a power-user reset

## 2. OpenAPI

- [ ] 2.1 Update the permission descriptions on `set_password` and the retrieve
  operation; regenerate `openapi.yaml`; keep the drift test green

## 3. Frontend — Teams screen affordance

- [ ] 3.1 Add a per-member **Reset password** action on `TeamsPage` (power_user),
  reusing `SetPasswordDialog` → `POST /api/v1/users/{id}/set_password/`
- [ ] 3.2 Fetch the member's profile via the scoped `GET /api/v1/users/{id}/`
  where the dialog needs name/context
- [ ] 3.3 Surface `400`/`403` inline; keep `npm run lint` and `npm run build` green

## 4. Verify

- [ ] 4.1 Backend `pytest` suite green
- [ ] 4.2 Frontend lint + build green

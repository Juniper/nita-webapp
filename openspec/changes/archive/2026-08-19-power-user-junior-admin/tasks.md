## 1. Backend — power user manages non-admin users

- [x] 1.1 Add `IsAdminOrManagesNonAdminUser` (admin → any; power_user → target
  `role != admin`)
- [x] 1.2 `UserViewSet.get_permissions`: `list`/`directory` → power_user/admin;
  `retrieve`/`set_password`/`update`/`partial_update` → `IsAdminOrManagesNonAdminUser`;
  `create`/`destroy`/`transfer` → admin-only
- [x] 1.3 `UserViewSet.get_queryset`: exclude `role=admin` from the power_user list
- [x] 1.4 `update`: reject a power_user setting `role=admin` (403); keep the
  last-active-admin and self-delete guards
- [x] 1.5 Audit-log entry on every power-user password reset (actor id, target id,
  timestamp; no password)
- [x] 1.6 Tests: power_user list excludes admins; view/reset/deactivate/role≤power_user
  on non-admins (200); view/modify admin (403); grant admin (403); create/delete
  (403); admin paths unchanged; audit emitted

## 2. Backend — power user manages all teams

- [x] 2.1 `TeamViewSet.get_queryset` → all teams; `get_permissions` → power_user/admin
  for every action (drop the creator restriction)
- [x] 2.2 Tests: power_user lists all teams; manages a team created by another

## 3. OpenAPI

- [x] 3.1 Update permission summaries; regenerate `openapi.yaml`; drift green

## 4. Frontend — Users screen for power users

- [x] 4.1 Nav **User Management** link + `UsersPage` guard/enable → `useIsPowerUser`
- [x] 4.2 Keep **New user** and **Delete** admin-only; cap the role picker (hide
  `admin`) for power users
- [x] 4.3 Teams screen per-member **Reset password** (already present)
- [x] 4.4 `npm run lint` and `npm run build` green

## 5. Verify


- [x] 5.1 Backend `pytest` suite green
- [x] 5.2 Frontend lint + build green

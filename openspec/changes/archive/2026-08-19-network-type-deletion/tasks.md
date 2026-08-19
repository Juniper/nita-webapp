## 1. Backend — role-based deletion

- [x] 1.1 `CampusTypeViewSet.get_permissions`: `destroy` →
  `[IsAuthenticated(), IsPowerUserOrAdmin()]` (drop `IsOwnerOrAdmin`)
- [x] 1.2 Tests: power user deletes a type created by another power user; power
  user deletes an orphaned type (`created_by=NULL`); admin unchanged; regular
  `user` still receives 403

## 2. Backend — in-use guard (409)

- [x] 2.1 In `destroy`, before deleting, collect
  `CampusNetwork.objects.filter(campus_type=obj)` names; if non-empty return
  `409` with `detail` + `networks` list (mirror the protected-user-deletion body)
- [x] 2.2 Confirm the guard applies to admins as well as power users
- [x] 2.3 Tests: delete blocked with 409 listing blocking networks; delete
  succeeds (204) once those networks are removed; actions belonging to the type
  are removed with it

## 3. Backend — audit

- [x] 3.1 Log actor id, type id/name and timestamp when a `power_user` deletes a
  network type
- [x] 3.2 Test: audit entry emitted on power-user deletion

## 4. OpenAPI

- [x] 4.1 Document the `409` response and the widened delete permission;
  regenerate `openapi.yaml`; keep the drift test green

## 5. Frontend — Network Types page

- [x] 5.1 Show the **Delete** control only for `power_user`/`admin`
  (`useIsPowerUser`)
- [x] 5.2 On `409`, surface the returned `detail` and blocking network names
  inline instead of `Delete failed: 409`
- [x] 5.3 `npm run lint` and `npm run build` green

## 6. Spec drift cleanup

- [x] 6.1 Remove the `PATCH`/update scenarios from the `network-types` spec
  (no `UpdateModelMixin`; such requests return 405)

## 7. Verify

- [x] 7.1 Backend `pytest` suite green
- [x] 7.2 Manual check on the cluster: power user deletes the unused type (204);
  the in-use type returns 409 naming its networks

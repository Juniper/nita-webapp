## Why

A `power_user` cannot delete network types. Two separate causes were confirmed
against the live deployment:

1. **Orphan dead-zone.** Deletion is gated by `IsOwnerOrAdmin`, which falls back
   to `created_by` and returns `False` when it is `NULL`. Both live types have
   `created_by = NULL` (they came from the seed fixture, which never sets a
   creator), so **only an admin can ever delete them**. This is not a one-off:
   `created_by` is `SET_NULL`, so *any* type becomes permanently
   power-user-undeletable the moment its creator is deleted.
2. **Creator scoping.** Even with `created_by` set, a power user may only delete
   types **they** created. Network types are now the **last** resource still
   creator-scoped — networks, teams, and non-admin users were all moved to
   admin-equivalent power-user reach by earlier changes.

While confirming this, a third and more serious problem surfaced:
`CampusNetwork.campus_type` is **`on_delete=CASCADE`**, so deleting a network type
**silently destroys every network built from it** — with no guard, for admins too.
On the live system `ebgp_wan_0.3` backs two networks owned by two different users.

## What Changes

- **Delete is allowed for any `power_user` or `admin`**, regardless of who created
  the type (drop the creator/`IsOwnerOrAdmin` check). This fixes the orphan
  dead-zone and removes the last creator-scoped resource.
- **In-use guard**: deleting a network type that is still referenced by one or
  more `CampusNetwork` rows SHALL be rejected with **`409 Conflict`**, listing the
  blocking network names — mirroring the existing protected-user-deletion flow.
  This applies to **admins as well**, closing the silent-cascade footgun.
- **Audit** every network-type deletion performed by a `power_user` (actor id,
  type id/name, timestamp), mirroring power-user password-reset auditing.
- **SPA**: the **Delete** control on the Network Types page is shown only to
  `power_user`/`admin` (today every authenticated user sees it and gets a 403),
  and a `409` response renders the blocking network names instead of the current
  bare `Delete failed: 409`.
- **Spec drift cleanup**: the `network-types` spec documents `PATCH`/`PUT` update
  scenarios, but `CampusTypeViewSet` has no `UpdateModelMixin` (nor
  `CreateModelMixin`) — those requests return **405**, not 200/403. Remove the
  scenarios that describe endpoints which do not exist.

## Capabilities

### Modified Capabilities

- `network-types`: deletion allowed for any power user/admin; deletion blocked
  (409) while networks still reference the type; power-user deletions audited;
  non-existent update endpoints removed from the spec.
- `spa-network-types`: Delete control role-gated; 409 blocking list surfaced.

## Impact

- **Backend**: `CampusTypeViewSet.get_permissions` drops `IsOwnerOrAdmin` for
  `destroy`; `destroy` gains an in-use check returning `409` with the blocking
  network names, plus an audit log line for power-user deletions.
- **Frontend**: `NetworkTypesPage` gates the Delete button on `useIsPowerUser`
  and renders the 409 detail/list.
- **OpenAPI**: document the `409` response and the widened permission;
  regenerate `openapi.yaml`.
- **Tests**: power user deletes a type created by someone else and an orphaned
  (`created_by=NULL`) type; delete blocked with 409 while networks reference it;
  delete succeeds after those networks are removed; regular `user` still 403;
  audit entry emitted for power-user deletion.

### Out of Scope

- Changing `Action.campus_type_id` cascade — actions belong to the uploaded type
  artifact and SHOULD be removed with it.
- A "migrate networks to another type" flow (network types are not
  interchangeable); clearing blockers means deleting those networks.
- Backfilling `created_by` on existing orphaned types (unnecessary once deletion
  no longer depends on it; `created_by` remains a display/audit field).
- Adding create/update endpoints for network types (creation stays via
  `POST /upload/`).

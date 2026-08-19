## Context

`CampusTypeViewSet` exposes `List`/`Retrieve`/`Destroy` mixins plus an `upload`
action — there is **no** `CreateModelMixin` or `UpdateModelMixin`. Permissions:

```python
if self.action == "upload":  [IsAuthenticated, IsPowerUserOrAdmin]
if self.action == "destroy": [IsAuthenticated, IsPowerUserOrAdmin, IsOwnerOrAdmin]
else:                        [IsAuthenticated]
```

`IsOwnerOrAdmin` returns `True` for admins, otherwise resolves `owner` →
`created_by` and returns `owner is not None and owner == request.user`. So a
`NULL` `created_by` yields `False` for every non-admin.

Verified on the live deployment:

```
ebgp_wan_0.3           created_by=NULL   networks=2 ['user1-wan','power1-wan']  actions=3
evpn_vxlan_erb_dc_1.3  created_by=NULL   networks=0 []                          actions=5

can_delete(ebgp_wan_0.3):  vagrant(admin)=True   power1=False   power2=False
```

`created_by` is `SET_NULL`; the seed fixture never sets it and only `/upload/`
does. Relevant cascades: `CampusNetwork.campus_type` → **CASCADE**;
`Action.campus_type_id` → **CASCADE**.

## Goals / Non-Goals

**Goals:**
- Any `power_user` or `admin` can delete a network type, including orphaned ones.
- Deleting a type that still backs networks is refused with an actionable `409`.
- Power-user deletions are auditable; the SPA reflects both rules.

**Non-Goals:**
- Type↔network migration, `created_by` backfill, new create/update endpoints,
  changing the actions cascade.

## Decisions

### Decision 1: Deletion is role-based, not creator-based

**Choice**: `destroy` → `[IsAuthenticated, IsPowerUserOrAdmin]`; drop
`IsOwnerOrAdmin`.

**Rationale**: Fixes the orphan dead-zone at the root (deletion no longer depends
on a nullable field) and makes network types consistent with networks, teams, and
non-admin users, which already grant admin-equivalent power-user reach. Keeping
creator scoping would require special-casing `NULL`, which only papers over the
inconsistency.

### Decision 2: In-use guard returns 409 with the blocking networks — for everyone

**Choice**: `destroy` refuses with `409 Conflict` when any `CampusNetwork`
references the type, returning a `detail` plus the blocking network names. This
applies to **admins too**.

**Rationale**: `campus_type` is `CASCADE`, so today deleting a type silently
destroys other users' networks — a footgun that exists for admins right now and
would be handed to every power user by Decision 1. The `409`-with-blocking-list
pattern already exists for protected user deletion, so it is familiar.

**Consequence (accepted, breaking)**: admins lose the ability to cascade-delete an
in-use type; they must remove the networks first. The previously unconditional
"delete → 204" requirement is modified.

### Decision 3: Actions still cascade with the type

**Choice**: Leave `Action.campus_type_id` as `CASCADE`; the guard considers
**networks only**.

**Rationale**: Actions are part of the uploaded type artifact and are meaningless
without it; networks are independent user-owned resources.

### Decision 4: Audit power-user deletions

**Choice**: Log actor id, type id/name and timestamp when a `power_user` deletes a
type, mirroring the power-user password-reset audit.

**Rationale**: Type deletion is effectively irreversible (the type is an uploaded
`.zip` artifact — if nobody kept the zip, it cannot be recreated), so the more
privileged path must leave a trace.

### Decision 5: SPA gates the control and explains the 409

**Choice**: Show **Delete** only to `power_user`/`admin`, and on `409` render the
returned blocking network names inline instead of `Delete failed: 409`.

**Rationale**: Today the button is shown to everyone and fails with 403; and a
bare "409" would replace one confusing error with another. Server authorization
remains the real boundary.

### Decision 6: Remove spec scenarios for endpoints that do not exist

**Choice**: Drop the `PATCH`/update scenarios from `network-types`; keep the
mutating-access requirement scoped to what exists (upload + delete).

**Rationale**: With no `UpdateModelMixin`, `PATCH` returns `405` — the spec
currently promises `200`/`403`. Removing drift keeps the contract honest.

## Risks / Trade-offs

- **Irreversibility**: deleting a type destroys an uploaded artifact and its
  actions → mitigated by the confirmation step, the 409 guard, and the audit log;
  not by backups (none exist).
- **Breaking change for admins**: in-use types can no longer be cascade-deleted →
  intentional; surfaced via a clear 409.
- **Jenkins coupling**: clearing blockers means deleting networks, which is
  Jenkins-triggered and returns `503` when Jenkins is down → deleting an in-use
  type transitively depends on Jenkins health.
- **Immediate expectation**: `ebgp_wan_0.3` stays undeletable (now `409` instead
  of `403`) until its two networks are removed; only the unused
  `evpn_vxlan_erb_dc_1.3` becomes deletable right away.

## Migration Plan

No schema or data migration. Permission widening + a new pre-delete check + SPA
gating. Regenerate `openapi.yaml` (new `409`, updated permissions) and keep the
drift test green.

## Open Questions

- **Codify the role principle?** This is the fourth resource moved to
  admin-equivalent power-user reach (networks, teams, users, now types). It may be
  cheaper to state once in `user-roles` that a `power_user` has admin-equivalent
  reach over operational resources, with admin-only limited to user
  create/delete, admin accounts, and granting `role=admin` — so future resources
  follow by default instead of being rediscovered. **Not included in this change**;
  raise separately if wanted.
- Should orphaned (`created_by=NULL`) types display "—" or "system/seed" in the
  UI? Cosmetic; unchanged here.

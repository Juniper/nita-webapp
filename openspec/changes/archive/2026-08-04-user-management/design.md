## Context

The NITA webapp runs a Django/DRF backend with `django.contrib.auth` already
installed. All API endpoints are currently gated behind `IsAuthenticated`
(session or token). There is a single implicit "admin" user (`vagrant/vagrant123`)
and no concept of ownership or roles. The codebase uses a `DefaultRouter` with
ViewSets, DRF serializers, and a custom `LabSessionAuthentication` for CSRF
relaxation in tunnel/port-forward environments.

The goal is to layer multi-user ownership and role-based access on top of the
existing foundation with minimal disruption to existing API consumers.

## Goals / Non-Goals

**Goals:**
- Custom User model with a `role` field (`user`, `power_user`, `admin`)
- Self-service registration defaulting to `role=user`
- Admin APIs for user and team management + offboarding flow
- Custom `Team` model for collaborative network sharing
- Ownership scoping on `CampusNetwork` (owner + team + admin)
- `created_by` curation on `CampusType` (power_user/admin write, all read)
- Bootstrap path for fresh deployments (management command + env vars)
- PROTECT-guarded user deletion with bulk ownership transfer

**Non-Goals:**
- Frontend registration or admin pages (Django Admin covers day-one needs)
- Email verification or password reset flows
- OAuth / SSO / external identity providers
- Fine-grained per-object permissions beyond the ownership model described here
- Audit logging (future concern)

## Decisions

### Decision 1: Extend `AbstractUser`, not `auth.User`

**Choice**: Subclass `django.contrib.auth.AbstractUser` in a new
`ngcn.models.User` class and set `AUTH_USER_MODEL = "ngcn.User"`.

**Rationale**: `AbstractUser` retains all built-in fields (username, password,
email, is_staff, is_superuser, groups, user_permissions) while letting us add
the `role` field cleanly. This is Django's recommended path and must be done
before any other migration in this change — swapping the user model mid-project
requires a clean initial migration.

**Alternative considered**: A separate `UserProfile` model with a OneToOne to
`auth.User`. Rejected because it adds join overhead on every permission check
and complicates queryset scoping.

**Migration note**: Because `AUTH_USER_MODEL` must be set before any migration
references `auth.User`, the first migration of this change must define the custom
User model. All existing FK references to `auth.User` (there are none in the
current codebase) would need to be updated — safe here.

---

### Decision 2: `role` as a CharField with explicit choices, not Django Groups

**Choice**: `role = CharField(choices=["user","power_user","admin"], default="user")`
on the custom User model.

**Rationale**: The access model has exactly three tiers with clear, non-additive
semantics. Django's `Group` + `Permission` system is designed for additive,
per-object permissions which is more machinery than needed. A `role` field is
readable in queries, serializers, and tests, and maps directly to three DRF
permission classes.

**Alternative considered**: Django Groups with custom permissions. Rejected
because groups are additive and can combine in unexpected ways; the three-tier
model is intentionally exclusive.

**Note**: `is_staff` and `is_superuser` are left as Django internals for admin
panel access only and are NOT used for application-level role checks.

---

### Decision 3: Custom `Team` model (not Django `auth.Group`)

**Choice**: New `Team` model with `name`, optional `description`, and a
`members` ManyToManyField to the custom User.

**Rationale**: Django's `Group` is a thin name+permissions container with no
metadata or membership API surface. A custom `Team` gives us a
first-class API resource (`/api/v1/teams/`) with its own serializer and
viewset. It also cleanly separates "application teams" from "Django admin
groups," avoiding semantic collision.

**Alternative considered**: Reusing `auth.Group`. Rejected for the reasons
above and because it would require registering groups in DRF routing and
serializing them separately anyway.

---

### Decision 4: Ownership scoping via ViewSet `get_queryset` override

**Choice**: Override `get_queryset()` in `CampusNetworkViewSet` to filter by
`owner=request.user OR team__members=request.user` for non-admin roles.

**Rationale**: Centralising the scope filter in `get_queryset` means it applies
to list, retrieve, update, and delete uniformly — no risk of forgetting to check
in a specific action. DRF's `get_object()` calls `get_queryset()` internally, so
detail endpoints are automatically protected.

**Alternative considered**: Object-level permissions via `has_object_permission`.
This works for detail views but would not filter list results, requiring a
separate queryset filter anyway. Using `get_queryset` is simpler and sufficient.

---

### Decision 5: `PROTECT` on `User` deletion with a bulk transfer endpoint

**Choice**: `owner` FK on `CampusNetwork` uses `on_delete=PROTECT`. A dedicated
`POST /api/v1/users/{id}/transfer/` endpoint allows admins to reassign all owned
resources before deletion.

**Rationale**: Silently deleting a user's networks (`CASCADE`) would destroy
production-adjacent configuration data. Orphaning them (`SET_NULL`) leaves
unowned ghosts with no clear custodian. PROTECT forces an explicit handoff
decision and makes offboarding auditable.

**Transfer endpoint contract**:
```
POST /api/v1/users/{id}/transfer/
{
  "networks_to": <user_id>,   // required if user owns networks
  "types_to": <user_id>       // required if user owns network types
}
→ 200 on success; then DELETE /api/v1/users/{id}/ will no longer be blocked
```

---

### Decision 6: Bootstrap via management command + env vars

**Choice**: Add a `create_admin` management command and check
`NITA_BOOTSTRAP_ADMIN_USERNAME` / `_EMAIL` / `_PASSWORD` env vars on startup
(via `AppConfig.ready()`). The env-var path only fires when zero users exist.

**Rationale**: Management command covers dev/CI workflows where CLI access is
available. Env-var path covers "appliance" Docker deployments where the operator
only has `docker-compose.yaml`. Both are idempotent.

---

### Decision 7: Permission class hierarchy

Four new DRF permission classes, composable with DRF's `|` and `&` operators:

| Class | Rule |
|---|---|
| `IsAdminRole` | `request.user.role == "admin"` |
| `IsPowerUserOrAdmin` | `role in ("power_user","admin")` |
| `IsOwnerOrAdmin` | `obj.owner == request.user OR IsAdminRole` |
| `IsOwnerOrTeamMemberOrAdmin` | owner OR team member OR admin |

`CampusNetworkViewSet` uses `IsAuthenticated` for list/create and
`IsOwnerOrTeamMemberOrAdmin` for retrieve/update/destroy.
`CampusTypeViewSet` uses `IsAuthenticated` for list/retrieve and
`IsPowerUserOrAdmin` for create/update/destroy (with `IsOwnerOrAdmin` for the
individual-object write check).

## Risks / Trade-offs

**Custom User model migration complexity** → Mitigation: squash or reset
migrations in the `ngcn` app before merging; document the migration order
explicitly in tasks.

**Existing `vagrant` default user breaks** → The `vagrant/vagrant123` user will
no longer be created by `auth.User` management commands after the model swap.
Mitigation: update CI scripts and `install_webapp.sh` to call `create_admin` or
set bootstrap env vars.

**`DISTINCT` requirement on scoped network queries** → `team__members`
ManyToMany join can produce duplicate rows when a user belongs to multiple teams
that share a network. Mitigation: use `.distinct()` on the queryset; add a DB
index on `(campus_network.owner_id, campus_network.team_id)`.

**No frontend for registration/team management on day one** → Mitigation: Django
Admin (`/admin/`) is wired and sufficient for initial deploys; SPA pages are a
follow-on change.

**PROTECT blocks user deletion if admin forgets to transfer** → Mitigation: the
`DELETE /api/v1/users/{id}/` endpoint returns a 409 with a list of owned
resources when PROTECT fires, guiding the admin to run transfer first.

## Migration Plan

1. Add custom User model migration (must be first — changes `AUTH_USER_MODEL`)
2. Add Team model migration
3. Add `owner`, `team` fields to `CampusNetwork` (nullable initially to avoid
   breaking existing rows; a data migration assigns existing records to the
   first admin)
4. Add `created_by` field to `CampusType` (nullable, SET_NULL)
5. Update `install_webapp.sh` and CI to use `create_admin` / bootstrap env vars
   instead of `createsuperuser`
6. Deploy; verify existing networks are owned by bootstrap admin
7. Rollback: revert `AUTH_USER_MODEL` is non-trivial — this change should be
   deployed to a fresh environment or behind a feature flag on existing installs

## Open Questions

- Should existing `CampusNetwork` rows (created before this change) be owned by
  the bootstrap admin or left with `owner=NULL` (making them admin-only visible)?
  Proposed: assign to bootstrap admin to avoid invisible orphans.
- Should `power_user` be able to promote another `user` to `power_user`, or is
  that strictly an `admin` action? Proposed: admin-only role changes.
- Is a `Team` name globally unique, or only per power_user? Proposed: globally
  unique to avoid confusion in team membership displays.

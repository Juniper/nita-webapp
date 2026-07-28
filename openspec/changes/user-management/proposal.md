## Why

The NITA webapp currently has a single shared identity — all authenticated users
see and operate on all networks and network types. As the tool is adopted by
small teams, there is a need for per-user ownership of network deployments,
role-based access control, and self-service account registration, so that users
can work independently without interfering with each other's environments.

## What Changes

- Introduce a three-tier role system (`user`, `power_user`, `admin`) via a custom
  `AbstractUser` subclass with a `role` field
- Add self-registration endpoint (`POST /api/v1/auth/register/`) defaulting new
  accounts to `role=user`
- Add admin-only user management API (list, role assignment, deactivation,
  ownership transfer, deletion)
- Introduce a custom `Team` model; power_users create teams and assign members;
  admins manage all teams
- Add `owner` (FK to User) and `team` (nullable FK to Team) fields on
  `CampusNetwork`; queries are scoped so users see only their own networks and
  networks belonging to their teams
- Add `created_by` (FK to User, nullable) on `CampusType`; only the creating
  user (power_user/admin) or an admin may edit or delete a type; all
  authenticated users may read all types
- Restrict `CampusType` create/update/delete to `power_user` and `admin` roles
- Add bootstrap support: a `create_admin` management command and an
  `NITA_BOOTSTRAP_*` env-variable path for zero-touch first-admin creation on
  fresh deployments
- User deletion is **PROTECT**-guarded; an admin must transfer or remove the
  user's owned resources before the account can be deleted
- **BREAKING**: `CampusNetwork` list/detail endpoints now return only records
  the requesting user is authorised to see (own + team-shared + admin-all)

## Capabilities

### New Capabilities

- `user-roles`: Three-tier role system (user / power_user / admin) on a custom
  User model; role-based permission enforcement across all API endpoints
- `user-registration`: Self-service account creation endpoint; accounts default
  to `role=user`; admin bootstrap path for fresh deployments
- `user-management`: Admin API for listing users, assigning roles, deactivating
  accounts, bulk ownership transfer, and protected deletion
- `teams`: Custom Team model with power_user-managed membership; networks can
  optionally be shared with a team for collaborative access
- `network-ownership`: CampusNetwork gains `owner` and `team` fields; all reads
  and writes are scoped to the requesting user's authorised set

### Modified Capabilities

- `auth`: User model changes from vanilla `auth.User` to custom `AbstractUser`
  subclass; default credentials policy updated; `me` endpoint extended to return
  `role` and team memberships
- `networks`: List/detail queries are now ownership-scoped (**BREAKING**); create
  auto-assigns `owner=request.user`; edit/delete restricted to owner or admin
- `network-types`: Create/update/delete restricted to `power_user` and `admin`;
  `created_by` field introduced; all authenticated users retain read access

## Impact

- **Django models**: new custom User model (migration required before any others
  in this change), new Team model, FK additions to CampusNetwork and CampusType
- **DRF views / permissions**: new permission classes `IsAdminRole`,
  `IsPowerUserOrAdmin`, `IsOwnerOrAdmin`, `IsOwnerOrTeamMemberOrAdmin`; queryset
  scoping on CampusNetworkViewSet
- **API surface**: new endpoints under `/api/v1/auth/register/`,
  `/api/v1/users/`, `/api/v1/teams/`
- **Django Admin**: custom User model must be registered; Team model registered
- **Management commands**: `create_admin` command added
- **Docker / CI**: `NITA_BOOTSTRAP_ADMIN_USERNAME` / `_EMAIL` / `_PASSWORD` env
  vars added to docker-compose and CI configuration
- **Frontend**: login page unchanged; registration page and user/team admin pages
  are out of scope for this change (Django Admin covers day-one management)
- **Tests**: new test module for auth, roles, ownership scoping, and team access

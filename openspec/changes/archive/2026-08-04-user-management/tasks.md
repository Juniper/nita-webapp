## 1. Custom User Model

- [x] 1.1 Add `ngcn.models.User` subclassing `AbstractUser` with `role = CharField(choices=["user","power_user","admin"], default="user")`
- [x] 1.2 Set `AUTH_USER_MODEL = "ngcn.User"` in `settings.py`
- [x] 1.3 Generate and apply the initial migration for the custom User model (must be the first new migration)
- [x] 1.4 Register the custom User model in `admin.py` with `role` visible in the admin list view
- [x] 1.5 Update `me_view` to return `role` and `teams` (list of team ids) in the response

## 2. Bootstrap / Initial Admin

- [x] 2.1 Add `create_admin` management command (`ngcn/management/commands/create_admin.py`) accepting `--username`, `--email`, `--password`; sets `role=admin`, `is_staff=True`
- [x] 2.2 Add `AppConfig.ready()` hook in `ngcn/apps.py` that reads `NITA_BOOTSTRAP_ADMIN_*` env vars and calls `create_admin` logic when zero users exist
- [x] 2.3 Add `NITA_BOOTSTRAP_ADMIN_USERNAME`, `_EMAIL`, `_PASSWORD` env var stubs to `docker-compose.yaml` (commented out by default)
- [x] 2.4 Update the startup/bootstrap script to use `create_admin` instead of `createsuperuser` (implemented in `wait-for-db.sh`, the actual bootstrap location)
- [x] 2.5 Update CI scripts (`ci-start.sh`) to use the bootstrap mechanism for the default test user

## 3. Self-Registration Endpoint

- [x] 3.1 Add `UserRegistrationSerializer` validating `username`, `password` (via Django validators), optional `email`; force `role=user` regardless of input
- [x] 3.2 Add `register_view` at `POST /api/v1/auth/register/` with `permission_classes=[AllowAny]`; returns 201 with `id`, `username`, `role`
- [x] 3.3 Wire `auth/register/` into `ngcn/api/urls.py`
- [x] 3.4 Write tests: successful registration, duplicate username → 400, weak password → 400, role escalation attempt → role stays `user`

## 4. Team Model

- [x] 4.1 Add `Team` model to `ngcn/models.py`: `name (unique)`, `description (nullable)`, `created_by FK→User (SET_NULL)`, `members ManyToManyField(User, related_name="teams")`
- [x] 4.2 Generate and apply migration for `Team`
- [x] 4.3 Register `Team` in `admin.py`
- [x] 4.4 Add `TeamSerializer` with `id`, `name`, `description`, `created_by`, `members` (list of user ids)
- [x] 4.5 Add `TeamViewSet` with scoped `get_queryset` (power_user sees own; admin sees all; user → 403 on list)
- [x] 4.6 Add `POST /api/v1/teams/{id}/members/` and `DELETE /api/v1/teams/{id}/members/{user_id}/` actions on `TeamViewSet`
- [x] 4.7 Register `teams` router in `ngcn/api/urls.py`
- [x] 4.8 Write tests: power_user create/list/delete own teams, member add/remove, regular user gets 403, admin manages any team

## 5. Network Ownership

- [x] 5.1 Add `owner FK→User (PROTECT)` and `team FK→Team (SET_NULL, null=True, blank=True)` to `CampusNetwork`
- [x] 5.2 Generate and apply migration; write data migration to assign `owner=<bootstrap admin>` to all existing orphaned networks
- [x] 5.3 Override `CampusNetworkViewSet.get_queryset()` to filter by `owner=request.user OR team__members=request.user` for non-admin; use `.distinct()`
- [x] 5.4 Set `owner=request.user` on create (in the overridden `create()` which persists the row)
- [x] 5.5 Apply `IsOwnerOrTeamMemberOrAdmin` permission for retrieve/update/destroy; team members get read access only
- [x] 5.6 Write tests: user sees only own + team networks, team member cannot modify, admin sees all, cross-user 404 on retrieve

## 6. Network Type Curation

- [x] 6.1 Add `created_by FK→User (SET_NULL, null=True)` to `CampusType`
- [x] 6.2 Generate and apply migration
- [x] 6.3 Set `created_by=request.user` on network-type creation (in the `upload` action)
- [x] 6.4 Apply `IsPowerUserOrAdmin` for create (upload); `IsOwnerOrAdmin` (checking `created_by`) for destroy
- [x] 6.5 Write tests: power_user can create, regular user gets 403 on create/delete, only creator or admin can delete a type

## 7. Permission Classes

- [x] 7.1 Add `IsAdminRole` permission class to `ngcn/api/permissions.py`
- [x] 7.2 Add `IsPowerUserOrAdmin` permission class
- [x] 7.3 Add `IsOwnerOrAdmin` permission class (checks `obj.owner` or `obj.created_by` depending on call site)
- [x] 7.4 Add `IsOwnerOrTeamMemberOrAdmin` permission class (used by `CampusNetworkViewSet`)
- [x] 7.5 Write unit tests for each permission class in isolation

## 8. Admin User Management API

- [x] 8.1 Add `UserSerializer` with `id`, `username`, `email`, `role`, `is_active`
- [x] 8.2 Add `UserViewSet` (list, retrieve, partial_update) gated by `IsAdminRole`
- [x] 8.3 Add `transfer` action at `POST /api/v1/users/{id}/transfer/`; reassigns `CampusNetwork.owner` and `CampusType.created_by` in a single transaction
- [x] 8.4 Override `UserViewSet.destroy()` to return 409 with blocking resource list when PROTECT fires; block self-deletion with 400
- [x] 8.5 Register `users` router in `ngcn/api/urls.py`
- [x] 8.6 Write tests: admin lists users, admin changes role, admin deactivates user, transfer then delete, self-delete blocked, non-admin gets 403

## 9. OpenAPI Schema and Tests

- [x] 9.1 Verify `drf-spectacular` generates correct schema for all new endpoints; add `@extend_schema` decorators where needed
- [x] 9.2 Run full test suite; fix any broken existing tests caused by ownership scoping or user model change — **done: 130 passed on Python 3.12 (Django 5.2). Also fixed a pre-existing `import os` bug in `networktypeparser.py` surfaced by the run. `makemigrations --check` confirms 0005/0006 match the models (only pre-existing verbose_name drift remains, unrelated to this change).**
- [x] 9.3 Update `openapi.yaml` snapshot — **done: regenerated via `manage.py spectacular`; the schema-drift test now passes.**

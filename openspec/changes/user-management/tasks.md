## 1. Custom User Model

- [ ] 1.1 Add `ngcn.models.User` subclassing `AbstractUser` with `role = CharField(choices=["user","power_user","admin"], default="user")`
- [ ] 1.2 Set `AUTH_USER_MODEL = "ngcn.User"` in `settings.py`
- [ ] 1.3 Generate and apply the initial migration for the custom User model (must be the first new migration)
- [ ] 1.4 Register the custom User model in `admin.py` with `role` visible in the admin list view
- [ ] 1.5 Update `me_view` to return `role` and `teams` (list of team ids) in the response

## 2. Bootstrap / Initial Admin

- [ ] 2.1 Add `create_admin` management command (`ngcn/management/commands/create_admin.py`) accepting `--username`, `--email`, `--password`; sets `role=admin`, `is_staff=True`
- [ ] 2.2 Add `AppConfig.ready()` hook in `ngcn/apps.py` that reads `NITA_BOOTSTRAP_ADMIN_*` env vars and calls `create_admin` logic when zero users exist
- [ ] 2.3 Add `NITA_BOOTSTRAP_ADMIN_USERNAME`, `_EMAIL`, `_PASSWORD` env var stubs to `docker-compose.yaml` (commented out by default)
- [ ] 2.4 Update `build-and-test-webapp/install_webapp.sh` to use `create_admin` instead of `createsuperuser`
- [ ] 2.5 Update CI scripts to use the bootstrap mechanism for the default test user

## 3. Self-Registration Endpoint

- [ ] 3.1 Add `UserRegistrationSerializer` validating `username`, `password` (via Django validators), optional `email`; force `role=user` regardless of input
- [ ] 3.2 Add `register_view` at `POST /api/v1/auth/register/` with `permission_classes=[AllowAny]`; returns 201 with `id`, `username`, `role`
- [ ] 3.3 Wire `auth/register/` into `ngcn/api/urls.py`
- [ ] 3.4 Write tests: successful registration, duplicate username → 400, weak password → 400, role escalation attempt → role stays `user`

## 4. Team Model

- [ ] 4.1 Add `Team` model to `ngcn/models.py`: `name (unique)`, `description (nullable)`, `created_by FK→User (SET_NULL)`, `members ManyToManyField(User, related_name="teams")`
- [ ] 4.2 Generate and apply migration for `Team`
- [ ] 4.3 Register `Team` in `admin.py`
- [ ] 4.4 Add `TeamSerializer` with `id`, `name`, `description`, `created_by`, `members` (list of user ids)
- [ ] 4.5 Add `TeamViewSet` with scoped `get_queryset` (power_user sees own; admin sees all; user → 403 on list)
- [ ] 4.6 Add `POST /api/v1/teams/{id}/members/` and `DELETE /api/v1/teams/{id}/members/{user_id}/` actions on `TeamViewSet`
- [ ] 4.7 Register `teams` router in `ngcn/api/urls.py`
- [ ] 4.8 Write tests: power_user create/list/delete own teams, member add/remove, regular user gets 403, admin manages any team

## 5. Network Ownership

- [ ] 5.1 Add `owner FK→User (PROTECT)` and `team FK→Team (SET_NULL, null=True, blank=True)` to `CampusNetwork`
- [ ] 5.2 Generate and apply migration; write data migration to assign `owner=<bootstrap admin>` to all existing orphaned networks
- [ ] 5.3 Override `CampusNetworkViewSet.get_queryset()` to filter by `owner=request.user OR team__members=request.user` for non-admin; use `.distinct()`
- [ ] 5.4 Override `CampusNetworkViewSet.perform_create()` to set `owner=request.user`
- [ ] 5.5 Apply `IsOwnerOrAdmin` permission for update/partial_update/destroy actions; team members get read access only
- [ ] 5.6 Write tests: user sees only own + team networks, team member cannot modify, admin sees all, cross-user 404 on retrieve

## 6. Network Type Curation

- [ ] 6.1 Add `created_by FK→User (SET_NULL, null=True)` to `CampusType`
- [ ] 6.2 Generate and apply migration
- [ ] 6.3 Override `CampusTypeViewSet.perform_create()` to set `created_by=request.user`
- [ ] 6.4 Apply `IsPowerUserOrAdmin` for create; `IsOwnerOrAdmin` (checking `created_by`) for update/destroy
- [ ] 6.5 Write tests: power_user can create, regular user gets 403 on create/update/delete, only creator or admin can update/delete a type

## 7. Permission Classes

- [ ] 7.1 Add `IsAdminRole` permission class to `ngcn/api/permissions.py`
- [ ] 7.2 Add `IsPowerUserOrAdmin` permission class
- [ ] 7.3 Add `IsOwnerOrAdmin` permission class (checks `obj.owner` or `obj.created_by` depending on call site)
- [ ] 7.4 Add `IsOwnerOrTeamMemberOrAdmin` permission class (used by `CampusNetworkViewSet`)
- [ ] 7.5 Write unit tests for each permission class in isolation

## 8. Admin User Management API

- [ ] 8.1 Add `UserSerializer` with `id`, `username`, `email`, `role`, `is_active`
- [ ] 8.2 Add `UserViewSet` (list, retrieve, partial_update) gated by `IsAdminRole`
- [ ] 8.3 Add `transfer` action at `POST /api/v1/users/{id}/transfer/`; reassigns `CampusNetwork.owner` and `CampusType.created_by` in a single transaction
- [ ] 8.4 Override `UserViewSet.destroy()` to return 409 with blocking resource list when PROTECT fires; block self-deletion with 400
- [ ] 8.5 Register `users` router in `ngcn/api/urls.py`
- [ ] 8.6 Write tests: admin lists users, admin changes role, admin deactivates user, transfer then delete, self-delete blocked, non-admin gets 403

## 9. OpenAPI Schema and Tests

- [ ] 9.1 Verify `drf-spectacular` generates correct schema for all new endpoints; add `@extend_schema` decorators where needed
- [ ] 9.2 Run full test suite; fix any broken existing tests caused by ownership scoping or user model change
- [ ] 9.3 Update `openapi.yaml` snapshot if the project maintains one

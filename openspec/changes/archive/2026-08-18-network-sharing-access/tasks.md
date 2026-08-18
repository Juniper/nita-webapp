## 1. Power User Network Reach (Reading 2)

- [ ] 1.1 `CampusNetworkViewSet.get_queryset`: return all networks when
  `role in {admin, power_user}` (else `owner | team-member`)
- [ ] 1.2 Widen object-level edit/delete permission to
  `owner OR role in {power_user, admin}` (update the network permission class)
- [ ] 1.3 Confirm lifecycle action / history / streaming access follows the same
  network visibility (power_user can run/inspect any network) — add coverage if
  any path scopes independently
- [ ] 1.4 Tests: power_user lists all networks; retrieves another user's network
  (200, not 404); edits and deletes another user's network; runs a lifecycle
  action on another user's network

## 2. My Teams Read

- [ ] 2.1 Add `GET /api/v1/teams/mine/` (permission `IsAuthenticated` only)
  returning `[{id, name}]` for `request.user.teams.all()`
- [ ] 2.2 Ensure the full `GET /api/v1/teams/` list remains `IsPowerUserOrAdmin`
- [ ] 2.3 Tests: `role=user` gets their teams (id+name); empty list when in no
  team; teams the user is not a member of never appear; endpoint works for
  power_user/admin too (their memberships)

## 3. Owner Team-Assignment Constraint

- [ ] 3.1 On `PATCH /api/v1/networks/{id}/` with `team`, reject (`400`) when the
  requester is the owner but not power_user/admin and is NOT a member of the
  target team
- [ ] 3.2 Allow power_user/admin to assign any network to any team; allow
  `team=null` (unassign) for owner/power_user/admin
- [ ] 3.3 Tests: owner assigns to a team they belong to (200); owner assigns to a
  team they do NOT belong to (400); power_user assigns any network to any team
  (200); unassign clears the team

## 4. OpenAPI & Verify

- [ ] 4.1 Add `@extend_schema` for `GET /api/v1/teams/mine/`; update
  visibility/permission descriptions on the network endpoints
- [ ] 4.2 Regenerate `openapi.yaml`; keep the drift test green
- [ ] 4.3 Run the full backend `pytest` suite green

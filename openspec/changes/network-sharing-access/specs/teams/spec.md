## ADDED Requirements

### Requirement: My Teams (Any Authenticated User)
The system SHALL provide `GET /api/v1/teams/mine/` accessible to any
authenticated user, including `role=user`, returning the `id` and `name` of every
team the requesting user is a **member** of. The endpoint SHALL be scoped to the
caller's own memberships and SHALL NOT expose teams the user does not belong to.
This endpoint is independent of the full `GET /api/v1/teams/` list, which remains
restricted to `power_user` and `admin`.

#### Scenario: Regular user lists their teams
- GIVEN a user with `role=user` who is a member of `"Team-X"` and `"Team-Y"`
- WHEN `GET /api/v1/teams/mine/` is called
- THEN a 200 response is returned containing `{id, name}` for `"Team-X"` and
  `"Team-Y"` only

#### Scenario: User in no team gets an empty list
- GIVEN a user with `role=user` who is a member of no team
- WHEN `GET /api/v1/teams/mine/` is called
- THEN a 200 response is returned with an empty list

#### Scenario: Teams the user does not belong to are never exposed
- GIVEN teams `"Team-X"` (user is a member) and `"Team-Z"` (user is NOT a member)
- WHEN `GET /api/v1/teams/mine/` is called
- THEN the response contains `"Team-X"` and does NOT contain `"Team-Z"`

#### Scenario: The full team list stays restricted
- GIVEN a user with `role=user`
- WHEN `GET /api/v1/teams/` is called
- THEN a 403 response is returned (the `mine` endpoint does not relax this)

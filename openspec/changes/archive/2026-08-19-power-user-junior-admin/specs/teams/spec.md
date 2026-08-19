## MODIFIED Requirements

### Requirement: Team Membership Management (Power User and Admin)
The system SHALL allow `power_user` and `admin` to add and remove members from
teams via `POST /api/v1/teams/{id}/members/` and
`DELETE /api/v1/teams/{id}/members/{user_id}/`. A `power_user` MAY manage
membership on **any** team, not only teams they created; an `admin` MAY manage
any team.

#### Scenario: Power user adds a member to any team
- GIVEN a `power_user` and a team created by a different power user
- WHEN `POST /api/v1/teams/{id}/members/` is called with `{"user_id": <id>}`
- THEN the specified user is added to the team and a 200 response is returned

#### Scenario: Admin can manage any team
- GIVEN a user with `role=admin`
- WHEN `POST /api/v1/teams/{id}/members/` is called for any team
- THEN the membership change is applied and a 200 response is returned

#### Scenario: Remove member from team
- GIVEN a `power_user` or `admin` and a team with user Bob as a member
- WHEN `DELETE /api/v1/teams/{id}/members/{bob_id}/` is called
- THEN Bob is removed from the team and a 204 response is returned

### Requirement: Team Listing and Detail
The system SHALL provide `GET /api/v1/teams/` and `GET /api/v1/teams/{id}/`.
Both `power_user` and `admin` SHALL see **all** teams. A `user` SHALL NOT have
access to the team list endpoint.

#### Scenario: Power user lists all teams
- GIVEN power_user Alice created `"Team-A"` and power_user Bob created `"Team-B"`
- WHEN Alice calls `GET /api/v1/teams/`
- THEN both `"Team-A"` and `"Team-B"` are returned

#### Scenario: Admin lists all teams
- GIVEN multiple teams exist across multiple power_users
- WHEN an admin calls `GET /api/v1/teams/`
- THEN all teams are returned

#### Scenario: Regular user cannot list teams
- GIVEN a user with `role=user`
- WHEN `GET /api/v1/teams/` is called
- THEN a 403 response is returned

### Requirement: Team Deletion (Power User or Admin)
The system SHALL allow `DELETE /api/v1/teams/{id}/` for any `power_user` or
`admin`, regardless of who created the team. Deleting a team SHALL set
`team=NULL` on all associated networks (SET_NULL). Active team membership SHALL
be cleared.

#### Scenario: Power user deletes any team
- GIVEN a team created by another power user, with 2 associated networks
- WHEN a `power_user` calls `DELETE /api/v1/teams/{id}/`
- THEN the team is deleted, both networks have `team=NULL`, and a 204 response is
  returned

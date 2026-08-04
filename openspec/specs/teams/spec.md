# Teams Specification

## Purpose
Custom Team model with power-user-managed membership for collaborative network
sharing.

## Requirements

### Requirement: Team Creation (Power User and Admin)
The system SHALL allow users with `role=power_user` or `role=admin` to create
teams via `POST /api/v1/teams/`. A team SHALL have a globally unique `name` and
an optional `description`.

#### Scenario: Power user creates a team
- GIVEN a user with `role=power_user`
- WHEN `POST /api/v1/teams/` is called with `{"name": "Project-X"}`
- THEN a 201 response is returned with the team `id` and `name`

#### Scenario: Regular user cannot create a team
- GIVEN a user with `role=user`
- WHEN `POST /api/v1/teams/` is called
- THEN a 403 response is returned

#### Scenario: Duplicate team name rejected
- GIVEN a team named `"Project-X"` already exists
- WHEN `POST /api/v1/teams/` is called with `{"name": "Project-X"}`
- THEN a 400 response is returned

### Requirement: Team Membership Management (Power User and Admin)
The system SHALL allow `power_user` and `admin` to add and remove members from
teams via `POST /api/v1/teams/{id}/members/` and
`DELETE /api/v1/teams/{id}/members/{user_id}/`.
A `power_user` SHALL only manage teams they created; an `admin` MAY manage any team.

#### Scenario: Power user adds a member to their team
- GIVEN a power_user who created team `"Project-X"`
- WHEN `POST /api/v1/teams/{id}/members/` is called with `{"user_id": <id>}`
- THEN the specified user is added to the team and a 200 response is returned

#### Scenario: Power user cannot manage another power_user's team
- GIVEN a power_user who did NOT create team `"Project-Y"`
- WHEN `POST /api/v1/teams/{project_y_id}/members/` is called
- THEN a 403 response is returned

#### Scenario: Admin can manage any team
- GIVEN a user with `role=admin`
- WHEN `POST /api/v1/teams/{id}/members/` is called for any team
- THEN the membership change is applied and a 200 response is returned

#### Scenario: Remove member from team
- GIVEN a power_user who manages a team, and user Bob is a member
- WHEN `DELETE /api/v1/teams/{id}/members/{bob_id}/` is called
- THEN Bob is removed from the team and a 204 response is returned

### Requirement: Team Listing and Detail
The system SHALL provide `GET /api/v1/teams/` and `GET /api/v1/teams/{id}/`.
A `power_user` SHALL see only teams they created. An `admin` SHALL see all teams.
A `user` SHALL NOT have access to the team list endpoint.

#### Scenario: Power user lists only their own teams
- GIVEN power_user Alice created `"Team-A"` and power_user Bob created `"Team-B"`
- WHEN Alice calls `GET /api/v1/teams/`
- THEN only `"Team-A"` is returned

#### Scenario: Admin lists all teams
- GIVEN multiple teams exist across multiple power_users
- WHEN an admin calls `GET /api/v1/teams/`
- THEN all teams are returned

#### Scenario: Regular user cannot list teams
- GIVEN a user with `role=user`
- WHEN `GET /api/v1/teams/` is called
- THEN a 403 response is returned

### Requirement: Team Deletion (Power User Creator or Admin)
The system SHALL allow `DELETE /api/v1/teams/{id}/` for the creating power_user
or an admin. Deleting a team SHALL set `team=NULL` on all associated networks
(SET_NULL). Active team membership SHALL be cleared.

#### Scenario: Power user deletes their team
- GIVEN a power_user who created team `"Project-X"` which has 2 associated networks
- WHEN `DELETE /api/v1/teams/{id}/` is called
- THEN the team is deleted and both networks have `team=NULL`
- AND a 204 response is returned

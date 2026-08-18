## MODIFIED Requirements

### Requirement: Network Visibility Scoping
The system SHALL scope `GET /api/v1/networks/` and `GET /api/v1/networks/{id}/`
so that a requesting user sees only:
- Networks they own (`owner=request.user`)
- Networks belonging to a team they are a member of (`team__members=request.user`)
- All networks if `role=admin` OR `role=power_user`

#### Scenario: User sees only own networks
- GIVEN user Alice owns networks `"Net-A"` and `"Net-B"`, and user Bob owns `"Net-C"`
- WHEN Alice (role=user) calls `GET /api/v1/networks/`
- THEN only `"Net-A"` and `"Net-B"` appear in the results

#### Scenario: User sees team-shared networks
- GIVEN user Alice is a member of `"Team-X"` which has network `"Shared-Net"`
  owned by Bob
- WHEN Alice calls `GET /api/v1/networks/`
- THEN `"Shared-Net"` appears in Alice's results

#### Scenario: User cannot retrieve another user's network directly
- GIVEN Bob owns network `"Net-C"` and Alice is not in Bob's team
- WHEN Alice (role=user) calls `GET /api/v1/networks/{net_c_id}/`
- THEN a 404 response is returned

#### Scenario: Power user sees all networks
- GIVEN multiple users own multiple networks, some with no team
- WHEN a `power_user` calls `GET /api/v1/networks/`
- THEN all networks are returned regardless of owner or team

#### Scenario: Power user retrieves any network directly
- GIVEN Bob owns network `"Net-C"` with no team
- WHEN a `power_user` calls `GET /api/v1/networks/{net_c_id}/`
- THEN a 200 response is returned with the network

#### Scenario: Admin sees all networks
- GIVEN multiple users own multiple networks
- WHEN an admin calls `GET /api/v1/networks/`
- THEN all networks are returned

### Requirement: Network Edit and Delete Restricted to Owner, Power User, or Admin
The system SHALL restrict `PATCH`, `PUT`, and `DELETE` on
`GET /api/v1/networks/{id}/` to the network's owner, a user with
`role=power_user`, or a user with `role=admin`.

#### Scenario: Owner can update their network
- GIVEN Alice owns `"Net-A"`
- WHEN Alice calls `PATCH /api/v1/networks/{net_a_id}/`
- THEN a 200 response is returned and the network is updated

#### Scenario: Power user can update any network
- GIVEN Bob owns `"Net-C"`
- WHEN a `power_user` calls `PATCH /api/v1/networks/{net_c_id}/`
- THEN a 200 response is returned and the network is updated

#### Scenario: Power user can delete any network
- GIVEN Bob owns `"Net-C"`
- WHEN a `power_user` calls `DELETE /api/v1/networks/{net_c_id}/`
- THEN a 204 response is returned and the network is deleted

#### Scenario: Regular team member cannot modify a shared network
- GIVEN Alice (role=user) is a member of a team that has access to Bob's `"Net-C"`
- WHEN Alice calls `PATCH /api/v1/networks/{net_c_id}/`
- THEN a 403 response is returned

### Requirement: Network Team Assignment
The system SHALL allow a network's owner, a `power_user`, or an `admin` to assign
or change the team for a network via `PATCH /api/v1/networks/{id}/` with a `team`
field. A non-admin, non-power_user owner MAY only assign the network to a team
they are a member of; a `power_user` or `admin` MAY assign any network to any
team. Setting `team=null` removes the team assignment and is allowed for the
owner, a `power_user`, or an `admin`.

#### Scenario: Owner assigns their network to a team they belong to
- GIVEN Alice (role=user) owns `"Net-A"` and is a member of `"Team-X"`
- WHEN Alice calls `PATCH /api/v1/networks/{net_a_id}/` with `{"team": <team_x_id>}`
- THEN `"Net-A"` is associated with `"Team-X"` and all team members can see it

#### Scenario: Owner cannot assign to a team they do not belong to
- GIVEN Alice (role=user) owns `"Net-A"` and is NOT a member of `"Team-Y"`
- WHEN Alice calls `PATCH /api/v1/networks/{net_a_id}/` with `{"team": <team_y_id>}`
- THEN a 400 response is returned and the assignment is not made

#### Scenario: Power user assigns any network to any team
- GIVEN Bob owns `"Net-C"` and `"Team-Z"` exists
- WHEN a `power_user` calls `PATCH /api/v1/networks/{net_c_id}/` with `{"team": <team_z_id>}`
- THEN a 200 response is returned and `"Net-C"` is associated with `"Team-Z"`

#### Scenario: Unassigning a team
- GIVEN `"Net-A"` is assigned to `"Team-X"`
- WHEN the owner, a power_user, or an admin calls
  `PATCH /api/v1/networks/{net_a_id}/` with `{"team": null}`
- THEN a 200 response is returned and `"Net-A"` has no team

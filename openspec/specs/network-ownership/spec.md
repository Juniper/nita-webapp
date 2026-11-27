# Network Ownership Specification

## Purpose
Per-user and per-team ownership and visibility scoping of CampusNetwork.

## Requirements

### Requirement: Network Owner Assignment on Creation
The system SHALL automatically set `owner=request.user` on a `CampusNetwork`
when it is created via `POST /api/v1/networks/`. Any authenticated user MAY
create a network.

#### Scenario: Network created by user is owned by that user
- GIVEN a logged-in user with `role=user`
- WHEN `POST /api/v1/networks/` is called with valid data
- THEN the created network has `owner` equal to the requesting user's id

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
The system SHALL allow `PATCH`/`PUT` on `/api/v1/networks/{id}/` and every
write sub-action of a network (hosts and workbook edit/upload/clear, action
trigger) for the network's owner, a member of the network's team, a
`power_user` or an `admin`. `DELETE /api/v1/networks/{id}/` and any write that
changes the `team` field SHALL be restricted to the owner, a `power_user` or an
`admin`.

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
- THEN the delete is accepted (a 202 response triggering the Jenkins delete job,
  not a 403 or 404) and the network row is removed once the job is queued

#### Scenario: Regular team member cannot modify a shared network
- GIVEN Alice (role=user) is a member of a team that has access to Bob's `"Net-C"`
- WHEN Alice calls `DELETE /api/v1/networks/{net_c_id}/`
- THEN a 403 response is returned and the network still exists
- AND the only modifications denied to her are deleting and changing `team`

#### Scenario: Regular team member can edit a shared network
- GIVEN Alice (role=user) is a member of a team that has access to Bob's `"Net-C"`
- WHEN Alice calls `PATCH /api/v1/networks/{net_c_id}/` with a new `description` or `host_file`, `POST …/workbook/save`, or `DELETE …/workbook/clear`
- THEN each call succeeds as it would for Bob

#### Scenario: Regular team member can trigger actions on a shared network
- GIVEN Alice (role=user) is a member of a team that has access to Bob's `"Net-C"`
- WHEN Alice calls `POST /api/v1/networks/{net_c_id}/trigger/{action_id}/`
- THEN a 202 response is returned and the history entry records `triggered_by_username: alice`

#### Scenario: Regular team member cannot re-share a network
- GIVEN Alice (role=user) is a member of `"Team-X"` and of `"Team-Y"`, and Bob's `"Net-C"` is shared with `"Team-X"`
- WHEN Alice calls `PATCH /api/v1/networks/{net_c_id}/` with `{"team": <team_y_id>}` or `{"team": null}`
- THEN a 403 response is returned and the network stays shared with `"Team-X"`

#### Scenario: Non-member regular user still has no access
- GIVEN Carl (role=user) is in no team that has access to Bob's `"Net-C"`
- WHEN Carl calls `PATCH`, `POST …/trigger/…` or `DELETE` on `/api/v1/networks/{net_c_id}/`
- THEN a 404 response is returned

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

### Requirement: Action History Visibility Scoping
Action-history visibility SHALL derive from network visibility. The system SHALL
scope `GET /api/v1/action-history/` and `/{id}/` (incl. `/console/`, `/stream/`,
`/robot-summary/`) so a user sees only entries whose `campus_network_id` is a
network visible to them under Network Visibility Scoping:

- own networks (`campus_network_id__owner=request.user`)
- their teams' networks (`campus_network_id__team__members=request.user`)
- all entries if `role=admin` OR `role=power_user`

#### Scenario: User sees history only for their own networks
- GIVEN Alice (role=user) owns `"Net-A"` and Bob owns `"Net-C"`
- AND both networks have action-history entries
- WHEN Alice calls `GET /api/v1/action-history/`
- THEN only entries for `"Net-A"` are returned

#### Scenario: User sees history for team-shared networks
- GIVEN Alice is a member of `"Team-X"` which has network `"Shared-Net"` owned by
  Bob, and `"Shared-Net"` has action-history entries
- WHEN Alice calls `GET /api/v1/action-history/`
- THEN entries for `"Shared-Net"` appear in Alice's results

#### Scenario: User cannot retrieve another user's history entry directly
- GIVEN Bob owns `"Net-C"` with an action-history entry, and Alice is not in
  Bob's team
- WHEN Alice (role=user) calls `GET /api/v1/action-history/{entry_id}/`
- THEN a 404 response is returned

#### Scenario: Power user sees all action history
- GIVEN action-history entries exist for networks owned by several users
- WHEN a `power_user` calls `GET /api/v1/action-history/`
- THEN all entries are returned regardless of owner or team

#### Scenario: Admin sees all action history
- GIVEN action-history entries exist for networks owned by several users
- WHEN an admin calls `GET /api/v1/action-history/`
- THEN all entries are returned

#### Scenario: Team membership does not duplicate rows
- GIVEN Alice is a member of `"Team-X"` which has three other members and one
  network with a single action-history entry
- WHEN Alice calls `GET /api/v1/action-history/`
- THEN that entry appears exactly once

### Requirement: Action History Networks Are a Subset of Visible Networks
For any user, the set of networks represented in their action-history results
SHALL be a subset of the networks returned by `GET /api/v1/networks/` for that
same user.

#### Scenario: Action history never reveals an unlisted network
- GIVEN any logged-in user
- WHEN the user calls `GET /api/v1/action-history/` and `GET /api/v1/networks/`
- THEN every `campus_network_id` in the action-history results is among the
  networks returned by `GET /api/v1/networks/`

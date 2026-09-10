## ADDED Requirements

### Requirement: Action History Visibility Scoping
Action-history visibility SHALL derive from network visibility. The system SHALL
scope `GET /api/v1/action-history/` and `GET /api/v1/action-history/{id}/`
(including the `/console/`, `/stream/` and `/robot-summary/` sub-routes) so that
a requesting user sees only entries whose `campus_network_id` refers to a network
that user may see under the Network Visibility Scoping requirement:

- Entries for networks they own (`campus_network_id__owner=request.user`)
- Entries for networks belonging to a team they are a member of
  (`campus_network_id__team__members=request.user`)
- All entries if `role=admin` OR `role=power_user`

For any user, the set of networks represented in their action-history results
SHALL be a subset of the networks returned by `GET /api/v1/networks/` for that
same user.

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

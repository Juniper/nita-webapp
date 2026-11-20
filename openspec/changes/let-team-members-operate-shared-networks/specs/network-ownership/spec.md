## MODIFIED Requirements

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

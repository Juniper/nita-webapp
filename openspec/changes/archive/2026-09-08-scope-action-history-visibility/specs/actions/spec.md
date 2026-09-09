## MODIFIED Requirements

### Requirement: Action History
The system SHALL record every triggered action and make the history available
via GET /api/v1/action-history/.
The list endpoint SHALL accept both `?campus_network_id=<id>` and
`?action_category_id=<id>` as independent, combinable query parameters.

The endpoint SHALL be scoped to the networks visible to the requesting user, as
defined by the Action History Visibility Scoping requirement in the
`network-ownership` capability. The query parameters SHALL narrow the scoped
result set and SHALL NOT widen it: requesting `?campus_network_id=<id>` for a
network the caller cannot see SHALL return an empty result set.

Because the detail routes resolve through the same queryset,
`GET /api/v1/action-history/{id}/` and its sub-routes (`/console/`, `/stream/`,
`/robot-summary/`) SHALL return `404` for an entry outside the caller's scope.

#### Scenario: History entry created on trigger
- GIVEN a successful trigger call
- WHEN GET /api/v1/action-history/{action_history_id}/ is called
- THEN an entry exists with status, timestamp, and jenkins_job_build_no

#### Scenario: Filter history by network
- GIVEN action history entries for multiple networks visible to the caller
- WHEN GET /api/v1/action-history/?campus_network_id=<id> is called
- THEN only entries for that network are returned

#### Scenario: Filter history by action category
- GIVEN action history entries with different categories exist
- WHEN GET /api/v1/action-history/?action_category_id=<id> is called
- THEN only entries belonging to that action category are returned

#### Scenario: Combined history filter
- GIVEN action history for multiple networks and categories
- WHEN GET /api/v1/action-history/?campus_network_id=<id>&action_category_id=<id> is called
- THEN only entries matching both network and category are returned

#### Scenario: Network filter cannot widen the scope
- GIVEN a user with `role=user` and a network `"Net-C"` they neither own nor
  share through a team
- WHEN GET /api/v1/action-history/?campus_network_id=<net_c_id> is called
- THEN a 200 response is returned with an empty result set

#### Scenario: Out-of-scope detail lookup returns 404
- GIVEN an action-history entry belonging to a network the caller cannot see
- WHEN GET /api/v1/action-history/{id}/ is called
- THEN a 404 response is returned

#### Scenario: Out-of-scope console and stream return 404
- GIVEN an action-history entry belonging to a network the caller cannot see
- WHEN GET /api/v1/action-history/{id}/console/,
  GET /api/v1/action-history/{id}/stream/, or
  GET /api/v1/action-history/{id}/robot-summary/ is called
- THEN a 404 response is returned
- AND no Jenkins console output is disclosed

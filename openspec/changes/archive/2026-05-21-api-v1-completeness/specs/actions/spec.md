## MODIFIED Requirements

### Requirement: List Actions
The system SHALL return a paginated list of actions via GET /api/v1/actions/.
The list endpoint SHALL accept both `?campus_type_id=<id>` and `?action_category_id=<id>`
as independent, combinable query parameters to filter results.

#### Scenario: Filter by campus type
- GIVEN actions for multiple network types exist
- WHEN GET /api/v1/actions/?campus_type_id=<id> is called
- THEN only actions belonging to that network type are returned

#### Scenario: Filter by action category
- GIVEN actions with different categories (e.g. BUILD, TEST) exist
- WHEN GET /api/v1/actions/?action_category_id=<id> is called
- THEN only actions belonging to that category are returned

#### Scenario: Combined filter
- GIVEN actions belonging to multiple types and categories exist
- WHEN GET /api/v1/actions/?campus_type_id=<id>&action_category_id=<id> is called
- THEN only actions matching both filters are returned

#### Scenario: No filter returns all
- GIVEN actions are registered for one or more network types
- WHEN GET /api/v1/actions/ is called with no query parameters
- THEN a 200 paginated response with all actions is returned

### Requirement: Action History
The system SHALL record every triggered action and make the history available
via GET /api/v1/action-history/.
The list endpoint SHALL accept both `?campus_network_id=<id>` and
`?action_category_id=<id>` as independent, combinable query parameters.

#### Scenario: History entry created on trigger
- GIVEN a successful trigger call
- WHEN GET /api/v1/action-history/{action_history_id}/ is called
- THEN an entry exists with status, timestamp, and jenkins_job_build_no

#### Scenario: Filter history by network
- GIVEN action history entries for multiple networks
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

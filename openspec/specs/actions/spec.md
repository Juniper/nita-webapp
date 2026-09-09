# Actions Specification

## Purpose
Actions represent Jenkins jobs associated with a network type. They define what
can be triggered (Build, Test, etc.) and which category (BUILD or TEST) they
belong to.

## Requirements

### Requirement: List Actions
The system SHALL return a paginated list of actions via GET /api/v1/actions/.
The list endpoint SHALL accept both `?campus_type_id=<id>` and `?action_category_id=<id>`
as independent, combinable query parameters to filter results.

#### Scenario: List all actions
- GIVEN actions are registered for one or more network types
- WHEN GET /api/v1/actions/ is called with no query parameters
- THEN a 200 paginated response with all actions is returned

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

### Requirement: Retrieve an Action
The system SHALL return full action detail including nested action_property and
action_category via GET /api/v1/actions/{id}/.

#### Scenario: Retrieve includes nested objects
- GIVEN an action with an associated ActionProperty and ActionCategory
- WHEN GET /api/v1/actions/{id}/ is called
- THEN the response includes `action_property` and `action_category` objects

### Requirement: Action Categories
The system SHALL maintain a read-only list of action categories (BUILD, TEST)
accessible via GET /api/v1/action-categories/.

#### Scenario: Categories include BUILD and TEST
- GIVEN a fresh NITA installation
- WHEN GET /api/v1/action-categories/ is called
- THEN the results include categories named BUILD and TEST

### Requirement: Trigger an Action
The system SHALL queue a Jenkins job for a given network and action via
POST /api/v1/networks/{id}/trigger/{action_id}/.

The `ActionHistory` entry created by a successful trigger SHALL record the
username of the requesting user in `triggered_by_username`, captured at trigger
time.

#### Scenario: Trigger succeeds
- GIVEN a network with workbook data and a valid action id
- WHEN POST /api/v1/networks/{id}/trigger/{action_id}/ is called
- THEN a 202 Accepted response is returned with `status: accepted`
  and `action_history_id`

#### Scenario: Trigger records the acting user
- GIVEN a user `"alice"` with access to a network with workbook data
- WHEN alice calls POST /api/v1/networks/{id}/trigger/{action_id}/
- THEN the created action-history entry has
  `triggered_by_username` equal to `"alice"`

#### Scenario: Each trigger records its own actor
- GIVEN users `"alice"` and `"bob"` who both have access to the same network
- WHEN alice triggers an action and then bob triggers an action on that network
- THEN the two action-history entries record `"alice"` and `"bob"` respectively

#### Scenario: No workbook data
- GIVEN a network with no workbook data uploaded
- WHEN the trigger endpoint is called
- THEN a 409 Conflict response is returned

#### Scenario: Unknown action
- GIVEN an action id that does not exist
- WHEN the trigger endpoint is called
- THEN a 404 Not Found response is returned

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

### Requirement: Action History Records the Triggering User
Each `ActionHistory` entry SHALL carry a `triggered_by_username` field holding
the username of the user who triggered the run. The field SHALL be a durable
string snapshot taken at trigger time, not a reference to a user record, so that
the attribution survives renaming or deletion of that user.

The field SHALL be exposed as a read-only string on
`GET /api/v1/action-history/` and `GET /api/v1/action-history/{id}/`. Entries
created before this field existed SHALL carry the empty string, and the presence
of action-history entries SHALL NOT prevent deletion of a user.

#### Scenario: Field is exposed by the API
- GIVEN an action-history entry created by user `"alice"`
- WHEN a client fetches GET /api/v1/action-history/
- THEN that entry includes `triggered_by_username` equal to `"alice"`

#### Scenario: Attribution survives a username change
- GIVEN an action-history entry recorded for user `"alice"`
- WHEN that user is renamed to `"alice.smith"`
- THEN the existing entry still reports `triggered_by_username` as `"alice"`

#### Scenario: Attribution survives deletion of the user
- GIVEN an action-history entry recorded for user `"alice"`
- WHEN the user `"alice"` is deleted
- THEN the deletion is not blocked by the action-history entry
- AND the entry still reports `triggered_by_username` as `"alice"`

#### Scenario: Pre-existing entries have no actor
- GIVEN an action-history entry created before this field was introduced
- WHEN a client fetches that entry
- THEN `triggered_by_username` is the empty string

### Requirement: Action History Reflects Terminal Jenkins State
The system SHALL persist action-history status as a terminal value after the Jenkins build completes.

#### Scenario: Running entry transitions to Success
- GIVEN an action-history entry with `status = Running`
- AND the corresponding Jenkins build has `building = false` and `result = SUCCESS`
- WHEN the status synchronization loop runs
- THEN the entry status is updated to `Success`

#### Scenario: Running entry transitions to Failed
- GIVEN an action-history entry with `status = Running`
- AND the corresponding Jenkins build has `building = false` and `result = FAILURE`
- WHEN the status synchronization loop runs
- THEN the entry status is updated to `Failure` or `Failed` per existing mapping

#### Scenario: Build still in progress
- GIVEN an action-history entry with `status = Running`
- AND the Jenkins build result is not yet available
- WHEN the status synchronization loop runs
- THEN the entry remains `Running`

### Requirement: Action History Sync Uses Canonical Jenkins Base URL
All action-history status synchronization calls to Jenkins SHALL use the canonical internal Jenkins base URL including the `/jenkins` context path.

#### Scenario: Prefixed Jenkins path is used for status lookups
- GIVEN Jenkins is served internally under `/jenkins`
- WHEN the ActionHistory status updater fetches build info
- THEN it queries Jenkins through the canonical prefixed base URL
- AND completed builds are resolvable by job name and build number

### Requirement: Jenkins Console Log Proxy
The system SHALL proxy the Jenkins build console output for a history entry via
GET /api/v1/action-history/{id}/console/.

#### Scenario: Console log returned
- GIVEN a completed Jenkins build
- WHEN GET /api/v1/action-history/{id}/console/ is called
- THEN a 200 response with a `console` string containing the build output is returned
- AND ANSI escape codes are stripped from the output

#### Scenario: Build queued or log unavailable
- GIVEN a Jenkins build that is still queued
- WHEN GET /api/v1/action-history/{id}/console/ is called
- THEN a 200 response is returned with a message indicating log is not yet available

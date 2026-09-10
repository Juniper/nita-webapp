## MODIFIED Requirements

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

## ADDED Requirements

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

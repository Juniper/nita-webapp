## MODIFIED Requirements

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

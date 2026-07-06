## ADDED Requirements

### Requirement: Action-history Robot Framework summary endpoint
The system SHALL expose `GET /api/v1/action-history/{id}/robot-summary/`, an authenticated endpoint that returns the Robot Framework result totals for the run's Jenkins build. The response SHALL include `available` (boolean) and, when available, `total`, `passed`, `failed`, `skipped`, and `pass_percentage`. The totals SHALL be sourced from the Jenkins Robot Framework plugin's per-build summary (`overallTotal`/`overallPassed`/`overallFailed`/`overallSkipped`/`passPercentage`). When the build has no Robot results or Jenkins is unreachable, the endpoint SHALL return `{ "available": false }`.

#### Scenario: Summary available for a TEST build
- **WHEN** an authenticated client requests `GET /api/v1/action-history/{id}/robot-summary/` for a run whose Jenkins build has Robot results
- **THEN** the response is `{ available: true, total, passed, failed, skipped, pass_percentage }` reflecting the build's Robot totals

#### Scenario: Summary unavailable
- **WHEN** the run's build has no Robot results or Jenkins is unreachable
- **THEN** the response is `{ available: false }`

### Requirement: History tab shows inline TEST result summary
For each History tab row in the **TEST** category, the network detail page SHALL fetch the run's Robot summary and, when available, display it inline as `Total N · Passed P · Failed F · Skipped S · Pass X%`. Rows in other categories SHALL NOT show a Robot summary.

#### Scenario: TEST row shows the inline summary
- **WHEN** the user opens the History tab and a TEST-category run has Robot results
- **THEN** that row shows an inline `Total / Passed / Failed / Skipped / Pass %` summary

#### Scenario: Non-TEST rows have no summary
- **WHEN** a history row is not in the TEST category
- **THEN** no Robot summary is shown for that row

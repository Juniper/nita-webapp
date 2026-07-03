## Why

TEST-category actions run Robot Framework suites via Jenkins. Today the History
tab only shows a run's status (Success/Failure) and a link to the Jenkins build;
to see how many tests passed or failed the user must open Jenkins and read the
Robot report. Surfacing the headline Robot totals inline — Total, Passed, Failed,
Skipped, and Pass % — gives an at-a-glance result without leaving the app.

The Jenkins Robot Framework plugin already exposes these totals per build at
`/job/{job}/{build}/robot/api/json` (`overallTotal`, `overallPassed`,
`overallFailed`, `overallSkipped`, `passPercentage`), so no test re-parsing is
needed — the backend just relays the plugin's summary.

## What Changes

- Add a backend endpoint `GET /api/v1/action-history/{id}/robot-summary/` that
  returns the Robot Framework result totals for the run's Jenkins build:
  `{ available, total, passed, failed, skipped, pass_percentage }`. When the
  build has no Robot results (e.g. a non-TEST run or the plugin has no data), it
  returns `{ available: false }`.
- The History tab SHALL, for each **TEST** category row, fetch this summary and
  display it inline as `Total N · Passed P · Failed F · Skipped S · Pass X%`.
- `openapi.yaml` SHALL be regenerated to include the new endpoint.

## Capabilities

### Modified Capabilities
- `spa-networks`: The action-history viewer shows an inline Robot Framework
  result summary for TEST-category runs, backed by a new action-history
  robot-summary endpoint.

## Impact

- **Backend**: `ngcn/jenkins_jobs.py` (new `robot_summary(job, build)` helper),
  `ngcn/api/views.py` (`ActionHistoryViewSet` gains a `robot-summary` action).
  `openapi.yaml` regenerated.
- **Frontend**: `frontend/src/pages/NetworkDetailPage.tsx` (History rows fetch
  and render the inline TEST summary).
- **No DB/model changes**; the summary is relayed live from Jenkins.

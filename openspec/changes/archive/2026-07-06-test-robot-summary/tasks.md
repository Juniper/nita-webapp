## 1. Backend: Robot summary helper + endpoint

- [x] 1.1 Add `robot_summary(job_name, build_no)` to `ngcn/jenkins_jobs.py` that
  fetches `{JENKINS}/job/{job}/{build}/robot/api/json` with the configured
  Jenkins credentials and returns a normalized dict
  `{total, passed, failed, skipped, pass_percentage}` or `None` when
  unavailable.
- [x] 1.2 Add a `robot-summary` detail action to `ActionHistoryViewSet` that
  returns `{available: false}` when the helper returns `None`, else
  `{available: true, ...summary}`.

## 2. API schema

- [x] 2.1 Regenerate `openapi.yaml` from the built image so the new endpoint is
  documented and the drift test passes.

## 3. Frontend: inline TEST summary

- [x] 3.1 In `frontend/src/pages/NetworkDetailPage.tsx`, after history loads,
  fetch `/api/v1/action-history/{id}/robot-summary/` for each `TEST` row and
  store results by id.
- [x] 3.2 Render an inline `Total N · Passed P · Failed F · Skipped S · Pass X%`
  line for TEST rows when the summary is available.

## 4. Verify

- [x] 4.1 Build and deploy; confirm the endpoint returns Robot totals for a TEST
  build and `{available:false}` for a non-TEST build.
- [x] 4.2 Confirm the History tab shows the inline summary for TEST rows.

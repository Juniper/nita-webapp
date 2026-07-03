## Context

TEST-category action runs execute Robot Framework suites in Jenkins. The Jenkins
Robot Framework plugin publishes per-build totals at
`GET {JENKINS}/job/{job}/{build}/robot/api/json`:

```json
{ "overallTotal": 140, "overallPassed": 119, "overallFailed": 21,
  "overallSkipped": 0, "passPercentage": 85.0 }
```

The History tab already knows each run's Jenkins job name (`jenkins_job_name`)
and build number (`jenkins_job_build_no`).

## Decisions

### Relay the plugin summary via a dedicated endpoint

Add `GET /api/v1/action-history/{id}/robot-summary/`. It computes the run's job
name + build number, fetches the Robot plugin JSON with the configured Jenkins
credentials, and returns a normalized shape:

```json
{ "available": true, "total": 140, "passed": 119, "failed": 21,
  "skipped": 0, "pass_percentage": 85.0 }
```

If the build has no Robot data or Jenkins is unreachable, it returns
`{ "available": false }` (HTTP 200) so the frontend can simply omit the summary.
A per-row, on-demand endpoint keeps the list payload cheap (no Jenkins call
during list serialization) and only fetches Robot data for TEST rows.

### `pass_percentage` fallback

Prefer the plugin's `passPercentage`; if absent, compute
`round(passed/total*100, 1)` (0 when total is 0).

### Frontend rendering

For rows where `category_name === 'TEST'`, the History tab fetches the summary
lazily and, when `available`, renders an inline muted line
`Total N · Passed P · Failed F · Skipped S · Pass X%` under the action name.

## Alternatives Considered

- **Embed the summary in the action-history list serializer**: rejected — would
  issue a Jenkins call per row on every list fetch, slowing the History tab and
  coupling list latency to Jenkins availability.
- **Parse Robot output.xml ourselves**: rejected — the plugin already computes
  and exposes the totals.

## Risks

- Robot totals depend on the Jenkins Robot plugin having archived results for the
  build; older/aborted builds may return `available: false` (handled by omission).

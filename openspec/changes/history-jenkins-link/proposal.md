## Why

The network detail **History** tab lists each triggered action run with a View
button that streams the run's console. Like the Actions tab (which now links each
action to its Jenkins job), the History tab should let the user jump straight to
the **specific build result** in Jenkins for a given run, to inspect artifacts,
parameters, or the full build page.

Each history row already knows its build number (`jenkins_job_build_no`), but the
API does not expose the Jenkins **job name** for the row (it only returns
`action_id`, `action_name`, `network_name`). The job name is
`{action.jenkins_url}-{network_name}` — the same value the backend computes for
console streaming. Exposing it as a read-only field lets the SPA build a direct
link to `/jenkins/job/{job_name}/{build_no}/`.

## What Changes

- The action-history API SHALL expose a read-only `jenkins_job_name` field equal
  to `{action.jenkins_url}-{network_name}`, alongside the existing computed
  `action_name`/`category_name`/`network_name` fields.
- Each History tab row SHALL show a **Jenkins** link that opens the run's Jenkins
  build result `/jenkins/job/{jenkins_job_name}/{jenkins_job_build_no}/` in a new
  tab (falling back to the job page when no build number is present).
- `openapi.yaml` SHALL be regenerated to include the new field.

The Jenkins reverse-proxy route (`/jenkins/`) added by the `action-jenkins-link`
change is reused; no proxy change is needed.

## Capabilities

### Modified Capabilities
- `spa-networks`: The action-history viewer gains a per-row link to the run's
  Jenkins build result. The action-history API gains a `jenkins_job_name` field.

## Impact

- **Backend**: `ngcn/api/serializers.py` (`ActionHistorySerializer` gains a
  `jenkins_job_name` computed field). `openapi.yaml` regenerated.
- **Frontend**: `frontend/src/pages/NetworkDetailPage.tsx` (History row adds a
  Jenkins build link; `ActionHistory` type gains `jenkins_job_name`).
- **No new endpoints, no DB/model changes** (the field is derived from existing
  relations).

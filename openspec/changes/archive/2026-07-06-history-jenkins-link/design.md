## Context

The History tab renders `ActionHistory` rows. Each row has `action_id`,
`action_name`, `category_name`, `network_name`, `status`, `timestamp`, and
`jenkins_job_build_no`. The Jenkins job for a run is
`{action.jenkins_url}-{network_name}`, but `jenkins_url` is not exposed on the
history payload, so the SPA cannot build the job URL from history data alone.

## Decisions

### Expose `jenkins_job_name` on the serializer

Add a read-only computed field `jenkins_job_name` to `ActionHistorySerializer`
returning `{action_id.jenkins_url}-{campus_network_id.name}` — the exact job name
the backend already derives for console streaming. This mirrors the existing
computed fields (`action_name`, `network_name`) and keeps the history row
self-describing, avoiding a frontend cross-reference against the actions list.

### Link to the specific build result

The History row links to `/jenkins/job/{jenkins_job_name}/{jenkins_job_build_no}/`
(the specific build), reusing the `/jenkins/` reverse-proxy route. When a row has
no build number, link to the job page `/jenkins/job/{jenkins_job_name}/` instead.

### Keep openapi.yaml in sync

Because a serializer field changes the generated schema (enforced by the drift
test), regenerate `openapi.yaml` via `manage.py spectacular` from the built image
so the committed schema matches.

## Alternatives Considered

- **Frontend maps `action_id` → `jenkins_url` via the actions list**: rejected —
  couples the History tab to the Actions data and breaks for history whose action
  was later removed; the computed field is simpler and canonical.

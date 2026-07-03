## ADDED Requirements

### Requirement: Action-history exposes the Jenkins job name
The action-history API (`GET /api/v1/action-history/`) SHALL include a read-only `jenkins_job_name` field for each entry equal to `{action.jenkins_url}-{network_name}`, so consumers can construct the Jenkins job/build URL without additional lookups.

#### Scenario: History entry includes the Jenkins job name
- **WHEN** a client fetches `GET /api/v1/action-history/`
- **THEN** each entry includes `jenkins_job_name` equal to the action's `jenkins_url` joined to the network name with a hyphen

### Requirement: Action-history Jenkins build link
Each row of the network detail History tab SHALL show a link that opens the run's Jenkins build result in a new browser tab, targeting `/jenkins/job/{jenkins_job_name}/{jenkins_job_build_no}/`. When a row has no build number, the link SHALL target the job page `/jenkins/job/{jenkins_job_name}/`. The link SHALL open with `rel="noopener"` and SHALL not interfere with the existing View (console) action.

#### Scenario: History row shows a Jenkins build link
- **WHEN** the user opens the History tab for a network with at least one run
- **THEN** each run row shows a Jenkins link alongside its View button
- **AND** the link points to `/jenkins/job/{jenkins_job_name}/{jenkins_job_build_no}/` and opens in a new tab

#### Scenario: Link is routed by the proxy to Jenkins
- **WHEN** the user activates a history row's Jenkins link
- **THEN** the request to `/jenkins/` is routed by the reverse proxy to the Jenkins service (not the SPA)

## 1. Backend: expose the Jenkins job name

- [x] 1.1 Add a read-only `jenkins_job_name` `SerializerMethodField` to
  `ActionHistorySerializer` returning
  `{action_id.jenkins_url}-{campus_network_id.name}`.

## 2. Frontend: per-row Jenkins build link

- [x] 2.1 Add `jenkins_job_name: string` to the `ActionHistory` type in
  `frontend/src/pages/NetworkDetailPage.tsx`.
- [x] 2.2 In the History tab row, add a Jenkins link next to View targeting
  `/jenkins/job/{jenkins_job_name}/{jenkins_job_build_no}/` (or the job page when
  no build number), `target="_blank"` + `rel="noopener noreferrer"`.

## 3. Keep the API schema in sync

- [x] 3.1 Regenerate `openapi.yaml` from the built image via
  `manage.py spectacular` so the drift test passes.

## 4. Verify

- [x] 4.1 Build and deploy; confirm `GET /api/v1/action-history/` returns
  `jenkins_job_name`.
- [x] 4.2 Confirm each History row shows a Jenkins link with the correct
  `/jenkins/job/<job>/<build>/` href that resolves to the Jenkins build page.

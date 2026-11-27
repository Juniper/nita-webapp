## 1. Forward-auth endpoint

- [x] 1.1 Add `forward_auth_view` (`GET /api/v1/auth/forward/`) with
      `LabSessionAuthentication` only; return `200` with
      `X-Forwarded-User` / `X-Forwarded-Groups` on success and a `302` safe
      login redirect otherwise; make no database writes; document with
      `extend_schema`
- [x] 1.2 Register the route in `ngcn/api/urls.py` alongside the other `auth/` routes
- [x] 1.3 Tests: authenticated session → 200 + identity and team headers; no
      session → 302 with no identity headers; unsafe return target is replaced;
      valid token without session is denied despite global `TokenAuthentication`
      being enabled; endpoint performs no database writes
- [x] 1.4 Regenerate `openapi.yaml` and confirm `test_openapi_drift.py` passes

## 2. Proxy integration

- [x] 2.1 Define the forward-auth response contract consumed by
      `migrate-proxy-to-traefik`; use the session cookie and original Jenkins
      URI, not a proxy-side cookie-presence check
- [x] 2.2 Ensure Traefik forwards only the authenticated identity/group response
      headers, strips client `Authorization` and identity headers, and fails
      closed when forward-auth is unavailable
- [x] 2.3 Verify denied browser requests return a 302 to login with a safe,
      URL-encoded Jenkins return path
- [x] 2.4 Verify the Compose and Kubernetes proxy integrations against the
      shared forward-auth contract

## 3. Login page `next` handling

- [x] 3.1 `LoginPage` reads `next` from the query string; after successful login navigates to it when it is a same-origin relative path (`/…`, not `//…`, no scheme), otherwise to `/`
- [x] 3.2 Tests in `LoginPage.test.tsx`: valid `next` is followed; `//evil`, `https://…`, and absent `next` all land on `/`
- [x] 3.3 `npm run lint` and `npm test` pass
- [x] 3.4 `AppLayout` sidebar gains a trailing `Jenkins ↗` anchor to `/jenkins/` (new tab, `noopener noreferrer`), after Teams / User Management, styled like the other entries; tests in `AppLayout.test.tsx` cover href/target/rel and ordering

## 4. Authenticated console stream

- [x] 4.1 Extract the Jenkins identity header construction from `robot_summary` into a module-private helper in `jenkins_jobs.py` (backed by `jenkins_config.jenkins_identity_headers`)
- [x] 4.2 Use the helper in `progressive_text_events` so every `progressiveText` request carries `X-Forwarded-User`
- [x] 4.3 Test in `test_api_streaming.py`: the request passed to
      `urllib.request.urlopen` has an `X-Forwarded-User` header and no
      `Authorization`; emitted console output strips ANSI escapes and Jenkins
      ConsoleNote markup; existing generator and view tests still pass

## 5. Identity propagation (build attribution)

- [x] 5.1 `invoke_job(..., *, initiated_by)` builds its jenkinsapi client with `X-Forwarded-User: <initiated_by>` so Jenkins records a `UserIdCause` for the webapp user; `_make_jenkins_server(acting_user=None)` and all python-jenkins callers (`networktypeparser`, `statusupdater`, `utils`) assert the service identity by header; no password is sent
- [x] 5.2 Action triggers pass `initiated_by=request.user` (identity + groups); network create/delete and network-type validation run `network_template_mgr` / `network_type_validator` as the service identity (`initiated_by=None`)
- [x] 5.3 Bootstrap scripts (`ping_jenkins.py`, `configure_jenkins.py`, `add_jenkins_job.py`) use `X-Forwarded-User` instead of Basic auth; `add_jenkins_job.py` pushes the shipped definition onto an already-existing job so upgrades take effect
- [x] 5.4 Traefik copies the forward-auth response's
      `X-Forwarded-User`/`X-Forwarded-Groups` to Jenkins and clears
      client-supplied identity and `Authorization` headers
- [x] 5.5 Tests: `invoke_job` asserts `initiated_by` (user + groups) via the
      requester session headers; management jobs run as service identity;
      `_make_jenkins_server` sets the header and no Basic auth;
      `jenkins_groups_for` = role + `team-<id>`; forward-auth emits
      `X-Forwarded-Groups`
- [x] 5.6 `network_template_mgr.xml`: replace the `jenkins-cli.jar -s http://user:pass@…` create-job/delete-job calls (401 under the header realm, and silently "SUCCESS") with crumb + `X-Forwarded-User` REST calls; drop the CLI-jar bootstrap; fail the build on HTTP errors
- [x] 5.8 Remove obsolete `JENKINS_PASS` defaults and passthroughs from the webapp image, Compose environment, and database-wait startup script.
- [x] 5.7 Per-network ACLs: `network_template_mgr` takes `owner` / `team_group`, renders an `AuthorizationMatrixProperty` (owner read/build/cancel, team read; team build/cancel later added by `let-team-members-operate-shared-networks`) into every generated job, and gains `operation=acl` to rewrite it on existing jobs; the webapp passes them on create and calls `jenkins_jobs.sync_network_acl` from `perform_update` (team change) and the user `transfer` endpoint; tests cover create params, team-change sync and no-op updates

## 6. Validation

- [x] 6.1 `pytest` green; `openspec validate gate-jenkins-behind-webapp-session --strict` passes
- [x] 6.2 End-to-end on the compose stack: log in → open a network → "Jenkins ↗" opens the job page; log out → same link redirects to login and returns to the job page after signing in; trigger an action → build page shows `Started by user <user>`; console stream and Robot summary still render
  - Verified in a headless browser on the Compose stack as a role-`user` owner: "Jenkins ↗" opened `/jenkins/job/build_e2e-<net>/` (`whoAmI` = owner, `[authenticated, user]`); after logout the link returned `302 /login?next=%2Fjenkins%2Fjob%2Fbuild_e2e-<net>%2F` and signing in returned to the job page; a UI-triggered build showed `Started by user <owner>`; the live console and the history viewer rendered `Finished: SUCCESS`; the history showed `Total 4 · Passed 3 · Failed 1 · Skipped 0 · Pass 75%`.
- [x] 6.3 Update `README.md` release notes
- [x] 6.4 Live on Kubernetes: session `whoAmI` returns the webapp user and role; spoofed identity headers are overridden; webapp-triggered build records `UserIdCause` for the webapp user; password Basic auth to Jenkins is rejected
- [x] 6.5 Live on Kubernetes: network create → `network_template_mgr` creates the three per-network jobs via REST (build log shows `Jenkins POST /createItem?name=… -> 200`); trigger from the network page → `Started by user <owner>`
- [x] 6.6 Live on Kubernetes (isolation): owner sees/builds own jobs;
      unrelated `user` gets 404 on others' jobs and management jobs;
      `power_user`/`admin` see all; header spoofing is ignored; removing a team
      member revokes access on the next request; `operation=acl` back-filled
      existing networks. Team-member build permission is covered by
      `test_team_member_can_trigger_shared_network` after
      `let-team-members-operate-shared-networks`.

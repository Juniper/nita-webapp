## Why

The Jenkins UI is reverse-proxied at `https://<host>/jenkins/` so the SPA can
deep-link to a job or build page. Nothing in front of that route checks who the
caller is. Combined with the Jenkins-side defaults (anonymous `Job/Build` and
`Job/Cancel`, CSRF disabled — being removed in the companion `nita-jenkins`
change), anyone who can reach the NITA host can browse every job, read every
console log, and start or abort builds without ever logging into the webapp.

The webapp already has the identity and the permission model: session login,
three roles, network ownership and team scoping. Jenkins should sit *behind*
that identity, not beside it. The first step — this change — is to make the
Jenkins route available only to callers who hold a valid webapp session, and to
close the one remaining place where the webapp itself still relies on Jenkins
being anonymous-readable.

Two facts shape the design:

- **The reverse proxy will change.** nginx is slated to be replaced by Traefik.
  Both support the same pattern — ask an external endpoint "is this request
  authenticated?" before forwarding (`auth_request` in nginx, `forwardAuth` in
  Traefik) — so the authentication contract must live in Django, not in proxy
  configuration.
- **Not every Django→Jenkins call is authenticated yet.** `invoke_job`,
  `robot_summary`, the status updater and the lifecycle history all send
  credentials. The live console stream in `progressive_text_events` does not:
  it issues a bare `urllib` request and works only because anonymous
  `Job/Read` is currently granted. Once Jenkins is tightened, that stream must
  carry credentials too.

## What Changes

- **Forward-auth endpoint.** A new `GET /api/v1/auth/forward/` using
  `LabSessionAuthentication` only, answering `200` with an empty body for a
  request carrying a valid webapp session and
  `401`/`403` otherwise. On success it also sets `X-Auth-User` and
  `X-Auth-Role` response headers describing the caller. This is the contract a
  reverse proxy consults before forwarding a request to Jenkins; it is
  proxy-agnostic by construction.
- **nginx gates `/jenkins/` on that endpoint.** The `location /jenkins/` block
  gains an `auth_request` sub-request to the forward-auth endpoint. A denial
  redirects the browser to `/login?next=<original path>` instead of showing a
  bare error. The webapp's own `/api/v1/` routes are unaffected.
- **Login page honours `?next=`.** After a successful login the SPA navigates
  to the `next` query parameter when it is a same-origin relative path, and to
  `/` otherwise. This completes the round-trip from a gated Jenkins deep link.
- **Sidebar shortcut to Jenkins.** The sidebar ends with a `Jenkins ↗` entry
  (after User Management) opening `/jenkins/` in a new tab, so the Jenkins home
  is one click away now that a webapp session is also a Jenkins session.
- **The SSE console stream authenticates to Jenkins.** `progressive_text_events`
  asserts the service identity by header, like `robot_summary`.
  No API shape change; the stream behaves identically from the SPA's view.
- **Builds record who asked for them.** Per-network action triggers assert the
  webapp user's identity and groups to Jenkins (`X-Forwarded-User` /
  `X-Forwarded-Groups`, trusted by Jenkins' Reverse Proxy Auth realm), so
  Jenkins records *Started by user <username>* instead of the service account.
  Management jobs (`network_template_mgr`, `network_type_validator`) run as the
  service identity. The proxy forwards the same identity for browser traffic,
  so a webapp session *is* the Jenkins session.
- **Jenkins access mirrors the webapp.** The groups header is the role plus one
  `team-<id>` per team. `network_template_mgr` writes a per-job matrix into
  every generated job (owner read/build/cancel, team read) and re-applies it
  (`operation=acl`) when the webapp changes a network's team or transfers
  ownership; admins administer, power users see everything, regular users see
  only their own and team-shared networks' jobs — exactly as in the webapp.

## Capabilities

### Modified Capabilities

- `auth`: adds the forward-auth endpoint used by the reverse proxy.
- `jenkins-reverse-proxy`: the `/jenkins/` route requires a valid webapp
  session and redirects unauthenticated browsers to the SPA login page.
- `jenkins-trigger-security`: *every* Django→Jenkins HTTP call asserts an
  identity by header (no password), explicitly including progressive console
  text and the Robot summary relay; builds are attributed to the triggering
  webapp user.
- `frontend-skeleton`: the login page redirects to a safe `next` target after
  success.
- `spa-layout`: the sidebar gains a trailing `Jenkins ↗` shortcut to the
  proxied Jenkins home.

## Impact

- **Backend:** one new view and URL; one header added in `jenkins_jobs.py`;
  one `initiated_by=` keyword threaded through `invoke_job` and its four callers
  (action trigger, network create, network delete, and network-type
  validation). The upload view passes the acting username into
  `NetworkTypeParser`. `openapi.yaml` is regenerated for the new endpoint.
- **Jenkins job template:** `network_template_mgr.xml` creates/deletes the
  per-network jobs through the REST API with the identity header instead of
  `jenkins-cli.jar` with a password (which the header realm rejects), and now
  fails the build when a job cannot be created or deleted.
- **Frontend:** `LoginPage` reads and validates `next`; `AppLayout` adds the
  sidebar `Jenkins ↗` anchor. No new dependencies.
- **Proxy:** `nginx/nginx.conf` gains an internal auth location, an
  `auth_request` directive in `location /jenkins/`, and a named location for
  the login redirect. The same file is what `nita/install.sh` publishes as the
  `proxy-config-cm` ConfigMap, so the k8s deployment picks it up on the next
  install/upgrade.
- **Operational:** every request under `/jenkins/` now costs one additional
  sub-request to Django (a session lookup). Jenkins pages load tens of assets,
  so this is noticeable but bounded; a short-lived cache keyed on the session
  cookie is a documented follow-up if it matters in practice.
- **Companion changes (separate repos, deploy together):**
  `nita-jenkins/revoke-anonymous-build-and-enable-csrf` removes the anonymous
  grants and re-enables CSRF; `nita/close-jenkins-direct-exposure` removes the
  host-port 8443 bypass and fixes the NetworkPolicy so the proxy pod may reach
  Jenkins. Deploy Jenkins hardening first, the NITA networking change second,
  and this session gate last. Until the gate is deployed, anonymous reads
  remain possible through the proxy, but anonymous build/cancel access has
  already been removed and the direct host-port route is closed.

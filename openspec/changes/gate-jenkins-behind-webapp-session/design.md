## Context

Jenkins reaches end users along two paths:

```
browser ──HTTPS──▶ nginx ──/jenkins/──▶ jenkins:8080/jenkins   (UI deep links)
browser ──HTTPS──▶ nginx ──/api/v1/──▶ webapp:8000 ──▶ jenkins:8080/jenkins   (everything else)
```

The second path is already authenticated end-to-end: the browser holds a
webapp session, Django checks permissions, and Django talks to Jenkins with
`JENKINS_SERVER_USER`/`JENKINS_SERVER_PASS` plus a CSRF crumb (the
`jenkins-trigger-security` capability). The first path has no check at all.

Relevant existing pieces:

- `me_view` (`GET /api/v1/auth/me/`) is a session-authenticated DRF view that
  already returns the caller's `username` and `role`. The forward-auth
  endpoint is a stripped-down sibling: same authentication, headers instead of
  a body, no serializer.
- `jenkins_jobs.robot_summary` already builds a Basic `Authorization` header
  from the configured credentials. `progressive_text_events` in the same module
  does not; it is the only Django→Jenkins HTTP call without one.
- `jenkins_jobs.invoke_job` wraps `jenkinsapi`'s `Job.invoke`. Its `cause`
  keyword is sent as a build *parameter* and only becomes a Jenkins cause when
  a job build-token is used; it does not attribute the build to a user.
- `LoginPage` navigates to `/` unconditionally after login.
- `nginx/nginx.conf` is the single proxy config; `nita/install.sh` downloads it
  from this repo and publishes it as a ConfigMap, so there is one place to
  change.

Constraints:

- The proxy is being replaced by Traefik later. Anything that only works in
  nginx is a liability.
- The per-job visibility model (owner/team) is explicitly *out of scope* here;
  it needs a Jenkins security-realm change and is planned as a follow-up wave.
  This change must not paint that follow-up into a corner.

## Goals / Non-Goals

**Goals**

- Only callers with a valid webapp session reach anything under `/jenkins/`.
- Unauthenticated browsers end up on the SPA login page and return to where
  they were going.
- Django never depends on Jenkins granting anything to `anonymous`.
- Jenkins build pages show which webapp user asked for a build.
- The authentication contract survives an nginx→Traefik swap unchanged.

**Non-Goals**

- Mapping webapp users to Jenkins identities or restricting which jobs a user
  can see inside Jenkins (next wave).
- Changing the Jenkins-side authorisation strategy (companion `nita-jenkins`
  change).
- Caching or rate-limiting the auth sub-request.
- Replacing the Jenkins deep links in the SPA (a sidebar shortcut to the Jenkins
  home is added; the per-job/per-build deep links are unchanged).

## Decisions

### Decision 1: The auth contract is a Django endpoint, not proxy config

**Choice:** `GET /api/v1/auth/forward/` uses `LabSessionAuthentication` only,
with `IsAuthenticated`. It returns `200` + an empty body on success with
`X-Auth-User: <username>` and `X-Auth-Role: <role>` response headers. It does
not use the global authentication-class list, which also enables
`TokenAuthentication`; a token without a webapp session must be denied. DRF's
default behaviour for an unauthenticated session request (`403`) is left as-is.

**Rationale:** nginx `auth_request` and Traefik `forwardAuth` both consume
exactly this shape — "2xx means forward, anything else means deny, optionally
copy some response headers onto the upstream request". Putting the decision in
Django means the proxy swap is a config rewrite, not a behaviour change, and it
means a single place to add logic later (e.g. role-based gating of the Jenkins
UI). The identity headers are emitted now even though nothing consumes them
yet: they cost nothing, they let an operator verify the gate from the proxy's
access log, and they are precisely what the next wave will forward to Jenkins.

**Rejected:** nginx-side checks on the `sessionid` cookie's presence (trivially
forged); a shared-secret header between nginx and Jenkins (does nothing for the
browser path); nginx `njs` scripting (nginx-specific).

### Decision 2: Deny → redirect to `/login?next=`

**Choice:** In `location /jenkins/`, `error_page 401 403 = @jenkins_login;`
where the named location returns `302 /login?next=$request_uri`.

**Rationale:** The people hitting this are humans following a link from the
SPA, or humans with a stale bookmark. A bare 403 page is a dead end; the login
page is where they need to be anyway. `$request_uri` keeps the full original
path and query so the redirect back lands on the intended job or build.

**Known rough edge (accepted):** nginx does not URL-encode `$request_uri` when
interpolating it. Jenkins paths are percent-encoded by the SPA already
(`encodeURIComponent` on the job name), so in practice the value is safe. If a
pathological URL breaks the round-trip the user simply lands on `/` after
login, which is the pre-existing behaviour.

### Decision 3: The auth sub-request is a dedicated internal location

**Choice:**

```nginx
location = /_auth/jenkins {
  internal;
  proxy_pass              http://webapp:8000/api/v1/auth/forward/;
  proxy_pass_request_body off;
  proxy_set_header        Content-Length "";
  proxy_set_header        X-Original-URI $request_uri;
}
```

**Rationale:** `auth_request` needs a location it can sub-request. Marking it
`internal` keeps it off the public surface. Dropping the body and
`Content-Length` is required by nginx for `auth_request` sub-requests, and the
original URI is handed to Django for logging. Cookies are inherited from the
original request automatically, which is how the session reaches Django.

### Decision 4: `next` is honoured only when it is a same-origin relative path

**Choice:** `LoginPage` accepts `next` if it starts with a single `/` and not
`//`, contains no scheme, and is otherwise used verbatim. Anything else falls
back to `/`.

**Rationale:** An unvalidated `next` is an open redirect. The rule above admits
every legitimate target (`/jenkins/job/x/`, `/networks/3`) and rejects
`//evil.example`, `https://evil.example`, and `javascript:` by construction.

### Decision 5: The console stream reuses the existing Basic-auth construction

**Choice:** Factor the `Authorization: Basic …` construction out of
`robot_summary` into a module-private helper and call it from both
`robot_summary` and `progressive_text_events`.

**Rationale:** Same credentials, same encoding, two call sites; a helper is the
smallest change that avoids a second copy. Behaviour of the stream — events,
ANSI stripping, timeouts, 404-while-queued tolerance — is untouched.

### Decision 6: Identity is propagated to Jenkins by header, not by cause text

**Choice:** Jenkins runs the Reverse Proxy Auth realm in header mode. The
webapp asserts an identity on every Jenkins call through `X-Forwarded-User`:
`invoke_job(..., initiated_by=username)` acts as the webapp user (so Jenkins
records a `UserIdCause`, *Started by user <username>*), and all service calls
(`_make_jenkins_server`, console/Robot relays, bootstrap scripts) act as the
`JENKINS_USER` service identity. nginx copies `X-Auth-User`/`X-Auth-Groups` from
the forward-auth response into `X-Forwarded-User`/`X-Forwarded-Groups` for
browser traffic, overriding any client-supplied values and stripping
`Authorization`. Jenkins runs a project-based matrix: `admin` Administer,
`power_user` read/build/cancel everywhere, `authenticated` Overall/Read only;
each per-network job carries its own matrix (owner read/build/cancel,
`team-<id>` read) written by `network_template_mgr` on create and re-applied
(`operation=acl`) on team change or ownership transfer. Management jobs are
invoked as the service identity so regular users never need Build on them.
No password is exchanged with Jenkins.

**Rationale:** Jenkins only honours a `cause` parameter together with a job
build-token (`RemoteCause`); without it the build is attributed to whoever
authenticated, i.e. the service account. Real attribution and "log in to
Jenkins as a webapp user" both require Jenkins to know the user, and the
forward-auth contract already produces exactly the identity headers the realm
consumes. The trust boundary is the network: Jenkins is reachable only from the
proxy and webapp pods (NetworkPolicy), which is the documented precondition of
the plugin.

**Rejected:** mirroring webapp users into Jenkins' private realm (passwords
would still not be shared, so no SSO); per-user API tokens (token lifecycle for
every user); build tokens with `cause` notes (*Started by remote host … with
note* — not a user, and still no Jenkins login).

## Risks / Trade-offs

- **Per-asset auth cost.** Every request under `/jenkins/` becomes two: a
  Django session lookup and the proxied call. Jenkins pages are asset-heavy.
  Accepted for now; mitigation (if needed) is an nginx `proxy_cache` on the
  auth location keyed by `$cookie_sessionid` with a short TTL, which is purely
  additive and documented here so it is not rediscovered.
- **Gate is only as good as the perimeter.** If Jenkins is reachable by any
  route other than this proxy, the gate is decorative. The `nita` companion
  change removes the host-port 8443 exposure; until it lands, this change
  reduces but does not eliminate anonymous access.
- **Session cookie scope.** The gate relies on the webapp `sessionid` cookie
  being sent with requests to `/jenkins/…`. The cookie is set with `Path=/`
  and default `SameSite=Lax`; Jenkins deep links are same-origin top-level
  navigations and Jenkins's own XHRs are same-origin, so the cookie is present.
  This would need revisiting only if Jenkins were ever moved to a different
  host.

## Migration Plan

1. Deploy `nita-jenkins/revoke-anonymous-build-and-enable-csrf`; verify that
  authenticated build clients still work and anonymous build/cancel requests
  are rejected.
2. Deploy `nita/close-jenkins-direct-exposure`; verify the direct host port is
  closed and the proxy can reach Jenkins on 8080 before enabling the gate.
3. Deploy this change and verify logged-in Jenkins UI access and anonymous
  redirect-to-login behavior. Keep the interval before this step short because
  Jenkins remains anonymously readable through the proxy, though build and
  cancel permissions have already been removed.

Rollback for this change is removing the `auth_request` line from
`location /jenkins/`; the Django endpoint and the extra header are harmless
if left in place.

## Open Questions

- None blocking. Whether to add the auth-location cache is deferred until
  there is evidence it is needed.

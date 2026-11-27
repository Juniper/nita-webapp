## Context

Jenkins reaches end users along two paths:

```
browser ──HTTPS──▶ Traefik ──/jenkins/──▶ jenkins:8080/jenkins   (UI deep links)
browser ──HTTPS──▶ Traefik ──/api/v1/──▶ webapp:8000 ──▶ jenkins:8080/jenkins   (everything else)
```

The second path is already authenticated end-to-end: the browser holds a
webapp session, Django checks permissions, and Django talks to Jenkins with
`X-Forwarded-User` / `X-Forwarded-Groups` plus a CSRF crumb (the
`jenkins-trigger-security` capability). The first path has no check at all.

Relevant existing pieces:

- `me_view` (`GET /api/v1/auth/me/`) is a session-authenticated DRF view that
  already returns the caller's `username` and `role`. The forward-auth
  endpoint is a stripped-down sibling: same authentication, headers instead of
  a body, no serializer.
- `jenkins_jobs.robot_summary` and `progressive_text_events` assert the
  configured service identity by header.
- `jenkins_jobs.invoke_job` wraps `jenkinsapi`'s `Job.invoke`. Its `cause`
  keyword is sent as a build *parameter* and only becomes a Jenkins cause when
  a job build-token is used; it does not attribute the build to a user.
- `LoginPage` navigates to `/` unconditionally after login.
- The companion `migrate-proxy-to-traefik` change implements proxy-side
  forward-auth and identity forwarding.

Constraints:

- The authentication contract must work with Traefik and remain independent
  of proxy-specific configuration.
- Jenkins visibility mirrors webapp ownership and team membership through the
  companion Jenkins security change and this change's job-management updates.

## Goals / Non-Goals

**Goals**

- Only callers with a valid webapp session reach anything under `/jenkins/`.
- Unauthenticated browsers end up on the SPA login page and return to where
  they were going.
- Django never depends on Jenkins granting anything to `anonymous`.
- Jenkins build pages show which webapp user asked for a build.
- The authenticated identity and groups are forwarded to Jenkins without
  trusting client-supplied identity headers.

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

**Choice:** `GET /api/v1/auth/forward/` uses `LabSessionAuthentication` only.
It returns `200` with `X-Forwarded-User` and `X-Forwarded-Groups` on success,
and redirects denied requests to `/login?next=<safe Jenkins path>`. It does not
use the global authentication-class list, which also enables
`TokenAuthentication`; a token without a webapp session is denied. The endpoint
does not write to the database.

**Rationale:** Traefik `forwardAuth` consumes this contract: 2xx authorizes the
request and selected response headers are copied to the Jenkins upstream.
Putting the decision in Django gives the proxy one shared source of session
validation and safe login redirects.

**Rejected:** proxy-side checks on the `sessionid` cookie's presence (trivially
forged) and a shared-secret header between the proxy and Jenkins (which does
nothing for the browser path).

### Decision 2: `next` is honoured only when it is a safe Jenkins path

**Choice:** The endpoint accepts `X-Forwarded-Uri` only when it is a same-origin
path equal to `/jenkins` or under `/jenkins/`, with no backslash, control
character or fragment. Otherwise it redirects to `/jenkins/`. `LoginPage`
accepts the resulting `next` only when it is a same-origin relative path.

**Rationale:** An unvalidated `next` is an open redirect. The rule above admits
every legitimate target (`/jenkins/job/x/`, `/networks/3`) and rejects
`//evil.example`, `https://evil.example`, and `javascript:` by construction.

### Decision 3: The console stream asserts the service identity

**Choice:** Both `robot_summary` and `progressive_text_events` use the shared
identity-header construction and send no Basic Authorization header.

**Rationale:** Both requests must be accepted by the header-based Jenkins
realm; one helper keeps the service identity consistent.

### Decision 4: Identity is propagated to Jenkins by header, not by cause text

**Choice:** Jenkins runs the Reverse Proxy Auth realm in header mode. The
webapp asserts an identity on every Jenkins call through `X-Forwarded-User`:
`invoke_job(..., initiated_by=username)` acts as the webapp user (so Jenkins
records a `UserIdCause`, *Started by user <username>*), and all service calls
(`_make_jenkins_server`, console/Robot relays, bootstrap scripts) act as the
`JENKINS_USER` service identity. Traefik copies the authenticated
`X-Forwarded-User`/`X-Forwarded-Groups` response headers to browser requests,
overriding client-supplied identity values and stripping `Authorization`.
Jenkins runs a project-based matrix: `admin` Administer,
`power_user` read/build/cancel everywhere, `authenticated` Overall/Read only;
each per-network job carries its own matrix (owner and `team-<id>`
read/build/cancel) written by `network_template_mgr` on create and re-applied
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
  Accepted for now; any caching must preserve session revocation and be
  evaluated against Traefik's forward-auth behavior.
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

1. Deploy `nita/close-jenkins-direct-exposure`; verify the direct host port is
  closed and the proxy can reach Jenkins on 8080.
2. Deploy the Jenkins hardening and session-gate changes together, then verify
  logged-in Jenkins UI access, safe login redirects, and rejection of
  unauthenticated requests. Coordinate with `migrate-proxy-to-traefik` so the
  proxy and webapp image use the same forward-auth contract.

Rollback must restore the compatible proxy and webapp image together; the
header-based Jenkins realm must not be exposed through an untrusted direct
route.

## Open Questions

- None blocking. Whether to add the auth-location cache is deferred until
  there is evidence it is needed.

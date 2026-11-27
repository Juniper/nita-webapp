# jenkins-reverse-proxy Specification

## Purpose
The webapp's HTTPS reverse proxy serves Jenkins under the `/jenkins/` path of the same origin, passing Jenkins responses through unmodified and terminating TLS at the proxy.

## Requirements

### Requirement: Jenkins UI proxied without response rewriting
The Traefik proxy SHALL route `/jenkins/` to the internal Jenkins service under
its native `/jenkins` context path without stripping the prefix, rewriting
response bodies, or relying on response URL translation.

#### Scenario: Jenkins UI loads fully under /jenkins/
- **GIVEN** Jenkins serves natively under the `/jenkins` context path
- **WHEN** an authenticated browser requests `https://<host>/jenkins/login`
- **THEN** the page and its assets load with no response rewriting

#### Scenario: No response-body rewriting configured
- **GIVEN** the Traefik route to Jenkins
- **WHEN** its configuration is inspected
- **THEN** it does not rewrite response bodies or blank `Accept-Encoding`

### Requirement: Proxy forwards standard headers to Jenkins
The Traefik proxy SHALL forward `Host`, `X-Forwarded-For`,
`X-Forwarded-Proto`, and `X-Forwarded-Prefix` to Jenkins while protecting
against untrusted client-supplied forwarding and identity headers.

#### Scenario: Forwarded scheme reflects external TLS
- **GIVEN** a browser reaches Traefik over HTTPS
- **WHEN** Jenkins receives the proxied request
- **THEN** `X-Forwarded-Proto` is `https`

### Requirement: TLS terminates at the proxy
The Traefik proxy SHALL terminate external Jenkins TLS and reach the internal
Jenkins service over plain HTTP on port 8080.

#### Scenario: Internal Jenkins hop is plain HTTP
- **GIVEN** external clients reach Jenkins via `https://<host>/jenkins/`
- **WHEN** Traefik proxies the request to Jenkins
- **THEN** the Traefik-to-Jenkins connection uses plain HTTP on port 8080

### Requirement: Jenkins route requires a webapp session
The reverse proxy SHALL forward a request under `/jenkins/` to Jenkins only
after its forward-auth check against the webapp endpoint
(`GET /api/v1/auth/forward/`) returns 2xx. The check SHALL carry the original
cookies and URI but not the body, and SHALL fail closed when the webapp is
unreachable. The authentication decision SHALL be made by the webapp.

#### Scenario: Authenticated browser reaches Jenkins
- GIVEN a browser holding a valid webapp `sessionid` cookie
- WHEN it requests `https://<host>/jenkins/job/<job>/`
- THEN the proxy's forward-auth check returns 200
- AND the request is forwarded to Jenkins and the job page loads with its assets

#### Scenario: Anonymous browser does not reach Jenkins
- GIVEN a browser with no webapp session
- WHEN it requests any URL under `/jenkins/`
- THEN the request is NOT forwarded to Jenkins

#### Scenario: Auth location is internal
- GIVEN the proxy configuration
- WHEN a client tries to bypass the check by addressing Jenkins directly or by sending its own forward-auth response headers
- THEN the request is not forwarded to Jenkins without a webapp-approved check

### Requirement: Proxy propagates the webapp identity to Jenkins
For a `/jenkins/` request that passed the forward-auth check, the proxy SHALL
copy `X-Forwarded-User` and `X-Forwarded-Groups` from the auth response,
overwriting any client-supplied values, and SHALL strip any client-supplied
`Authorization` header. Jenkins thus sees the webapp user with the webapp role
and `team-<id>` memberships as groups.

#### Scenario: Browser user is known to Jenkins
- GIVEN a browser logged in to the webapp as `alice` with role `user` who belongs to team 7
- WHEN it requests `/jenkins/whoAmI/api/json`
- THEN Jenkins reports `name: alice` with authorities `authenticated`, `user` and `team-7`

#### Scenario: Team membership change takes effect immediately
- GIVEN `bob` can read a network's jobs only through his team
- WHEN an admin removes `bob` from that team
- THEN his next `/jenkins/` request no longer carries that `team-<id>` group and the job pages are HTTP 404

#### Scenario: Client cannot spoof identity headers
- GIVEN a browser logged in to the webapp as `alice`
- WHEN it requests a `/jenkins/` URL with its own `X-Forwarded-User: admin` and `X-Forwarded-Groups: admin` headers
- THEN Jenkins still identifies the caller as `alice` with her real role

#### Scenario: Webapp admins administer Jenkins
- GIVEN a browser logged in to the webapp with role `admin`
- WHEN it requests `/jenkins/manage/`
- THEN the page loads (HTTP 200)

### Requirement: Denied Jenkins requests redirect to the login page
When the forward-auth check for a `/jenkins/` request is denied, the proxy
SHALL relay the endpoint's `302` redirect to `/login?next=<original request URI>`
rather than an error page, so that the browser can authenticate and return to
the originally requested Jenkins page.

#### Scenario: Deep link round-trips through login
- GIVEN an unauthenticated browser
- WHEN it requests `/jenkins/job/test-robot-net1/`
- THEN it receives a 302 to `/login?next=/jenkins/job/test-robot-net1/` (URL-encoded)
- AND after a successful login the SPA navigates to `/jenkins/job/test-robot-net1/`
- AND that request is now forwarded to Jenkins

### Requirement: Traefik preserves Jenkins session authentication
The proxy SHALL enforce the webapp session gate for Jenkins, fail closed when
authentication is unavailable, redirect denied browser requests to login with
a safe return path, and pass only the authenticated user and groups to Jenkins.
Client-supplied identity headers and Authorization SHALL NOT be trusted.

#### Scenario: Unauthenticated browser
- **WHEN** a browser without a valid session requests a Jenkins page
- **THEN** it is redirected to login and cannot reach Jenkins

#### Scenario: Client attempts identity spoofing
- **WHEN** an authenticated client supplies Jenkins identity headers
- **THEN** Jenkins receives the identity and groups verified by the webapp instead

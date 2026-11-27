## ADDED Requirements

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

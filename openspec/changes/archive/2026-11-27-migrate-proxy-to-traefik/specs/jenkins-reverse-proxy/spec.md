## RENAMED Requirements

- FROM: ### Requirement: TLS terminates at nginx
- TO: ### Requirement: TLS terminates at the proxy

## MODIFIED Requirements

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

## ADDED Requirements

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

# jenkins-reverse-proxy Specification

## Purpose
TBD - created by archiving change jenkins-path-prefix. Update Purpose after archive.
## Requirements
### Requirement: Jenkins UI proxied without response rewriting
The nginx reverse proxy SHALL route `location /jenkins/` to the internal Jenkins service, which serves natively under the `/jenkins` context path, by passing responses through verbatim. The proxy SHALL NOT rewrite Jenkins response bodies (no `sub_filter`) and SHALL NOT rely on `proxy_redirect` URL translation to make Jenkins pages load.

#### Scenario: Jenkins UI loads fully under /jenkins/
- GIVEN Jenkins serves natively under the `/jenkins` context path
- WHEN a browser requests `https://<host>/jenkins/login`
- THEN the login page and all its assets load with no rewriting by the proxy

#### Scenario: No response-body rewriting configured
- GIVEN the nginx `location /jenkins/` block
- WHEN its configuration is inspected
- THEN it contains no `sub_filter` directives and does not blank `Accept-Encoding`

### Requirement: Proxy forwards standard headers to Jenkins
The nginx reverse proxy SHALL forward `Host`, `X-Forwarded-For`, `X-Forwarded-Proto`, and `X-Forwarded-Prefix` to the Jenkins service so Jenkins can generate correct external URLs while receiving plain HTTP behind the TLS terminator.

#### Scenario: Forwarded scheme reflects external TLS
- GIVEN a browser reaches nginx over HTTPS and nginx proxies to Jenkins over plain HTTP
- WHEN Jenkins receives the proxied request
- THEN `X-Forwarded-Proto` is `https`

### Requirement: TLS terminates at nginx
The reverse proxy SHALL be the sole TLS terminator for external Jenkins access; the internal Jenkins service SHALL be reached over plain HTTP on port 8080, with no Jenkins-side HTTPS listener required for external access.

#### Scenario: Internal Jenkins hop is plain HTTP
- GIVEN external clients reach Jenkins via `https://<host>/jenkins/`
- WHEN nginx proxies the request to Jenkins
- THEN the nginx→Jenkins connection uses plain HTTP on port 8080


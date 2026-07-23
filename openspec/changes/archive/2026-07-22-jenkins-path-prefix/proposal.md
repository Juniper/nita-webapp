## Why

The webapp's nginx reverse proxy surfaces Jenkins under `/jenkins/` today, but Jenkins
itself serves from the server root. To bridge that gap, the `location /jenkins/` block
proxies to `http://jenkins:8080/` and then uses `sub_filter` to rewrite `href="/"`/`src="/"`
to `/jenkins/` "on a best-effort basis" (its own comment). That rewriting is inherently
leaky: it cannot fix URLs built in JavaScript, `action=` form targets, Ajax endpoints, or
`Location:` redirect headers, so Jenkins pages half-load or break under the prefix.

The companion `nita-jenkins` change (`jenkins-path-prefix`) makes Jenkins serve natively
under `--prefix=/jenkins`. Once that lands, this repo can proxy `/jenkins/` straight through
with no response rewriting, point the Django backend's Jenkins client at the prefixed base
URL, and drop Jenkins' own `:8443`/keystore in favour of the single nginx TLS terminator.

## What Changes

- **`nginx/nginx.conf`**: change the `/jenkins/` `proxy_pass` to the prefixed Jenkins
  (`http://jenkins:8080/jenkins/`) and delete the `sub_filter`/`proxy_redirect`/
  `Accept-Encoding ""` rewriting lines; keep the `X-Forwarded-*` headers
- **`jenkins_config.py`**: append `/jenkins` to `JENKINS_SERVER_URL` so the Django Jenkins
  client targets the prefixed server on the internal port
- **container startup scripts** (`ping_jenkins.py`, `configure_jenkins.py`,
  `add_jenkins_job.py`): append `/jenkins` to the Jenkins base URL so the startup readiness
  gate and job bootstrap in `wait-for-db.sh` target the prefixed server (otherwise the pod's
  startup gate loops on a 404 and Django never boots)
- **k8s deployment**: serve Jenkins as plain HTTP on 8080 behind nginx; drop the `:8443`
  exposure and JKS keystore (nginx is the sole TLS terminator)
- **Frontend**: no change — deep-links already target `/jenkins/job/...`

## Capabilities

### New Capabilities

- `jenkins-reverse-proxy`: nginx proxies `/jenkins/` to a natively-prefixed Jenkins with no
  response-body URL rewriting, forwarding proxy headers and terminating TLS at the edge

### Modified Capabilities

- `jenkins-trigger-security`: the Django→Jenkins internal base URL includes the `/jenkins`
  path prefix

## Impact

- Depends on the `nita-jenkins` `jenkins-path-prefix` change; both MUST deploy together —
  if the proxy/backend expect the prefix before Jenkins serves it (or vice-versa),
  `/jenkins/` requests 404 and triggers fail
- Removes the fragile `sub_filter` rewriting, fixing Jenkins pages that previously
  half-loaded under the proxy
- Jenkins session cookie is scoped to `/jenkins`, so it no longer collides with the webapp
  session cookie at `/`
- Consolidates external access on the single nginx origin and TLS certificate

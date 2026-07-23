## Context

`nita-webapp` fronts the SPA and Django API with an nginx reverse proxy that terminates a
single TLS certificate. It also surfaces the Jenkins UI at `/jenkins/` so the SPA can
deep-link to job/build pages (`/jenkins/job/<job>/<build>/`).

Two facts drive this change:

1. **nginx rewrites Jenkins responses.** `location /jenkins/` proxies to
   `http://jenkins:8080/` (root) and uses `sub_filter` to rewrite `href="/"`/`src="/"` to
   `/jenkins/`. The config comment admits this is "best-effort"; it misses JS-built URLs,
   form actions, Ajax calls, and redirect `Location:` headers.
2. **The Django backend talks to Jenkins at the root.** `jenkins_config.py` builds
   `JENKINS_SERVER_URL = http://<host>:<port>` (no prefix) for the `python-jenkins` client.

The companion `nita-jenkins` change makes Jenkins serve natively under `--prefix=/jenkins`,
which removes the reason for both behaviours.

## Goals / Non-Goals

**Goals:**
- Proxy `/jenkins/` straight through to a natively-prefixed Jenkins with no response rewriting
- Point the Django Jenkins client at the prefixed internal base URL
- Terminate TLS only at nginx; Jenkins serves plain HTTP behind it (drop `:8443`/keystore)
- Preserve all existing SPA deep-links and trigger/streaming behaviour

**Non-Goals:**
- Changing the trigger/auth model in `jenkins-trigger-security` beyond the base URL
- Changing SPA deep-link paths (already `/jenkins/...`)
- Introducing in-cluster mTLS or a service mesh

## Decisions

### Proxy pass-through instead of response rewriting
**Decision:** Set `proxy_pass http://jenkins:8080/jenkins/;` for `location /jenkins/` and
delete the `sub_filter`, `proxy_redirect`, and `Accept-Encoding ""` lines; keep
`X-Forwarded-For`/`X-Forwarded-Proto`/`X-Forwarded-Host`/`Host`.

**Rationale:** With Jenkins prefixed, every URL Jenkins emits already starts with `/jenkins/`,
so nginx can forward bytes verbatim. Removing `sub_filter` also lets responses stay
compressed (no need to blank `Accept-Encoding`), improving performance and eliminating the
class of "page half-loads" bugs.

### Append the prefix to the Django Jenkins base URL
**Decision:** `JENKINS_SERVER_URL` becomes `http://<host>:<port>/jenkins`.

**Rationale:** `--prefix` is global to the Jenkins process, so the internal port 8080 also
serves under `/jenkins`. `python-jenkins` accepts a base URL and appends API paths to it, so
adding the suffix is sufficient; no other backend change is required.

### TLS terminates only at nginx
**Decision:** In the k8s deployment, Jenkins serves plain HTTP on 8080 behind nginx; the
`:8443` listener and JKS keystore are removed.

**Rationale:** The only untrusted hop is browser→nginx (HTTPS). The nginx→Jenkins hop is
inside the cluster network already restricted by NetworkPolicy, and the backend already
speaks plain HTTP to Jenkins on 8080. This removes the keystore, its embedded password, and
cert-rotation overhead. nginx forwards `X-Forwarded-Proto=https` so Jenkins still advertises
`https://` external URLs (with the root URL set via `JENKINS_URL` in the `nita-jenkins`
change).

## Risks / Trade-offs

- **[Risk] Cross-repo cutover ordering** — the proxy/backend expecting `/jenkins` before
  Jenkins serves it (or vice-versa) breaks the UI and triggers → Mitigated by deploying this
  change together with the `nita-jenkins` `jenkins-path-prefix` change.
- **[Trade-off] Plain HTTP inside the cluster** — nginx→Jenkins traffic is unencrypted →
  Accepted; standard for edge-terminated TLS and already true of existing webapp→Jenkins
  calls; NetworkPolicy restricts access to port 8080.

## Migration Plan

1. Land the `nita-jenkins` `jenkins-path-prefix` change (image serves under `/jenkins`)
2. Update `nginx/nginx.conf`: prefixed `proxy_pass`; delete rewriting lines
3. Update `jenkins_config.py`: append `/jenkins` to `JENKINS_SERVER_URL`
4. Update the k8s deployment: Jenkins plain HTTP on 8080; drop `:8443`/keystore
5. Deploy both repos together; verify `https://<host>/jenkins/login` renders fully and the
   SPA can trigger and stream jobs and open Jenkins deep-links

**Rollback:** Revert nginx, `jenkins_config.py`, and the deployment change together with the
`nita-jenkins` revert. No persistent state changes.

## Open Questions

- None — the external origin (`JENKINS_URL`) is deployment-provided and owned by the
  `nita-jenkins` change; this repo only needs the internal prefixed base URL and the proxy
  pass-through.

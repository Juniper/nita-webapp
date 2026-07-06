## Context

Actions on the network detail Actions tab render as rows with a Run button. Each
action has a `jenkins_url` (job-name prefix). The concrete Jenkins job for an
action within a network is `{jenkins_url}-{network_name}` (the same job name the
backend uses for triggering and console streaming).

Jenkins is deployed as an internal `jenkins:8080` service with no external
ingress; the only browser entry point is the nginx proxy. The proxy already
forwards everything to the webapp via `location /`.

## Decisions

### Relative `/jenkins/` link, routed by the proxy

The button links to `/jenkins/job/{job}/` (relative), keeping the frontend
host/port agnostic. The nginx proxy gains a `location /jenkins/` that forwards to
`http://jenkins:8080/`. This mirrors how the app already delegates Jenkins
concerns to the proxy layer and avoids hard-coding a Jenkins address in the SPA
or adding a backend config round-trip.

### Best-effort asset rewriting

The bundled Jenkins runs at the server root, so its pages emit root-relative
asset URLs (`/static/...`, `/adjuncts/...`). Under the `/jenkins/` subpath these
would miss. The proxy applies `sub_filter` rewrites for the common
`href="/`/`src="/` cases to prepend `/jenkins`, on a best-effort basis, so the
job page is navigable. Fully correct subpath rendering would require running
Jenkins with a matching prefix, which is out of scope (it would break the
internal `http://jenkins:8080/` build integration).

## Alternatives Considered

- **Configurable external Jenkins URL exposed to the SPA**: rejected for now —
  there is no externally reachable Jenkins URL in this deployment, and a
  relative proxied path is deployment-agnostic.
- **Set Jenkins `--prefix=/jenkins`**: rejected — breaks the internal build
  integration that targets `http://jenkins:8080/` at the root.

## Risks

- Jenkins UI styling under `/jenkins/` may be imperfect without a matching
  Jenkins prefix; the deep link still resolves to the correct job.

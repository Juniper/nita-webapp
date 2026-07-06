## 1. Frontend: per-action Jenkins link

- [x] 1.1 In `frontend/src/pages/NetworkDetailPage.tsx` Actions tab, add a
  Jenkins link next to each action's Run button, targeting
  `/jenkins/job/{action.jenkins_url}-{network.name}/`, `target="_blank"` with
  `rel="noopener noreferrer"`.
- [x] 1.2 Style it consistently with the existing small action buttons and keep
  the Run button behavior unchanged.

## 2. Proxy: route `/jenkins/`

- [x] 2.1 Add an nginx `location /jenkins/` to the deployed proxy config
  (`proxy-config-cm`) that proxies to `http://jenkins:8080/` with buffering off
  and best-effort `sub_filter` rewrites of root-relative `href="/`/`src="/`
  references to `/jenkins/`.
- [x] 2.2 Also add the same location to the repo's `nginx/nginx.conf` so the
  compose deployment stays in sync.
- [x] 2.3 Apply the updated ConfigMap and restart the proxy.

## 3. Verify

- [x] 3.1 Build and deploy the webapp; confirm each action row shows a Jenkins
  link with the correct `/jenkins/job/<job>/` href.
- [x] 3.2 Confirm `/jenkins/` is served by Jenkins (not the SPA) through the
  proxy.

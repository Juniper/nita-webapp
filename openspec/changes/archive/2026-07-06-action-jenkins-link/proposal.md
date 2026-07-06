## Why

On the network detail **Actions** tab each action can be run, and its run
history streams the Jenkins console. But there is no quick way to jump to the
action's **Jenkins job** itself (to inspect configuration, full build history,
or artifacts). Each action already carries a `jenkins_url` (the job name
prefix); combined with the network name it identifies the concrete Jenkins job
`{jenkins_url}-{network_name}` (e.g. `build_qfx_fabric-dc1`). Exposing a direct
link removes a manual navigation step.

## What Changes

- Each action row on the network detail Actions tab SHALL show a **Jenkins**
  link/button that opens the action's Jenkins job page in a new browser tab.
- The link target SHALL be the reverse-proxied Jenkins path
  `/jenkins/job/{jenkins_url}-{network_name}/`, so it is host/port agnostic and
  routed by the proxy rather than hard-coding a Jenkins address.
- The reverse proxy SHALL route `/jenkins/` to the internal Jenkins service so
  the link resolves from the browser.

No backend or database changes are required; the action serializer already
returns `jenkins_url` and the page already knows the network name.

## Capabilities

### Modified Capabilities
- `spa-networks`: The network detail Actions tab gains a per-action Jenkins job
  link.

## Impact

- **Frontend**: `frontend/src/pages/NetworkDetailPage.tsx` (Actions tab row adds
  a Jenkins link next to Run).
- **Infra (proxy)**: add an nginx `location /jenkins/` that proxies to the
  Jenkins service (`jenkins:8080`), mirroring the existing pattern used for the
  streaming endpoints. Because the bundled Jenkins runs at the server root, the
  proxy rewrites root-relative asset references to the `/jenkins/` prefix on a
  best-effort basis.
- **No backend / API / DB changes.**

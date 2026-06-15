## Why

The React SPA frontend (`frontend/`) must be compiled to static files before the Django container can serve them. Currently the Dockerfile has no Node.js toolchain, so the production build artifact (`frontend/dist/`) is never produced inside Docker. This change adds a multi-stage build so that `npm run build` runs inside Docker and the resulting static files are copied into the Django image — eliminating the need to check in build artifacts or pre-build outside Docker.

## What Changes

- Add a `node:22-slim` build stage (`frontend-builder`) that installs npm deps and runs `npm run build` for `frontend/`
- Copy `frontend/dist/` from the build stage into the Django image at a path served by the app (e.g., `/app/frontend/dist/`)
- Update `.dockerignore` (or create one) to exclude `frontend/node_modules` and `frontend/dist` from the build context
- No changes to `docker-compose.yaml` or runtime config — the static files are embedded in the image

## Capabilities

### New Capabilities
- `docker-node-build-stage`: Multi-stage Dockerfile that builds the React SPA inside Docker using Node 22 and embeds the compiled static assets into the final Django image

### Modified Capabilities
<!-- None — runtime specs (auth, API) are unchanged -->

## Impact

- `Dockerfile`: gains a `frontend-builder` stage
- `.dockerignore`: gains exclusions for `frontend/node_modules` and `frontend/dist`
- Docker image build time increases by ~30–60 s (npm install + vite build)
- No change to `docker-compose.yaml`, API, or Django settings

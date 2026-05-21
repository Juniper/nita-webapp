## ADDED Requirements

### Requirement: Docker image includes compiled React SPA
The Dockerfile SHALL use a multi-stage build with a `frontend-builder` stage based on `node:22-slim`. The builder stage SHALL install npm dependencies with `npm ci` and produce a production build with `npm run build`. The final Django image SHALL copy the compiled static files from the builder stage into `/app/frontend/dist/`.

#### Scenario: Image build produces frontend dist artefacts
- **WHEN** `docker build .` is run
- **THEN** the final image contains `/app/frontend/dist/index.html` and associated JS/CSS assets

#### Scenario: Node runtime is absent from final image
- **WHEN** the final image is inspected
- **THEN** `node` and `npm` binaries are NOT present (Node toolchain stays in builder stage only)

### Requirement: Build context excludes frontend node_modules and dist
The project SHALL have a `.dockerignore` file that excludes `frontend/node_modules` and `frontend/dist` from the Docker build context.

#### Scenario: node_modules not sent to daemon
- **WHEN** `docker build .` is run
- **THEN** `frontend/node_modules` is not transferred to the Docker daemon (excluded by `.dockerignore`)

#### Scenario: Pre-existing dist not injected
- **WHEN** `docker build .` is run
- **THEN** `frontend/dist` is not transferred to the Docker daemon; the builder stage produces it fresh

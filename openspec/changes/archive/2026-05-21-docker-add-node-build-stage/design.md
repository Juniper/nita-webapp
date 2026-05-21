## Context

The project Dockerfile is a single-stage Python image. The React SPA lives in `frontend/` and must be compiled to static files before Django can serve them. Without a Node.js build step inside Docker the compiled output is not available unless pre-built on the host and checked in, which is unsuitable for CI/CD.

## Goals / Non-Goals

**Goals:**
- Add a `frontend-builder` stage using the official `node:22-slim` image
- Run `npm ci` + `npm run build` inside that stage to produce `frontend/dist/`
- `COPY --from=frontend-builder` those static files into the final Django image
- Keep the final image size unchanged (Node runtime is NOT included)
- Add `.dockerignore` rules to keep `node_modules` and `dist` out of the build context

**Non-Goals:**
- Serving the static files via a separate nginx container (later change)
- Hot-reload or dev-mode inside Docker
- Changing how Django serves the files (no `STATICFILES_DIRS` wiring in this change)

## Decisions

### Multi-stage build (Node builder stage)
**Decision**: Use `FROM node:22-slim AS frontend-builder` as the first stage.  
**Rationale**: Multi-stage builds are the idiomatic Docker approach — the Node toolchain never lands in the final image, keeping it lean. `node:22-slim` matches the Node version on the host (`22.22.3`).

**Alternatives considered**:  
- Build on host, `COPY dist/` → fragile, requires pre-build step, pollutes VCS  
- Install Node in the Python image → bloats final image by ~200 MB

### Copy target path
**Decision**: `COPY --from=frontend-builder /build/dist /app/frontend/dist`  
**Rationale**: Using `/build/` as the working dir in the builder keeps it separate from the final `/app/` tree. The Django app will later serve files from `/app/frontend/dist/`.

### `.dockerignore`
**Decision**: Exclude `frontend/node_modules` and `frontend/dist` from build context.  
**Rationale**: `node_modules` is large (~200 MB) and must not be copied into the builder stage (would shadow `npm ci` result). `dist` should be produced by the build, not injected.

## Risks / Trade-offs

- [Risk] Increased image build time (~30–60 s for npm install + vite build) → Mitigation: Docker layer cache means this only re-runs when `frontend/package.json` or source files change  
- [Risk] Version skew between host Node (22.22.3) and `node:22-slim` → Mitigation: Both are Node 22 LTS; minor patch differences are benign for `vite build`

## Migration Plan

1. Update `Dockerfile` — add builder stage before the existing `FROM python:...` stage
2. Create or update `.dockerignore`
3. Rebuild image: `docker build .` — verify exit 0
4. No `docker-compose.yaml` changes required

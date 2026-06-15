## 1. Build Context

- [x] 1.1 Create `.dockerignore` at repo root excluding `frontend/node_modules` and `frontend/dist`

## 2. Dockerfile Multi-Stage Build

- [x] 2.1 Add `frontend-builder` stage (`FROM node:22-slim AS frontend-builder`) before the Python stage
- [x] 2.2 Set `WORKDIR /build` and `COPY frontend/ .` in the builder stage
- [x] 2.3 Run `npm ci` then `npm run build` in the builder stage
- [x] 2.4 Add `COPY --from=frontend-builder /build/dist /app/frontend/dist` in the Python stage (after `WORKDIR /app`)

## 3. Verification

- [x] 3.1 Run `docker build -t nita-webapp-test .` and confirm exit 0
- [x] 3.2 Confirm `/app/frontend/dist/index.html` exists in the built image: `docker run --rm nita-webapp-test ls /app/frontend/dist/index.html`
- [x] 3.3 Confirm `node` is absent from the final image: `docker run --rm nita-webapp-test which node` should return non-zero

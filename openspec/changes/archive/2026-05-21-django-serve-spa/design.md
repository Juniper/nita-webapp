## Context

Django's `BASE_DIR` is `ngcn_workbench/` (3 levels below `/app/` in Docker). The compiled SPA lives at `/app/frontend/dist/` in Docker. Vite builds assets with root-relative paths (`/assets/index-xxx.js`), so Django must serve `/assets/` from `frontend/dist/assets/`.

The existing Django template UI occupies the root URL (`path("", views.indexView)`). Mounting the SPA at `/app/` avoids all conflicts and matches the React Router `basename`.

## Goals / Non-Goals

**Goals:**
- Serve `frontend/dist/assets/` at `/assets/` via WhiteNoise middleware
- Serve `frontend/dist/index.html` at `/app/` and any `/app/<subpath>` via a Django view
- React Router works correctly with `basename="/app"` — `/app/login` and `/app/` resolve to the correct components
- Existing Django template UI and API endpoints unchanged
- Graceful 503 if `frontend/dist/index.html` doesn't exist (dev without a build)

**Non-Goals:**
- Serving the SPA at the root URL `/` (that is change ⑲)
- Running `collectstatic` in Docker (WhiteNoise serves `WHITENOISE_ROOT` directly without collectstatic)
- Hot-reload inside Docker

## Decisions

### WhiteNoise over Django staticfiles
**Decision**: Use `whitenoise.middleware.WhiteNoiseMiddleware` with `WHITENOISE_ROOT`.  
**Rationale**: WhiteNoise intercepts requests for files that exist in `WHITENOISE_ROOT` before they reach URL routing — so `/assets/index-xxx.js` is served efficiently without adding URL patterns. `WHITENOISE_ROOT` (as opposed to `WHITENOISE_STATIC_PREFIX`) serves files at their natural paths, matching the root-relative `/assets/...` references baked into `index.html` by Vite.  
**Alternatives considered**: `STATICFILES_DIRS` + collectstatic — requires an extra build step in Docker and `runserver --insecure` in dev; more moving parts.

### SPA mounted at `/app/` not `/`
**Decision**: `path('app/', spa_index)` + `re_path(r'^app/.*$', spa_index)`.  
**Rationale**: The existing Django template UI has `path("", views.indexView)` at the root. Mounting at `/app/` requires zero changes to existing URLs and keeps the transition reversible. Change ⑲ will flip this.

### FRONTEND_DIST env var with fallback
**Decision**: `WHITENOISE_ROOT = os.environ.get('FRONTEND_DIST', os.path.join(BASE_DIR, '../../../frontend/dist'))`.  
**Rationale**: The 3-level relative path (`BASE_DIR` → `/app/`) is correct in Docker but may differ in other setups. The env var allows override without a code change.

### `spa_index` view in `urls.py` (not a separate file)
**Decision**: Define `spa_index` directly in `ngcn_workbench/urls.py`.  
**Rationale**: It's a single 10-line function; no need for a new module.

## Risks / Trade-offs

- [Risk] `frontend/dist/` absent in dev (no prior `npm run build`) → Mitigation: `spa_index` returns `HttpResponse("SPA not built", status=503)` if `index.html` missing  
- [Risk] WhiteNoise `WHITENOISE_ROOT` serves ALL files in `frontend/dist/` including `index.html` at `/index.html` → Mitigation: acceptable; that path has no existing Django route and isn't linked from the SPA
- [Risk] Asset content-hash filenames change on each build; browser cache busting works automatically since filenames change → no mitigation needed

## Migration Plan

1. Add `whitenoise` to `requirements.txt`
2. Update `settings.py` (middleware + `WHITENOISE_ROOT`)
3. Update `ngcn_workbench/urls.py` (add imports + `spa_index` + two URL patterns)
4. Update `frontend/src/App.tsx` (`basename="/app"`)
5. Rebuild frontend: `cd frontend && npm run build`
6. Run `pytest` — all existing tests must pass
7. Smoke-test: `GET /app/` returns the React SPA HTML; `GET /assets/index-*.js` returns JS

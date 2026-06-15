## Why

The React SPA has been scaffolded (④) and is compiled inside Docker (⑤), but Django does not yet serve it. Users cannot reach the new frontend at all. This change wires Django to serve the compiled SPA's static assets and `index.html`, making the new React UI accessible at `/app/` while keeping the existing Django template UI untouched at its current URLs.

## What Changes

- Install `whitenoise` — serves `frontend/dist/assets/` at `/assets/` with caching headers
- `settings.py`: add WhiteNoise middleware and `WHITENOISE_ROOT` pointing to `frontend/dist/`
- `ngcn_workbench/urls.py`: add `spa_index` view + URL patterns for `/app/` and `/app/<path:rest>`
- `frontend/src/App.tsx`: add `basename="/app"` to `<BrowserRouter>` so React Router paths are relative to `/app/`
- No changes to existing Django template routes or API routes

## Capabilities

### New Capabilities
- `django-spa-serve`: Django serves the compiled React SPA — static assets via WhiteNoise and `index.html` via a dedicated view mounted at `/app/`

### Modified Capabilities

## Impact

- `requirements.txt`: adds `whitenoise`
- `ngcn_workbench/settings.py`: WhiteNoise middleware + `WHITENOISE_ROOT` setting
- `ngcn_workbench/urls.py`: two new URL patterns + `spa_index` view function
- `frontend/src/App.tsx`: `basename` prop on `BrowserRouter`
- Existing Django template UI and API are unaffected
- In development: `frontend/dist/` must exist (run `npm run build` first); `npm run dev` continues to serve the SPA directly through Vite

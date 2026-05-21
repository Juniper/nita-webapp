## 1. Backend: WhiteNoise + static assets

- [x] 1.1 Add `whitenoise` to `requirements.txt`
- [x] 1.2 Add `whitenoise.middleware.WhiteNoiseMiddleware` after `SecurityMiddleware` in `MIDDLEWARE` in `settings.py`
- [x] 1.3 Add `WHITENOISE_ROOT` to `settings.py`: `os.environ.get('FRONTEND_DIST', os.path.join(BASE_DIR, '../../../frontend/dist'))`

## 2. Backend: SPA index view + URL patterns

- [x] 2.1 Add `spa_index` view function to `ngcn_workbench/urls.py` — reads `frontend/dist/index.html` and returns `HttpResponse` (status 503 if file missing)
- [x] 2.2 Add `path('app/', spa_index, name='spa')` to `urlpatterns` in `ngcn_workbench/urls.py` (before the `ngcn.urls` include)
- [x] 2.3 Add `re_path(r'^app/.*$', spa_index)` to `urlpatterns` in `ngcn_workbench/urls.py`

## 3. Frontend: BrowserRouter basename

- [x] 3.1 Update `frontend/src/App.tsx`: add `basename="/app"` to `<BrowserRouter>`

## 4. Verification

- [x] 4.1 Run `cd frontend && npm run build` to regenerate `dist/` with current code
- [x] 4.2 Run full test suite (`pytest`) — all existing tests must pass
- [x] 4.3 Start Django dev server and confirm `GET /app/` returns HTML containing `<div id="root">`
- [x] 4.4 Confirm `GET /assets/index-*.js` returns the compiled JS (WhiteNoise serving)
- [x] 4.5 Confirm `GET /` still returns the Django template index view (not the SPA)

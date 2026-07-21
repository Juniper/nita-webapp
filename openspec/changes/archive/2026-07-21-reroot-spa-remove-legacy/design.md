## Context

The NITA webapp is a Django project (`ngcn_workbench`) with a single app (`ngcn`). nginx is a thin reverse proxy — it forwards everything to `webapp:8000` (Django) except a few streaming and Jenkins-deep-link locations. Django therefore owns the split between the two UIs:

```
nginx ──▶ Django (ngcn_workbench/urls.py)
            ├─ /admin/        → Django admin
            ├─ /api/v1/       → ngcn.api            (used by the SPA)
            ├─ /api/schema, /api/docs
            ├─ /app/, /app/*  → spa_index (React SPA, basename="/app")
            └─ /              → ngcn.urls           (LEGACY server-rendered UI)
```

The legacy UI is server-rendered Django (templates + `django_tables2` + forms + jQuery/SlickGrid static assets), entered through `ngcn/urls.py` → `ngcn/views.py`. The SPA is a compiled React app served by a single `spa_index` view and its assets served by WhiteNoise at `/assets/`.

The critical wrinkle: `ngcn/views.py` is not purely legacy. The new SPA API and shared helpers import symbols out of it:

```
ngcn/api/views.py       →  from ngcn.views import GridDataManager, create_new_inv,
                              create_workbook, create_workbook_from_db, parse_workbook
                           (lazy) from ngcn.views import updateCampusNetworkStatusOnDB
                           (lazy) from ngcn.views import _make_jenkins_server
ngcn/jenkins_jobs.py    →  (lazy) from ngcn.views import JENKINS_SERVER_URL,
                              JENKINS_SERVER_USER, JENKINS_SERVER_PASS
tests/test_supporting_units.py → from ngcn.views import GridDataManager, escape_ansi
```

Several of these are lazy, in-function imports, so static analysis will not flag them if one is missed — the failure only surfaces at runtime when a workbook is parsed or a Jenkins job is triggered.

## Goals / Non-Goals

**Goals:**
- The SPA is the default UI, served at `/` (React Router `basename="/"`).
- Reserved backend prefixes (`api/`, `admin/`, `assets/`, `jenkins/`, `api/schema`, `api/docs`) continue to route correctly; the SPA catch-all never swallows them.
- The legacy server-rendered UI, its routes, templates, tables, forms, legacy static assets, legacy views, and legacy-only tests are removed.
- Shared business logic and Jenkins config currently trapped in `ngcn/views.py` is relocated to neutral modules that the API owns, so no runtime module depends on legacy code.
- `django_tables2` is removed as a dependency.
- The app is green (tests + a manual smoke of the SPA and API) at every intermediate step.

**Non-Goals:**
- Changing the API contract (`/api/v1/**` stays identical).
- Changing how assets are built or served (WhiteNoise + Vite root-relative assets are untouched).
- Changing authentication or session behaviour.
- Rewriting or improving any SPA feature — this is a re-root + delete, not a feature change.
- Touching Django admin functionality (only verifying it still resolves under `/admin/`).

## Decisions

### D1 — Serve the SPA at `/` for its own client routes; everything else 404s

**Decision**: Mount `spa_index` at the root and for an explicit allowlist of the SPA's top-level route segments. Any path that matches neither a backend route nor a SPA route falls through to Django's default 404. Removed legacy paths therefore return **HTTP 404**, not the SPA shell.

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("ngcn.api.urls")),
    path("api/v1/auth/token/", TokenAuthView.as_view(), name="api-token-auth"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(), name="swagger-ui"),
    # React SPA is the default app at "/" — served for the root and the SPA's
    # own client-side routes only. Keep this list in sync with App.tsx routes.
    path("", spa_index, name="spa"),
    re_path(r"^(?:login|network-types|networks)(?:/.*)?$", spa_index),
    # Any other path (including every removed legacy URL) → Django default 404.
]
```

**The tension this resolves**: SPA deep links (`/networks/5` refreshed in the browser) and removed legacy paths (`/campustype/`) are *both* "paths Django has no explicit view for." A blind catch-all (`re_path(r"^.*$", spa_index)`) would serve `index.html` for every unknown path — so refreshing `/networks/5` works, but `/campustype/` would also render the SPA and React Router would show a client-side "not found" page with an HTTP **200**. The resolved decision is that removed legacy paths return a real **HTTP 404**, so the catch-all cannot be blind: Django serves `index.html` only for paths the SPA actually owns.

**Rationale**: Django resolves patterns top-to-bottom, so backend routes listed first take precedence. Enumerating the SPA's top-level segments (`login`, `network-types`, `networks`, plus the bare root) makes Django and the SPA agree on exactly which paths are client-rendered; genuinely unknown paths (including every deleted legacy URL) get a correct 404. The `(?:/.*)?` suffix lets deep links like `/networks/5` resolve to `index.html` so a browser refresh on a detail page works.

**Trade-off**: Django must be kept in sync with the SPA's top-level routes — adding a new top-level page (e.g. `/reports`) requires adding `reports` to the regex. This is a small, explicit contract and is preferable to legacy paths silently rendering the SPA. A regression test SHALL assert that a removed legacy path returns 404 so drift is caught.

**Performance & consequences**: The allowlist has no meaningful runtime cost relative to a blind catch-all — URL resolution walks ~7 patterns top-to-bottom and the allowlist regex is a trivial, backtracking-free alternation (a few microseconds); API traffic matches earlier patterns and never reaches it. The only per-request cost in this path is `spa_index` itself, which does a `stat` + full read of `index.html` on every SPA request — but that file is ~1 KB, sits in the OS page cache, fires only on initial load / refresh / deep-link (not client-side navigation), and is **identical under either routing scheme**, so it is not a consequence of this decision (it could be read once into memory if it ever mattered). If anything the allowlist does *less* work under adversarial traffic: scanners and crawlers hitting random paths (`/wp-login.php`, `/.env`) get a cheap Django 404 instead of being handed the 200 SPA shell — which, for a real browser, would otherwise trigger a full JS/CSS bundle download just to render a client-side "not found". The consequences that actually matter are therefore correctness and maintenance, not speed: correct HTTP 404 semantics (accurate monitoring/logs, crawler/SEO signals) in exchange for the routing contract above. Drift risk cuts both ways — a *new* SPA route not added to Django deep-links to 404 even though client-side navigation to it works; mitigate by deriving the allowlist from a single list of route segments and adding a guard test that asserts each known SPA route serves `index.html` (the inverse of the legacy-404 test).

**Alternative considered — blind catch-all + client-side 404 (HTTP 200).** Rejected per the decision above: removed legacy paths must return HTTP 404, not a 200 SPA shell.

**Alternative considered — nginx owns the split** (`location /api/`, `location /admin/`, `location / → try_files index.html`). Rejected: it duplicates asset-serving responsibilities that WhiteNoise already handles inside Django and spreads the routing contract across two files. Keeping the split in Django preserves the current single-source-of-truth design.

### D2 — Extract shared symbols before deleting legacy views

**Decision**: Move the shared symbols out of `ngcn/views.py` into neutral modules, update all importers, verify tests pass, and only then delete the legacy views.

Proposed placement:

```
ngcn/workbook.py        GridDataManager, create_new_inv, create_workbook,
                        create_workbook_from_db, parse_workbook,
                        updateCampusNetworkStatusOnDB, escape_ansi
ngcn/jenkins_config.py  JENKINS_SERVER_URL, JENKINS_SERVER_USER,
                        JENKINS_SERVER_PASS, _make_jenkins_server
```

(Exact module names/splits can be adjusted during implementation; the invariant is that no non-legacy module imports from `ngcn.views` afterward.)

**Rationale**: Extraction-before-deletion keeps the build green at every step and makes the deletion a mechanical, low-risk operation. Because several importers use lazy in-function imports, the implementation must grep for every `from ngcn.views import` and `from ngcn import views` (including inside function bodies) and repoint them — a single missed lazy import becomes a runtime `ImportError` under a Jenkins trigger or workbook parse.

**Alternative considered — delete legacy views and inline the helpers into `ngcn/api/views.py`.** Rejected: it bloats the API module and couples unrelated concerns (Excel/workbook handling, Jenkins server construction) into the request-handling layer.

### D3 — Frontend re-root is a single `basename` change

**Decision**: Change `<BrowserRouter basename="/app">` to `<BrowserRouter basename="/">` in `frontend/src/App.tsx`. No other frontend change is required.

**Rationale**: The SPA's coupling to `/app` is limited to this one line. All API calls (`fetch('/api/v1/...')`), Vite asset URLs (`/assets/...`), and downloads (`window.location.assign('/api/...')`) are already root-relative, so re-rooting the router prefix is sufficient. React Router internal navigation (`useNavigate`, `<Route path=...>`) is relative to the basename and needs no edits.

### D4 — Remove `django_tables2` only after all `tables.py`/template usages are gone

**Decision**: Delete `ngcn/tables.py`, all `{% load django_tables2 %}` templates, and legacy views first; then remove `"django_tables2"` from `INSTALLED_APPS` and `django-tables2==2.7.0` from `requirements.txt`; then regenerate `NOTICES`.

**Rationale**: Removing the app from `INSTALLED_APPS` while a template still `{% load %}`s it, or while `tables.py` still imports it, breaks Django startup / template rendering. Ordering the dependency removal last avoids a transient broken state.

## Risks / Trade-offs

- **Missed lazy import → runtime break.** Mitigation: exhaustive grep for `ngcn.views` / `from ngcn import views` across the whole tree (not just top-of-file imports); run the full test suite plus a manual trigger + workbook-parse smoke after extraction.
- **No coverage gate exists (confirmed).** There is no `pytest-cov`/`coverage` dependency, no `--cov`/`--cov-fail-under` in `pytest.ini` (`addopts = -ra`), and no `.coveragerc` or `[tool.coverage]` in `pyproject.toml`. Deleting the legacy test files therefore trips no threshold. The only related cleanup is stale ruff `per-file-ignores` in `pyproject.toml` for `**/ngcn/forms.py` and `**/ngcn/views.py`, which become dead config once those files are deleted/emptied and should be removed.
- **Breaking external links.** Anything bookmarking or scripting a legacy `/` path will get a hard **HTTP 404** (per D1). Mitigation: documented as breaking in the proposal; this is the intended, explicit behaviour rather than silently rendering the SPA.
- **`servicestartupmiddleware` / `statusupdater`.** These run a background status thread and are unrelated to the legacy UI — they must be preserved. Mitigation: explicitly out of scope for deletion.

## Migration Plan

Sequenced so the app is verifiable (tests green + SPA/API smoke) after each step:

```
1. Extract shared symbols from views.py → new neutral modules; repoint all
   importers (top-level AND lazy in-function). Run full test suite.
2. Re-root: frontend basename "/app" → "/"; Django urls.py root mount +
   catch-all; remove nginx  rewrite ^/webapp .  Smoke: SPA loads at /, API works.
3. Delete legacy: ngcn/urls.py routes, templates/ngcn/**, tables.py, forms.py,
   legacy static assets, legacy views in views.py, legacy test files.
4. Drop dependency: remove "django_tables2" from INSTALLED_APPS and
   django-tables2 from requirements.txt.
5. Regenerate NOTICES via merge_spdx.sh; update IMPLEMENTATION_PLAN.md /
   openapi.yaml references. Final full test + smoke.
```

Rollback at any step is a git revert of that step; steps are independent commits.

## Resolved Questions

- **Removed legacy paths → hard HTTP 404** (not SPA-handled). Django serves `index.html` only for the SPA's own route segments; all other unknown paths 404. See D1. A regression test asserts a former legacy path (e.g. `/campustype/`) returns 404.
- **`templates/base.html` / `base_site.html` → KEEP (revised during implementation).** These were assumed to be legacy-app chrome, but the template chain is `templates/admin/login.html → base_site.html → base.html` — i.e. they are the **Django admin login customization** (HPE/Juniper branding), still reachable at `/admin/login/` after re-rooting. No legacy `ngcn/templates/**` template extends them. They must be kept unless we deliberately revert the admin login to Django's default (see Open Decision below).
- **Coverage gate → none exists.** No `pytest-cov`/`coverage`, no `--cov`/`fail_under` in `pytest.ini`, no `.coveragerc`/`[tool.coverage]`. Deleting legacy tests trips nothing. The only related cleanup is removing the now-stale ruff `per-file-ignores` for `forms.py`/`views.py` in `pyproject.toml`.
